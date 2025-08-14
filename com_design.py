import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Pipefy Dashboard", layout="wide")

# --- CSS Personalizado ---
st.markdown("""
    <style>
        .metric-card {
            background-color: #F5F5F5;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            text-align: center;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #1A73E8;
        }
        .metric-label {
            font-size: 1rem;
            color: #555;
        }
        .stDataFrame thead tr th {
            background-color: #1A73E8;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Pipefy Dashboard")

# --- Carrega segredos ---
PIPEFY_TOKEN = st.secrets["PIPEFY_TOKEN"]
PIPE_ID = st.secrets["PIPE_ID"]

@st.cache_data(ttl=300)
def get_data(pipe_id, token):
    url = "https://api.pipefy.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    query = f"""
    {{
      pipe(id: {pipe_id}) {{
        name
        cards(first: 100) {{
          edges {{
            node {{
              id
              title
              created_at
              current_phase {{
                name
              }}
              fields {{
                name
                value
              }}
            }}
          }}
        }}
      }}
    }}
    """

    response = requests.post(url, json={"query": query}, headers=headers)
    cards = response.json()["data"]["pipe"]["cards"]["edges"]

    data = []
    for card in cards:
        node = card["node"]
        card_data = {
            "ID": node["id"],
            "Título": node["title"],
            "Criado em": node["created_at"],
            "Fase Atual": node["current_phase"]["name"]
        }
        for field in node["fields"]:
            card_data[field["name"]] = field["value"]
        data.append(card_data)

    df = pd.DataFrame(data)
    df["Criado em"] = pd.to_datetime(df["Criado em"]).dt.strftime('%d/%m/%Y %H:%M')
    return df

# --- Dados ---
with st.spinner("🔄 Buscando cards do Pipefy..."):
    df = get_data(PIPE_ID, PIPEFY_TOKEN)

# --- Sidebar com filtros ---
st.sidebar.header("🔍 Filtros")
fases = df["Fase Atual"].dropna().unique().tolist()
filtro_fase = st.sidebar.multiselect("Filtrar por fase:", fases, default=fases)
df_filtrado = df[df["Fase Atual"].isin(filtro_fase)]

# --- Métricas (cards de resumo) ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Total de Cards</div>
        </div>
    """.format(len(df_filtrado)), unsafe_allow_html=True)

with col2:
    fases_unicas = df_filtrado["Fase Atual"].nunique()
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{fases_unicas}</div>
            <div class="metric-label">Fases Ativas</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    datas = pd.to_datetime(df_filtrado["Criado em"], format='%d/%m/%Y %H:%M')
    data_mais_recente = datas.max().strftime("%d/%m/%Y %H:%M") if not datas.empty else "-"
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{data_mais_recente}</div>
            <div class="metric-label">Último Card Criado</div>
        </div>
    """, unsafe_allow_html=True)

# --- Tabela com os dados filtrados ---
st.markdown("### 📋 Lista de Cards")
st.dataframe(df_filtrado, use_container_width=True, height=500)
