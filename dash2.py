import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# Configurações Pipefy
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDY1MzQ1NzgsImp0aSI6ImUyZjRhYzc4LWNkMDAtNDc2Mi04MTAwLTgwYjQ1ZjYwNWQxNCIsInN1YiI6MzA0NzUxMTc1LCJ1c2VyIjp7ImlkIjozMDQ3NTExNzUsImVtYWlsIjoiY2FybG9zZ2FicmllbEBlamVjdHVmcm4uY29tLmJyIn19.g-dg4RVfW7-Mvl5K11dtT9sKX-sSWqThnvOZt2X3MsqoLcGazET6NxHKEcKO2mPm_l76hoqN-TuaAYJ7atD4Dw"
PIPEFY_URL = "https://app.pipefy.com/pipes/305708346"
PIPE_ID = "305708346"
PAGE_SIZE=100

# Função para puxar dados do Pipefy
@st.cache_data(show_spinner="Carregando dados do Pipefy...")
def get_cards():
    url = "https://api.pipefy.com/graphql"
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }

    all_cards = []
    has_next_page = True
    cursor = None

    while has_next_page:
        after_str = f', after: "{cursor}"' if cursor else ""
        query = f"""
        {{
          allCards(pipeId: {PIPE_ID}, first: {PAGE_SIZE}{after_str}) {{
            edges {{
              cursor
              node {{
                id
                title
                created_at
                current_phase {{
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

        edges = response["data"]["allCards"]["edges"]
        for edge in edges:
            node = edge["node"]
            all_cards.append({
                "ID": node["id"],
                "Título": node["title"],
                "Criado em": node["created_at"],
                "Fase Atual": node["current_phase"]["name"]
            })

        page_info = response["data"]["allCards"]["pageInfo"]
        has_next_page = page_info["hasNextPage"]
        cursor = page_info["endCursor"]

    df = pd.DataFrame(all_cards)

    # Conversão de datas
    if not df.empty:
        df["Criado em"] = pd.to_datetime(df["Criado em"], errors="coerce")
    return df

# Interface Streamlit
st.set_page_config(page_title="Dashboard Pipefy", layout="wide")
st.title("📊 Dashboard - Pipefy")

df = get_cards()

if not df.empty:
    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Cards", len(df))
    col2.metric("Fases Únicas", df["Fase Atual"].nunique())

    ultima_data = df["Criado em"].max()
    ultima_data_str = ultima_data.strftime("%d/%m/%Y") if pd.notna(ultima_data) else "-"
    col3.metric("Data mais recente", ultima_data_str)

    st.markdown("---")

    # Gráfico de barras: cards por fase
    st.subheader("📌 Cards por Fase")
    fase_count = df["Fase Atual"].value_counts().reset_index()
    fase_count.columns = ["Fase", "Quantidade"]
    fig_bar = px.bar(
        fase_count, x="Fase", y="Quantidade", color="Fase",
        text="Quantidade", title="Distribuição de Cards por Fase"
    )
    fig_bar.update_traces(textposition="outside")
    st.plotly_chart(fig_bar, use_container_width=True)

    # Gráfico de linha: cards por data
    st.subheader("📅 Cards Criados ao Longo do Tempo")
    date_count = df.groupby(df["Criado em"].dt.date).size().reset_index(name="Quantidade")
    date_count = date_count.sort_values("Criado em")
    fig_line = px.line(
        date_count, x="Criado em", y="Quantidade",
        markers=True, title="Evolução de Criação de Cards"
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # Tabela completa
    st.subheader("📋 Detalhes dos Cards")
    st.dataframe(df.sort_values("Criado em", ascending=False))
else:
    st.warning("Nenhum dado encontrado.")
