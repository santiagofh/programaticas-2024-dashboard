# %%
"""
=============================================================
DENOMINADORES DE COBERTURA VACUNAL - RM 2024
=============================================================
Fuente    : Nacidos Vivos Inscritos (SRCeI)
Columnas  : DIA_NAC, MES_NAC, ANO_NAC, COMUNA_N, COMUNA
Región    : Metropolitana (COMUNA_N 13000–13999)
t         : 2024
=============================================================
"""

import pandas as pd
from pathlib import Path

# ─────────────────────────────────────────────
# 1. RUTAS
# ─────────────────────────────────────────────
BASE = Path(r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\NACIMIENTO")

RUTAS = {
    2021: BASE / "2021" / "NAC2021.csv",
    2022: BASE / "2022" / "NAC2022.csv",
    2023: BASE / "2023" / "NAC2023.csv",
    2024: BASE / "2024" / "NAC2024.csv",
}

READ_OPTS = dict(encoding="LATIN1", sep=";", low_memory=False)

DIR_OUTPUT = Path(__file__).parent / "output"
DIR_OUTPUT.mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# 2. COHORTES — deben coincidir EXACTAMENTE con
#    las claves y ventanas del numerador v2
# ─────────────────────────────────────────────
COHORTES = {
    # Recién nacido — claves separadas por vacuna
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
    # 2 meses: Hexavalente 1ra, Neumocócica Conjugada 1ra,
    #          Meningocócica Recombinante 1ra
    "Cohorte_2M": (
        "2023-11-01", "2024-10-31",
        ["VACUNA HEXAVALENTE 1RA DOSIS",
         "VACUNA NEUMOCOCICA CONJUGADA 1RA DOSIS",
         "VACUNA MENINGOCOCICA RECOMBINANTE 1RA DOSIS"],
        "Nacidos vivos Nov 2023 – Oct 2024 (2 meses)",
    ),
    # 4 meses: Hexavalente 2da, Neumocócica Conjugada 2da,
    #          Meningocócica Recombinante 2da
    "Cohorte_4M": (
        "2023-09-01", "2024-08-31",
        ["VACUNA HEXAVALENTE 2DA DOSIS",
         "VACUNA NEUMOCOCICA CONJUGADA 2DA DOSIS",
         "VACUNA MENINGOCOCICA RECOMBINANTE 2DA DOSIS"],
        "Nacidos vivos Sep 2023 – Ago 2024 (4 meses)",
    ),
    # 6 meses: Hexavalente 3ra
    "Hexavalente_3d_6m": (
        "2023-07-01", "2024-06-30",
        ["VACUNA HEXAVALENTE 3RA DOSIS"],
        "Nacidos vivos Jul 2023 – Jun 2024 (6 meses)",
    ),
    # 12 meses: SRP 1ra, Neumocócica Conjugada refuerzo,
    #           Meningocócica Conjugada dosis única
    "Cohorte_12M": (
        "2023-01-01", "2023-12-31",
        ["VACUNA SRP (TRIVIRICA) 1RA DOSIS",
         "VACUNA NEUMOCOCICA CONJUGADA REFUERZO",
         "VACUNA MENINGOCOCICA CONJUGADA DOSIS UNICA"],
        "Nacidos vivos Ene–Dic 2023 (12 meses)",
    ),
    # 18 meses: Varicela 1ra, Hepatitis A pediátrica,
    #           Meningocócica Recombinante refuerzo
    "Cohorte_18M": (
        "2022-07-01", "2023-06-30",
        ["VACUNA VARICELA 1RA DOSIS",
         "VACUNA HEPATITIS A PEDIATRICA",
         "VACUNA MENINGOCOCICA RECOMBINANTE REFUERZO"],
        "Nacidos vivos Jul 2022 – Jun 2023 (18 meses)",
    ),
    # 36 meses: SRP 2da, Varicela 2da
    "Cohorte_36M": (
        "2021-01-01", "2021-12-31",
        ["VACUNA SRP (TRIVIRICA) 2DA DOSIS",
         "VACUNA VARICELA 2DA DOSIS"],
        "Nacidos vivos Ene–Dic 2021 (36 meses)",
    ),
    # Refuerzo Hexavalente 18 meses
    "Hexavalente_ref_18m": (
        "2022-07-01", "2023-06-30",
        ["VACUNA HEXAVALENTE REFUERZO"],
        "Nacidos vivos Jul 2022 – Jun 2023 (18 meses — ref Hexa)",
    ),
}

# ─────────────────────────────────────────────
# 3. CARGA — solo RM (COMUNA_N 13000–13999)
# ─────────────────────────────────────────────
def cargar_nacimientos(rutas: dict) -> pd.DataFrame:
    dfs = []
    for anio, ruta in rutas.items():
        print(f"  Cargando {anio}...")
        df = pd.read_csv(ruta, **READ_OPTS,
                         usecols=["DIA_NAC", "MES_NAC", "ANO_NAC",
                                  "COMUNA_N", "COMUNA"])
        df["COMUNA_N"] = pd.to_numeric(df["COMUNA_N"], errors="coerce")
        df = df[df["COMUNA_N"].between(13000, 13999)]
        dfs.append(df)

    nac = pd.concat(dfs, ignore_index=True)
    nac["FECHA_NAC"] = pd.to_datetime(
        dict(year=nac["ANO_NAC"], month=nac["MES_NAC"], day=nac["DIA_NAC"]),
        errors="coerce",
    )
    nac = nac.dropna(subset=["FECHA_NAC", "COMUNA_N"])
    nac["COMUNA_N"] = nac["COMUNA_N"].astype(int)
    print(f"  Total registros válidos RM: {len(nac):,}")
    return nac

# ─────────────────────────────────────────────
# 4. CÁLCULO DE DENOMINADORES POR COMUNA
# ─────────────────────────────────────────────
def calcular_denominadores(nac: pd.DataFrame, cohortes: dict) -> pd.DataFrame:
    comunas = (nac[["COMUNA_N", "COMUNA"]]
               .drop_duplicates()
               .sort_values("COMUNA_N")
               .reset_index(drop=True))

    for clave, (inicio, fin, _, _) in cohortes.items():
        mascara = nac["FECHA_NAC"].between(
            pd.Timestamp(inicio), pd.Timestamp(fin)
        )
        conteo = nac[mascara].groupby("COMUNA_N").size().rename(clave)
        comunas = comunas.merge(conteo, on="COMUNA_N", how="left")
        comunas[clave] = comunas[clave].fillna(0).astype(int)

    return comunas

# ─────────────────────────────────────────────
# 5. RESUMEN REGIONAL
# ─────────────────────────────────────────────
def mostrar_resumen(df: pd.DataFrame, cohortes: dict):
    print("\n" + "=" * 65)
    print("TOTALES REGIONALES — DENOMINADORES RM 2024")
    print("=" * 65)
    for clave, (inicio, fin, vacunas, desc) in cohortes.items():
        total = df[clave].sum()
        print(f"\n  [{', '.join(vacunas)}]")
        print(f"  Cohorte : {desc}")
        print(f"  Total   : {total:,}")
    print("=" * 65)

# ─────────────────────────────────────────────
# 6. EJECUCIÓN
# ─────────────────────────────────────────────
if __name__ == "__main__":

    print("\nCargando archivos de nacimientos (solo RM)...")
    nac = cargar_nacimientos(RUTAS)

    print("\nCalculando denominadores por comuna...")
    denominadores = calcular_denominadores(nac, COHORTES)

    mostrar_resumen(denominadores, COHORTES)

    # ── CSV con claves originales (para join en script 3)
    denominadores.to_csv(
        DIR_OUTPUT / "denominador_nacimientos_2024.csv",
        index=False, encoding="utf-8-sig"
    )

    # ── Excel con descripciones legibles
    col_rename = {k: v[3] for k, v in COHORTES.items()}
    salida_legible = denominadores.rename(columns=col_rename)
    salida_legible.to_excel(
        DIR_OUTPUT / "denominador_nacimientos_2024.xlsx",
        index=False
    )

    print(f"\n✓ Guardado en: {DIR_OUTPUT}")
    print("\nVista previa (primeras 5 comunas):")
    print(denominadores.head().to_string(index=False))
# %%
