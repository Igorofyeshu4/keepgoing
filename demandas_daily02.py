import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
import logging
import os
from pathlib import Path
import sys
from rich import print
from rich.console import Console
from rich.table import Table
from rich.progress import track
import matplotlib.pyplot as plt
import unicodedata  # Importando para normalização de nomes

# Configuração de logging detalhado
logging.basicConfig(
    level=logging.DEBUG,  # Aumentado para DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('demandas_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

# Console rico para output mais bonito
console = Console()

class DemandasAnalyzer:
    """Classe para análise de demandas financeiras."""
    
    def __init__(self, file_path: str):
        """
        Inicializa o analisador de demandas.
        
        Args:
            file_path: Caminho para o arquivo Excel de demandas
        """
        self.file_path = Path(file_path)
        self.excel_file = None
        self.sheets = []
        self.current_df = None
        
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
        
        console.print(f"[bold green]Inicializando análise de demandas...[/bold green]")
        console.print(f"[blue]Arquivo: {self.file_path}[/blue]")
        self.initialize_excel()
    
    def normalize_name(self, name: str) -> str:
        """
        Normaliza um nome removendo acentos, espaços extras e convertendo para maiúsculas.
        
        Args:
            name: Nome a ser normalizado
            
        Returns:
            Nome normalizado
        """
        if pd.isna(name):
            return name
        name = unicodedata.normalize('NFKD', str(name).strip().upper()).encode('ASCII', 'ignore').decode('ASCII')
        return name
    
    def initialize_excel(self) -> None:
        """Inicializa a leitura do arquivo Excel e lista as abas disponíveis."""
        try:
            logger.debug(f"Tentando abrir arquivo: {self.file_path}")
            self.excel_file = pd.ExcelFile(self.file_path)
            self.sheets = self.excel_file.sheet_names
            
            # Criar tabela com informações das abas
            table = Table(title="Abas Encontradas")
            table.add_column("Nº", justify="right", style="cyan")
            table.add_column("Nome da Aba", style="green")
            
            for i, sheet in enumerate(self.sheets, 1):
                table.add_row(str(i), sheet)
            
            console.print(table)
            
        except Exception as e:
            logger.error(f"Erro ao ler arquivo Excel: {e}")
            console.print(f"[bold red]ERRO: {str(e)}[/bold red]")
            raise
    
    def load_sheet(self, sheet_name: str) -> pd.DataFrame:
        """
        Carrega uma aba específica do Excel.
        
        Args:
            sheet_name: Nome da aba a ser carregada
            
        Returns:
            DataFrame com os dados da aba
        """
        try:
            console.print(f"\n[bold yellow]Carregando aba: {sheet_name}[/bold yellow]")
            logger.debug(f"Iniciando carregamento da aba: {sheet_name}")
            
            df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
            self.current_df = df
            
            # Normaliza os nomes dos responsáveis no DataFrame
            self.current_df['RESPONSÁVEL'] = self.current_df['RESPONSÁVEL'].apply(self.normalize_name)
            
            # Exibir informações do DataFrame
            console.print("\n[bold blue]Informações do DataFrame:[/bold blue]")
            console.print(f"Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
            
            # Criar tabela com amostra dos dados
            sample_table = Table(title="Amostra dos Dados")
            for col in df.columns:
                sample_table.add_column(str(col))
            
            for _, row in df.head().iterrows():
                sample_table.add_row(*[str(val) for val in row])
            
            console.print(sample_table)
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao carregar aba {sheet_name}: {e}")
            console.print(f"[bold red]ERRO ao carregar aba: {str(e)}[/bold red]")
            raise
    
    def analyze_resolutions_by_team(self, target_date):
        """
        Analisa as resoluções por equipe para uma data específica.
        
        Args:
            target_date: Data alvo para análise (pode ser string 'YYYY-MM-DD' ou objeto date)
        """
        if isinstance(target_date, str):
            target_date = pd.to_datetime(target_date).date()
        
        # Filtra demandas resolvidas
        resolved_df = self.current_df[
            (self.current_df['SITUAÇÃO'] == 'RESOLVIDO') & 
            (pd.to_datetime(self.current_df['RESOLUÇÃO']).dt.date == target_date)
        ].copy()
        
        if resolved_df.empty:
            console.print(f"[yellow]Nenhuma demanda resolvida encontrada para {target_date.strftime('%d/%m/%Y')}[/yellow]")
            return
        
        # Função para classificar equipe
        get_team = lambda resp: "Sem Responsável" if pd.isna(resp) else (
            "Equipe Júlio" if resp in self.equipe_julio
            else ("Equipe Leandro e Adriano" if resp in self.equipe_leandro_adriano
            else "Outros")
        )
        
        # Adiciona coluna de equipe
        resolved_df['EQUIPE'] = resolved_df['RESPONSÁVEL'].apply(get_team)
        
        # Análise por equipe
        team_stats = resolved_df['EQUIPE'].value_counts()
        
        console.print(f"\n[bold cyan]Resoluções por Equipe em {target_date.strftime('%d/%m/%Y')}:[/bold cyan]")
        for team, count in team_stats.items():
            console.print(f"{team}: {count} demandas")
        
        # Análise por responsável
        resp_stats = resolved_df['RESPONSÁVEL'].value_counts()
        
        console.print(f"\n[bold cyan]Resoluções por Responsável em {target_date.strftime('%d/%m/%Y')}:[/bold cyan]")
        for resp, count in resp_stats.items():
            if pd.isna(resp):
                resp = "Sem Responsável"
            console.print(f"{resp}: {count} demandas")
        
        # Gera gráficos
        try:
            # Gráfico de pizza para distribuição por equipe
            fig_team = px.pie(
                values=team_stats.values,
                names=team_stats.index,
                title=f'Distribuição de Resoluções por Equipe - {target_date.strftime("%d/%m/%Y")}'
            )
            team_chart_path = f'reports/team_distribution_{target_date.strftime("%Y%m%d")}.html'
            fig_team.write_html(team_chart_path)
            logger.debug(f"Gráfico de equipes gerado: {team_chart_path}")
            
            # Gráfico de barras para responsáveis
            fig_resp = px.bar(
                x=resp_stats.index.fillna('Sem Responsável'),
                y=resp_stats.values,
                title=f'Resoluções por Responsável - {target_date.strftime("%d/%m/%Y")}'
            )
            resp_chart_path = f'reports/resp_distribution_{target_date.strftime("%Y%m%d")}.html'
            fig_resp.write_html(resp_chart_path)
            logger.debug(f"Gráfico de responsáveis gerado: {resp_chart_path}")
            
            # Exibe os caminhos dos gráficos gerados
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Tipo", style="dim")
            table.add_column("Arquivo")
            table.add_row("Equipes", team_chart_path)
            table.add_row("Responsáveis", resp_chart_path)
            console.print("\n[bold cyan]Gráficos Gerados:[/bold cyan]")
            console.print(table)
            
        except Exception as e:
            logger.error(f"Erro ao gerar gráficos: {e}")
            console.print(f"[red]Erro ao gerar gráficos: {e}[/red]")
    
    # Outros métodos da classe (como `process_dates`, `plot_team_members`, etc.) permanecem inalterados
    # ...

def main():
    """Função principal para execução da análise."""
    try:
        console.print("[bold blue]Iniciando Análise de Demandas[/bold blue]")
        
        # Caminho do arquivo Excel
        file_path = "docs/_DEMANDAS DE JANEIRO_2025.xlsx"
        
        # Inicializa o analisador
        analyzer = DemandasAnalyzer(file_path)
        
        # Lista de abas para análise
        abas_analise = ["DEMANDAS JULIO", "DEMANDA LEANDROADRIANO"]
        
        # DataFrame combinado
        combined_df = pd.DataFrame()
        
        for aba in abas_analise:
            if aba in analyzer.sheets:
                console.print(f"\n[bold yellow]Analisando aba: {aba}[/bold yellow]")
                
                df = analyzer.load_sheet(aba)
                combined_df = pd.concat([combined_df, df], ignore_index=True)
                
                # Análise individual da aba
                analyzer.analyze_columns()
                analyzer.get_daily_metrics()
        
        # Atualiza o DataFrame atual com os dados combinados
        analyzer.current_df = combined_df
        
        # Processa datas
        datas_resolucao = analyzer.process_dates()
        
        # Análise para cada data em janeiro/2025
        for data in sorted(datas_resolucao):
            if data.year == 2025 and data.month == 1:
                console.print(f"\n[bold yellow]Analisando resoluções para {data.strftime('%d/%m/%Y')}[/bold yellow]")
                analyzer.analyze_resolutions_by_team(data)
        
        # Gera gráficos
        analyzer.plot_team_members()
        
        # Gera relatórios visuais
        analyzer.create_daily_report()
        
        console.print("\n[bold green]Análise concluída com sucesso![/bold green]")
            
    except Exception as e:
        logger.error(f"Erro durante a análise: {e}")
        console.print(f"[bold red]ERRO: {str(e)}[/bold red]")
        raise

if __name__ == "__main__":
    main()