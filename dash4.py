import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# =================== Sidebar - Configurações ===================
st.sidebar.header("⚙️ Configurações Pipefy")

PIPEFY_TOKEN = st.sidebar.text_input("Token Pipefy", type="password")
PIPEFY_URL = st.sidebar.text_input("URL do Pipe", value="https://app.pipefy.com/pipes/")
PIPE_ID = st.sidebar.text_input("ID do Pipe")
PAGE_SIZE = st.sidebar.number_input("Tamanho da página", min_value=10, max_value=500, value=100, step=10)

st.sidebar.markdown("---")

# Checar se todas as variáveis foram preenchidas
if not all([PIPEFY_TOKEN, PIPE_ID]):
    st.warning("Preencha o Token e o ID do Pipe para carregar os dados.")
    st.stop()

# =================== Função para puxar dados do Pipefy ===================
@st.cache_data(show_spinner=True)
def get_cards(pipe_id, token, page_size):
    url = "https://api.pipefy.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    all_cards = []
    has_next_page = True
    cursor = None

    while has_next_page:
        after_str = f', after: "{cursor}"' if cursor else ""
        query = f"""
        {{
          allCards(pipeId: {pipe_id}, first: {page_size}{after_str}) {{
            edges {{
              cursor
              node {{
                id
                title
                created_at
                current_phase {{
                  name
                }}
                labels {{
                  name
                }}
              }}
            }}
            pageInfo {{
              hasNextPage
              endCursor
            }}
          }}
        }}
        """

        response = requests.post(url, json={"query": query}, headers=headers).json()

        if "errors" in response:
            st.error(f"Erro ao buscar dados do Pipefy: {response['errors']}")
            return pd.DataFrame()

        edges = response["data"]["allCards"]["edges"]
        for edge in edges:
            node = edge["node"]
            labels = [lbl["name"] for lbl in node.get("labels", [])]  # Lista de labels
            all_cards.append({
                "ID": node["id"],
                "Título": node["title"],
                "Criado em": node["created_at"],
                "Fase Atual": node["current_phase"]["name"] if node["current_phase"] else "N/A",
                "Labels": labels
            })

        page_info = response["data"]["allCards"]["pageInfo"]
        has_next_page = page_info["hasNextPage"]
        cursor = page_info["endCursor"]

    df = pd.DataFrame(all_cards)
    # Converter "Criado em" para datetime
    if not df.empty:
        df["Criado em"] = pd.to_datetime(df["Criado em"])
    return df

# =================== Carregar Dados ===================
st.title("📊 Dashboard Pipefy")
df = get_cards(PIPE_ID, PIPEFY_TOKEN, PAGE_SIZE)

if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

# =================== KPIs Gerais ===================
st.subheader("📈 KPIs Gerais")
col1, col2, col3 = st.columns(3)
col1.metric("Total de Cards", len(df))
col2.metric("Fases Únicas", df["Fase Atual"].nunique())
col3.metric("Data mais recente", df["Criado em"].max().strftime("%d/%m/%Y"))

st.markdown("---")

# =================== Gráficos Gerais ===================
# Cards por Fase
st.subheader("📌 Cards por Fase")
fase_count = df["Fase Atual"].value_counts().reset_index()
fase_count.columns = ["Fase", "Quantidade"]
fig_bar = px.bar(fase_count, x="Fase", y="Quantidade", color="Fase",
                 text="Quantidade", title="Distribuição de Cards por Fase")
st.plotly_chart(fig_bar, use_container_width=True)

# Evolução ao longo do tempo
st.subheader("📅 Cards Criados ao Longo do Tempo")
date_count = df.groupby(df["Criado em"].dt.date).size().reset_index(name="Quantidade")
fig_line = px.line(date_count, x="Criado em", y="Quantidade",
                   markers=True, title="Evolução de Criação de Cards")
st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

# =================== Progresso das Correções por Módulo ===================
st.subheader("🛠️ Progresso das Correções por Módulo")

# Normalizar Labels e Fase Atual
df["Labels_norm"] = df["Labels"].apply(lambda x: [lbl.strip() for lbl in x] if isinstance(x, list) else [])
df["Fase_norm"] = df["Fase Atual"].str.strip().str.lower()

# Lista de labels irrelevantes
labels_excluir = ["complexo", "tranquilo", "prioritária", "mediana", "alta", "mediano"]

# Módulos válidos
modulos = sorted({lbl for sublist in df["Labels_norm"] for lbl in sublist if lbl not in labels_excluir})

# Seletor de módulo
modulo_selecionado = st.selectbox("Escolha o módulo", modulos)

# Seleciona cards do módulo
df_mod = df[df["Labels_norm"].apply(lambda x: modulo_selecionado in x)]

# Fases que indicam conclusão
fases_concluidas = ["validar", "produção", "concluído"]

# Cálculo de progresso
total = len(df_mod)
concluidos = len(df_mod[df_mod["Fase_norm"].isin(fases_concluidas)])
percentual = round((concluidos / total) * 100, 1) if total > 0 else 0

# Gráfico 1: Progresso geral do módulo
fig1 = px.pie(
    names=["Concluídos", "Pendentes"],
    values=[concluidos, total - concluidos],
    hole=0.4,
    title=f"Progresso Geral - {modulo_selecionado}"
)
fig1.update_traces(textinfo="percent+label")

# Gráfico 2: Distribuição por fase
fase_count_mod = df_mod["Fase_norm"].value_counts().reset_index()
fase_count_mod.columns = ["Fase", "Quantidade"]
fig2 = px.bar(
    fase_count_mod,
    x="Quantidade",
    y="Fase",
    orientation="h",
    text="Quantidade",
    title=f"Distribuição de Cards por Fase - {modulo_selecionado}",
    color="Quantidade",
    color_continuous_scale="Blues"
)
fig2.update_traces(texttemplate="%{text}", textposition="outside")

# Mostrar gráficos lado a lado
col1, col2 = st.columns(2)
col1.plotly_chart(fig1, use_container_width=True)
col2.plotly_chart(fig2, use_container_width=True)

# =================== Tabela completa ===================
st.markdown("---")
st.subheader("📋 Detalhes dos Cards")
st.dataframe(df)
