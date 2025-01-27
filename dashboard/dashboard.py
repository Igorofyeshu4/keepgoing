import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from data_processor import DataProcessor
import os

@st.cache_data
def load_data():
    """Carrega e processa os dados do CSV"""
    try:
        # Inicializa o processador de dados com caminho absoluto
        processor = DataProcessor(data_dir=os.path.join(os.path.dirname(__file__), '..', 'docs'))
        
        # Carrega e processa o arquivo
        df = processor.load_and_process_file('_DEMANDAS DE JANEIRO_2025 - DEMANDAS JULIO.csv')
        
        if df is None:
            st.error("Erro ao carregar o arquivo CSV. Verifique o log para mais detalhes.")
            return None, None
            
        return df, processor.get_debug_info()
        
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        st.write("Detalhes do erro:")
        st.write(f"- Tipo: {type(e).__name__}")
        st.write(f"- Mensagem: {str(e)}")
        return None, None

def main():
    st.set_page_config(
        page_title="Dashboard Financeiro - Análise de Demandas",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Estilo CSS personalizado
    st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
        }
        .stMetric {
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .team-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 10px 0;
        }
        .header-container {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .stDateInput>div>div>input {
            border-radius: 5px;
        }
        .team-metric {
            border-left: 5px solid;
            padding-left: 10px;
            margin: 10px 0;
        }
        .plotly-graph {
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 10px;
            background-color: white;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Cores para cada equipe
    TEAM_COLORS = {
        'JULIO': '#1f77b4',    # Azul
        'LEANDRO': '#2ca02c',  # Verde
        'ADRIANO': '#ff7f0e'   # Laranja
    }
    
    # Lista arquivos disponíveis
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
    st.sidebar.write("### Arquivos disponíveis:")
    for file in os.listdir(docs_dir):
        if file.endswith('.csv'):
            st.sidebar.write(f"- {file}")
            
    # Carrega dados
    df, debug_info = load_data()
    
    # Checkbox para debug (fora da função load_data)
    show_debug = st.sidebar.checkbox("Mostrar informações de debug")
    if show_debug and debug_info is not None:
        st.sidebar.json(debug_info)
    
    if df is None:
        st.error("Não foi possível carregar os dados. Verifique as mensagens de erro acima.")
        return
        
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/financial-analytics.png", width=100)
        st.title("Filtros")
        
        # Filtro de data
        start_date = st.date_input(
            "Data Inicial",
            value=datetime.now() - timedelta(days=7),
            max_value=datetime.now()
        )
        end_date = st.date_input(
            "Data Final",
            value=datetime.now(),
            max_value=datetime.now(),
            min_value=start_date
        )
        
        # Filtro de equipes
        teams = ['JULIO', 'LEANDRO', 'ADRIANO']
        selected_teams = st.multiselect(
            "Equipes",
            teams,
            default=teams
        )
        
        # Filtro de status
        status_options = sorted(df['situacao'].unique().tolist())
        selected_status = st.multiselect(
            "Status",
            status_options,
            default=status_options
        )
        
        st.markdown("---")
        st.markdown("### Legendas")
        for team in teams:
            st.markdown(
                f'<div class="team-metric" style="border-color:{TEAM_COLORS[team]}">{team}</div>',
                unsafe_allow_html=True
            )
    
    # Conteúdo principal
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("Dashboard Financeiro - Análise de Demandas")
    current_date = datetime.now().strftime("%d/%m/%Y")
    st.markdown(f"*Atualizado em: {current_date}*")
    
    # Link para a página de explicação
    st.markdown("""
        <a href='templates/analysis_importance.html' target='_blank' style='
            display: inline-block;
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        '>
            📊 Entenda a Importância das Análises
        </a>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Filtra dados
    mask = (
        (df['resolucao'].dt.date >= start_date) &
        (df['resolucao'].dt.date <= end_date) &
        (df['equipe'].isin(selected_teams)) &
        (df['situacao'].isin(selected_status))
    )
    filtered_df = df[mask]
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_demands = len(filtered_df)
        st.metric(
            "Total de Demandas",
            f"{total_demands:,}",
            delta=None,
            delta_color="normal"
        )
        
    with col2:
        resolved = len(filtered_df[filtered_df['situacao'].str.contains('RESOLV|CONCLU|APROV', case=False, regex=True)])
        st.metric(
            "Demandas Resolvidas",
            f"{resolved:,}",
            delta=f"{(resolved/total_demands*100):.1f}%" if total_demands > 0 else "0%"
        )
        
    with col3:
        today_demands = len(filtered_df[filtered_df['resolucao'].dt.date == datetime.now().date()])
        st.metric(
            "Demandas Hoje",
            f"{today_demands:,}",
            delta=None
        )
        
    with col4:
        avg_daily = resolved / ((end_date - start_date).days + 1)
        st.metric(
            "Média Diária",
            f"{avg_daily:.1f}",
            delta=None
        )
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Demandas por Equipe")
        team_data = filtered_df['equipe'].value_counts()
        fig = px.bar(
            x=team_data.index,
            y=team_data.values,
            color=team_data.index,
            color_discrete_map=TEAM_COLORS,
            labels={'x': 'Equipe', 'y': 'Quantidade de Demandas'}
        )
        fig.update_layout(
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=20, l=20, r=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        st.markdown("### Evolução Temporal")
        daily_data = filtered_df.groupby(['resolucao', 'equipe']).size().reset_index(name='count')
        fig = px.line(
            daily_data,
            x='resolucao',
            y='count',
            color='equipe',
            color_discrete_map=TEAM_COLORS,
            labels={'resolucao': 'Data', 'count': 'Quantidade de Demandas'}
        )
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=20, l=20, r=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Detalhamento por equipe
    st.markdown("### Detalhamento por Equipe")
    
    for team in selected_teams:
        team_df = filtered_df[filtered_df['equipe'] == team]
        
        with st.expander(f"Equipe {team}", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                team_total = len(team_df)
                st.metric(
                    "Total de Demandas",
                    f"{team_total:,}",
                    delta=f"{(team_total/total_demands*100):.1f}%" if total_demands > 0 else "0%"
                )
                
            with col2:
                team_resolved = len(team_df[team_df['situacao'].str.contains('RESOLV|CONCLU|APROV', case=False, regex=True)])
                st.metric(
                    "Resolvidas",
                    f"{team_resolved:,}",
                    delta=f"{(team_resolved/team_total*100):.1f}%" if team_total > 0 else "0%"
                )
                
            with col3:
                team_today = len(team_df[team_df['resolucao'].dt.date == datetime.now().date()])
                st.metric(
                    "Hoje",
                    f"{team_today:,}",
                    delta=None
                )
            
            # Lista das últimas demandas
            st.markdown("#### Últimas Demandas")
            latest_demands = team_df.sort_values('resolucao', ascending=False).head(5)
            for _, row in latest_demands.iterrows():
                st.markdown(f"""
                    <div style='padding: 10px; background-color: #f8f9fa; border-radius: 5px; margin: 5px 0;
                         border-left: 5px solid {TEAM_COLORS[team]}'>
                        <strong>Data:</strong> {row['resolucao'].strftime('%d/%m/%Y')} |
                        <strong>Status:</strong> {row['situacao']}
                    </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
