# %%
"""
=============================================================
DENOMINADORES DE COBERTURA VACUNAL - RM 2024
=============================================================
Fuentes   :
  A) Nacidos Vivos Inscritos (SRCeI)        → vacunas infantiles
  B) Proyecciones INE 2002-2035 por comuna  → Neumocócica Polisacárida 65 años
  C) Matrícula Mineduc 2024 por curso       → dTpa escolar y VPH

Outputs   :
  output/denominador_nacimientos_2024.csv
  output/denominador_neumococica_65_2024.csv
  output/denominador_matricula_escolar_2024.csv

t         : 2024
Región    : Metropolitana
=============================================================
"""

import pandas as pd
from pathlib import Path
from datetime import date

# ─────────────────────────────────────────────
# 1. RUTAS
# ─────────────────────────────────────────────
# — CONFIGURAR RUTA LOCAL —
# RUTA_BASE_NAC = Path("ruta/a/tus/datos/NACIMIENTO")
# Ejemplo local:
# RUTA_BASE_NAC = Path(r"C:\Users\...\DATA\NACIMIENTO")
RUTA_BASE_NAC = Path("data/nacimientos")
RUTA_INE  = Path(r"data/estimaciones-y-proyecciones-2002-2035-comunas(Est. y Proy. de Pob.csv")
# RUTA_MIN  = Path(r"data/20241003_Resumen_Matrícula_Curso_2024_20240430_PUBL.csv")  # LEGACY
RUTA_POB_ESC = Path(r"data/Poblacion Escolar 2024.xlsx")  # Población Escolar MINEDUC (pre-calculada)

RUTAS_NAC = {
    2021: RUTA_BASE_NAC / "2021" / "NAC2021.csv",
    2022: RUTA_BASE_NAC / "2022" / "NAC2022.csv",
    2023: RUTA_BASE_NAC / "2023" / "NAC2023.csv",
    2024: RUTA_BASE_NAC / "2024" / "NAC2024.csv",
}

DIR_OUTPUT = Path(__file__).parent / "output"
DIR_OUTPUT.mkdir(exist_ok=True)

T = 2024
RUN_DATE = date.today().isoformat()

# ═══════════════════════════════════════════════════════
# A) DENOMINADOR NACIMIENTOS — vacunas infantiles/lactantes
# ═══════════════════════════════════════════════════════

COHORTES_NAC = {
    "BCG_RN": (
        "2024-01-01", "2024-12-31",
        ["VACUNA BCG"],
        "Nacidos vivos Ene–Dic 2024 (RN)",
    ),
    "HepB_RN": (
        "2024-01-01", "2024-12-31",
        ["VACUNA HEPATITIS B RN"],
        "Nacidos vivos Ene–Dic 2024 (RN)",
    ),
    "Cohorte_2M": (
        "2023-11-01", "2024-10-31",
        ["VACUNA HEXAVALENTE 1RA DOSIS",
         "VACUNA NEUMOCOCICA CONJUGADA 1RA DOSIS",
         "VACUNA MENINGOCOCICA RECOMBINANTE 1RA DOSIS"],
        "Nacidos vivos Nov 2023 – Oct 2024 (2 meses)",
    ),
    "Cohorte_4M": (
        "2023-09-01", "2024-08-31",
        ["VACUNA HEXAVALENTE 2DA DOSIS",
         "VACUNA NEUMOCOCICA CONJUGADA 2DA DOSIS",
         "VACUNA MENINGOCOCICA RECOMBINANTE 2DA DOSIS"],
        "Nacidos vivos Sep 2023 – Ago 2024 (4 meses)",
    ),
    "Hexavalente_3d_6m": (
        "2023-07-01", "2024-06-30",
        ["VACUNA HEXAVALENTE 3RA DOSIS"],
        "Nacidos vivos Jul 2023 – Jun 2024 (6 meses)",
    ),
    "Cohorte_12M": (
        "2023-01-01", "2023-12-31",
        ["VACUNA SRP (TRIVIRICA) 1RA DOSIS",
         "VACUNA NEUMOCOCICA CONJUGADA REFUERZO",
         "VACUNA MENINGOCOCICA CONJUGADA DOSIS UNICA"],
        "Nacidos vivos Ene–Dic 2023 (12 meses)",
    ),
    "Cohorte_18M": (
        "2022-07-01", "2023-06-30",
        ["VACUNA VARICELA 1RA DOSIS",
         "VACUNA HEPATITIS A PEDIATRICA",
         "VACUNA MENINGOCOCICA RECOMBINANTE REFUERZO"],
        "Nacidos vivos Jul 2022 – Jun 2023 (18 meses)",
    ),
    "Cohorte_36M": (
        "2021-01-01", "2021-12-31",
        ["VACUNA SRP (TRIVIRICA) 2DA DOSIS",
         "VACUNA VARICELA 2DA DOSIS"],
        "Nacidos vivos Ene–Dic 2021 (36 meses)",
    ),
    "Hexavalente_ref_18m": (
        "2022-07-01", "2023-06-30",
        ["VACUNA HEXAVALENTE REFUERZO"],
        "Nacidos vivos Jul 2022 – Jun 2023 (18 meses — ref Hexa)",
    ),
}

print("\n" + "=" * 65)
print("A) DENOMINADOR NACIMIENTOS")
print("=" * 65)

dfs_nac = []
for anio, ruta in RUTAS_NAC.items():
    print(f"  Cargando {anio}...")
    df_n = pd.read_csv(ruta, encoding="LATIN1", sep=";", low_memory=False,
                       usecols=["DIA_NAC", "MES_NAC", "ANO_NAC", "COMUNA_N", "COMUNA"])
    df_n["COMUNA_N"] = pd.to_numeric(df_n["COMUNA_N"], errors="coerce")
    df_n = df_n[df_n["COMUNA_N"].between(13000, 13999)]
    dfs_nac.append(df_n)

nac = pd.concat(dfs_nac, ignore_index=True)
nac["FECHA_NAC"] = pd.to_datetime(
    dict(year=nac["ANO_NAC"], month=nac["MES_NAC"], day=nac["DIA_NAC"]),
    errors="coerce",
)
nac = nac.dropna(subset=["FECHA_NAC", "COMUNA_N"])
nac["COMUNA_N"] = nac["COMUNA_N"].astype(int)
print(f"  Total registros válidos RM: {len(nac):,}")

comunas = (nac[["COMUNA_N", "COMUNA"]]
           .drop_duplicates()
           .sort_values("COMUNA_N")
           .reset_index(drop=True))

for clave, (inicio, fin, _, _) in COHORTES_NAC.items():
    mascara = nac["FECHA_NAC"].between(pd.Timestamp(inicio), pd.Timestamp(fin))
    conteo = nac[mascara].groupby("COMUNA_N").size().rename(clave)
    comunas = comunas.merge(conteo, on="COMUNA_N", how="left")
    comunas[clave] = comunas[clave].fillna(0).astype(int)

print("\n  TOTALES REGIONALES:")
for clave, (ini, fin, vacs, desc) in COHORTES_NAC.items():
    print(f"  {desc}: {comunas[clave].sum():,}")

nombre_nac_csv = f"{RUN_DATE}_denominador_nacimientos_2024.csv"
nombre_nac_xlsx = f"{RUN_DATE}_denominador_nacimientos_2024.xlsx"
comunas.to_csv(DIR_OUTPUT / nombre_nac_csv, index=False, encoding="utf-8-sig")
col_rename = {k: v[3] for k, v in COHORTES_NAC.items()}
comunas.rename(columns=col_rename).to_excel(DIR_OUTPUT / nombre_nac_xlsx, index=False)
print(f"\n  OK denominador_nacimientos_2024.csv guardado ({len(comunas)} comunas)")

# ═══════════════════════════════════════════════════════
# B) DENOMINADOR INE 65 AÑOS — Neumocócica Polisacárida
# ═══════════════════════════════════════════════════════

print("\n" + "=" * 65)
print("B) DENOMINADOR INE 65 AÑOS")
print("=" * 65)

df_ine = pd.read_csv(RUTA_INE, encoding="latin1", sep=";", low_memory=False)
print(f"  Columnas encontradas: {list(df_ine.columns[:8])} ...")

col_region = [c for c in df_ine.columns if "Region" in c and "Nombre" not in c]
col_comuna = [c for c in df_ine.columns if "Comuna" in c and "Nombre" not in c]

if col_region:
    df_ine = df_ine[df_ine[col_region[0]] == 13]
elif col_comuna:
    df_ine = df_ine[df_ine[col_comuna[0]].astype(str).str.startswith("13")]

df_ine = df_ine[df_ine["Edad"] == 65].copy()
print(f"  Registros RM edad 65: {len(df_ine):,}")

col_pob = f"Poblacion {T}"
if col_pob not in df_ine.columns:
    raise ValueError(f"Columna '{col_pob}' no encontrada en INE.")

col_nombre_comuna = "Nombre Comuna"
col_codigo_comuna = "Comuna"

denom_65 = (
    df_ine.groupby([col_codigo_comuna, col_nombre_comuna])[col_pob]
    .sum().reset_index()
    .rename(columns={
        col_pob: "Neumococica_Polisacarida_65",
        col_nombre_comuna: "COMUNA",
        col_codigo_comuna: "COMUNA_N_INE",
    })
)
denom_65["Neumococica_Polisacarida_65"] = denom_65["Neumococica_Polisacarida_65"].astype(int)
denom_65["COMUNA_N"] = pd.to_numeric(denom_65["COMUNA_N_INE"], errors="coerce").astype("Int64")
denom_65 = denom_65[["COMUNA_N", "COMUNA", "Neumococica_Polisacarida_65"]]

print(f"  Total RM 65 años: {denom_65['Neumococica_Polisacarida_65'].sum():,}")

nombre_65_csv = f"{RUN_DATE}_denominador_neumococica_65_2024.csv"
nombre_65_xlsx = f"{RUN_DATE}_denominador_neumococica_65_2024.xlsx"
denom_65.to_csv(DIR_OUTPUT / nombre_65_csv, index=False, encoding="utf-8-sig")
denom_65.to_excel(DIR_OUTPUT / nombre_65_xlsx, index=False)
print(f"  OK denominador_neumococica_65_2024.csv guardado ({len(denom_65)} comunas)")

# ═══════════════════════════════════════════════════════
# Mapeo comuna nombre → código (RM)
# ═══════════════════════════════════════════════════════

COMUNA_MAP = {
    # Provincia de Santiago (13101-13132)
    "Santiago": 13101, "Cerrillos": 13102, "Cerro Navia": 13103,
    "Conchalí": 13104, "El Bosque": 13105, "Estación Central": 13106,
    "Huechuraba": 13107, "Independencia": 13108, "La Cisterna": 13109,
    "La Florida": 13110, "La Granja": 13111, "La Pintana": 13112,
    "La Reina": 13113, "Las Condes": 13114, "Lo Barnechea": 13115,
    "Lo Espejo": 13116, "Lo Prado": 13117, "Macul": 13118,
    "Maipú": 13119, "Ñuñoa": 13120, "Pedro Aguirre Cerda": 13121,
    "Peñalolén": 13122, "Providencia": 13123, "Pudahuel": 13124,
    "Quilicura": 13125, "Quinta Normal": 13126, "Recoleta": 13127,
    "Renca": 13128, "San Joaquín": 13129, "San Miguel": 13130,
    "San Ramón": 13131, "Vitacura": 13132,
    # Provincia de Cordillera (13201-13203)
    "Puente Alto": 13201, "Pirque": 13202, "San José de Maipo": 13203,
    # Provincia de Chacabuco (13301-13303)
    "Colina": 13301, "Lampa": 13302, "Tiltil": 13303,
    # Provincia de Maipo (13401-13404)
    "San Bernardo": 13401, "Buin": 13402, "Calera De Tango": 13403,
    "Paine": 13404,
    # Provincia de Melipilla (13501-13505)
    "Melipilla": 13501, "Alhué": 13502, "Curacavi": 13503,
    "María Pinto": 13504, "San Pedro": 13505,
    # Provincia de Talagante (13601-13605)
    "Talagante": 13601, "El Monte": 13602, "Isla De Maipo": 13603,
    "Padre Hurtado": 13604, "Peñaflor": 13605,
}

# ═══════════════════════════════════════════════════════
# C) DENOMINADOR MATRÍCULA ESCOLAR — dTpa y VPH
#    Fuente: Población Escolar 2024 (pre-calculada por MINEDUC)
# ═══════════════════════════════════════════════════════

print("\n" + "=" * 65)
print("C) DENOMINADOR MATRÍCULA ESCOLAR (Población Escolar 2024)")
print("=" * 65)

df_esc = pd.read_excel(RUTA_POB_ESC, header=None)
print(f"  Filas: {len(df_esc)}")

# Estructura del Excel:
#   Row(iloc 5) = "Region Metropolitana" (total regional)
#   Rows(iloc 6-57) = 52 comunas RM
#   Col 0 = nombre comuna | Col 1-4 = MATRICULA 1°/4°/5°/8° básico
data = df_esc.iloc[6:58, [0, 1, 2, 3, 4]].copy()
data.columns = ["COMUNA", "dTpa_1basico", "VPH_4basico", "VPH_5basico", "dTpa_8basico"]
data = data.dropna(subset=["COMUNA"])
data["COMUNA"] = data["COMUNA"].astype(str).str.strip()

for col in ["dTpa_1basico", "VPH_4basico", "VPH_5basico", "dTpa_8basico"]:
    data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0).astype(int)

data["COMUNA_N"] = data["COMUNA"].map(COMUNA_MAP)
unmapped = data[data["COMUNA_N"].isna()]["COMUNA"].unique()
if len(unmapped):
    print(f"  ⚠ Comunas sin mapear: {unmapped}")
data = data.dropna(subset=["COMUNA_N"])
data["COMUNA_N"] = data["COMUNA_N"].astype(int)

mat_wide = data[["COMUNA_N", "COMUNA", "dTpa_1basico", "VPH_4basico", "VPH_5basico", "dTpa_8basico"]]
mat_wide = mat_wide.sort_values("COMUNA_N").reset_index(drop=True)

print(f"  dTpa 1° básico   : {mat_wide['dTpa_1basico'].sum():,}")
print(f"  VPH  4° básico   : {mat_wide['VPH_4basico'].sum():,}")
print(f"  VPH  5° básico   : {mat_wide['VPH_5basico'].sum():,}")
print(f"  dTpa 8° básico   : {mat_wide['dTpa_8basico'].sum():,}")

nombre_mat_csv = f"{RUN_DATE}_denominador_matricula_escolar_2024.csv"
nombre_mat_xlsx = f"{RUN_DATE}_denominador_matricula_escolar_2024.xlsx"
mat_wide.to_csv(DIR_OUTPUT / nombre_mat_csv, index=False, encoding="utf-8-sig")
mat_wide.to_excel(DIR_OUTPUT / nombre_mat_xlsx, index=False)
print(f"  OK denominador_matricula_escolar_2024.csv guardado ({len(mat_wide)} comunas)")

# ═══════════════════════════════════════════════════════
# RESUMEN FINAL
# ═══════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("OK TODOS LOS DENOMINADORES GUARDADOS EN: output/")
print("=" * 65)
print(f"  {nombre_nac_csv}")
print(f"  {nombre_65_csv}")
print(f"  {nombre_mat_csv}")
# %%
