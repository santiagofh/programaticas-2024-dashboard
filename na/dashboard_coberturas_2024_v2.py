"""
dashboard_coberturas_2024_v2.py
Ejecutar: streamlit run dashboard_coberturas_2024_v2.py
"""

import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Coberturas Vacunales RM 2024",
    page_icon="💉",
    layout="centered",
)

st.markdown("""
<style>
    [data-testid="metric-container"] {
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    [data-testid="stMetricDelta"] { display: none; }
    h1 { font-weight: 800; letter-spacing: -1px; }
    hr { border-color: #e9ecef; }
    .caption-text {
        font-size: 0.75rem;
        opacity: 0.6;
        margin-top: 32px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

DIR_OUTPUT = Path(__file__).parent / "output"

# ─────────────────────────────────────────────
# MAPA: VACUNA_DASHBOARD → (Vacuna, Dosis)
# ─────────────────────────────────────────────
VACUNA_DOSIS_MAP = {
    "VACUNA BCG":                                  ("BCG",                        "Dosis Única"),
    "VACUNA HEPATITIS A PEDIATRICA":               ("Hepatitis A Pediátrica",     "Dosis Única"),
    "VACUNA HEPATITIS B RN":                       ("Hepatitis B RN",             "Dosis Única"),
    "VACUNA HEXAVALENTE 1RA DOSIS":                ("Hexavalente",                "1ª Dosis"),
    "VACUNA HEXAVALENTE 2DA DOSIS":                ("Hexavalente",                "2ª Dosis"),
    "VACUNA HEXAVALENTE 3RA DOSIS":                ("Hexavalente",                "3ª Dosis"),
    "VACUNA HEXAVALENTE REFUERZO":                 ("Hexavalente",                "Refuerzo"),
    "VACUNA MENINGOCOCICA CONJUGADA DOSIS UNICA":  ("Meningocócica Conjugada",    "Dosis Única"),
    "VACUNA MENINGOCOCICA RECOMBINANTE 1RA DOSIS": ("Meningocócica Recombinante", "1ª Dosis"),
    "VACUNA MENINGOCOCICA RECOMBINANTE 2DA DOSIS": ("Meningocócica Recombinante", "2ª Dosis"),
    "VACUNA MENINGOCOCICA RECOMBINANTE REFUERZO":  ("Meningocócica Recombinante", "Refuerzo"),
    "VACUNA NEUMOCOCICA CONJUGADA 1RA DOSIS":      ("Neumocócica Conjugada",      "1ª Dosis"),
    "VACUNA NEUMOCOCICA CONJUGADA 2DA DOSIS":      ("Neumocócica Conjugada",      "2ª Dosis"),
    "VACUNA NEUMOCOCICA CONJUGADA REFUERZO":       ("Neumocócica Conjugada",      "Refuerzo"),
    "VACUNA SRP (TRIVIRICA) 1RA DOSIS":            ("SRP (Trivirica)",            "1ª Dosis"),
    "VACUNA SRP (TRIVIRICA) 2DA DOSIS":            ("SRP (Trivirica)",            "2ª Dosis"),
    "VACUNA VARICELA 1RA DOSIS":                   ("Varicela",                   "1ª Dosis"),
    "VACUNA VARICELA 2DA DOSIS":                   ("Varicela",                   "2ª Dosis"),
}

# Orden deseado para las dosis (para que el selectbox no quede aleatorio)
ORDEN_DOSIS = ["Dosis Única", "1ª Dosis", "2ª Dosis", "3ª Dosis", "Refuerzo"]

# ─────────────────────────────────────────────
# CARGA
# ─────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    df = pd.read_csv(DIR_OUTPUT / "coberturas_vacunas_2024.csv", encoding="utf-8-sig")
    df = df[df["POBLACION_OBJETIVO"] > 0].copy()
    # Agregar columnas separadas de vacuna y dosis
    df["VACUNA_NOMBRE"] = df["VACUNA_DASHBOARD"].map(
        lambda x: VACUNA_DOSIS_MAP.get(x, (x, ""))[0]
    )
    df["DOSIS_NOMBRE"] = df["VACUNA_DASHBOARD"].map(
        lambda x: VACUNA_DOSIS_MAP.get(x, ("", x))[1]
    )
    return df

df = cargar_datos()

# Listas únicas en orden
vacunas_lista = sorted(df["VACUNA_NOMBRE"].unique())

# ─────────────────────────────────────────────
# SIDEBAR — selector en cascada
# ─────────────────────────────────────────────
st.sidebar.markdown("## 💉 Coberturas RM")
st.sidebar.markdown("---")

# 1. Seleccionar vacuna
vacuna_sel = st.sidebar.selectbox(
    "Vacuna",
    vacunas_lista,
)

# 2. Seleccionar dosis (solo las que existen para esa vacuna, en orden)
dosis_disponibles = df[df["VACUNA_NOMBRE"] == vacuna_sel]["DOSIS_NOMBRE"].unique().tolist()
dosis_disponibles = [d for d in ORDEN_DOSIS if d in dosis_disponibles]  # orden correcto

# Si solo hay una dosis, no mostrar el selectbox (ocultar automáticamente)
if len(dosis_disponibles) == 1:
    dosis_sel = dosis_disponibles[0]
    st.sidebar.markdown(f"**Dosis:** {dosis_sel}")
else:
    dosis_sel = st.sidebar.selectbox(
        "Dosis",
        dosis_disponibles,
    )

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<small>Fuente: RNI · SRCeI<br>Región Metropolitana · 2024<br>Primer corte preliminar</small>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# FILTRO
# ─────────────────────────────────────────────
df_vac = (
    df[
        (df["VACUNA_NOMBRE"] == vacuna_sel) &
        (df["DOSIS_NOMBRE"]  == dosis_sel)
    ]
    .sort_values("PORC_COBERTURA", ascending=False)
    .reset_index(drop=True)
)

total_num    = df_vac["VACUNAS_ADMINISTRADAS"].sum()
total_denom  = df_vac["POBLACION_OBJETIVO"].sum()
cob_regional = round(total_num / total_denom * 100, 1) if total_denom > 0 else 0.0

# ─────────────────────────────────────────────
# ENCABEZADO
# ─────────────────────────────────────────────
st.markdown("# Coberturas Vacunales")
st.markdown(f"### {vacuna_sel} · {dosis_sel}")
st.markdown("Región Metropolitana · Año 2024 · Primer corte preliminar")
st.divider()

# ─────────────────────────────────────────────
# MÉTRICAS
# ─────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Cobertura regional", f"{cob_regional}%")
c2.metric("Vacunas administradas", f"{total_num:,}")
c3.metric("Población objetivo", f"{total_denom:,}")

st.divider()

# ─────────────────────────────────────────────
# TABLA POR COMUNA
# ─────────────────────────────────────────────
st.markdown("#### Cobertura por comuna")

def semaforo(val):
    if val >= 95:    return "background-color:#d4edda"
    elif val >= 90:  return "background-color:#fff3cd"
    elif val >= 80:  return "background-color:#fde8d8"
    else:            return "background-color:#f8d7da"

tabla = df_vac[[
    "COMUNA_RESIDENCIA", "POBLACION_OBJETIVO",
    "VACUNAS_ADMINISTRADAS", "PORC_COBERTURA"
]].copy()
tabla.columns = ["Comuna", "Población objetivo", "Vacunados", "% Cobertura"]

st.dataframe(
    tabla.style
        .format({
            "% Cobertura":       "{:.1f}%",
            "Población objetivo": "{:,.0f}",
            "Vacunados":         "{:,.0f}",
        })
        .applymap(semaforo, subset=["% Cobertura"]),
    hide_index=True,
    use_container_width=True,
    height=420,
)

st.divider()

# ─────────────────────────────────────────────
# GRÁFICO — Población vs Vacunados
# ─────────────────────────────────────────────
st.markdown("#### Población objetivo vs Vacunados — Total Regional")

df_totales = pd.DataFrame({
    "": ["Población objetivo", "Vacunados"],
    "Cantidad": [total_denom, total_num],
})

fig = px.bar(
    df_totales,
    x="",
    y="Cantidad",
    color="",
    text="Cantidad",
    color_discrete_map={
        "Población objetivo": "#ced4da",
        "Vacunados":          "#339af0",
    },
)
fig.update_traces(
    texttemplate="%{text:,.0f}",
    textposition="outside",
    marker_line_width=0,
    width=0.35,
)
fig.update_layout(
    showlegend=False,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=20, b=0),
    yaxis=dict(
        showgrid=True,
        gridcolor="rgba(128,128,128,0.15)",
        zeroline=False,
        range=[0, max(total_denom, total_num) * 1.18],
        tickformat=",",
    ),
    xaxis=dict(showgrid=False),
    height=380,
    font=dict(family="sans-serif", size=13),
    bargap=0.5,
)

st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# NOTA AL PIE
# ─────────────────────────────────────────────
st.divider()
st.markdown(f"""
<div class="caption-text">
    <strong>Nota metodológica</strong><br>
    El <strong>numerador</strong> corresponde a vacunados del RNI año 2024,
    filtrados por cohorte de nacimiento y comuna de residencia (Metodología DEIS-PNI v2.0).<br>
    El <strong>denominador</strong> corresponde a nacidos vivos inscritos en el SRCeI
    para la cohorte de edad objetivo de cada vacuna.<br>
    Coberturas superiores al 100% pueden reflejar diferencias de residencia entre fuentes RNI y SRCeI.<br>
    La cobertura del <em>Refuerzo Meningocócica Recombinante</em> es baja por diseño:
    esta dosis se incorporó al PNI el 1 de noviembre de 2024.<br><br>
    Fuente: RNI · SRCeI · SEREMI de Salud Región Metropolitana · 2024
</div>
""", unsafe_allow_html=True)
