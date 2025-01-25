import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import gc
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import warnings
from functools import lru_cache

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ignorar warnings específicos
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# Configurações de memória para pandas
pd.options.mode.chained_assignment = None

# Configuração da página
try:
    st.set_page_config(
        page_title="Relatório Diário de Demandas",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception as e:
    logger.error(f"Erro ao configurar página: {str(e)}")
    st.error("Erro ao configurar página. Por favor, recarregue.")

def get_column_dtypes(sheet_name: str) -> Dict:
    """
    Retorna os tipos de dados específicos para cada planilha.
    """
    # Tipos padrão para colunas comuns
    common_dtypes = {
        'CTT': str,
        'CONTRATO': str,
        'SITUACAO': str,
        'SITUAÇÃO': str,
        'ATIVO/RECEPTIVO': str,
        'EQUIPE': str,
        'NOME': str,
        'PRIORIDADE': str,
        'STATUS': str,
    }
    
    # Tipos específicos por planilha
    sheet_specific_dtypes = {
        'REGIÕES': {
            **common_dtypes,
            'CÓDIGO': str,
            'REGIÃO': str
        },
        'DEMANDAS JULIO': {
            **common_dtypes,
            'VALOR': 'float64',
            'DATA': str  # Será convertido para datetime depois
        },
        'DEMANDA LEANDROADRIANO': {
            **common_dtypes,
            'VALOR': 'float64',
            'DATA': str
        },
        'APROVADO E QUITADO CLIENTE': {
            **common_dtypes,
            'VALOR': 'float64',
            'DATA': str
        },
        'CALCULO DE PORCENTAGEM': {
            **common_dtypes,
            'VALOR': 'float64',
            'PERCENTUAL': 'float64'
        },
        'QUITADOS': {
            **common_dtypes,
            'VALOR': 'float64',
            'DATA': str
        },
        'FINALIZADOS': {
            **common_dtypes,
            'VALOR': 'float64',
            'DATA': str
        },
        'TICKTES': {
            **common_dtypes,
            'NÚMERO': str,
            'DATA': str
        },
        'PREENCHIMENTO ARTES': {
            **common_dtypes,
            'DATA': str
        },
        'SISTEMA ANTIGO': {
            **common_dtypes,
            'DATA': str
        },
        'Q.A': {
            **common_dtypes,
            'DATA': str,
            'VALOR': 'float64'
        }
    }
    
    return sheet_specific_dtypes.get(sheet_name, common_dtypes)

def safe_convert_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte colunas de data com tratamento de erros.
    """
    date_columns = ['DATA', 'RESOLUCAO', 'Data', 'DATA CONCLUSÃO', 'DATA INÍCIO']
    
    for col in date_columns:
        if col in df.columns:
            try:
                # Tenta converter para datetime, mantendo valores NaN para erros
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except Exception as e:
                logger.warning(f"Erro ao converter coluna {col} para datetime: {str(e)}")
    
    return df

def safe_convert_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte colunas numéricas com tratamento de erros.
    """
    numeric_columns = ['VALOR', 'PERCENTUAL']
    
    for col in numeric_columns:
        if col in df.columns:
            try:
                # Remove caracteres não numéricos e converte para float
                df[col] = df[col].astype(str).str.replace('[^\d.-]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception as e:
                logger.warning(f"Erro ao converter coluna {col} para numérico: {str(e)}")
    
    return df

# Decorador para cache de dados
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_data() -> Tuple[Optional[pd.DataFrame], Optional[Dict]]:
    """
    Carrega dados com tratamento de erros e gestão de memória.
    """
    try:
        # Carregar CSV com chunks para economia de memória
        csv_chunks = pd.read_csv(
            'docs/metricas_colaboradores.csv',
            chunksize=1000,
            parse_dates=['Data']
        )
        df = pd.concat(csv_chunks, ignore_index=True)
        
        # Carregar Excel com verificação de memória
        excel_path = 'docs/_DEMANDAS DE JANEIRO_2025.xlsx'
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {excel_path}")
            
        dfs = {}
        with pd.ExcelFile(excel_path) as xls:
            for sheet_name in xls.sheet_names:
                try:
                    # Obter tipos de dados específicos para a planilha
                    dtypes = get_column_dtypes(sheet_name)
                    
                    # Carregar a planilha com os tipos de dados especificados
                    sheet_data = pd.read_excel(
                        xls,
                        sheet_name=sheet_name,
                        dtype=dtypes
                    )
                    
                    # Converter datas e números com segurança
                    sheet_data = safe_convert_dates(sheet_data)
                    sheet_data = safe_convert_numeric(sheet_data)
                    
                    # Limpar e padronizar nomes de colunas
                    sheet_data.columns = sheet_data.columns.str.strip().str.upper()
                    
                    # Remover linhas totalmente vazias
                    sheet_data = sheet_data.dropna(how='all')
                    
                    # Converter strings para categoria quando apropriado
                    for col in sheet_data.select_dtypes(include=['object']):
                        if sheet_data[col].nunique() / len(sheet_data) < 0.5:
                            sheet_data[col] = sheet_data[col].astype('category')
                    
                    dfs[sheet_name] = sheet_data
                    logger.info(f"Planilha {sheet_name} carregada com sucesso")
                    
                except Exception as sheet_error:
                    logger.error(f"Erro ao carregar planilha {sheet_name}: {str(sheet_error)} (sheet: {sheet_name})")
                    continue
                finally:
                    gc.collect()
        
        if not dfs:
            raise ValueError("Nenhuma planilha foi carregada com sucesso")
        
        return df, dfs
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {str(e)}")
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None, None
    finally:
        gc.collect()

def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Otimiza tipos de dados do DataFrame para reduzir uso de memória.
    """
    try:
        for col in df.columns:
            if df[col].dtype == 'object':
                # Converter strings para categoria se tiver poucos valores únicos
                if df[col].nunique() / len(df) < 0.5:
                    df[col] = df[col].astype('category')
            elif df[col].dtype == 'float64':
                # Reduzir precisão de floats quando possível
                df[col] = df[col].astype('float32')
            elif df[col].dtype == 'int64':
                # Reduzir precisão de ints quando possível
                if df[col].min() >= -32768 and df[col].max() <= 32767:
                    df[col] = df[col].astype('int16')
                elif df[col].min() >= -2147483648 and df[col].max() <= 2147483647:
                    df[col] = df[col].astype('int32')
        return df
    except Exception as e:
        logger.warning(f"Erro ao otimizar tipos de dados: {str(e)}")
        return df

def get_situacao_column(df: pd.DataFrame) -> Optional[str]:
    """
    Identifica a coluna correta de situação no DataFrame.
    """
    possible_columns = ['SITUACAO', 'SITUAÇÃO', 'STATUS', 'ESTADO']
    for col in possible_columns:
        if col in df.columns:
            return col
    return None

@st.cache_data(ttl=3600)
def calculate_daily_metrics(dfs: Dict, date: datetime, selected_team: str = None) -> Dict:
    """
    Calcula métricas diárias com tratamento de erros.
    """
    metrics = {
        'Resolvidos': 0,
        'Pendente_Ativo': 0,
        'Pendente_Receptivo': 0,
        'Prioridade': 0,
        'Prioridade_Total': 0,
        'Soma_Prioridades': 0,
        'Analise': 0,
        'Analise_Dia': 0,
        'Receptivo': 0,
        'Quitado_Cliente': 0,
        'Quitado': 0,
        'Aprovados': 0
    }
    
    try:
        for sheet_name, df in dfs.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            
            logger.info(f"Processando planilha: {sheet_name}")
            
            # Processar em chunks para grandes DataFrames
            chunk_size = 1000
            for chunk_start in range(0, len(df), chunk_size):
                chunk_end = min(chunk_start + chunk_size, len(df))
                df_chunk = df.iloc[chunk_start:chunk_end].copy()
                
                # Filtrar por equipe se selecionada
                if selected_team:
                    equipe_col = next((col for col in df_chunk.columns if 'EQUIPE' in col.upper()), None)
                    if equipe_col and not df_chunk[equipe_col].empty:
                        df_chunk = df_chunk[df_chunk[equipe_col].astype(str).str.upper() == selected_team.upper()]
                
                # Identificar coluna de situação
                situacao_col = get_situacao_column(df_chunk)
                
                # Filtrar por data usando as colunas disponíveis
                date_mask = pd.Series(False, index=df_chunk.index)
                date_columns = ['DATA', 'RESOLUCAO', 'Data', 'DATA CONCLUSÃO', 'DATA INÍCIO']
                
                for date_col in date_columns:
                    if date_col in df_chunk.columns and not df_chunk[date_col].empty:
                        if pd.api.types.is_datetime64_any_dtype(df_chunk[date_col]):
                            date_mask |= (df_chunk[date_col].dt.date == date.date())
                
                df_date = df_chunk[date_mask]
                
                if df_date.empty:
                    continue
                
                # Calcular métricas
                if situacao_col:
                    try:
                        # Converter situação para uppercase e remover espaços extras
                        situacao_series = df_date[situacao_col].astype(str).str.upper().str.strip()
                        
                        # Contagem de resolvidos
                        resolvido_mask = situacao_series.str.contains('RESOLVID|FINALIZADO|CONCLUÍDO', na=False)
                        metrics['Resolvidos'] += resolvido_mask.sum()
                        
                        # Contagem de análise
                        analise_mask = situacao_series.str.contains('ANALIS|ANÁLISE', na=False)
                        metrics['Analise'] += analise_mask.sum()
                        
                        # Contagem de quitados
                        quitado_mask = situacao_series.str.contains('QUITAD', na=False)
                        metrics['Quitado'] += quitado_mask.sum()
                        
                        # Contagem de aprovados
                        aprovado_mask = situacao_series.str.contains('APROVAD', na=False)
                        metrics['Aprovados'] += aprovado_mask.sum()
                        
                        # Contagem de pendentes
                        pendente_mask = situacao_series.str.contains('PENDENT', na=False)
                        
                        if 'ATIVO/RECEPTIVO' in df_date.columns:
                            ativo_mask = df_date['ATIVO/RECEPTIVO'].astype(str).str.upper().str.contains('ATIVO', na=False)
                            receptivo_mask = df_date['ATIVO/RECEPTIVO'].astype(str).str.upper().str.contains('RECEPTIVO', na=False)
                            
                            metrics['Pendente_Ativo'] += (pendente_mask & ativo_mask).sum()
                            metrics['Pendente_Receptivo'] += (pendente_mask & receptivo_mask).sum()
                            metrics['Receptivo'] += receptivo_mask.sum()
                        
                        # Análise do dia
                        if analise_mask.any():
                            metrics['Analise_Dia'] += len(df_date[
                                analise_mask & (df_date[date_columns[0]].dt.date == date.date())
                            ])
                        
                    except Exception as e:
                        logger.error(f"Erro ao processar métricas da planilha {sheet_name}: {str(e)}")
                        continue
                
                # Limpar memória
                del df_chunk, df_date
                gc.collect()
        
        logger.info("Métricas calculadas com sucesso")
        return metrics
        
    except Exception as e:
        logger.error(f"Erro ao calcular métricas: {str(e)}")
        st.error(f"Erro ao calcular métricas: {str(e)}")
        return metrics

def main():
    try:
        # Título principal
        st.title('📊 RELATÓRIO DIÁRIO')
        
        # Carregar dados
        with st.spinner('Carregando dados...'):
            df, dfs = load_data()
            
        if df is None or dfs is None:
            st.error("Não foi possível carregar os dados. Verifique os logs para mais detalhes.")
            return
        
        # Sidebar para filtros
        st.sidebar.title('Filtros')
        
        # Seleção de equipe
        equipes = ['LEANDRO/ADRIANO', 'JULIO']
        selected_team = st.sidebar.radio(
            "Selecione a Equipe",
            equipes,
            index=0
        )
        
        st.sidebar.markdown("---")  # Separador
        
        # Seleção de data
        max_date = df['Data'].max()
        min_date = df['Data'].min()
        selected_date = st.sidebar.date_input(
            "Selecione a Data",
            value=max_date.date(),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
        
        # Converter selected_date para datetime
        selected_datetime = pd.to_datetime(selected_date)
        
        # Calcular métricas
        with st.spinner('Calculando métricas...'):
            daily_metrics = calculate_daily_metrics(dfs, selected_datetime, selected_team)
        
        # Layout em grid para métricas principais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Resolvidos", daily_metrics['Resolvidos'])
            st.metric("Pendente Ativo", daily_metrics['Pendente_Ativo'])
            st.metric("Pendente Receptivo", daily_metrics['Pendente_Receptivo'])
            st.metric("Prioridade", daily_metrics['Prioridade'])
        
        with col2:
            st.metric("Prioridade Total", daily_metrics['Prioridade_Total'])
            st.metric("Soma Prioridades", daily_metrics['Soma_Prioridades'])
            st.metric("Análise", daily_metrics['Analise'])
            st.metric("Análise do Dia", daily_metrics['Analise_Dia'])
        
        with col3:
            st.metric("Receptivo", daily_metrics['Receptivo'])
            st.metric("Quitado Cliente", daily_metrics['Quitado_Cliente'])
            st.metric("Quitado", daily_metrics['Quitado'])
            st.metric("Aprovados", daily_metrics['Aprovados'])
        
        # Gráficos
        st.header(f"📈 Análise Gráfica - Equipe {selected_team}")
        
        # Filtrar dados para a data selecionada e equipe
        df_day = df[
            (df['Data'].dt.date == selected_date) &
            (df['Equipe'] == selected_team)
        ]
        
        # Gráfico de barras - Métricas por Equipe
        try:
            fig_team = go.Figure()
            
            # Adicionar barras para a equipe selecionada
            fig_team.add_trace(go.Bar(
                name=selected_team,
                x=['Resolvidos', 'Pendentes', 'Análise'],
                y=[
                    daily_metrics['Resolvidos'],
                    daily_metrics['Pendente_Ativo'] + daily_metrics['Pendente_Receptivo'],
                    daily_metrics['Analise']
                ]
            ))
            
            fig_team.update_layout(
                title=f'Métricas da Equipe {selected_team}',
                barmode='group',
                height=500
            )
            st.plotly_chart(fig_team, use_container_width=True)
        except Exception as e:
            logger.error(f"Erro ao criar gráfico: {str(e)}")
            st.error("Erro ao criar gráfico de métricas por equipe")
        
        # Tabela detalhada
        st.header(f"📋 Detalhamento - Equipe {selected_team}")
        
        try:
            detailed_df = df_day.groupby(['Nome']).agg({
                'Resolvidos': 'sum',
                'Pendentes': 'sum'
            }).reset_index()
            
            detailed_df = detailed_df.sort_values('Resolvidos', ascending=False)
            st.dataframe(
                detailed_df.style.highlight_max(subset=['Resolvidos', 'Pendentes'], color='lightgreen'),
                use_container_width=True
            )
        except Exception as e:
            logger.error(f"Erro ao criar tabela detalhada: {str(e)}")
            st.error("Erro ao criar tabela de detalhamento por colaborador")
        
    except Exception as e:
        logger.error(f"Erro geral na aplicação: {str(e)}")
        st.error(f"Ocorreu um erro na aplicação: {str(e)}")
    finally:
        # Limpar memória ao finalizar
        gc.collect()

if __name__ == "__main__":
    main()
