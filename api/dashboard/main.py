import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Demandas",
    page_icon="📊",
    layout="wide"
)

# Configuração da API
API_URL = "http://localhost:8000/api/v1"

def get_api_data(endpoint):
    """Função para fazer requisições à API"""
    try:
        response = requests.get(f"{API_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao conectar com a API: {str(e)}")
        return None

def format_metric(value):
    """Formata valores para exibição"""
    if isinstance(value, (int, float)):
        return f"{value:,.0f}".replace(",", ".")
    return value

# Sidebar
st.sidebar.title("Filtros")

# Buscar intervalo de datas
date_range = get_api_data("metrics/date-range")
if date_range:
    min_date = datetime.fromisoformat(date_range["start_date"].split("T")[0])
    max_date = datetime.fromisoformat(date_range["end_date"].split("T")[0])
else:
    min_date = datetime.now() - timedelta(days=30)
    max_date = datetime.now()

# Seletor de data
selected_date = st.sidebar.date_input(
    "Data",
    value=max_date.date(),
    min_value=min_date.date(),
    max_value=max_date.date()
)

# Buscar equipes
teams_response = get_api_data("metrics/teams")
if teams_response:
    teams = ["Todas"] + teams_response
else:
    teams = ["Todas"]

# Seletor de equipe
selected_team = st.sidebar.selectbox("Equipe", teams)

# Título principal
st.title("📊 Dashboard de Demandas")

# Buscar métricas
endpoint = f"metrics/daily?date={selected_date}"
if selected_team != "Todas":
    endpoint += f"&team={selected_team}"

metrics = get_api_data(endpoint)

if metrics:
    # Criar colunas para métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Resolvidos",
            format_metric(metrics["resolvidos"]),
            delta=None
        )
    
    with col2:
        st.metric(
            "Em Análise",
            format_metric(metrics["analise"]),
            delta=None
        )
    
    with col3:
        st.metric(
            "Pendentes (Ativo)",
            format_metric(metrics["pendente_ativo"]),
            delta=None
        )
    
    with col4:
        st.metric(
            "Pendentes (Receptivo)",
            format_metric(metrics["pendente_receptivo"]),
            delta=None
        )
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribuição de Status")
        status_data = {
            "Status": ["Resolvidos", "Em Análise", "Pendentes (Ativo)", "Pendentes (Receptivo)"],
            "Quantidade": [
                metrics["resolvidos"],
                metrics["analise"],
                metrics["pendente_ativo"],
                metrics["pendente_receptivo"]
            ]
        }
        fig = px.pie(
            status_data,
            values="Quantidade",
            names="Status",
            title="Distribuição por Status"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Métricas Adicionais")
        additional_metrics = {
            "Métrica": [
                "Quitados",
                "Aprovados",
                "Receptivo Total",
                "Análise do Dia"
            ],
            "Valor": [
                metrics["quitado"],
                metrics["aprovados"],
                metrics["receptivo"],
                metrics["analise_dia"]
            ]
        }
        fig = px.bar(
            additional_metrics,
            x="Métrica",
            y="Valor",
            title="Métricas Adicionais"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabela detalhada
    st.subheader("Detalhamento das Métricas")
    metrics_df = pd.DataFrame({
        "Métrica": [
            "Resolvidos",
            "Em Análise",
            "Pendentes (Ativo)",
            "Pendentes (Receptivo)",
            "Quitados",
            "Aprovados",
            "Receptivo Total",
            "Análise do Dia"
        ],
        "Valor": [
            metrics["resolvidos"],
            metrics["analise"],
            metrics["pendente_ativo"],
            metrics["pendente_receptivo"],
            metrics["quitado"],
            metrics["aprovados"],
            metrics["receptivo"],
            metrics["analise_dia"]
        ]
    })
    st.dataframe(
        metrics_df,
        column_config={
            "Valor": st.column_config.NumberColumn(
                "Valor",
                format="%d"
            )
        },
        hide_index=True
    )
else:
    st.warning("Não foi possível carregar os dados. Verifique se a API está funcionando.")
