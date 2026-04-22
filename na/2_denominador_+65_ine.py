# %%
"""
=============================================================
DENOMINADOR NEUMOCÓCICA POLISACÁRIDA (65 AÑOS) — COMUNA RM 2024
=============================================================
Fuente    : Proyecciones INE 2002-2035 por comuna
Vacuna    : Neumocócica polisacárida
Fórmula   : Proyección INE población de 65 años del año t
            por comuna de residencia
t         : 2024
=============================================================
"""

import pandas as pd
from pathlib import Path

# ─────────────────────────────────────────────
# 1. RUTAS
# ─────────────────────────────────────────────
RUTA_INE = r"data/estimaciones-y-proyecciones-2002-2035-comunas(Est. y Proy. de Pob.csv"

DIR_OUTPUT = Path(__file__).parent / "output"
DIR_OUTPUT.mkdir(exist_ok=True)

T = 2024

# ─────────────────────────────────────────────
# 2. CARGA Y FILTRO
# ─────────────────────────────────────────────
def cargar_ine(ruta: Path, año: int) -> pd.DataFrame:
    print(f"  Cargando archivo INE...")
    df = pd.read_csv(ruta, encoding="latin1", sep=";", low_memory=False)

    print(f"  Columnas encontradas: {list(df.columns[:8])} ...")

    col_region = [c for c in df.columns if "Region" in c and "Nombre" not in c]
    col_comuna = [c for c in df.columns if "Comuna" in c and "Nombre" not in c]

    if col_region:
        df = df[df[col_region[0]] == 13]
    elif col_comuna:
        df = df[df[col_comuna[0]].astype(str).str.startswith("13")]

    print(f"  Registros RM encontrados: {len(df):,}")

    df = df[df["Edad"] == 65].copy()
    print(f"  Registros edad 65 RM: {len(df):,}")

    return df

# ─────────────────────────────────────────────
# 3. CÁLCULO DENOMINADOR POR COMUNA
# ─────────────────────────────────────────────
def calcular_denominador_65(df: pd.DataFrame, año: int) -> pd.DataFrame:
    col_pob = f"Poblacion {año}"

    if col_pob not in df.columns:
        raise ValueError(f"Columna '{col_pob}' no encontrada. "
                         f"Columnas disponibles: {[c for c in df.columns if 'Poblacion' in c]}")

    col_nombre_comuna = "Nombre Comuna"
    col_codigo_comuna = "Comuna"

    resultado = (
        df.groupby([col_codigo_comuna, col_nombre_comuna])[col_pob]
        .sum()
        .reset_index()
        .rename(columns={
            col_pob: "Neumococica_Polisacarida_65",
            col_nombre_comuna: "COMUNA",
            col_codigo_comuna: "COMUNA_N_INE",
        })
    )

    resultado["Neumococica_Polisacarida_65"] = resultado["Neumococica_Polisacarida_65"].astype(int)

    return resultado

# ─────────────────────────────────────────────
# 4. HOMOLOGAR CÓDIGO COMUNA
# ─────────────────────────────────────────────
def homologar_codigo_comuna(df: pd.DataFrame) -> pd.DataFrame:
    df["COMUNA_N"] = pd.to_numeric(df["COMUNA_N_INE"], errors="coerce").astype("Int64")
    df = df.drop(columns=["COMUNA_N_INE"])
    df = df[["COMUNA_N", "COMUNA", "Neumococica_Polisacarida_65"]]
    return df

# ─────────────────────────────────────────────
# 5. RESUMEN REGIONAL
# ─────────────────────────────────────────────
def mostrar_resumen(df: pd.DataFrame, año: int):
    print("\n" + "=" * 65)
    print(f"TOTAL REGIONAL — DENOMINADOR NEUMOCÓCICA POLISACÁRIDA RM {año}")
    print("=" * 65)
    print(f"\n  [VACUNA NEUMOCÓCICA POLISACÁRIDA]")
    print(f"  Cohorte : Proyección INE población 65 años año {año}")
    print(f"  Total   : {df['Neumococica_Polisacarida_65'].sum():,}")
    print("=" * 65)

# ─────────────────────────────────────────────
# 6. EJECUCIÓN
# ─────────────────────────────────────────────
if __name__ == "__main__":

    print(f"\nCargando archivo INE (solo RM, edad 65, año {T})...")
    df_ine = cargar_ine(RUTA_INE, T)

    print(f"\nCalculando denominador por comuna...")
    denominador = calcular_denominador_65(df_ine, T)
    denominador = homologar_codigo_comuna(denominador)

    mostrar_resumen(denominador, T)

    denominador.to_csv(
        DIR_OUTPUT / "denominador_neumococica_65_2024.csv",
        index=False, encoding="utf-8-sig"
    )

    denominador.to_excel(
        DIR_OUTPUT / "denominador_neumococica_65_2024.xlsx",
        index=False
    )

    print(f"\n✓ Guardado en: {DIR_OUTPUT}")
    print("\nVista previa (primeras 5 comunas):")
    print(denominador.head().to_string(index=False))
# %%
