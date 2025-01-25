import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import altair as alt

# Configuração da página
st.set_page_config(
    page_title="Análise de Resoluções",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("📊 Dashboard de Resoluções por Responsável")

# Função para carregar os dados
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("docs/_DEMANDAS DE JANEIRO_2025.xlsx")
        df['DATA'] = pd.to_datetime(df['DATA'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

# Carregar dados
df = load_data()

if df is not None:
    # Sidebar com filtros
    st.sidebar.header("Filtros")
    
    # Filtro de data
    min_date = df['DATA'].min().date()
    max_date = df['DATA'].max().date()
    
    date_range = st.sidebar.date_input(
        "Selecione o período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Converter para datetime
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df['DATA'].dt.date >= start_date) & (df['DATA'].dt.date <= end_date)
        filtered_df = df[mask]
    else:
        filtered_df = df
    
    # Métricas principais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_resolvidos = len(filtered_df[filtered_df['STATUS'] == 'RESOLVIDO'])
        st.metric("Total de Resoluções", total_resolvidos)
    
    with col2:
        total_dias = (end_date - start_date).days + 1
        media_diaria = total_resolvidos / total_dias if total_dias > 0 else 0
        st.metric("Média Diária", f"{media_diaria:.1f}")
    
    with col3:
        total_responsaveis = filtered_df[filtered_df['STATUS'] == 'RESOLVIDO']['RESPONSÁVEL'].nunique()
        st.metric("Total de Responsáveis Ativos", total_responsaveis)
    
    # Análise por responsável
    st.header("Resoluções por Responsável")
    
    # Calcular resoluções por responsável
    resolucoes_resp = filtered_df[filtered_df['STATUS'] == 'RESOLVIDO']['RESPONSÁVEL'].value_counts().reset_index()
    resolucoes_resp.columns = ['Responsável', 'Total Resolvido']
    
    # Criar gráfico de barras
    chart = alt.Chart(resolucoes_resp).mark_bar().encode(
        x=alt.X('Total Resolvido:Q', title='Total Resolvido'),
        y=alt.Y('Responsável:N', sort='-x', title='Responsável'),
        tooltip=['Responsável', 'Total Resolvido']
    ).properties(
        height=400
    )
    
    st.altair_chart(chart, use_container_width=True)
    
    # Tabela detalhada
    st.header("Detalhamento por Responsável")
    
    # Adicionar análise diária
    st.subheader("Análise Diária")
    
    # Criar DataFrame com resoluções diárias por responsável
    daily_resolutions = filtered_df[filtered_df['STATUS'] == 'RESOLVIDO'].pivot_table(
        index='DATA',
        columns='RESPONSÁVEL',
        aggfunc='size',
        fill_value=0
    ).reset_index()
    
    # Formatar data para exibição
    daily_resolutions['DATA'] = daily_resolutions['DATA'].dt.strftime('%d/%m/%Y')
    
    # Exibir tabela com scroll horizontal
    st.dataframe(
        daily_resolutions,
        use_container_width=True,
        hide_index=True
    )
    
    # Download dos dados
    st.download_button(
        label="📥 Download dos dados",
        data=daily_resolutions.to_csv(index=False).encode('utf-8'),
        file_name=f'resolucoes_diarias_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv'
    )
    
else:
    st.error("Não foi possível carregar os dados. Verifique se o arquivo está na pasta correta.")
