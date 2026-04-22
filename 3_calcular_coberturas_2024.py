# %%
"""
=============================================================
CÁLCULO DE COBERTURAS VACUNALES - RM 2024
=============================================================
Inputs  : output/*_numerador_rni_2024.csv (último por fecha)
          output/*_denominador_nacimientos_2024.csv
          output/*_denominador_neumococica_65_2024.csv
          output/*_denominador_matricula_escolar_2024.csv
          output/*_denominador_gestantes_2024.csv  (opcional)
Output  : output/YYYY-MM-DD_coberturas_vacunas_2024.csv / .xlsx
t       : 2024 — CORTE FINAL
=============================================================
NOTA JOIN:
  La comuna de cálculo está unificada en COD_COMUNA_JOIN
  (residencia) para todas las vacunas, incluyendo escolares,
  según instrucción de reporte. El numerador ya trae
  COD_COMUNA_JOIN precomputado.
=============================================================
"""

import pandas as pd
from pathlib import Path
from datetime import date
from glob import glob

# ─────────────────────────────────────────────
# 1. RUTAS
# ─────────────────────────────────────────────
DIR_OUTPUT = Path(__file__).parent / "output"

RUN_DATE = date.today().isoformat()

def latest_dated_file(dir_path: Path, base_name: str) -> Path:
    pattern = str(dir_path / f"????-??-??_{base_name}")
    candidates = sorted(glob(pattern))
    if candidates:
        return Path(candidates[-1])
    legacy = dir_path / base_name
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"No se encontró archivo para {base_name} en {dir_path}")

ruta_numerador   = latest_dated_file(DIR_OUTPUT, "numerador_rni_2024.csv")
ruta_denominador = latest_dated_file(DIR_OUTPUT, "denominador_nacimientos_2024.csv")
ruta_denom_65    = latest_dated_file(DIR_OUTPUT, "denominador_neumococica_65_2024.csv")
ruta_matricula   = latest_dated_file(DIR_OUTPUT, "denominador_matricula_escolar_2024.csv")
ruta_gestantes   = DIR_OUTPUT / "denominador_gestantes_2024.csv"   # opcional (fallback)

# ─────────────────────────────────────────────
# 2. CARGA
# ─────────────────────────────────────────────
print("Cargando numerador...")
numerador = pd.read_csv(ruta_numerador, encoding="utf-8-sig")

print("Cargando denominador nacimientos...")
denominador_wide = pd.read_csv(ruta_denominador, encoding="utf-8-sig")

print("Cargando denominador INE 65 años...")
denom_65 = pd.read_csv(ruta_denom_65, encoding="utf-8-sig")

print("Cargando denominador matrícula escolar...")
matricula = pd.read_csv(ruta_matricula, encoding="utf-8-sig")

# Gestantes: solo si el archivo existe
denom_gestantes = None
try:
    ruta_gestantes = latest_dated_file(DIR_OUTPUT, "denominador_gestantes_2024.csv")
    print("Cargando denominador gestantes...")
    denom_gestantes = pd.read_csv(ruta_gestantes, encoding="utf-8-sig")
except FileNotFoundError:
    if (DIR_OUTPUT / "denominador_gestantes_2024.csv").exists():
        ruta_gestantes = DIR_OUTPUT / "denominador_gestantes_2024.csv"
        print("Cargando denominador gestantes (legado)...")
        denom_gestantes = pd.read_csv(ruta_gestantes, encoding="utf-8-sig")
    else:
        print("ℹ  denominador_gestantes_2024.csv no encontrado — dTpa gestantes se omite del cálculo")

# ─────────────────────────────────────────────
# 3. CLAVE DE JOIN
#    COD_COMUNA_JOIN ya viene precomputado en el numerador:
#      - vacunas escolares → COD_COMUNA_OCURR
#      - resto             → COD_COMUNA_RESID
# ─────────────────────────────────────────────
numerador["CLAVE_DEN"] = numerador["CLAVE_DENOMINADOR"]

print(f"\nClaves en numerador: {sorted(numerador['CLAVE_DEN'].unique())}")

# ─────────────────────────────────────────────
# 4. CONSTRUIR DENOMINADOR UNIFICADO (long)
# ─────────────────────────────────────────────

# 4a. Nacimientos wide → long
cols_cohorte = [c for c in denominador_wide.columns if c not in ("COMUNA_N", "COMUNA")]
denominador_long = denominador_wide.melt(
    id_vars=["COMUNA_N", "COMUNA"],
    value_vars=cols_cohorte,
    var_name="CLAVE_DEN",
    value_name="POBLACION_OBJETIVO",
)[["COMUNA_N", "CLAVE_DEN", "POBLACION_OBJETIVO"]]

# 4b. INE 65 años
denom_65_long = (
    denom_65
    .assign(CLAVE_DEN="Neumococica_Polisacarida_65")
    .rename(columns={"Neumococica_Polisacarida_65": "POBLACION_OBJETIVO"})
    [["COMUNA_N", "CLAVE_DEN", "POBLACION_OBJETIVO"]]
)

# 4c. Matrícula escolar wide → long
# VPH_5basico: solo incluir si existe la columna (solo aplica en 2024)
cols_matricula = ["dTpa_1basico", "VPH_4basico", "dTpa_8basico"]
if "VPH_5basico" in matricula.columns:
    cols_matricula.append("VPH_5basico")

matricula_long = matricula.melt(
    id_vars=["COMUNA_N", "COMUNA"],
    value_vars=cols_matricula,
    var_name="CLAVE_DEN",
    value_name="POBLACION_OBJETIVO",
)[["COMUNA_N", "CLAVE_DEN", "POBLACION_OBJETIVO"]]

# 4d. Gestantes (si existe)
partes = [denominador_long, denom_65_long, matricula_long]

if denom_gestantes is not None:
    denom_gest_long = (
        denom_gestantes
        .assign(CLAVE_DEN="dTpa_Gestantes")
        .rename(columns={"GESTANTES_ESTIMADAS": "POBLACION_OBJETIVO"})
        [["COMUNA_N", "CLAVE_DEN", "POBLACION_OBJETIVO"]]
    )
    partes.append(denom_gest_long)

# 4e. Apilar todo
denominador_long = pd.concat(partes, ignore_index=True)

print(f"Claves en denominador: {sorted(denominador_long['CLAVE_DEN'].unique())}")

# Mapa de comunas para reportar "comuna de cálculo"
def build_comuna_map(*dfs):
    mapa = {}
    for d in dfs:
        if d is None:
            continue
        if "COMUNA_N" not in d.columns or "COMUNA" not in d.columns:
            continue
        tmp = d[["COMUNA_N", "COMUNA"]].copy()
        tmp["COMUNA_N"] = pd.to_numeric(tmp["COMUNA_N"], errors="coerce")
        tmp = tmp.dropna(subset=["COMUNA_N", "COMUNA"])
        for _, row in tmp.iterrows():
            code = int(row["COMUNA_N"])
            name = str(row["COMUNA"]).strip()
            if not name:
                continue
            name_is_numeric = name.isdigit()
            if code not in mapa:
                mapa[code] = name
            else:
                # Si lo actual es numérico y el nuevo es texto, preferir texto
                if mapa[code].isdigit() and not name_is_numeric:
                    mapa[code] = name
    return mapa

comuna_map = build_comuna_map(denominador_wide, denom_65, matricula, denom_gestantes)

# Verificar cobertura de claves
claves_num = set(numerador["CLAVE_DEN"].unique())
claves_den = set(denominador_long["CLAVE_DEN"].unique())
sin_den = claves_num - claves_den
if sin_den:
    print(f"\n⚠ Claves del numerador SIN denominador: {sin_den}")
else:
    print("\n✓ Todas las claves del numerador tienen denominador")

# ─────────────────────────────────────────────
# 5. JOIN numerador + denominador
#    Usa COD_COMUNA_JOIN (ocurrencia para escolares, residencia para el resto)
# ─────────────────────────────────────────────
coberturas = numerador.merge(
    denominador_long[["COMUNA_N", "CLAVE_DEN", "POBLACION_OBJETIVO"]],
    left_on=["COD_COMUNA_JOIN", "CLAVE_DEN"],
    right_on=["COMUNA_N", "CLAVE_DEN"],
    how="left",
).drop(columns="COMUNA_N")

# ─────────────────────────────────────────────
# 6. CÁLCULO DE COBERTURA
# ─────────────────────────────────────────────
coberturas["PORC_COBERTURA"] = (
    coberturas["VACUNAS_ADMINISTRADAS"] /
    coberturas["POBLACION_OBJETIVO"].replace(0, pd.NA) * 100
).round(1)

coberturas["PORC_COBERTURA"] = coberturas["PORC_COBERTURA"].fillna(0)

sin_denom = coberturas[coberturas["POBLACION_OBJETIVO"].isna()]
if not sin_denom.empty:
    print(f"\n⚠ Registros sin denominador: {len(sin_denom)}")
    print(sin_denom[["COD_COMUNA_JOIN", "VACUNA_DASHBOARD",
                      "CLAVE_DENOMINADOR"]].drop_duplicates().to_string(index=False))

# ─────────────────────────────────────────────
# 7. ORDEN Y FORMATO FINAL
# ─────────────────────────────────────────────
coberturas = coberturas[[
    "COD_COMUNA_JOIN",
    "VACUNA_DASHBOARD",
    "CLAVE_DENOMINADOR",
    "VACUNAS_ADMINISTRADAS",
    "POBLACION_OBJETIVO",
    "PORC_COBERTURA",
]].sort_values(["COD_COMUNA_JOIN", "VACUNA_DASHBOARD"]).reset_index(drop=True)

# Añadir comuna de cálculo (según COD_COMUNA_JOIN)
coberturas.insert(1, "COMUNA_CALCULO", coberturas["COD_COMUNA_JOIN"].map(comuna_map))

# ─────────────────────────────────────────────
# 8. RESUMEN REGIONAL
#    El numerador se suma desde coberturas.
#    El denominador se obtiene directamente de denominador_long
#    (suma única por clave, sin duplicaciones por el join).
# ─────────────────────────────────────────────

# 8a. Suma de vacunados por vacuna
num_regional = (
    coberturas
    .groupby(["VACUNA_DASHBOARD", "CLAVE_DENOMINADOR"], as_index=False)
    .agg(VACUNAS_ADMINISTRADAS=("VACUNAS_ADMINISTRADAS", "sum"))
)

# 8b. Suma de población objetivo por clave (una vez por commune, sin duplicar)
den_regional = (
    denominador_long
    .groupby("CLAVE_DEN", as_index=False)
    .agg(POBLACION_OBJETIVO=("POBLACION_OBJETIVO", "sum"))
    .rename(columns={"CLAVE_DEN": "CLAVE_DENOMINADOR"})
)

# 8c. Join y cálculo
resumen_regional = num_regional.merge(den_regional, on="CLAVE_DENOMINADOR", how="left")
resumen_regional["PORC_COBERTURA"] = (
    resumen_regional["VACUNAS_ADMINISTRADAS"] /
    resumen_regional["POBLACION_OBJETIVO"].replace(0, pd.NA) * 100
).round(1)
resumen_regional["PORC_COBERTURA"] = resumen_regional["PORC_COBERTURA"].fillna(0)

print("\n" + "=" * 70)
print(f"  COBERTURAS VACUNALES RM — AÑO EVALUADO 2024 (CORTE FINAL)")
print("=" * 70)
print(resumen_regional[["VACUNA_DASHBOARD", "VACUNAS_ADMINISTRADAS",
                         "POBLACION_OBJETIVO", "PORC_COBERTURA"]].to_string(index=False))
print("=" * 70)

print("\n=== ALERTAS ===")
for _, row in resumen_regional.iterrows():
    if row["PORC_COBERTURA"] > 105:
        print(f"⚠ SUPERA 105%: {row['VACUNA_DASHBOARD']} → {row['PORC_COBERTURA']}%")
    if row["PORC_COBERTURA"] < 20:
        print(f"ℹ MUY BAJA: {row['VACUNA_DASHBOARD']} → {row['PORC_COBERTURA']}% "
              f"(verificar si vacuna fue incorporada recientemente al PNI o si hay pocos datos)")

# ─────────────────────────────────────────────
# 9. GUARDAR — CSV + Excel con dos pestañas
# ─────────────────────────────────────────────
nombre_cob_csv = f"{RUN_DATE}_coberturas_vacunas_2024.csv"
nombre_cob_xlsx = f"{RUN_DATE}_coberturas_vacunas_2024.xlsx"

coberturas.to_csv(
    DIR_OUTPUT / nombre_cob_csv,
    index=False, encoding="utf-8-sig"
)

with pd.ExcelWriter(
    DIR_OUTPUT / nombre_cob_xlsx, engine="openpyxl"
) as writer:
    coberturas.to_excel(writer, sheet_name="Por_Comuna", index=False)
    resumen_regional.to_excel(writer, sheet_name="Resumen_Regional", index=False)

print(f"\n✓ Guardado en: {DIR_OUTPUT}")
print(f"  - {nombre_cob_csv}")
print(f"  - {nombre_cob_xlsx}  (pestañas: Por_Comuna / Resumen_Regional)")
# %%
