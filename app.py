import streamlit as st
import pandas as pd
import plotly.express as px
import pandas as pd

df = pd.read_csv("/content/Ranking.csv")

#Limpiar texto y convertir a datetime
s = df['lastupdated'].astype(str).str.strip()
try:
    dt = pd.to_datetime(s, errors='coerce', format='mixed')
except TypeError:
    s1 = s.str.replace('-', '/', regex=False)
    dt = pd.to_datetime(s1, format='%m/%d/%Y', errors='coerce')
    dt = dt.fillna(pd.to_datetime(s, errors='coerce'))

df['lastupdated_dt'] = dt

#Calcular distancia absoluta a hoy
hoy = pd.Timestamp.today().normalize()
df_valid = df.dropna(subset=['lastupdated_dt']).copy()
df_valid['lastupdated_date'] = df_valid['lastupdated_dt'].dt.normalize()
df_valid['diff_to_today'] = (df_valid['lastupdated_date'] - hoy).abs()

#Elegir por cada 'name' la fila más cercana a hoy
df_keep = (
    df_valid
      .sort_values(['name', 'diff_to_today', 'lastupdated_dt'],
                   ascending=[True, True, False])
      .drop_duplicates(subset='name', keep='first')
      .drop(columns=['diff_to_today', 'lastupdated_date'])
      .reset_index(drop=True)
)

print(df_keep.shape)
print(df_keep.head())

# Configuración de la página
st.set_page_config(
    page_title="Chess Ranking Dashboard",
    layout="wide"
)

# Paleta de colores con Markdown/CSS
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f5f5f7;
        color: #000000;
    }

    [data-testid="stSidebar"] {
        background-color: #040085;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff;
    }

    h1, h2, h3, h4 {
        color: #003366;
    }

    [data-testid="stMetricLabel"] {
        color: #003366;
    }
    [data-testid="stMetricValue"] {
        color: #000000;
    }

    .stButton > button {
        background-color: #003399;
        color: #ffffff;
        border-radius: 8px;
        border: none;
    }
    .stButton > button:hover {
        background-color: #001f7f;
        color: #ffffff;
    }

    [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    .stRadio > label, .stRadio div {
        color: #000000;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
    [data-testid="stToolbar"] {
        background-color: #040085;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        color: #ff4b4b; /* color del texto del título principal */
        margin-bottom: 0.2rem;
    }
    .main-subtitle {
        font-size: 1.4rem;
        font-weight: 500;
        color: #f97316; /* color del texto del subtítulo */
        margin-top: 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-title">Dashboard de Rankings y Ratings de Ajedrez</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-subtitle">KPIs principales de ratings (toda la base)</div>',
    unsafe_allow_html=True
)

# Carga de datos
@st.cache_data
def load_data():
    df = pd.read_csv("/content/Ranking.csv")
    return df

df = load_data()

# Mapeo de nombres amigables a columnas
RATING_MAP = {
    "Classical": "classicalrating",
    "Rapid": "rapidrating",
    "Blitz": "blitzrating"
}

# Opciones generales
all_countries = sorted(df["country"].dropna().unique().tolist())
all_titles = sorted(df["title"].dropna().unique().tolist())
max_rank = int(df["rank"].max())

# KPIs PRINCIPALES

avg_classical = df["classicalrating"].mean()
avg_rapid = df["rapidrating"].mean()
avg_blitz = df["blitzrating"].mean()

kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.metric("Promedio Classical", f"{avg_classical:.1f}")

with kpi2:
    st.metric("Promedio Rapid", f"{avg_rapid:.1f}")

with kpi3:
    st.metric("Promedio Blitz", f"{avg_blitz:.1f}")

#  FILTROS GLOBALES (SIDEBAR)
with st.sidebar:
    st.header("Filtros globales")

    rating_choice_global = st.selectbox(
        "Tipo de rating",
        options=list(RATING_MAP.keys()),
        index=0,
        key="rating_choice_global"
    )
    rating_col_global = RATING_MAP[rating_choice_global]

    selected_countries = st.multiselect(
        "País",
        options=all_countries,
        default=all_countries,
        key="countries_global"
    )

    selected_titles = st.multiselect(
        "Título (GM, IM, etc.)",
        options=all_titles,
        default=all_titles,
        key="titles_global"
    )

    chart_type_global = st.radio(
        "Tipo de gráfica de distribución",
        options=["Histograma", "Violin", "Boxplot"],
        index=0,
        key="chart_type_global"
    )

    top_n_global = st.slider(
        "Top N jugadores (por rank) para comparativa",
        min_value=5,
        max_value=max_rank,
        value=min(50, max_rank),
        step=1,
        key="top_n_global"
    )

# Aplicar filtros globales a la base
df_filtered = df.copy()

if selected_countries:
    df_filtered = df_filtered[df_filtered["country"].isin(selected_countries)]

if selected_titles:
    df_filtered = df_filtered[df_filtered["title"].isin(selected_titles)]

# TABS

tab1, tab2, tab3 = st.tabs(["Ranking vs Rating", "Distribución ratings", "Top N - Comparación ratings"])

# Ranking vs Rating
with tab1:
    st.header("1. Ranking vs Rating")

    if df_filtered.empty:
        st.warning("No hay jugadores que cumplan con los filtros globales.")
    else:
        fig1 = px.scatter(
            df_filtered,
            x="rank",
            y=rating_col_global,
            color="country",
            hover_name="name",
            hover_data=["title"],
            title=f"Ranking vs {rating_choice_global} Rating",
            size=rating_col_global,
        )

        fig1.update_xaxes(autorange="reversed", title_text="Rank (1 = mejor)")
        fig1.update_yaxes(title_text=f"{rating_choice_global} rating")

        st.plotly_chart(fig1, use_container_width=True)

# Distribución de ratings por modalidad
with tab2:
    st.header("2. Distribución de ratings por modalidad")

    if df_filtered.empty:
        st.warning("No hay jugadores que cumplan con los filtros globales.")
    else:
        if chart_type_global == "Histograma":
            fig2 = px.histogram(
                df_filtered,
                x=rating_col_global,
                nbins=20,
                color="country",
                opacity=0.7,
                marginal="box",
                title=f"Distribución de {rating_choice_global} rating (Histograma)"
            )
            fig2.update_xaxes(title_text=f"{rating_choice_global} rating")
            fig2.update_yaxes(title_text="Número de jugadores")

        elif chart_type_global == "Violin":
            fig2 = px.violin(
                df_filtered,
                x="country",
                y=rating_col_global,
                box=True,
                points="all",
                title=f"Distribución de {rating_choice_global} rating por país (Violin)"
            )
            fig2.update_xaxes(title_text="País")
            fig2.update_yaxes(title_text=f"{rating_choice_global} rating")

        else:
            fig2 = px.box(
                df_filtered,
                x="country",
                y=rating_col_global,
                points="all",
                title=f"Distribución de {rating_choice_global} rating por país (Boxplot)"
            )
            fig2.update_xaxes(title_text="País")
            fig2.update_yaxes(title_text=f"{rating_choice_global} rating")

        st.plotly_chart(fig2, use_container_width=True)

# Comparación entre ratings
with tab3:
    st.header(f"3. Comparación entre ratings (Top {top_n_global} por rank)")

    if df_filtered.empty:
        st.warning("No hay jugadores que cumplan con los filtros globales.")
    else:
        df3 = df_filtered[df_filtered["rank"] <= top_n_global].copy()

        if df3.empty:
            st.warning("No hay jugadores dentro del Top N con los filtros seleccionados.")
        else:
            fig3 = px.scatter_matrix(
                df3,
                dimensions=["classicalrating", "rapidrating", "blitzrating"],
                color="country",
                hover_name="name",
                title=f"Comparación de ratings (Top {top_n_global} por rank)"
            )
            fig3.update_traces(diagonal_visible=False)
            st.plotly_chart(fig3, use_container_width=True)
