from io import BytesIO
from pathlib import Path
from glob import glob

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

st.set_page_config(
    page_title="Dashboard Programáticas 2024",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp h1, .stApp h2, .stApp h3 {
        color: #006FB3;
        font-weight: 700;
    }
    .provisional-badge {
        display: inline-block;
        margin: 0.15rem 0 0.6rem 0;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: #FFF3CD;
        border: 1px solid #F2C94C;
        color: #7A4D00;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.01em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.logo(
    str(BASE_DIR / "assets" / "seremi_sidebar_logo.svg"),
    size="large",
    icon_image=str(BASE_DIR / "assets" / "seremi_sidebar_icon.svg"),
)


VACUNA_META = {
    "VACUNA BCG": {
        "vacuna": "BCG",
        "dosis": "Dosis única",
        "grupo": "Recién nacidos",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA HEPATITIS B RN": {
        "vacuna": "Hepatitis B RN",
        "dosis": "Dosis única",
        "grupo": "Recién nacidos",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA HEXAVALENTE 1RA DOSIS": {
        "vacuna": "Hexavalente",
        "dosis": "1ra dosis",
        "grupo": "2 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA NEUMOCOCICA CONJUGADA 1RA DOSIS": {
        "vacuna": "Neumocócica conjugada",
        "dosis": "1ra dosis",
        "grupo": "2 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA MENINGOCOCICA RECOMBINANTE 1RA DOSIS": {
        "vacuna": "Meningocócica recombinante",
        "dosis": "1ra dosis",
        "grupo": "2 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA HEXAVALENTE 2DA DOSIS": {
        "vacuna": "Hexavalente",
        "dosis": "2da dosis",
        "grupo": "4 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA NEUMOCOCICA CONJUGADA 2DA DOSIS": {
        "vacuna": "Neumocócica conjugada",
        "dosis": "2da dosis",
        "grupo": "4 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA MENINGOCOCICA RECOMBINANTE 2DA DOSIS": {
        "vacuna": "Meningocócica recombinante",
        "dosis": "2da dosis",
        "grupo": "4 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA HEXAVALENTE 3RA DOSIS": {
        "vacuna": "Hexavalente",
        "dosis": "3ra dosis",
        "grupo": "6 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA MENINGOCOCICA CONJUGADA DOSIS UNICA": {
        "vacuna": "Meningocócica conjugada",
        "dosis": "Dosis única",
        "grupo": "12 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA SRP (TRIVIRICA) 1RA DOSIS": {
        "vacuna": "SRP (Trivirica)",
        "dosis": "1ra dosis",
        "grupo": "12 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA NEUMOCOCICA CONJUGADA REFUERZO": {
        "vacuna": "Neumocócica conjugada",
        "dosis": "Refuerzo",
        "grupo": "12 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA HEPATITIS A PEDIATRICA": {
        "vacuna": "Hepatitis A pediátrica",
        "dosis": "Dosis única",
        "grupo": "18 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA VARICELA 1RA DOSIS": {
        "vacuna": "Varicela",
        "dosis": "1ra dosis",
        "grupo": "18 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA HEXAVALENTE REFUERZO": {
        "vacuna": "Hexavalente",
        "dosis": "Refuerzo",
        "grupo": "18 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA MENINGOCOCICA RECOMBINANTE REFUERZO": {
        "vacuna": "Meningocócica recombinante",
        "dosis": "Refuerzo",
        "grupo": "18 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "Cobertura regional muy baja en 2024; la documentación sugiere revisar la clasificación del refuerzo en RNI.",
    },
    "VACUNA SRP (TRIVIRICA) 2DA DOSIS": {
        "vacuna": "SRP (Trivirica)",
        "dosis": "2da dosis",
        "grupo": "36 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA VARICELA 2DA DOSIS": {
        "vacuna": "Varicela",
        "dosis": "2da dosis",
        "grupo": "36 meses",
        "estrategia": "Infantil",
        "fuente": "SRCeI",
        "alerta": "",
    },
    "VACUNA DTPA 1 BASICO": {
        "vacuna": "dTpa",
        "dosis": "1er básico",
        "grupo": "Escolar",
        "estrategia": "Escolar",
        "fuente": "Mineduc",
        "alerta": "En la salida final existen filas sin denominador para códigos de comuna fuera de RM; la vista principal las excluye por defecto.",
    },
    "VACUNA VPH 4 BASICO": {
        "vacuna": "VPH",
        "dosis": "4to básico",
        "grupo": "Escolar",
        "estrategia": "Escolar",
        "fuente": "Mineduc",
        "alerta": "En 2024 coexisten dosis única nonavalente y rezagados; la vista principal excluye filas sin denominador.",
    },
    "VACUNA VPH 5 BASICO": {
        "vacuna": "VPH",
        "dosis": "5to básico",
        "grupo": "Escolar",
        "estrategia": "Escolar",
        "fuente": "Mineduc",
        "alerta": "Aplica solo en 2024 por transición de esquema; la vista principal excluye filas sin denominador.",
    },
    "VACUNA DTPA 8 BASICO": {
        "vacuna": "dTpa",
        "dosis": "8vo básico",
        "grupo": "Escolar",
        "estrategia": "Escolar",
        "fuente": "Mineduc",
        "alerta": "En la salida final existen filas sin denominador para códigos de comuna fuera de RM; la vista principal las excluye por defecto.",
    },
    "VACUNA NEUMOCOCICA POLISACARIDA": {
        "vacuna": "Neumocócica polisacárida",
        "dosis": "Dosis única",
        "grupo": "65 años",
        "estrategia": "Personas mayores",
        "fuente": "INE",
        "alerta": "Interpretar según metodología vigente del programa; revisar con equipo si se esperan rescates o definiciones especiales del numerador.",
    },
    "VACUNA DTPA GESTANTES": {
        "vacuna": "dTpa gestantes",
        "dosis": "Dosis única",
        "grupo": "Gestantes",
        "estrategia": "Gestantes",
        "fuente": "Estimación gestantes",
        "alerta": "El denominador de gestantes depende de estimación específica del programa; conviene validar la lectura con el equipo técnico.",
    },
}

DISPLAY_ORDER = list(VACUNA_META.keys())

COMUNA_TO_SS = {
    "Alhué": "Servicio de Salud Metropolitano Occidente",
    "Buin": "Servicio de Salud Metropolitano Sur",
    "Calera de Tango": "Servicio de Salud Metropolitano Sur",
    "Cerrillos": "Servicio de Salud Metropolitano Occidente",
    "Cerro Navia": "Servicio de Salud Metropolitano Occidente",
    "Colina": "Servicio de Salud Metropolitano Norte",
    "Conchalí": "Servicio de Salud Metropolitano Norte",
    "Curacaví": "Servicio de Salud Metropolitano Occidente",
    "El Bosque": "Servicio de Salud Metropolitano Sur",
    "El Monte": "Servicio de Salud Metropolitano Occidente",
    "Estación Central": "Servicio de Salud Metropolitano Central",
    "Huechuraba": "Servicio de Salud Metropolitano Norte",
    "Independencia": "Servicio de Salud Metropolitano Norte",
    "Isla de Maipo": "Servicio de Salud Metropolitano Occidente",
    "La Cisterna": "Servicio de Salud Metropolitano Sur",
    "La Florida": "Servicio de Salud Metropolitano Sur Oriente",
    "La Granja": "Servicio de Salud Metropolitano Sur",
    "La Pintana": "Servicio de Salud Metropolitano Sur Oriente",
    "La Reina": "Servicio de Salud Metropolitano Oriente",
    "Lampa": "Servicio de Salud Metropolitano Norte",
    "Las Condes": "Servicio de Salud Metropolitano Oriente",
    "Lo Barnechea": "Servicio de Salud Metropolitano Oriente",
    "Lo Espejo": "Servicio de Salud Metropolitano Sur",
    "Lo Prado": "Servicio de Salud Metropolitano Occidente",
    "Macul": "Servicio de Salud Metropolitano Oriente",
    "Maipú": "Servicio de Salud Metropolitano Central",
    "María Pinto": "Servicio de Salud Metropolitano Occidente",
    "Melipilla": "Servicio de Salud Metropolitano Occidente",
    "Ñuñoa": "Servicio de Salud Metropolitano Oriente",
    "Padre Hurtado": "Servicio de Salud Metropolitano Occidente",
    "Paine": "Servicio de Salud Metropolitano Sur",
    "Pedro Aguirre Cerda": "Servicio de Salud Metropolitano Sur",
    "Peñaflor": "Servicio de Salud Metropolitano Occidente",
    "Peñalolén": "Servicio de Salud Metropolitano Oriente",
    "Pirque": "Servicio de Salud Metropolitano Sur Oriente",
    "Providencia": "Servicio de Salud Metropolitano Oriente",
    "Pudahuel": "Servicio de Salud Metropolitano Occidente",
    "Puente Alto": "Servicio de Salud Metropolitano Sur Oriente",
    "Quilicura": "Servicio de Salud Metropolitano Norte",
    "Quinta Normal": "Servicio de Salud Metropolitano Occidente",
    "Recoleta": "Servicio de Salud Metropolitano Norte",
    "Renca": "Servicio de Salud Metropolitano Occidente",
    "San Bernardo": "Servicio de Salud Metropolitano Sur",
    "San Joaquín": "Servicio de Salud Metropolitano Sur",
    "San José de Maipo": "Servicio de Salud Metropolitano Sur Oriente",
    "San Miguel": "Servicio de Salud Metropolitano Sur",
    "San Pedro": "Servicio de Salud Metropolitano Occidente",
    "San Ramón": "Servicio de Salud Metropolitano Sur Oriente",
    "Santiago": "Servicio de Salud Metropolitano Central",
    "Talagante": "Servicio de Salud Metropolitano Occidente",
    "Tiltil": "Servicio de Salud Metropolitano Norte",
    "Vitacura": "Servicio de Salud Metropolitano Oriente",
}


def latest_dated_file(dir_path: Path, base_name: str) -> Path:
    pattern = str(dir_path / f"????-??-??_{base_name}")
    candidates = sorted(glob(pattern))
    if candidates:
        return Path(candidates[-1])
    legacy = dir_path / base_name
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"No existe {base_name} en {dir_path}")


def enrich_metadata(df: pd.DataFrame) -> pd.DataFrame:
    meta = pd.DataFrame.from_dict(VACUNA_META, orient="index").reset_index(names="VACUNA_DASHBOARD")
    out = df.merge(meta, on="VACUNA_DASHBOARD", how="left")
    out["vacuna"] = out["vacuna"].fillna(out["VACUNA_DASHBOARD"])
    out["dosis"] = out["dosis"].fillna("")
    out["grupo"] = out["grupo"].fillna("Sin clasificar")
    out["estrategia"] = out["estrategia"].fillna("Sin clasificar")
    out["fuente"] = out["fuente"].fillna("")
    out["alerta"] = out["alerta"].fillna("")
    out["VACUNA_DASHBOARD"] = pd.Categorical(out["VACUNA_DASHBOARD"], categories=DISPLAY_ORDER, ordered=True)
    return out.sort_values(["VACUNA_DASHBOARD"]).reset_index(drop=True)


def normalize_comuna_name(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .replace(
            {
                "Nunoa": "Ñuñoa",
                "Ńuńoa": "Ñuñoa",
                "Nuñoa": "Ñuñoa",
                "Maipu": "Maipú",
                "Penalolen": "Peñalolén",
                "Penaflor": "Peñaflor",
                "Maria Pinto": "María Pinto",
                "Estacion Central": "Estación Central",
                "Alhue": "Alhué",
            }
        )
    )


def add_ss_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["comuna"] = normalize_comuna_name(out["comuna"])
    out["servicio_salud"] = out["comuna"].map(COMUNA_TO_SS)
    return out


@st.cache_data(show_spinner=False)
def load_detail() -> tuple[pd.DataFrame, Path]:
    path = latest_dated_file(OUTPUT_DIR, "coberturas_vacunas_2024.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = enrich_metadata(df)

    comuna_source = None
    for candidate in ["COMUNA_CALCULO", "COMUNA_RESIDENCIA", "COMUNA"]:
        if candidate in df.columns:
            comuna_source = candidate
            break

    if comuna_source is None:
        raise KeyError("No se encontró una columna de comuna esperada en el archivo de detalle.")

    df["comuna"] = df[comuna_source].astype(str).str.strip()
    df["valid_denom"] = df["POBLACION_OBJETIVO"].notna()
    df = add_ss_column(df)
    return df, path


@st.cache_data(show_spinner=False)
def load_regional() -> tuple[pd.DataFrame, Path]:
    path = latest_dated_file(OUTPUT_DIR, "coberturas_vacunas_2024.xlsx")
    df = pd.read_excel(path, sheet_name="Resumen_Regional")
    df = enrich_metadata(df)
    return df, path


def aggregate_ss(df: pd.DataFrame) -> pd.DataFrame:
    tmp = df.copy()
    tmp["VACUNA_DASHBOARD"] = tmp["VACUNA_DASHBOARD"].astype(str)
    key_cols = ["servicio_salud", "VACUNA_DASHBOARD"]
    sums = (
        tmp.groupby(key_cols, dropna=False, observed=True)[["VACUNAS_ADMINISTRADAS", "POBLACION_OBJETIVO"]]
        .sum()
        .reset_index()
    )
    meta = (
        tmp[["VACUNA_DASHBOARD", "vacuna", "dosis", "grupo", "estrategia", "fuente"]]
        .drop_duplicates(subset=["VACUNA_DASHBOARD"])
        .reset_index(drop=True)
    )
    grouped = sums.merge(meta, on="VACUNA_DASHBOARD", how="left")
    grouped["PORC_COBERTURA"] = (
        grouped["VACUNAS_ADMINISTRADAS"] / grouped["POBLACION_OBJETIVO"].replace(0, pd.NA) * 100
    ).round(1)
    grouped["PORC_COBERTURA"] = grouped["PORC_COBERTURA"].fillna(0)
    grouped["alerta"] = ""
    return grouped


def style_percent_table(df: pd.DataFrame):
    pct_cols = [c for c in df.columns if "(%)" in str(c)]
    fmt = {c: "{:.1f}%" for c in pct_cols}
    for col in df.columns:
        if col in {"Vacunados", "Población objetivo", "Registros sin denominador"}:
            fmt[col] = "{:,.0f}"

    def pct_bold(col: pd.Series):
        return ["font-weight: 700" if col.name in pct_cols else "" for _ in col]

    return (
        df.style.format(fmt, na_rep="")
        .apply(pct_bold, axis=0)
        .set_table_styles([{"selector": "th", "props": [("font-weight", "700")]}])
    )


def to_excel_bytes(df: pd.DataFrame, quality_df: pd.DataFrame | None = None) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="tabla_filtrada")
        if quality_df is not None and not quality_df.empty:
            quality_df.to_excel(writer, index=False, sheet_name="calidad_datos")
    buffer.seek(0)
    return buffer.getvalue()


def render_provisional_badge():
    st.markdown(
        """
        <div class="provisional-badge">Datos Provisorios</div>
        """,
        unsafe_allow_html=True,
    )


detail_df, detail_path = load_detail()
regional_df, regional_path = load_regional()

valid_detail_df = detail_df[detail_df["valid_denom"]].copy()
invalid_detail_df = detail_df[~detail_df["valid_denom"]].copy()

st.title("Dashboard Coberturas Vacunas Programáticas")
render_provisional_badge()
st.caption("Año 2024. Vista de coberturas regionales y comunales basada en los outputs consolidados del programa.")

with st.sidebar:
    st.header("Filtros")
    st.caption("Año fijo: 2024")

    level = st.selectbox("Nivel", ["Regional", "Comuna"], index=0)

    strategy_options = ["Todas"] + sorted(regional_df["estrategia"].dropna().unique().tolist())
    strategy_choice = st.selectbox("Población / grupo", strategy_options, index=0)

    vaccine_options = ["Todas"] + [VACUNA_META[k]["vacuna"] for k in DISPLAY_ORDER]
    vaccine_options = list(dict.fromkeys(vaccine_options))
    vaccine_choice = st.selectbox("Vacuna", vaccine_options, index=0)

    if vaccine_choice == "Todas":
        dose_options = ["Todas"] + sorted(regional_df["dosis"].dropna().unique().tolist())
        dose_choice = st.selectbox("Dosis", dose_options, index=0)
    else:
        possible_doses = regional_df.loc[regional_df["vacuna"] == vaccine_choice, "dosis"].dropna().unique().tolist()
        possible_doses = [d for d in possible_doses if d]
        if len(possible_doses) <= 1:
            dose_choice = possible_doses[0] if possible_doses else "Todas"
            if dose_choice != "Todas":
                st.markdown(f"**Dosis:** {dose_choice}")
        else:
            dose_options = ["Todas"] + sorted(possible_doses)
            dose_choice = st.selectbox("Dosis", dose_options, index=0)

    show_only_pct = st.checkbox("Mostrar solo porcentajes", value=False)


if level == "Regional":
    source_df = regional_df.copy()
else:
    source_df = valid_detail_df.copy()

if strategy_choice != "Todas":
    source_df = source_df[source_df["estrategia"] == strategy_choice]

if vaccine_choice != "Todas":
    source_df = source_df[source_df["vacuna"] == vaccine_choice]

if dose_choice != "Todas":
    source_df = source_df[source_df["dosis"] == dose_choice]

if level == "Comuna":
    ss_options = sorted(source_df["servicio_salud"].dropna().unique().tolist())
    with st.sidebar:
        selected_ss = st.multiselect("Servicio de Salud", ss_options, default=ss_options)
    if ss_options:
        source_df = source_df[source_df["servicio_salud"].isin(selected_ss)]

    comuna_options = sorted(source_df["comuna"].dropna().unique().tolist())
    with st.sidebar:
        selected_comunas = st.multiselect("Comuna", comuna_options, default=comuna_options)
    if comuna_options:
        source_df = source_df[source_df["comuna"].isin(selected_comunas)]

if source_df.empty:
    st.warning("No hay datos para la combinación de filtros seleccionada.")
    st.stop()

if level == "Regional":
    metric_label = "Vacunas visibles"
    metric_value = len(source_df)
else:
    metric_label = "Registros visibles"
    metric_value = len(source_df)

coverage_mean = source_df["PORC_COBERTURA"].mean()
coverage_min = source_df["PORC_COBERTURA"].min()
coverage_max = source_df["PORC_COBERTURA"].max()
coverage_total = (
    source_df["VACUNAS_ADMINISTRADAS"].sum() / source_df["POBLACION_OBJETIVO"].replace(0, pd.NA).sum() * 100
).round(1)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cobertura total", f"{coverage_total:.1f}%")
c2.metric(metric_label, f"{metric_value:,}".replace(",", "."))
c3.metric("Cobertura promedio", f"{coverage_mean:.1f}%")
c4.metric("Cobertura máxima", f"{coverage_max:.1f}%")

base_cols = ["vacuna", "dosis", "grupo", "fuente"]
rename_map = {
    "servicio_salud": "Servicio de Salud",
    "vacuna": "Vacuna",
    "dosis": "Dosis",
    "grupo": "Población / cohorte",
    "fuente": "Fuente denominador",
    "comuna": "Comuna",
    "VACUNAS_ADMINISTRADAS": "Vacunados",
    "POBLACION_OBJETIVO": "Población objetivo",
    "PORC_COBERTURA": "Cobertura (%)",
}

if level == "Comuna":
    base_cols = ["servicio_salud", "comuna"] + base_cols

display_cols = base_cols + ["VACUNAS_ADMINISTRADAS", "POBLACION_OBJETIVO", "PORC_COBERTURA"]
display_df = source_df[display_cols].copy().rename(columns=rename_map)

if show_only_pct:
    keep_cols = [rename_map[c] for c in base_cols] + ["Cobertura (%)"]
    display_df = display_df[keep_cols]

st.subheader("Tabla")
st.dataframe(
    style_percent_table(display_df),
    width="stretch",
    hide_index=True,
)

quality_summary = pd.DataFrame(
    [
        {
            "Archivo detalle": detail_path.name,
            "Archivo regional": regional_path.name,
            "Registros válidos": int(valid_detail_df.shape[0]),
            "Registros sin denominador": int(invalid_detail_df.shape[0]),
            "Comunas válidas RM": int(valid_detail_df["comuna"].nunique()),
            "Servicios de Salud RM": int(valid_detail_df["servicio_salud"].nunique()),
        }
    ]
)

with st.expander("Metodología y calidad de datos"):
    st.markdown(
        """
        - La vista principal usa por defecto solo registros con denominador válido.
        - En la salida consolidada existen filas sin denominador, asociadas principalmente a vacunas escolares con códigos de comuna fuera de RM.
        - Las coberturas regionales provienen de la hoja `Resumen_Regional`, que evita duplicaciones de denominador en el consolidado.
        - En nivel comunal se muestra además el Servicio de Salud al que pertenece la comuna.
        - No se incluye nivel establecimiento porque los outputs finales actuales no traen identificador de establecimiento.
        """
    )
    st.dataframe(quality_summary, width="stretch", hide_index=True)

    if not invalid_detail_df.empty:
        invalid_sample = (
            invalid_detail_df[["comuna", "vacuna", "dosis", "COD_COMUNA_JOIN"]]
            .rename(
                columns={
                    "comuna": "Comuna residencia",
                    "vacuna": "Vacuna",
                    "dosis": "Dosis",
                    "COD_COMUNA_JOIN": "Código comuna join",
                }
            )
            .drop_duplicates()
            .sort_values(["Vacuna", "Comuna residencia"])
            .reset_index(drop=True)
        )
        st.markdown("**Muestra de registros excluidos por falta de denominador**")
        st.dataframe(invalid_sample, width="stretch", hide_index=True, height=240)

download_bytes = to_excel_bytes(display_df, quality_summary)

st.download_button(
    "Descargar tabla filtrada (Excel)",
    data=download_bytes,
    file_name=f"dashboard_programaticas_2024_{level.lower()}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
