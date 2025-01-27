import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import logging
from rich.console import Console
from rich.table import Table
import unicodedata

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_corrections/logs/timeline_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
console = Console()

class DemandsTimelineAnalyzer:
    def __init__(self):
        self.equipe_julio = [
            'ADRIANO', 'ELISANGELA', 'FELIPE', 'IGOR', 'ANA GESSICA', 'ALINE', 
            'NUNO', 'THALISSON', 'LUARA', 'MATHEUS', 'JULIANE', 'POLIANA', 
            'YURI', 'ANA LÍDIA'
        ]
        
        self.equipe_leandro_adriano = [
            'ALINE SALVADOR', 'AMANDA SANTANA', 'BRUNO MARIANO', 'EDIANE', 
            'FABIANA', 'GREICY', 'ITAYNNARA', 'IZABEL', 'JULIANA', 'JULIA', 
            'KATIA', 'MARIA BRUNA', 'MONYZA', 'SABRINA', 'SOFIA', 
            'VICTOR ADRIANO', 'VITORIA'
        ]
        
        # Normaliza os nomes das equipes
        self.equipe_julio = [self.normalize_name(name) for name in self.equipe_julio]
        self.equipe_leandro_adriano = [self.normalize_name(name) for name in self.equipe_leandro_adriano]
    
    def normalize_name(self, name: str) -> str:
        """Normaliza um nome removendo acentos e padronizando formato."""
        if pd.isna(name):
            return name
        name = unicodedata.normalize('NFKD', str(name).strip().upper())
        return name.encode('ASCII', 'ignore').decode('ASCII')
    
    def get_team(self, responsavel: str) -> str:
        """Identifica a equipe do responsável."""
        if pd.isna(responsavel):
            return "Sem Responsável"
        
        responsavel = self.normalize_name(responsavel)
        if responsavel in self.equipe_julio:
            return "Equipe Júlio"
        elif responsavel in self.equipe_leandro_adriano:
            return "Equipe Leandro e Adriano"
        return "Outros"
    
    def load_and_prepare_data(self):
        """Carrega e prepara os dados dos arquivos CSV."""
        try:
            # Carrega os arquivos
            df_julio = pd.read_csv('docs/_DEMANDAS DE JANEIRO_2025 - DEMANDAS JULIO.csv', encoding='latin1')
            df_leandro = pd.read_csv('docs/_DEMANDAS DE JANEIRO_2025 - DEMANDA LEANDROADRIANO.csv', encoding='latin1')
            
            # Função para encontrar coluna
            def find_column(df, patterns):
                for pattern in patterns:
                    matches = [col for col in df.columns if pattern in col.upper()]
                    if matches:
                        return matches[0]
                return None
            
            # Identifica colunas para cada DataFrame
            for df, name in [(df_julio, 'Júlio'), (df_leandro, 'Leandro')]:
                resolution_col = find_column(df, ['RESOL', 'RESOLUCAO', 'RESOLUÇÃO'])
                responsible_col = find_column(df, ['RESP', 'RESPONSAVEL', 'RESPONSÁVEL'])
                situation_col = find_column(df, ['SITU', 'STATUS', 'SITUACAO', 'SITUAÇÃO'])
                
                if not all([resolution_col, responsible_col]):
                    raise ValueError(f"Colunas necessárias não encontradas no DataFrame {name}")
                
                # Renomeia as colunas encontradas
                rename_map = {}
                if resolution_col:
                    rename_map[resolution_col] = 'RESOLUÇÃO'
                if responsible_col:
                    rename_map[responsible_col] = 'RESPONSÁVEL'
                if situation_col:
                    rename_map[situation_col] = 'SITUAÇÃO'
                
                df.rename(columns=rename_map, inplace=True)
            
            # Combina os DataFrames
            df_combined = pd.concat([df_julio, df_leandro], ignore_index=True)
            
            # Converte datas e remove valores inválidos
            df_combined['RESOLUÇÃO'] = pd.to_datetime(df_combined['RESOLUÇÃO'], errors='coerce')
            df_combined = df_combined.dropna(subset=['RESOLUÇÃO'])
            
            # Filtra apenas demandas resolvidas/aprovadas/quitadas
            status_filter = ['RESOLV', 'APROV', 'QUIT']
            mask_status = df_combined['SITUAÇÃO'].str.contains('|'.join(status_filter), case=False, na=False)
            df_combined = df_combined[mask_status]
            
            # Ordena por data decrescente
            df_combined = df_combined.sort_values('RESOLUÇÃO', ascending=False)
            
            # Normaliza nomes dos responsáveis
            df_combined['RESPONSÁVEL'] = df_combined['RESPONSÁVEL'].apply(self.normalize_name)
            
            # Adiciona coluna de equipe
            df_combined['EQUIPE'] = df_combined['RESPONSÁVEL'].apply(self.get_team)
            
            # Adiciona informações temporais
            df_combined['DATA'] = df_combined['RESOLUÇÃO'].dt.strftime('%d/%m/%Y')
            
            logger.info(f"Total de demandas: {len(df_combined)}")
            
            if not df_combined.empty:
                # Análise por equipe e responsável
                for equipe in ['Equipe Júlio', 'Equipe Leandro e Adriano']:
                    logger.info(f"\n{equipe}:")
                    equipe_df = df_combined[df_combined['EQUIPE'] == equipe]
                    resp_counts = equipe_df['RESPONSÁVEL'].value_counts()
                    
                    for resp, count in resp_counts.items():
                        logger.info(f"{resp} {count}")
                    
                    logger.info(f"TOTAL {len(equipe_df)}")
                
                # Análise diária
                daily_counts = df_combined.groupby(['DATA', 'EQUIPE']).size().unstack(fill_value=0)
                logger.info("\nResumo diário por equipe:")
                logger.info(daily_counts)
                
                # Salva os resultados em CSV
                daily_counts.to_csv('ml_corrections/reports/resumo_diario.csv')
                
                # Lista de responsáveis por equipe
                equipes = {
                    'Equipe Leandro e Adriano': [
                        'ALINE SALVADOR', 'AMANDA SANTANA', 'BRUNO MARIANO', 'EDIANE',
                        'FABIANA', 'GREICY', 'ITAYNNARA', 'IZABEL', 'JULIANA', 'JULIA',
                        'KATIA', 'MARIA BRUNA', 'MONYZA', 'SABRINA', 'SOFIA',
                        'VICTOR ADRIANO', 'VITORIA'
                    ],
                    'Equipe Júlio': [
                        'ADRIANO', 'ALINE', 'ANA GESSICA', 'ANA LIDIA', 'ELISANGELA',
                        'FELIPE', 'IGOR', 'JULIANE', 'LUARA', 'MATHEUS', 'NUNO',
                        'POLIANA', 'THALISSON', 'YURI'
                    ]
                }
                
                # Cria relatório detalhado por equipe
                for equipe, responsaveis in equipes.items():
                    with open(f'ml_corrections/reports/relatorio_{equipe.lower().replace(" ", "_")}.txt', 'w') as f:
                        f.write(f"{equipe}\n\n")
                        total = 0
                        for resp in responsaveis:
                            count = len(df_combined[df_combined['RESPONSÁVEL'] == resp])
                            f.write(f"{resp} {count}\n\n")
                            total += count
                        f.write(f"TOTAL {total}\n")
            
            return df_combined
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {str(e)}")
            raise
    
    def analyze_demands_timeline(self, df):
        """Analisa as demandas ao longo do tempo."""
        # Filtra apenas demandas resolvidas com data válida
        df_resolved = df[df['RESOLUÇÃO'].notna()].copy()
        
        # Agrupa por data e equipe
        daily_by_team = df_resolved.groupby(['RESOLUÇÃO', 'EQUIPE']).size().reset_index(name='count')
        daily_by_team['RESOLUÇÃO'] = pd.to_datetime(daily_by_team['RESOLUÇÃO']).dt.date
        
        # Agrupa por data e responsável
        daily_by_resp = df_resolved.groupby(['RESOLUÇÃO', 'RESPONSÁVEL', 'EQUIPE']).size().reset_index(name='count')
        daily_by_resp['RESOLUÇÃO'] = pd.to_datetime(daily_by_resp['RESOLUÇÃO']).dt.date
        
        return daily_by_team, daily_by_resp
    
    def create_timeline_visualization(self, daily_by_team, daily_by_resp):
        """Cria visualizações da linha do tempo."""
        # Gráfico de linha do tempo por equipe
        fig_team = px.line(daily_by_team, x='RESOLUÇÃO', y='count', color='EQUIPE',
                          title='Demandas Resolvidas por Equipe ao Longo do Tempo')
        fig_team.write_html('ml_corrections/reports/timeline_by_team.html')
        
        # Gráfico de linha do tempo por responsável
        fig_resp = px.line(daily_by_resp, x='RESOLUÇÃO', y='count', color='RESPONSÁVEL',
                          facet_col='EQUIPE', facet_col_wrap=2,
                          title='Demandas Resolvidas por Responsável ao Longo do Tempo')
        fig_resp.write_html('ml_corrections/reports/timeline_by_responsible.html')
    
    def display_summary_tables(self, df):
        """Exibe tabelas resumo das demandas."""
        # Resumo por equipe
        team_summary = df.groupby(['EQUIPE', 'DATA']).agg({
            'RESPONSÁVEL': 'count'
        }).reset_index()
        
        # Resumo por responsável
        resp_summary = df.groupby(['EQUIPE', 'RESPONSÁVEL', 'DATA']).agg({
            'RESOLUÇÃO': 'count'
        }).reset_index()
        
        # Exibe tabela de equipes
        console.print("\n[bold cyan]Resumo por Equipe e Data:[/bold cyan]")
        table_team = Table(show_header=True, header_style="bold magenta")
        table_team.add_column("Equipe", style="cyan")
        table_team.add_column("Data", style="yellow")
        table_team.add_column("Total de Demandas", justify="right")
        
        for _, row in team_summary.iterrows():
            table_team.add_row(
                str(row['EQUIPE']),
                str(row['DATA']),
                str(row['RESPONSÁVEL'])
            )
        
        console.print(table_team)
        
        # Exibe tabela de responsáveis
        console.print("\n[bold cyan]Resumo por Responsável e Data:[/bold cyan]")
        table_resp = Table(show_header=True, header_style="bold magenta")
        table_resp.add_column("Equipe", style="cyan")
        table_resp.add_column("Responsável", style="green")
        table_resp.add_column("Data", style="yellow")
        table_resp.add_column("Total de Demandas", justify="right")
        
        for _, row in resp_summary.iterrows():
            table_resp.add_row(
                str(row['EQUIPE']),
                str(row['RESPONSÁVEL']),
                str(row['DATA']),
                str(row['RESOLUÇÃO'])
            )
        
        console.print(table_resp)
        
        # Salva os resumos em CSV
        team_summary.to_csv('ml_corrections/reports/resumo_equipes_por_data.csv', index=False, encoding='utf-8-sig')
        resp_summary.to_csv('ml_corrections/reports/resumo_responsaveis_por_data.csv', index=False, encoding='utf-8-sig')

def main():
    """Função principal para análise temporal das demandas."""
    try:
        analyzer = DemandsTimelineAnalyzer()
        
        # Carrega e prepara os dados
        df = analyzer.load_and_prepare_data()
        
        if df is None:
            logger.info("Análise temporal concluída sem dados.")
            return
        
        # Analisa a linha do tempo
        daily_by_team, daily_by_resp = analyzer.analyze_demands_timeline(df)
        
        # Cria visualizações
        analyzer.create_timeline_visualization(daily_by_team, daily_by_resp)
        
        # Exibe resumos
        analyzer.display_summary_tables(df)
        
        logger.info("Análise temporal concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante a análise: {str(e)}")
        raise

if __name__ == "__main__":
    main()
