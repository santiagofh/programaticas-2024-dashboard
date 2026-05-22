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
  Escolar           : dTpa 1° básico, dTpa 8° básico, VPH 4° básico (dosis única),
                        VPH 5° básico (2da dosis, solo 2024)
  Gestantes         : dTpa gestantes (≥28 sem gestación)
  Personas mayores  : Neumocócica Polisacárida (65 años)

NOTA METODOLÓGICA COBERTURAS ESCOLARES:
  Las vacunas escolares se identifican por CRITERIO_ELEGIBILIDAD
  del RNI y se agregan por COD_COMUNA_OCURR.
=============================================================
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date

# ─────────────────────────────────────────────
# 1. RUTAS
# ─────────────────────────────────────────────
DIR_OUTPUT = Path(__file__).parent / "output"
DIR_OUTPUT.mkdir(exist_ok=True)

T = 2024
RUN_DATE = date.today().isoformat()

# — CONFIGURAR RUTA LOCAL —
# RUTA_BASE_RNI = Path("ruta/a/tus/datos/RNI/PROGRAMATICAS")
# Ejemplo local:
# RUTA_BASE_RNI = Path(r"D:\DATA\RNI\PROGRAMATICAS")
RUTA_BASE_RNI = Path("data")
RUTAS_AÑOS = {
    T:   RUTA_BASE_RNI / f"Programaticas_{T}.csv",
    T+1: RUTA_BASE_RNI / f"Programaticas_{T+1}.csv",
    T+2: RUTA_BASE_RNI / f"Programaticas_{T+2}.csv",
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
# Chile: ingresa a 1° básico el año en que cumple 6 antes del 1 de abril
# 1° básico 2024: nacidos ~2017      (6-7 años)
# 4° básico 2024: nacidos ~2014-2015 (9-10 años) → VPH nonavalente DOSIS_UNICA
# 5° básico 2024: nacidos ~2013-2014 (10-11 años)→ VPH tetravalente 2DA_DOSIS (solo 2024)
# 8° básico 2024: nacidos ~2010      (13-14 años)
# Ventanas ~1.5 años para incluir estudiantes con rezago de un año
COHORTES_ESCOLAR = {
    "1basico": ("2016-07-01", "2018-06-30"),   # nacidos ~2017
    "4basico": ("2014-01-01", "2015-06-30"),   # nacidos ~2014-2015
    "5basico": ("2013-01-01", "2014-06-30"),   # nacidos ~2013-2014
    "8basico": ("2009-07-01", "2011-06-30"),   # nacidos ~2010
}
# 22-05-2026 - NO SE CONSIDERA CORTES DE AÑOS 

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
    "SEMANA_GESTACIONAL",
]

# ─────────────────────────────────────────────
# 4. CARGA MULTI-AÑO
# ─────────────────────────────────────────────
def cargar_y_filtrar(path):
    chunks = []

    for chunk in pd.read_csv(
        path,
        encoding="LATIN1",
        sep="|",
        usecols=COLUMNAS,
        low_memory=False,
        chunksize=500000,
    ):

        resid_rm = chunk["COD_COMUNA_RESID"].between(13000, 13999)
        ocurr_rm = chunk["COD_COMUNA_OCURR"].between(13000, 13999)

        chunk = chunk[
            (resid_rm | ocurr_rm) &
            (chunk["VACUNA_ADMINISTRADA"] == "SI") &
            (chunk["REGISTRO_ELIMINADO"] == "NO") &
            (chunk["CRITERIO_ELEGIBILIDAD"] != "EPRO") &
            (~chunk["DOSIS"].str.contains("EPRO", case=False, na=False))
        ]

        chunks.append(chunk)

    df = pd.concat(chunks, ignore_index=True)

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
    if not ruta.exists():
        print(f"  [{anio}] ⏭  Archivo no encontrado — se omite")
        continue

    print(f"\n  [{anio}] ✓ Cargando {ruta.name}...")
    lista_df.append(cargar_y_filtrar(ruta))
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

def normalizar_texto(serie):
    return (
        serie.fillna("")
        .astype(str)
        .str.upper()
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .str.decode("ascii")
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

df["CRITERIO_NORM"] = normalizar_texto(df["CRITERIO_ELEGIBILIDAD"])
df["SEXO_NORM"] = normalizar_texto(df["SEXO"])
df["SEMANA_GESTACIONAL_NUM"] = pd.to_numeric(df["SEMANA_GESTACIONAL"], errors="coerce")

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
#    En escolares solo usar ocurrencia
# ─────────────────────────────────────────────
df["CLAVE_DENOMINADOR"] = None
df["VACUNA_DASHBOARD"]  = None
df["COD_COMUNA_JOIN"] = pd.NA

def asignar(mascara, clave, etiqueta):
    """Vacunas regulares: join por residencia."""
    mascara = mascara.fillna(False)
    traslape = mascara & df["VACUNA_DASHBOARD"].notna()
    if traslape.any():
        print(f"⚠ Regla '{etiqueta}' traslapa {traslape.sum():,} registros ya clasificados; no se sobreescriben")
    mascara_final = mascara & df["VACUNA_DASHBOARD"].isna()
    df.loc[mascara_final, "CLAVE_DENOMINADOR"] = clave
    df.loc[mascara_final, "VACUNA_DASHBOARD"]  = etiqueta
    df.loc[mascara_final, "COD_COMUNA_JOIN"]   = df.loc[mascara_final, "COD_COMUNA_RESID"]

def asignar_escolar(mascara, clave, etiqueta):
    """Vacunas escolares: join por comuna de ocurrencia."""
    mascara = mascara.fillna(False)
    traslape = mascara & df["VACUNA_DASHBOARD"].notna()
    if traslape.any():
        print(f"⚠ Regla '{etiqueta}' traslapa {traslape.sum():,} registros ya clasificados; no se sobreescriben")
    mascara_final = mascara & df["VACUNA_DASHBOARD"].isna()
    df.loc[mascara_final, "CLAVE_DENOMINADOR"] = clave
    df.loc[mascara_final, "VACUNA_DASHBOARD"]  = etiqueta
    df.loc[mascara_final, "COD_COMUNA_JOIN"]   = df.loc[mascara_final, "COD_COMUNA_OCURR"]

CRITERIOS_ESCOLARES = {
    "1basico": [
        "1° básico (Est. De Salud)",
        "1° básico (Est. Educacional)",
    ],
    "4basico": [
        "4º básico (Est. de Salud)",
        "4º básico (Est. Educacional)",
    ],
    "5basico": [
        "5º básico",
        "5º básico (Est. de Salud)",
        "5º básico (Est. Educacional)",
        "5º básico (Est. de Salud)",
        "5º básico (Est. Educacional)"

    ],
    "8basico": [
        "8° básico (Est. De Salud)",
        "8° básico (Est. Educacional)",
    ],
    "vph_pendientes": [
        # "6º básico dosis pendiente",
        # "7º básico dosis pendiente",
        # "8º básico dosis pendiente",
    ],
    "8basico_pendiente": [
        # "8º básico dosis pendiente",
    ],
}

CRITERIOS_ESCOLARES_NORM = {
    clave: set(normalizar_texto(pd.Series(valores)))
    for clave, valores in CRITERIOS_ESCOLARES.items()
}

def criterio_escolar(clave):
    return df["CRITERIO_NORM"].isin(CRITERIOS_ESCOLARES_NORM[clave])

criterio_embarazada = (
    df["CRITERIO_NORM"].str.contains(r"\bEMBARAZADAS?\b", na=False) |
    (df["SEMANA_GESTACIONAL_NUM"] >= 28)
)
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
    df["VAC"].str.contains("MENQUADFI|NIMENRIX|MENVEO|MENACTRA") &
    # ACTACEL removido: no es vacuna meningocócica (DTaP-IPV). Confirmar dónde clasificarla.
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
# Metodología DEIS v2.0 (pág 22, sección 7.1.14):
#   Numerador : vacunados año t + t+1 + t+2, nacidos en el año t-65
#   Denominador: Proyección INE 65 años del año t
#
# Se incluyen SOLO personas nacidas en el año t-65 (= 1959 para t=2024):
#   - Pueden vacunarse a los 64 años si cumplen 65 durante el año calendario
#   - Los de 66+ NO se incluyen en este numerador
# Esto es consistente con el denominador (proyección INE de quienes cumplen 65 en t)
asignar(
    df["VAC"].str.contains("NEUMOC") &
    df["VAC"].str.contains("POLISACARIDA|POLISACÁRIDA") &
    (df["FECHA_NACIMIENTO"].dt.year == T - 65),   # nacidos en 1959 para t=2024
    "Neumococica_Polisacarida_65", "VACUNA NEUMOCOCICA POLISACARIDA",
)

# ─────────────────────────────────────────────
# 11. CLASIFICACIÓN VACUNAS ESCOLARES
#     Se separan por CRITERIO_ELEGIBILIDAD para evitar que 1°, 4°, 5°
#     y 8° básico se pisen entre sí.
# ─────────────────────────────────────────────

# ── dTpa 1° BÁSICO ────────────────────────────────────────────────────────────
# Refuerzo en escolares de 1° básico (~6-7 años en 2024)
asignar_escolar(
    df["VAC"].str.contains("DTPA|TDPA", case=False) &
    criterio_escolar("1basico") &
    (df["FECHA_INMUNIZACION"].dt.year == T),  # solo vacunados en año t (escolar no t+1/t+2)
    "dTpa_1basico", "VACUNA DTPA 1 BASICO",
)

# ── dTpa 8° BÁSICO ────────────────────────────────────────────────────────────
asignar_escolar(
    df["VAC"].str.contains("DTPA|TDPA", case=False) &
    (criterio_escolar("8basico")) &
    (df["FECHA_INMUNIZACION"].dt.year == T),
    "dTpa_8basico", "VACUNA DTPA 8 BASICO",
)

# ── VPH 4° BÁSICO ────────────────────────────────────────────────────────────
# En 2024 coexisten dos esquemas (Anexo 1, pág 26):
#   - DOSIS_UNICA: nonavalente (nuevo desde 2024)
#   - 1RA_DOSIS:  tetravalente rezagados de 4° básico
# Ambas se capturan con el mismo denominador (matriculados 4° básico)
asignar_escolar(
    df["VAC"].str.contains("VPH|PAPILOMA|GARDASIL|CERVARIX|SILGARD", case=False) &
    # (df["DOSIS_NORM"].isin(["DOSIS_UNICA", "1RA_DOSIS"])) &
    criterio_escolar("4basico") &
    (df["FECHA_INMUNIZACION"].dt.year == T),
    "VPH_4basico", "VACUNA VPH 4 BASICO",
)


# ── VPH 5° BÁSICO — 2da dosis tetravalente (completando esquema 2023) ─────────
# Solo aplica en 2024: escolares de 5° básico que recibieron 1° dosis en 2023
# A partir de 2025 este grupo ya no existe (solo queda 4° básico nonavalente)
asignar_escolar(
    df["VAC"].str.contains("VPH|PAPILOMA|GARDASIL|CERVARIX|SILGARD", case=False) &
    # (df["DOSIS_NORM"] == "2DA_DOSIS") &
    (criterio_escolar("5basico")) &
    (df["FECHA_INMUNIZACION"].dt.year == T),
    "VPH_5basico", "VACUNA VPH 5 BASICO",
)

# ─────────────────────────────────────────────
# 12. CLASIFICACIÓN VACUNAS GESTANTES
#     dTpa desde semana 28 de gestación
#     Denominador: estimación embarazadas (script 2_denominador_gestantes)
#     Se distingue de dTpa escolar por rango de edad (nacidas ~1975-2008)
# ─────────────────────────────────────────────
asignar(
    df["VAC"].str.contains("DTPA|TDPA", case=False) &
    df["SEXO_NORM"].isin(["MUJER", "FEMENINA"]) &
    criterio_embarazada &
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
# 14. DEDUPLICACIÓN POR PERSONA Y VACUNA
#     Identificador final con prioridad: RUN > PASAPORTE > OTRO
#     Se elimina duplicidad dentro de la misma vacuna del dashboard.
# ─────────────────────────────────────────────
df_final = df[df["VACUNA_DASHBOARD"].notna()].copy()

for col in ["RUN", "PASAPORTE", "OTRO"]:
    df_final[col] = (
        df_final[col]
        .astype(str)
        .str.strip()
        .replace(["nan", "NaN", "None", "<NA>", ""], pd.NA)
    )

df_final["IDENTIFICACION_FINAL"] = pd.NA
mask_run = df_final["RUN"].notna()
mask_pas = df_final["PASAPORTE"].notna() & ~mask_run
mask_otro = df_final["OTRO"].notna() & ~mask_run & ~mask_pas

df_final.loc[mask_run, "IDENTIFICACION_FINAL"] = "RUN_" + df_final.loc[mask_run, "RUN"]
df_final.loc[mask_pas, "IDENTIFICACION_FINAL"] = "PAS_" + df_final.loc[mask_pas, "PASAPORTE"]
df_final.loc[mask_otro, "IDENTIFICACION_FINAL"] = "OTRO_" + df_final.loc[mask_otro, "OTRO"]

sin_identificacion = df_final["IDENTIFICACION_FINAL"].isna().sum()
if sin_identificacion > 0:
    print(f"\n⚠ Registros clasificados sin identificación válida: {sin_identificacion:,} — se omiten")
df_final = df_final[df_final["IDENTIFICACION_FINAL"].notna()].copy()

df_final["COD_COMUNA_JOIN"] = pd.to_numeric(df_final["COD_COMUNA_JOIN"], errors="coerce").astype("Int64")
fuera_rm = df_final[~df_final["COD_COMUNA_JOIN"].between(13000, 13999)]
if not fuera_rm.empty:
    print(f"\n⚠ Registros clasificados con comuna de cálculo fuera de RM: {len(fuera_rm):,} — se omiten")
df_final = df_final[df_final["COD_COMUNA_JOIN"].between(13000, 13999)].copy()

cols_duplicado = ["IDENTIFICACION_FINAL", "VACUNA_DASHBOARD"]
duplicados_unicos_programaticas = (
    df_final[df_final.duplicated(cols_duplicado, keep=False)]
    .sort_values(cols_duplicado + ["FECHA_INMUNIZACION"])
)
if not duplicados_unicos_programaticas.empty:
    nombre_dup = f"{RUN_DATE}_duplicados_unicos_programaticas_2024.xlsx"
    duplicados_unicos_programaticas.to_excel(DIR_OUTPUT / nombre_dup, index=False)
    print(
        f"\n⚠ Duplicados persona-vacuna: {len(duplicados_unicos_programaticas):,} "
        f"registros — auditoría: {nombre_dup}"
    )

registros_antes_dedup = len(df_final)
df_final = (
    df_final
    .sort_values(["IDENTIFICACION_FINAL", "VACUNA_DASHBOARD", "FECHA_INMUNIZACION"])
    .drop_duplicates(subset=cols_duplicado, keep="first")
)
print(f"✓ Registros tras deduplicar persona-vacuna: {len(df_final):,} "
      f"(eliminados {registros_antes_dedup - len(df_final):,})")

# ─────────────────────────────────────────────
# 15. OUTPUT
#     Para vacunas regulares: agrupa por COD_COMUNA_RESID
#     Para vacunas escolares: agrupa por COD_COMUNA_OCURR
#     → ambos están en COD_COMUNA_JOIN
# ─────────────────────────────────────────────
numerador = (
    df_final
    .groupby(["COD_COMUNA_JOIN", "VACUNA_DASHBOARD", "CLAVE_DENOMINADOR"])
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
print(f"✓ Registros únicos       : {len(df_final):,}")
print(f"✓ Comunas únicas         : {numerador['COD_COMUNA_JOIN'].nunique()}")
print(f"✓ Vacunas únicas         : {numerador['VACUNA_DASHBOARD'].nunique()}")
print("\nVacunas clasificadas (total región):")
resumen = (df_final
           .groupby("VACUNA_DASHBOARD").size()
           .reset_index(name="n")
           .sort_values("VACUNA_DASHBOARD"))
print(resumen.to_string(index=False))

nombre_csv = f"{RUN_DATE}_numerador_rni_2024.csv"
nombre_xlsx = f"{RUN_DATE}_numerador_rni_2024.xlsx"
numerador.to_csv(DIR_OUTPUT / nombre_csv,   index=False, encoding="utf-8-sig")
numerador.to_excel(DIR_OUTPUT / nombre_xlsx, index=False)
print(f"\n✓ Guardado en: {DIR_OUTPUT}")
# %%
