"""
dashboard_coberturas_2024.py
Ejecutar: streamlit run dashboard_coberturas_2024.py
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
    /* Métricas */
    [data-testid="metric-container"] {
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }

    /* Quitar borde rojo de streamlit */
    [data-testid="stMetricDelta"] { display: none; }

    /* Título principal */
    h1 { font-weight: 800; letter-spacing: -1px; }

    /* Divisor más sutil */
    hr { border-color: #e9ecef; }

    /* Caption */
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
# CARGA
# ─────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    df = pd.read_csv(DIR_OUTPUT / "coberturas_vacunas_2024.csv", encoding="utf-8-sig")
    return df[df["POBLACION_OBJETIVO"] > 0].copy()

df = cargar_datos()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
st.sidebar.markdown("## 💉 Coberturas RM")
st.sidebar.markdown("---")
vacuna_sel = st.sidebar.selectbox(
    "Selecciona una vacuna",
    sorted(df["VACUNA_DASHBOARD"].dropna().unique()),
    label_visibility="collapsed",
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<small>Fuente: RNI · SRCel<br>Región Metropolitana · 2024<br>Cifras preliminares</small>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# FILTRO
# ─────────────────────────────────────────────
df_vac = (
    df[df["VACUNA_DASHBOARD"] == vacuna_sel]
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
st.markdown(f"### {vacuna_sel}")
st.markdown("Región Metropolitana · Año 2024 · Cifras preliminares")
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
# GRÁFICO 1 — Tabla de comunas
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
        .format({"% Cobertura": "{:.1f}%", "Población objetivo": "{:,.0f}", "Vacunados": "{:,.0f}"})
        .applymap(semaforo, subset=["% Cobertura"]),
    hide_index=True,
    use_container_width=True,
    height=420,
)

st.divider()

# ─────────────────────────────────────────────
# GRÁFICO 2 — Barras totales regionales
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
    El <strong>numerador</strong> corresponde a las vacunas administradas registradas en el RNI durante el año 2024,
    filtradas por comuna de residencia del paciente.<br>
    El <strong>denominador</strong> corresponde a los nacidos vivos inscritos en el SRCel
    para la cohorte de edad objetivo de cada vacuna.<br>
    Coberturas superiores al 100% pueden reflejar vacunación de cohortes de años anteriores
    o diferencias en el corte de datos entre fuentes.<br><br>
    Fuente: RNI · SRCel · SEREMI de Salud Región Metropolitana · 2024
</div>
""", unsafe_allow_html=True)