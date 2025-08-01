import requests
import pandas as pd
import streamlit as st

PIPEFY_TOKEN = ""
PIPEFY_URL = ""
PIPE_ID = ""

st.title("📌 Dashboard Pipefy")

# Informações do usuário
#PIPEFY_TOKEN = st.secrets["PIPEFY_TOKEN"]
#PIPE_ID = st.secrets["PIPE_ID"]

def get_data():
    url = "https://api.pipefy.com/graphql"
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    query = f"""
    {{
      pipe(id: {PIPE_ID}) {{
        name
        cards {{
          edges {{
            node {{
              id
              title
              created_at
              current_phase {{
                name
              }}
            }}
          }}
        }}
      }}
    }}
    """
    response = requests.post(url, json={"query": query}, headers=headers)
    cards = response.json()["data"]["pipe"]["cards"]["edges"]
    data = [{
        "ID": c["node"]["id"],
        "Título": c["node"]["title"],
        "Criado em": c["node"]["created_at"],
        "Fase Atual": c["node"]["current_phase"]["name"]
    } for c in cards]
    return pd.DataFrame(data)

df = get_data()
st.dataframe(df)