# %%
"""
=============================================================
NUMERADOR COBERTURA VACUNAL - RM 2024
=============================================================
Metodología : DEIS v2.0 (Dic-2025)
Numerador   : vacunados cohorte en año t + t+1 + t+2
Región      : Metropolitana
t           : 2024
=============================================================
VACUNAS INCLUIDAS:
  Infantil/Lactante : BCG, HepB RN, Hexavalente (1-2-3-ref),
                      Neumocócica Conjugada (1-2-ref),
                      Meningocócica Recombinante (1-2-ref),
                      Meningocócica Conjugada, SRP (1-2),
                      Hepatitis A, Varicela (1-2)
  Escolar           : dTpa 1° básico, dTpa 8° básico, VPH 4° básico
  Gestantes         : dTpa gestantes (≥28 sem gestación)
  Personas mayores  : Neumocócica Polisacárida (65 años)

NOTA METODOLÓGICA COBERTURAS ESCOLARES:
  La cobertura escolar se calcula por lugar de OCURRENCIA
  (COD_COMUNA_OCURR), no por residencia. Por eso el output
  incluye COD_COMUNA_JOIN que es:
    - COD_COMUNA_OCURR → vacunas escolares
    - COD_COMUNA_RESID → todas las demás
=============================================================
"""

import pandas as pd
import numpy as np
import os
from glob import glob
from pathlib import Path

# ─────────────────────────────────────────────
# 1. RUTAS
# ─────────────────────────────────────────────
DIR_OUTPUT = Path(__file__).parent / "output"
DIR_OUTPUT.mkdir(exist_ok=True)

T = 2024

RUTAS_AÑOS = {
    T:   r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\RNI\PROGRAMATICAS\2024",
    T+1: r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\RNI\PROGRAMATICAS\2025",
    T+2: r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\RNI\PROGRAMATICAS\2026",
}

# ─────────────────────────────────────────────
# 2. VENTANAS DE COHORTE (fijas para t=2024)
# ─────────────────────────────────────────────
COHORTES = {
    "RN":  (f"{T}-01-01",   f"{T}-12-31"),         # Recién nacido
    "2M":  (f"{T-1}-11-01", f"{T}-10-31"),          # 2 meses
    "4M":  (f"{T-1}-09-01", f"{T}-08-31"),          # 4 meses
    "6M":  (f"{T-1}-07-01", f"{T}-06-30"),          # 6 meses
    "12M": (f"{T-1}-01-01", f"{T-1}-12-31"),        # 12 meses
    "18M": (f"{T-2}-07-01", f"{T-1}-06-30"),        # 18 meses
    "36M": (f"{T-3}-01-01", f"{T-3}-12-31"),        # 36 meses
}

# Ventanas de nacimiento para grados escolares 2024
# 1° básico: nacidos ~2017 (6-7 años en 2024)
# 4° básico: nacidos ~2014 (9-10 años en 2024)
# 8° básico: nacidos ~2010 (13-14 años en 2024)
COHORTES_ESCOLAR = {
    "1basico": ("2016-01-01", "2018-06-30"),
    "4basico": ("2013-01-01", "2015-06-30"),
    "8basico": ("2009-01-01", "2011-06-30"),
}

# ─────────────────────────────────────────────
# 3. COLUMNAS
# ─────────────────────────────────────────────
COLUMNAS = [
    "RUN", "PASAPORTE", "OTRO",
    "ID_INMUNIZACION",
    "COD_COMUNA_OCURR", "COMUNA_OCURR",
    "COD_COMUNA_RESID", "COMUNA_RESIDENCIA",
    "NOMBRE_VACUNA",
    "CRITERIO_ELEGIBILIDAD",
    "DOSIS",
    "VACUNA_ADMINISTRADA",
    "REGISTRO_ELIMINADO",
    "SEXO",
    "FECHA_NACIMIENTO",
    "FECHA_INMUNIZACION",
]

# ─────────────────────────────────────────────
# 4. CARGA MULTI-AÑO
# ─────────────────────────────────────────────
def cargar_y_filtrar(path):
    df = pd.read_csv(
        path, encoding="LATIN1", sep="|",
        usecols=COLUMNAS, low_memory=False,
    )
    df = df[
        df["COD_COMUNA_RESID"].between(13000, 13999) &
        (df["VACUNA_ADMINISTRADA"] == "SI") &
        (df["REGISTRO_ELIMINADO"] == "NO") &
        (df["CRITERIO_ELEGIBILIDAD"] != "EPRO") &
        (~df["DOSIS"].str.contains("EPRO", case=False, na=False))
    ]
    duplicados = df[df.duplicated("ID_INMUNIZACION", keep=False)]
    if len(duplicados) > 0:
        print(f"    ⚠ Duplicados ID_INM: {len(duplicados)}")
    df = df.drop_duplicates("ID_INMUNIZACION")
    return df

AÑOS_DISPONIBLES = []
lista_df = []

print("=" * 55)
print(f"  CARGANDO DATOS PARA COHORTE t={T}")
print("=" * 55)

for anio, ruta in RUTAS_AÑOS.items():
    archivos = glob(os.path.join(ruta, "*.csv"))
    archivos = [f for f in archivos if not os.path.basename(f).startswith("~")]

    if not os.path.exists(ruta):
        print(f"  [{anio}] ⏭  Carpeta no encontrada — se omite")
        continue
    if not archivos:
        print(f"  [{anio}] ⏭  Carpeta vacía — se omite")
        continue

    print(f"\n  [{anio}] ✓ {len(archivos)} archivo(s) encontrado(s)")
    for archivo in archivos:
        print(f"    Leyendo {os.path.basename(archivo)}...")
        lista_df.append(cargar_y_filtrar(archivo))
    AÑOS_DISPONIBLES.append(anio)

if not lista_df:
    raise FileNotFoundError("No se encontraron archivos CSV en ninguna carpeta.")

df = pd.concat(lista_df, ignore_index=True)
print(f"\n  Años cargados   : {AÑOS_DISPONIBLES}")
print(f"  Registros RM    : {len(df):,}")

CORTE = {1: "PRIMER CORTE PRELIMINAR",
         2: "SEGUNDO CORTE PRELIMINAR",
         3: "CORTE FINAL"}.get(len(AÑOS_DISPONIBLES), f"{len(AÑOS_DISPONIBLES)} años")

# ─────────────────────────────────────────────
# 5. FECHAS Y FILTRO AÑOS VÁLIDOS
# ─────────────────────────────────────────────
df["FECHA_NACIMIENTO"]   = pd.to_datetime(df["FECHA_NACIMIENTO"],   errors="coerce")
df["FECHA_INMUNIZACION"] = pd.to_datetime(df["FECHA_INMUNIZACION"], errors="coerce")

AÑOS_VALIDOS = [T, T+1, T+2]
df = df[df["FECHA_INMUNIZACION"].dt.year.isin(AÑOS_VALIDOS)].copy()
print(f"  Registros en años válidos ({AÑOS_VALIDOS}): {len(df):,}")

# ─────────────────────────────────────────────
# 6. NORMALIZACIÓN DOSIS
# ─────────────────────────────────────────────
DOSIS_MAP = {
    "0.05 ml":                     "DOSIS_UNICA",
    "0.1 ml":                      "DOSIS_UNICA",
    "Única":                       "DOSIS_UNICA",
    "Única (no programática)":     "DOSIS_UNICA",
    "Única (50 mg)":               "DOSIS_UNICA",
    "1° Dosis":                    "1RA_DOSIS",
    "1° dosis":                    "1RA_DOSIS",
    "1º dosis":                    "1RA_DOSIS",
    "1°dosis":                     "1RA_DOSIS",
    "1ra dosis (programática)":    "1RA_DOSIS",
    "2° Dosis":                    "2DA_DOSIS",
    "2° dosis":                    "2DA_DOSIS",
    "2º dosis":                    "2DA_DOSIS",
    "2°dosis":                     "2DA_DOSIS",
    "2da dosis (programatica)":    "2DA_DOSIS",
    "3° Dosis":                    "3RA_DOSIS",
    "3° dosis":                    "3RA_DOSIS",
    "3º dosis, prematuros":        "3RA_DOSIS",
    "4° Dosis":                    "4TA_DOSIS",
    "4° dosis":                    "4TA_DOSIS",
    "5° Dosis":                    "5TA_DOSIS",
    "1er Refuerzo":                "REFUERZO",
    "1er refuerzo":                "REFUERZO",
    "1er refuerzo (programática)": "REFUERZO",
    "1er refuerzo, 12 meses":      "REFUERZO",
    "1°  Refuerzo":                "REFUERZO",
    "1° Refuerzo":                 "REFUERZO",
    "Refuerzo":                    "REFUERZO",
}
df["DOSIS_NORM"] = df["DOSIS"].map(DOSIS_MAP)

no_mapeadas = df["DOSIS"][df["DOSIS_NORM"].isna()].value_counts()
if not no_mapeadas.empty:
    print("\n⚠ DOSIS sin mapear (revisar):")
    print(no_mapeadas.to_string())

# ─────────────────────────────────────────────
# 7. NORMALIZACIÓN NOMBRE VACUNA
# ─────────────────────────────────────────────
df["VAC"] = (
    df["NOMBRE_VACUNA"]
    .str.upper()
    .str.replace(r"\(.*?\)", "", regex=True)
    .str.replace("_MATERNIDAD", "", regex=False)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

# ─────────────────────────────────────────────
# 8. HELPERS
# ─────────────────────────────────────────────
def en_cohorte(clave):
    ini, fin = COHORTES[clave]
    return df["FECHA_NACIMIENTO"].between(ini, fin)

def en_cohorte_escolar(grado):
    ini, fin = COHORTES_ESCOLAR[grado]
    return df["FECHA_NACIMIENTO"].between(ini, fin)

# ─────────────────────────────────────────────
# 9. INICIALIZAR COLUMNAS DE CLASIFICACIÓN
#    COD_COMUNA_JOIN: por defecto = residencia
#    Para vacunas escolares se sobreescribe con ocurrencia
# ─────────────────────────────────────────────
df["CLAVE_DENOMINADOR"] = None
df["VACUNA_DASHBOARD"]  = None
df["COD_COMUNA_JOIN"]   = df["COD_COMUNA_RESID"]   # default = residencia

def asignar(mascara, clave, etiqueta):
    """Vacunas regulares: join por RESIDENCIA (default)."""
    df.loc[mascara, "CLAVE_DENOMINADOR"] = clave
    df.loc[mascara, "VACUNA_DASHBOARD"]  = etiqueta
    # COD_COMUNA_JOIN ya es COD_COMUNA_RESID — no se modifica

def asignar_escolar(mascara, clave, etiqueta):
    """Vacunas escolares: join por OCURRENCIA (comuna del colegio)."""
    df.loc[mascara, "CLAVE_DENOMINADOR"] = clave
    df.loc[mascara, "VACUNA_DASHBOARD"]  = etiqueta
    df.loc[mascara, "COD_COMUNA_JOIN"]   = df.loc[mascara, "COD_COMUNA_OCURR"]

# ─────────────────────────────────────────────
# 10. CLASIFICACIÓN VACUNAS INFANTILES / LACTANTES
# ─────────────────────────────────────────────

# ── BCG (dosis única, RN) ────────────────────────────────────────────────────
asignar(
    df["VAC"].str.contains("BCG") & en_cohorte("RN"),
    "BCG_RN", "VACUNA BCG",
)

# ── HEPATITIS B RN ───────────────────────────────────────────────────────────
asignar(
    df["VAC"].str.contains("HEPATITIS B") &
    ~df["VAC"].str.contains("ADULTO|DIALIZADOS|A-B") &
    en_cohorte("RN"),
    "HepB_RN", "VACUNA HEPATITIS B RN",
)

# ── HEXAVALENTE ──────────────────────────────────────────────────────────────
asignar(
    df["VAC"].str.contains("HEXAVALENTE") &
    (df["DOSIS_NORM"] == "1RA_DOSIS") & en_cohorte("2M"),
    "Cohorte_2M", "VACUNA HEXAVALENTE 1RA DOSIS",
)
asignar(
    df["VAC"].str.contains("HEXAVALENTE") &
    (df["DOSIS_NORM"] == "2DA_DOSIS") & en_cohorte("4M"),
    "Cohorte_4M", "VACUNA HEXAVALENTE 2DA DOSIS",
)
asignar(
    df["VAC"].str.contains("HEXAVALENTE") &
    (df["DOSIS_NORM"] == "3RA_DOSIS") & en_cohorte("6M"),
    "Hexavalente_3d_6m", "VACUNA HEXAVALENTE 3RA DOSIS",
)
asignar(
    df["VAC"].str.contains("HEXAVALENTE") &
    (df["DOSIS_NORM"] == "REFUERZO") & en_cohorte("18M"),
    "Hexavalente_ref_18m", "VACUNA HEXAVALENTE REFUERZO",
)

# ── NEUMOCÓCICA CONJUGADA ─────────────────────────────────────────────────────
asignar(
    df["VAC"].str.contains("NEUMOC") &
    df["VAC"].str.contains("CONJUGADA") &
    ~df["VAC"].str.contains("POLISACARIDA|POLISACÁRIDA") &
    (df["DOSIS_NORM"] == "1RA_DOSIS") & en_cohorte("2M"),
    "Cohorte_2M", "VACUNA NEUMOCOCICA CONJUGADA 1RA DOSIS",
)
asignar(
    df["VAC"].str.contains("NEUMOC") &
    df["VAC"].str.contains("CONJUGADA") &
    ~df["VAC"].str.contains("POLISACARIDA|POLISACÁRIDA") &
    (df["DOSIS_NORM"] == "2DA_DOSIS") & en_cohorte("4M"),
    "Cohorte_4M", "VACUNA NEUMOCOCICA CONJUGADA 2DA DOSIS",
)
asignar(
    df["VAC"].str.contains("NEUMOC") &
    df["VAC"].str.contains("CONJUGADA") &
    ~df["VAC"].str.contains("POLISACARIDA|POLISACÁRIDA") &
    (df["DOSIS_NORM"] == "REFUERZO") & en_cohorte("12M"),
    "Cohorte_12M", "VACUNA NEUMOCOCICA CONJUGADA REFUERZO",
)

# ── MENINGOCÓCICA RECOMBINANTE (Bexsero) ─────────────────────────────────────
asignar(
    df["VAC"].str.contains("BEXSERO") &
    (df["DOSIS_NORM"] == "1RA_DOSIS") & en_cohorte("2M"),
    "Cohorte_2M", "VACUNA MENINGOCOCICA RECOMBINANTE 1RA DOSIS",
)
asignar(
    df["VAC"].str.contains("BEXSERO") &
    (df["DOSIS_NORM"] == "2DA_DOSIS") & en_cohorte("4M"),
    "Cohorte_4M", "VACUNA MENINGOCOCICA RECOMBINANTE 2DA DOSIS",
)
asignar(
    df["VAC"].str.contains("BEXSERO") &
    (df["DOSIS_NORM"] == "REFUERZO") & en_cohorte("18M"),
    "Cohorte_18M", "VACUNA MENINGOCOCICA RECOMBINANTE REFUERZO",
)

# ── MENINGOCÓCICA CONJUGADA (12 meses) ───────────────────────────────────────
asignar(
    df["VAC"].str.contains("MENQUADFI|NIMENRIX|MENVEO|MENACTRA|ACTACEL") &
    (df["DOSIS_NORM"] == "DOSIS_UNICA") & en_cohorte("12M"),
    "Cohorte_12M", "VACUNA MENINGOCOCICA CONJUGADA DOSIS UNICA",
)

# ── SRP ───────────────────────────────────────────────────────────────────────
asignar(
    df["VAC"].str.contains("SRP|TRIVIR") &
    (df["DOSIS_NORM"] == "1RA_DOSIS") & en_cohorte("12M"),
    "Cohorte_12M", "VACUNA SRP (TRIVIRICA) 1RA DOSIS",
)
asignar(
    df["VAC"].str.contains("SRP|TRIVIR") &
    (df["DOSIS_NORM"] == "2DA_DOSIS") & en_cohorte("36M"),
    "Cohorte_36M", "VACUNA SRP (TRIVIRICA) 2DA DOSIS",
)

# ── HEPATITIS A PEDIÁTRICA (18 meses) ────────────────────────────────────────
asignar(
    df["VAC"].str.contains("HEPATITIS A") &
    ~df["VAC"].str.contains("ADULTO|A-B") &
    (df["DOSIS_NORM"] == "DOSIS_UNICA") & en_cohorte("18M"),
    "Cohorte_18M", "VACUNA HEPATITIS A PEDIATRICA",
)

# ── VARICELA ──────────────────────────────────────────────────────────────────
asignar(
    df["VAC"].str.contains("VARICELA") &
    (df["DOSIS_NORM"] == "1RA_DOSIS") & en_cohorte("18M"),
    "Cohorte_18M", "VACUNA VARICELA 1RA DOSIS",
)
asignar(
    df["VAC"].str.contains("VARICELA") &
    (df["DOSIS_NORM"] == "2DA_DOSIS") & en_cohorte("36M"),
    "Cohorte_36M", "VACUNA VARICELA 2DA DOSIS",
)

# ── NEUMOCÓCICA POLISACÁRIDA (65 años) ───────────────────────────────────────
asignar(
    df["VAC"].str.contains("NEUMOC") &
    df["VAC"].str.contains("POLISACARIDA|POLISACÁRIDA"),
    "Neumococica_Polisacarida_65", "VACUNA NEUMOCOCICA POLISACARIDA",
)

# ─────────────────────────────────────────────
# 11. CLASIFICACIÓN VACUNAS ESCOLARES
#     Join por COD_COMUNA_OCURR (metodología DEIS v2.0)
#     Ventana de nacimiento define el grado esperado en 2024
# ─────────────────────────────────────────────

# ── dTpa 1° BÁSICO ────────────────────────────────────────────────────────────
# Refuerzo en escolares de 1° básico (~6-7 años en 2024)
asignar_escolar(
    df["VAC"].str.contains("DTPA|TDPA", case=False) &
    en_cohorte_escolar("1basico") &
    (df["FECHA_INMUNIZACION"].dt.year == T),  # solo vacunados en año t (escolar no t+1/t+2)
    "dTpa_1basico", "VACUNA DTPA 1 BASICO",
)

# ── dTpa 8° BÁSICO ────────────────────────────────────────────────────────────
asignar_escolar(
    df["VAC"].str.contains("DTPA|TDPA", case=False) &
    en_cohorte_escolar("8basico") &
    (df["FECHA_INMUNIZACION"].dt.year == T),
    "dTpa_8basico", "VACUNA DTPA 8 BASICO",
)

# ── VPH 4° BÁSICO ─────────────────────────────────────────────────────────────
asignar_escolar(
    df["VAC"].str.contains("VPH|PAPILOMA|GARDASIL|CERVARIX|SILGARD", case=False) &
    en_cohorte_escolar("4basico") &
    (df["FECHA_INMUNIZACION"].dt.year == T),
    "VPH_4basico", "VACUNA VPH 4 BASICO",
)

# ─────────────────────────────────────────────
# 12. CLASIFICACIÓN VACUNAS GESTANTES
#     dTpa desde semana 28 de gestación
#     Denominador: estimación embarazadas (script 2_denominador_gestantes)
#     Se distingue de dTpa escolar por rango de edad (nacidas ~1975-2008)
# ─────────────────────────────────────────────
asignar(
    df["VAC"].str.contains("DTPA|TDPA", case=False) &
    df["FECHA_NACIMIENTO"].dt.year.between(1975, 2008) &
    (df["FECHA_INMUNIZACION"].dt.year == T),
    "dTpa_Gestantes", "VACUNA DTPA GESTANTES",
)

# ─────────────────────────────────────────────
# 13. DIAGNÓSTICO — vacunas del programa no clasificadas
# ─────────────────────────────────────────────
vacunas_programa = [
    "BCG", "HEPATITIS B", "HEXAVALENTE",
    "NEUMOC",
    "BEXSERO", "MENQUADFI", "NIMENRIX", "MENVEO", "MENACTRA", "ACTACEL",
    "SRP", "TRIVIR", "HEPATITIS A", "VARICELA",
    "DTPA", "TDPA", "VPH", "PAPILOMA", "GARDASIL", "CERVARIX", "SILGARD",
]
mascara_programa = df["VAC"].str.contains("|".join(vacunas_programa), na=False)
no_clasificados  = df[mascara_programa & df["VACUNA_DASHBOARD"].isna()]

if not no_clasificados.empty:
    print(f"\n⚠ Registros de vacunas del programa NO clasificados: {len(no_clasificados):,}")
    print("  (pueden ser dosis/cohortes fuera de rango — revisar si son esperados)")
    print(no_clasificados.groupby(["VAC", "DOSIS_NORM"])
          .size().reset_index(name="n")
          .sort_values("n", ascending=False)
          .head(20).to_string(index=False))

# ─────────────────────────────────────────────
# 14. OUTPUT
#     Para vacunas regulares: agrupa por COD_COMUNA_RESID
#     Para vacunas escolares: agrupa por COD_COMUNA_OCURR
#     → ambos están en COD_COMUNA_JOIN
# ─────────────────────────────────────────────
numerador = (
    df[df["VACUNA_DASHBOARD"].notna()]
    .groupby(["COD_COMUNA_JOIN", "COD_COMUNA_RESID", "COMUNA_RESIDENCIA",
              "VACUNA_DASHBOARD", "CLAVE_DENOMINADOR"])
    .size()
    .reset_index(name="VACUNAS_ADMINISTRADAS")
    .sort_values(["COD_COMUNA_JOIN", "VACUNA_DASHBOARD"])
    .reset_index(drop=True)
)

print(f"\n{'='*55}")
print(f"  AÑO EVALUADO (t) : {T}")
print(f"  CORTE            : {CORTE}")
print(f"  AÑOS CARGADOS    : {AÑOS_DISPONIBLES}")
print(f"{'='*55}")
print(f"✓ Registros clasificados : {df['VACUNA_DASHBOARD'].notna().sum():,}")
print(f"✓ Comunas únicas         : {numerador['COD_COMUNA_JOIN'].nunique()}")
print(f"✓ Vacunas únicas         : {numerador['VACUNA_DASHBOARD'].nunique()}")
print("\nVacunas clasificadas (total región):")
resumen = (df[df["VACUNA_DASHBOARD"].notna()]
           .groupby("VACUNA_DASHBOARD").size()
           .reset_index(name="n")
           .sort_values("VACUNA_DASHBOARD"))
print(resumen.to_string(index=False))

numerador.to_csv(DIR_OUTPUT / "numerador_rni_2024.csv",   index=False, encoding="utf-8-sig")
numerador.to_excel(DIR_OUTPUT / "numerador_rni_2024.xlsx", index=False)
print(f"\n✓ Guardado en: {DIR_OUTPUT}")
# %%
