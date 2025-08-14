import requests
import pandas as pd
import streamlit as st

PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDY1MzQ1NzgsImp0aSI6ImUyZjRhYzc4LWNkMDAtNDc2Mi04MTAwLTgwYjQ1ZjYwNWQxNCIsInN1YiI6MzA0NzUxMTc1LCJ1c2VyIjp7ImlkIjozMDQ3NTExNzUsImVtYWlsIjoiY2FybG9zZ2FicmllbEBlamVjdHVmcm4uY29tLmJyIn19.g-dg4RVfW7-Mvl5K11dtT9sKX-sSWqThnvOZt2X3MsqoLcGazET6NxHKEcKO2mPm_l76hoqN-TuaAYJ7atD4Dw"
PIPEFY_URL = "https://app.pipefy.com/pipes/305708346"
PIPE_ID = "305708346"

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
        allCards(pipeId: {PIPE_ID}, first: 50) {{
          edges {{
            node {{
              id
              title
              createdAt
            }}
          }}
        }}
      }}
    """
    response = requests.post(url, json={"query": query}, headers=headers)
    print(response.json())
    cards = response.json()["data"]["allCards"]["edges"]
    data = [{
        "ID": c["node"]["id"],
        "Título": c["node"]["title"],
    } for c in cards]
    return pd.DataFrame(data)

df = get_data()
st.dataframe(df)