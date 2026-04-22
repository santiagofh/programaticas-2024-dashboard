# %%
"""
=============================================================
DENOMINADOR MATRÍCULA ESCOLAR — dTpa Y VPH - RM 2024
=============================================================
Fuente    : Resumen Matrícula por Curso, Mineduc 2024
            (datos.mineduc.cl / datosabiertos.mineduc.cl)
Vacunas   :
  - dTpa 1° básico  → COD_GRADO = 1
  - VPH  4° básico  → COD_GRADO = 4
  - dTpa 8° básico  → COD_GRADO = 8
Filtros   :
  - Solo enseñanza básica regular (COD_ENSE = 110)
  - Solo Región Metropolitana (COD_REG_RBD = 13)
  - Solo establecimientos activos (ESTADO_ESTAB = 1)
Denominador: suma de N_ALU por COD_COM_RBD y COD_GRADO

Nota metodológica (DEIS v2.0):
  La cobertura escolar se calcula según el lugar donde
  OCURRE la vacunación (COD_COMUNA_OCURR en el numerador),
  NO por residencia. El denominador es la matrícula del
  colegio según su comuna.
=============================================================
"""

import pandas as pd
from pathlib import Path

# ─────────────────────────────────────────────
# 1. RUTAS
# ─────────────────────────────────────────────
RUTA_MINEDUC = Path(r"data/20241003_Resumen_Matrícula_Curso_2024_20240430_PUBL.csv")

DIR_OUTPUT = Path(__file__).parent / "output"
DIR_OUTPUT.mkdir(exist_ok=True)

T = 2024

# ─────────────────────────────────────────────
# 2. CARGA
# ─────────────────────────────────────────────
print("Cargando matrícula Mineduc...")
df = pd.read_csv(
    RUTA_MINEDUC,
    sep=";",           # el archivo Mineduc viene separado por tabulación
    encoding="latin1",
    low_memory=False,
    usecols=[
        "AGNO", "COD_REG_RBD", "COD_COM_RBD", "NOM_COM_RBD",
        "COD_ENSE", "COD_ENSE2", "COD_GRADO",
        "ESTADO_ESTAB", "N_ALU"
    ]
)
print(f"  Registros totales: {len(df):,}")

# ─────────────────────────────────────────────
# 3. FILTROS
# ─────────────────────────────────────────────
df = df[
    (df["COD_REG_RBD"] == 13) &          # Región Metropolitana
    (df["COD_ENSE"] == 110) &             # Enseñanza básica regular
    (df["ESTADO_ESTAB"] == 1) &           # Establecimientos activos
    (df["COD_GRADO"].isin([1, 4, 8]))     # Grados de interés
].copy()

print(f"  Registros RM básica regular (grados 1, 4, 8): {len(df):,}")

# Convertir N_ALU a numérico (puede venir con NA)
df["N_ALU"] = pd.to_numeric(df["N_ALU"], errors="coerce").fillna(0).astype(int)

# ─────────────────────────────────────────────
# 4. AGREGACIÓN POR COMUNA Y GRADO
# ─────────────────────────────────────────────
matricula = (
    df.groupby(["COD_COM_RBD", "NOM_COM_RBD", "COD_GRADO"])["N_ALU"]
    .sum()
    .reset_index()
)

# Pasar a formato wide — una columna por grado
matricula_wide = matricula.pivot_table(
    index=["COD_COM_RBD", "NOM_COM_RBD"],
    columns="COD_GRADO",
    values="N_ALU",
    aggfunc="sum",
    fill_value=0
).reset_index()

# Renombrar columnas al estándar del proyecto
matricula_wide.columns.name = None
matricula_wide = matricula_wide.rename(columns={
    "COD_COM_RBD": "COMUNA_N",
    "NOM_COM_RBD": "COMUNA",
    1: "dTpa_1basico",
    4: "VPH_4basico",
    8: "dTpa_8basico",
})

# Asegurar que existen las tres columnas aunque no haya datos
for col in ["dTpa_1basico", "VPH_4basico", "dTpa_8basico"]:
    if col not in matricula_wide.columns:
        matricula_wide[col] = 0

matricula_wide = matricula_wide[[
    "COMUNA_N", "COMUNA",
    "dTpa_1basico", "VPH_4basico", "dTpa_8basico"
]].sort_values("COMUNA_N").reset_index(drop=True)

# ─────────────────────────────────────────────
# 5. RESUMEN REGIONAL
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print(f"TOTALES REGIONALES — DENOMINADOR MATRÍCULA RM {T}")
print("=" * 65)
print(f"\n  [VACUNA dTpa ESCOLAR — 1° básico]")
print(f"  Total matriculados : {matricula_wide['dTpa_1basico'].sum():,}")
print(f"\n  [VACUNA VPH — 4° básico]")
print(f"  Total matriculados : {matricula_wide['VPH_4basico'].sum():,}")
print(f"\n  [VACUNA dTpa ESCOLAR — 8° básico]")
print(f"  Total matriculados : {matricula_wide['dTpa_8basico'].sum():,}")
print("=" * 65)

# Verificar comunas sin matrícula
sin_data = matricula_wide[
    (matricula_wide["dTpa_1basico"] == 0) |
    (matricula_wide["VPH_4basico"] == 0) |
    (matricula_wide["dTpa_8basico"] == 0)
]
if not sin_data.empty:
    print(f"\n⚠ Comunas con algún grado en 0: {len(sin_data)}")
    print(sin_data.to_string(index=False))

# ─────────────────────────────────────────────
# 6. GUARDAR
# ─────────────────────────────────────────────
matricula_wide.to_csv(
    DIR_OUTPUT / "denominador_matricula_escolar_2024.csv",
    index=False, encoding="utf-8-sig"
)
matricula_wide.to_excel(
    DIR_OUTPUT / "denominador_matricula_escolar_2024.xlsx",
    index=False
)

print(f"\n✓ Guardado en: {DIR_OUTPUT}")
print("\nVista previa (primeras 5 comunas):")
print(matricula_wide.head().to_string(index=False))
# %%
