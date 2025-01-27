import pandas as pd
import numpy as np
from pathlib import Path
import unicodedata
from typing import Dict, List
from rich.console import Console
from rich.table import Table
import logging
import plotly.express as px
import os

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Console para output formatado
console = Console()

class DemandasProcessor:
    def __init__(self):
        self.docs_path = Path('f:/demandstest/organized_project/docs')
        
        # Definição das equipes com nomes normalizados
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
        
        # Normalizando os nomes das equipes
        self.equipe_julio = [self.normalize_name(name) for name in self.equipe_julio]
        self.equipe_leandro_adriano = [self.normalize_name(name) for name in self.equipe_leandro_adriano]
        
        # DataFrames
        self.df_julio = None
        self.df_leandro = None
        self.df_quitados = None
        self.df_combined = None

    def normalize_name(self, name: str) -> str:
        """Normaliza um nome removendo acentos e padronizando o formato."""
        if pd.isna(name):
            return name
        # Remove acentos e converte para maiúsculas
        name = unicodedata.normalize('NFKD', str(name).strip().upper())
        name = name.encode('ASCII', 'ignore').decode('ASCII')
        return name

    def read_csv_files(self):
        """Lê os arquivos CSV e armazena em DataFrames."""
        try:
            # Lendo os arquivos CSV
            self.df_julio = pd.read_csv(self.docs_path / '_DEMANDAS DE JANEIRO_2025 - DEMANDAS JULIO.csv')
            self.df_leandro = pd.read_csv(self.docs_path / '_DEMANDAS DE JANEIRO_2025 - DEMANDA LEANDROADRIANO.csv')
            self.df_quitados = pd.read_csv(self.docs_path / '_DEMANDAS DE JANEIRO_2025 - QUITADOS.csv')
            
            logger.info("Arquivos CSV carregados com sucesso")
            
            # Exibindo informações dos DataFrames
            self._print_dataframe_info("DEMANDAS JULIO", self.df_julio)
            self._print_dataframe_info("DEMANDA LEANDROADRIANO", self.df_leandro)
            self._print_dataframe_info("QUITADOS", self.df_quitados)
            
        except Exception as e:
            logger.error(f"Erro ao ler arquivos CSV: {str(e)}")
            raise

    def _print_dataframe_info(self, name: str, df: pd.DataFrame):
        """Exibe informações sobre um DataFrame."""
        console.print(f"\n[bold cyan]Informações do DataFrame {name}:[/bold cyan]")
        console.print(f"Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
        console.print("Colunas encontradas:")
        for col in df.columns:
            console.print(f"- {col}")

    def preprocess_data(self):
        """Limpa e pré-processa os dados dos DataFrames."""
        # Mapeamento de nomes de colunas para padronização
        column_mapping = {
            'RESPONSAVEL': 'RESPONSÁVEL',
            'SITUACAO': 'SITUAÇÃO',
            'RESOLUCAO': 'RESOLUÇÃO'
        }
        
        # Lista de colunas para manter
        columns_to_keep = [
            'DATA', 'RESOLUÇÃO', 'CTT', 'DEMANDA', 'ATIVO/RECEPTIVO',
            'DIRETOR', 'BANCO', 'RESPONSÁVEL', 'SITUAÇÃO'
        ]
        
        for df_name, df in [('JULIO', self.df_julio), 
                          ('LEANDRO', self.df_leandro), 
                          ('QUITADOS', self.df_quitados)]:
            if df is not None:
                logger.info(f"Processando DataFrame {df_name}")
                
                # Removendo colunas vazias ou desnecessárias
                df.drop(columns=[col for col in df.columns if 
                               col.startswith('Unnamed:') or 
                               col.strip() == ''], 
                       inplace=True, errors='ignore')
                
                # Renomeando colunas para o padrão
                df.rename(columns=column_mapping, inplace=True)
                
                # Convertendo colunas de data
                date_columns = ['DATA', 'RESOLUÇÃO']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                
                # Normalizando nomes dos responsáveis
                if 'RESPONSÁVEL' in df.columns:
                    df['RESPONSÁVEL'] = df['RESPONSÁVEL'].apply(self.normalize_name)
                
                # Padronizando valores da coluna SITUAÇÃO
                if 'SITUAÇÃO' in df.columns:
                    df['SITUAÇÃO'] = df['SITUAÇÃO'].str.upper().str.strip()
                
                # Adicionando colunas faltantes com valores NA
                for col in columns_to_keep:
                    if col not in df.columns:
                        df[col] = pd.NA
                
                # Reordenando e selecionando apenas as colunas necessárias
                df_columns = [col for col in columns_to_keep if col in df.columns]
                df = df[df_columns]
                
                # Atualizando o DataFrame original
                if df_name == 'JULIO':
                    self.df_julio = df
                elif df_name == 'LEANDRO':
                    self.df_leandro = df
                else:
                    self.df_quitados = df
                
                # Exibindo informações após o processamento
                console.print(f"\n[bold cyan]Colunas após processamento ({df_name}):[/bold cyan]")
                for col in df.columns:
                    n_missing = df[col].isna().sum()
                    n_total = len(df)
                    pct_missing = (n_missing / n_total) * 100
                    console.print(f"- {col}: {n_missing}/{n_total} valores ausentes ({pct_missing:.1f}%)")

        logger.info("Pré-processamento dos dados concluído")

    def calculate_totals(self):
        """Calcula totais por responsável e equipe."""
        # Combinando os DataFrames
        dfs_to_combine = [df for df in [self.df_julio, self.df_leandro] if df is not None]
        if dfs_to_combine:
            self.df_combined = pd.concat(dfs_to_combine, ignore_index=True)
            
            # Função para classificar equipe
            def get_team(resp):
                if pd.isna(resp):
                    return "Sem Responsável"
                resp = self.normalize_name(resp)
                if resp in self.equipe_julio:
                    return "Equipe Júlio"
                elif resp in self.equipe_leandro_adriano:
                    return "Equipe Leandro e Adriano"
                return "Outros"
            
            # Adicionando coluna de equipe
            self.df_combined['EQUIPE'] = self.df_combined['RESPONSÁVEL'].apply(get_team)
            
            # Calculando totais por responsável
            resp_totals = self.df_combined.groupby('RESPONSÁVEL')['SITUAÇÃO'].value_counts().unstack(fill_value=0)
            
            # Calculando totais por equipe
            team_totals = self.df_combined.groupby('EQUIPE')['SITUAÇÃO'].value_counts().unstack(fill_value=0)
            
            # Exibindo resultados
            self._display_totals("Totais por Responsável", resp_totals)
            self._display_totals("Totais por Equipe", team_totals)
            
            # Gerando gráficos
            self._generate_plots()

    def _display_totals(self, title: str, df: pd.DataFrame):
        """Exibe os totais em uma tabela formatada."""
        console.print(f"\n[bold cyan]{title}:[/bold cyan]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Nome", style="cyan")
        
        # Adicionando colunas para cada status
        for status in df.columns:
            table.add_column(status, justify="right")
        
        # Adicionando linhas
        for idx in df.index:
            row = [str(idx)] + [str(df.loc[idx, col]) for col in df.columns]
            table.add_row(*row)
        
        console.print(table)

    def _generate_plots(self):
        """Gera visualizações dos dados."""
        if not os.path.exists('reports'):
            os.makedirs('reports')
            
        # Gráfico de status por equipe
        fig_team = px.bar(
            self.df_combined,
            x='EQUIPE',
            color='SITUAÇÃO',
            title='Distribuição de Status por Equipe',
            barmode='group'
        )
        fig_team.write_html('reports/status_por_equipe.html')
        
        # Gráfico de pizza para distribuição de demandas por equipe
        fig_pie = px.pie(
            self.df_combined,
            names='EQUIPE',
            title='Distribuição de Demandas por Equipe'
        )
        fig_pie.write_html('reports/distribuicao_equipes.html')
        
        logger.info("Gráficos gerados com sucesso")

def main():
    """Função principal para execução do processamento."""
    try:
        processor = DemandasProcessor()
        
        # Executando as etapas do processamento
        console.print("[bold green]Iniciando processamento das demandas...[/bold green]")
        
        processor.read_csv_files()
        processor.preprocess_data()
        processor.calculate_totals()
        
        console.print("[bold green]Processamento concluído com sucesso![/bold green]")
        
    except Exception as e:
        logger.error(f"Erro durante o processamento: {str(e)}")
        console.print(f"[bold red]ERRO: {str(e)}[/bold red]")

if __name__ == "__main__":
    main()
