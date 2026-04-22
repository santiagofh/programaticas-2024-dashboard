#%%
import pandas as pd
import os
from glob import glob
#%%
# 📁 Ruta del folder
ruta = r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\RNI\PROGRAMATICAS\2024"

# 📂 Obtener archivos
archivos = glob(os.path.join(ruta, "*.csv"))
archivos = [f for f in archivos if not os.path.basename(f).startswith("~")]
df_columnas = pd.read_csv(
        archivos[0],
        encoding="LATIN1",
        sep="|",
        nrows=0,
        low_memory=False
    )
columnas=df_columnas.columns
#%%
# 🎯 Columnas necesarias
columnas_necesarias = [
    'RUN', 'PASAPORTE', 'OTRO',
    "ID_INMUNIZACION",
    "COD_COMUNA_OCURR",
    "COMUNA_OCURR",
    "COD_COMUNA_RESID",
    "COMUNA_RESIDENCIA",
    'NOMBRE_VACUNA',
    "CRITERIO_ELEGIBILIDAD",
    "DOSIS",
    "VACUNA_ADMINISTRADA",
    "REGISTRO_ELIMINADO",
    "SEXO",
    "FECHA_NACIMIENTO",
    "FECHA_INMUNIZACION"
]

# 🧩 Función optimizada
def transformar_y_filtrar(path):

    df = pd.read_csv(
        path,
        encoding="LATIN1",
        sep="|",
        usecols=columnas_necesarias,
        low_memory=False
    )

    # 🔎 Filtrar inmediatamente (reduce RAM drásticamente)
    df = df[
        (
            (df["COD_COMUNA_RESID"].between(13000, 13999))
        ) &
        (df["VACUNA_ADMINISTRADA"] == "SI") &
        (df["REGISTRO_ELIMINADO"] == "NO") &
        (df["CRITERIO_ELEGIBILIDAD"] != "EPRO")&
        (df["DOSIS"] != "EPRO")
    ]
    df = df[~df["DOSIS"].str.contains("EPRO", case=False, na=False)]
    return df

# 🔁 Leer + filtrar archivo por archivo
lista_df = []

for archivo in archivos:
    print(f"Leyendo {os.path.basename(archivo)}...")
    df_temp = transformar_y_filtrar(archivo)
    lista_df.append(df_temp)

# 🔗 Concatenar SOLO data ya filtrada
df_final = pd.concat(lista_df, ignore_index=True)

lista_dosis=df_final.DOSIS.unique()
#%%
# 📅 Convertir fecha
df_final["FECHA_NACIMIENTO"] = pd.to_datetime(df_final["FECHA_NACIMIENTO"], errors="coerce")
df_final["FECHA_INMUNIZACION"] = pd.to_datetime(
    df_final["FECHA_INMUNIZACION"],
    errors="coerce"
)
df_final["EDAD_ANIOS"] = (
    (df_final["FECHA_INMUNIZACION"] - df_final["FECHA_NACIMIENTO"])
    .dt.days / 365.25
)
df_final["EDAD_ANIOS"] = df_final["EDAD_ANIOS"].astype(int)
#%% FILTRAR vacunas
df_final["DOSIS_LIMPIA"] = (
    df_final["DOSIS"]
    .str.upper()
    .str.strip()
)
import numpy as np

condiciones = [

    # Volumen → única
    df_final["DOSIS_LIMPIA"].str.contains("0.05|0.1"),

    # 1ra dosis
    df_final["DOSIS_LIMPIA"].str.contains(r"\b1\s*[°ºRA]*\s*D", regex=True),

    # 2da dosis
    df_final["DOSIS_LIMPIA"].str.contains(r"\b2\s*[°ºDA]*\s*D", regex=True),

    # 3ra dosis
    df_final["DOSIS_LIMPIA"].str.contains(r"\b3\s*[°ºRA]*\s*D", regex=True),

    # 4ta dosis
    df_final["DOSIS_LIMPIA"].str.contains(r"\b4\s*[°ºTA]*\s*D", regex=True),

    # 5ta dosis
    df_final["DOSIS_LIMPIA"].str.contains(r"\b5\s*[°ºTA]*\s*D", regex=True),
    
    # Refuerzo
    df_final["DOSIS_LIMPIA"].str.contains("REFUERZO"),

    # Única
    df_final["DOSIS_LIMPIA"].str.contains("ÚNICA"),
]

valores = [
    "DOSIS_UNICA",
    "1RA_DOSIS",
    "2DA_DOSIS",
    "3RA_DOSIS",
    "4TA_DOSIS",
    "5TA_DOSIS",
    "REFUERZO",
    "DOSIS_UNICA",
]

df_final["DOSIS_NORMALIZADA"] = np.select(condiciones, valores, default="OTRO")
# %%
df_final["DOSIS_NORMALIZADA"].value_counts()
# %%
df_final[df_final["DOSIS_NORMALIZADA"] == "OTRO"]["DOSIS_LIMPIA"].value_counts()
#%%
df_final["VACUNA_LIMPIA"] = (
    df_final["NOMBRE_VACUNA"]
    .str.upper()
    .str.replace(r"\(.*?\)", "", regex=True)  # elimina texto entre paréntesis
    .str.replace("_MATERNIDAD", "", regex=False)
    .str.strip()
)
#%%
condiciones_vacunas = [

    # BCG
    df_final["VACUNA_LIMPIA"].str.contains("BCG"),

    # HEPATITIS B RN — solo excluye las variantes de adultos
    (
        df_final["VACUNA_LIMPIA"].str.contains("HEPATITIS B") &
        ~df_final["VACUNA_LIMPIA"].str.contains("ADULTO|DIALIZADOS|PEDIÁTRICA|A-B")
    ),
    # HEPATITIS B — solo pediátrica RN, excluye adulto y dializados
    (
        df_final["VACUNA_LIMPIA"].str.contains("HEPATITIS B") &
        ~df_final["VACUNA_LIMPIA"].str.contains("ADULTO|DIALIZADOS|PEDIÁTRICA|A-B") &
        (df_final["EDAD_ANIOS"] == 0)
    ),

    # HEXAVALENTE 3ª DOSIS — 6 meses
    (
        df_final["VACUNA_LIMPIA"].str.contains("HEXAVALENTE") &
        (df_final["DOSIS_NORMALIZADA"] == "3RA_DOSIS")
    ),

    # SRP (TRIVIRICA) 1ª DOSIS — 12 meses  ← nombre real en RNI es SRP
    (
        df_final["VACUNA_LIMPIA"].str.contains("SRP") &
        (df_final["DOSIS_NORMALIZADA"] == "1RA_DOSIS")
    ),

    # SRP (TRIVIRICA) 2ª DOSIS — 36 meses  ← faltaba en tu código
    (
        df_final["VACUNA_LIMPIA"].str.contains("SRP") &
        (df_final["DOSIS_NORMALIZADA"] == "2DA_DOSIS")
    ),

    # NEUMOCÓCICA CONJUGADA 1er REFUERZO — 12 meses
    (
        df_final["VACUNA_LIMPIA"].str.contains("NEUMOCÓCICA CONJUGADA") &
        (df_final["DOSIS_NORMALIZADA"] == "REFUERZO")
    ),

    # MENINGOCÓCICA DOSIS ÚNICA — 12 meses  ← agrega MENVEO y MENACTRA
    (
        df_final["VACUNA_LIMPIA"].str.contains("MENQUADFI|NIMENRIX|MENVEO|MENACTRA") &
        (df_final["DOSIS_NORMALIZADA"] == "DOSIS_UNICA")
    ),

    # VARICELA 1ª DOSIS — 18 meses
    (
        df_final["VACUNA_LIMPIA"].str.contains("VARICELA") &
        (df_final["DOSIS_NORMALIZADA"] == "1RA_DOSIS")
    ),

    # HEPATITIS A PEDIÁTRICA DOSIS ÚNICA — 18 meses  ← faltaba en tu código
    (
        df_final["VACUNA_LIMPIA"].str.contains("HEPATITIS A PEDIÁTRICA") &
        (df_final["DOSIS_NORMALIZADA"] == "DOSIS_UNICA")
    ),

    # VARICELA 2ª DOSIS — 36 meses  ← faltaba en tu código
    (
        df_final["VACUNA_LIMPIA"].str.contains("VARICELA") &
        (df_final["DOSIS_NORMALIZADA"] == "2DA_DOSIS")
    ),

    # NEUMOCÓCICA POLISACÁRIDA 23V — adultos ≥65 años
    (
        df_final["VACUNA_LIMPIA"].str.contains("POLISACÁRIDA 23V") &
        (df_final["EDAD_ANIOS"] >= 65)
    ),
]

valores_vacunas = [
    "VACUNA BCG",
    "VACUNA HEPATITIS B RN",
    "VACUNA HEXAVALENTE 3RA DOSIS",
    "VACUNA SRP 1RA DOSIS",
    "VACUNA SRP 2DA DOSIS",
    "VACUNA NEUMOCOCICA CONJUGADA REFUERZO",
    "VACUNA MENINGOCOCICA DOSIS UNICA",
    "VACUNA VARICELA 1RA DOSIS",
    "VACUNA HEPATITIS A 18M",
    "VACUNA VARICELA 2DA DOSIS",
    "VACUNA NEUMOCOCICA POLISACARIDA 23V ADULTOS",
]

valores_vacunas = [
    "VACUNA VARICELA 1º DOSIS",
    "VACUNA NEUMOCOCICA CONJUGADA 1er REFUERZO",
    "VACUNA MENINGOCOCICA DOSIS UNICA",
    "VACUNA TRIVIRICA 1 DOSIS",
    "VACUNA HEXAVALENTE 3RA DOSIS",
    "VACUNA HEPATITIS B",
    "VACUNA NEUMOCOCICA POLISACARICA 23 VALENTE EN ADULTOS DE 65 AÑOS",
    "VACUNA CONTRA BACILLUS DE CALMETTE Y GUERIN BCG",
]

df_final["VACUNA_DASHBOARD"] = np.select(
    condiciones_vacunas,
    valores_vacunas,
    default=None
)

