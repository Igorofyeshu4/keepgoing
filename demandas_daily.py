#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análise Diária de Demandas Financeiras
-------------------------------------
Autor: Data Analytics Team
Data: 2025-01-26

Este script realiza análise detalhada das demandas diárias do setor financeiro,
processando dados de múltiplas abas de uma planilha Excel e gerando insights
automatizados.
"""

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
        console.print(f"[bold green]Inicializando análise de demandas...[/bold green]")
        console.print(f"[blue]Arquivo: {self.file_path}[/blue]")
        self.initialize_excel()
    
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
    
    def analyze_columns(self) -> Dict:
        """
        Analisa as colunas do DataFrame atual.
        
        Returns:
            Dicionário com informações sobre as colunas
        """
        if self.current_df is None:
            raise ValueError("Nenhuma aba carregada. Use load_sheet primeiro.")
        
        console.print("\n[bold green]Analisando colunas...[/bold green]")
        
        analysis = {
            "total_columns": len(self.current_df.columns),
            "columns": self.current_df.columns.tolist(),
            "dtypes": self.current_df.dtypes.to_dict(),
            "null_counts": self.current_df.isnull().sum().to_dict(),
            "unique_counts": {col: self.current_df[col].nunique() 
                            for col in self.current_df.columns}
        }
        
        # Criar tabela com análise das colunas
        col_table = Table(title="Análise de Colunas")
        col_table.add_column("Coluna", style="cyan")
        col_table.add_column("Tipo", style="green")
        col_table.add_column("Valores Nulos", justify="right")
        col_table.add_column("Valores Únicos", justify="right")
        
        for col in analysis['columns']:
            col_table.add_row(
                col,
                str(analysis['dtypes'][col]),
                str(analysis['null_counts'][col]),
                str(analysis['unique_counts'][col])
            )
        
        console.print(col_table)
        
        return analysis
    
    def get_daily_metrics(self, date_column: str = 'DATA') -> Dict:
        """
        Calcula métricas diárias das demandas.
        
        Args:
            date_column: Nome da coluna de data
            
        Returns:
            Dicionário com métricas diárias
        """
        if self.current_df is None:
            raise ValueError("Nenhuma aba carregada. Use load_sheet primeiro.")
        
        console.print("\n[bold green]Calculando métricas diárias...[/bold green]")
        
        metrics = {
            "total_demandas": len(self.current_df),
            "demandas_por_status": self.current_df['SITUAÇÃO'].value_counts().to_dict(),
            "demandas_por_responsavel": self.current_df['RESPONSÁVEL'].value_counts().to_dict(),
            "demandas_por_tipo": self.current_df['ATIVO/RECEPTIVO'].value_counts().to_dict()
        }
        
        # Adiciona análise temporal se a coluna de data existir
        if date_column in self.current_df.columns:
            logger.debug(f"Processando coluna de data: {date_column}")
            self.current_df[date_column] = pd.to_datetime(self.current_df[date_column])
            
            metrics.update({
                "demandas_por_dia": self.current_df[date_column].dt.date.value_counts().sort_index().to_dict(),
                "media_diaria": len(self.current_df) / self.current_df[date_column].nunique()
            })
            
            # Criar tabela com métricas diárias
            metrics_table = Table(title="Métricas Diárias")
            metrics_table.add_column("Métrica", style="cyan")
            metrics_table.add_column("Valor", style="green")
            
            metrics_table.add_row("Total de Demandas", str(metrics['total_demandas']))
            metrics_table.add_row("Média Diária", f"{metrics['media_diaria']:.2f}")
            
            console.print(metrics_table)
            
            # Tabela de status
            status_table = Table(title="Distribuição por Status")
            status_table.add_column("Status", style="cyan")
            status_table.add_column("Quantidade", style="green")
            
            for status, count in metrics['demandas_por_status'].items():
                status_table.add_row(str(status), str(count))
            
            console.print(status_table)
        
        return metrics
    
    def analyze_resolutions_by_team(self, target_date):
        """
        Analisa as resoluções por equipe para uma data específica.
        
        Args:
            target_date: Data alvo para análise (pode ser string 'YYYY-MM-DD' ou objeto date)
        """
        if isinstance(target_date, str):
            target_date = pd.to_datetime(target_date).date()
        
        # Filtra demandas resolvidas
        resolved_df = self.current_df[self.current_df['SITUAÇÃO'] == 'RESOLVIDO'].copy()
        
        # Filtra por data de resolução
        resolved_df = resolved_df[resolved_df['RESOLUÇÃO'].dt.date == target_date]
        
        if resolved_df.empty:
            console.print(f"[yellow]Nenhuma demanda resolvida encontrada para {target_date.strftime('%d/%m/%Y')}[/yellow]")
            return
        
        # Define as equipes
        equipe_julio = ["JULIO", "JULIO CESAR", "JULIO CESAR PEREIRA"]
        equipe_leandro_adriano = ["LEANDRO", "ADRIANO"]
        
        # Função para classificar equipe
        def get_team(responsavel):
            if pd.isna(responsavel):
                return "Sem Responsável"
            responsavel = str(responsavel).upper()
            if any(membro in responsavel for membro in equipe_julio):
                return "Equipe Julio"
            elif any(membro in responsavel for membro in equipe_leandro_adriano):
                return "Equipe Leandro/Adriano"
            return "Outros"
        
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
    
    def create_daily_report(self, output_dir: str = "reports") -> None:
        """
        Cria relatório diário com visualizações.
        
        Args:
            output_dir: Diretório onde os relatórios serão salvos
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        console.print(f"\n[bold green]Gerando relatório em {output_dir}...[/bold green]")
        
        report_files = []
        
        # Gráfico de distribuição de status
        try:
            fig_status = px.pie(
                self.current_df,
                names='SITUAÇÃO',
                title='Distribuição de Status das Demandas'
            )
            status_file = f"{output_dir}/status_distribution.html"
            fig_status.write_html(status_file)
            logger.debug(f"Gráfico de status gerado: {status_file}")
            report_files.append(("Status", status_file))
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de status: {e}")
            
        # Gráfico de demandas por responsável
        try:
            resp_counts = self.current_df['RESPONSÁVEL'].value_counts().reset_index()
            resp_counts.columns = ['RESPONSÁVEL', 'Quantidade']
            
            fig_resp = px.bar(
                resp_counts,
                x='RESPONSÁVEL',
                y='Quantidade',
                title='Demandas por Responsável'
            )
            resp_file = f"{output_dir}/responsaveis_distribution.html"
            fig_resp.write_html(resp_file)
            logger.debug(f"Gráfico de responsáveis gerado: {resp_file}")
            report_files.append(("Responsáveis", resp_file))
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de responsáveis: {e}")
            
        # Tabela com arquivos gerados
        if report_files:
            table = Table(title="Relatórios Gerados")
            table.add_column("Tipo", style="cyan")
            table.add_column("Arquivo", style="green")
            
            for report_type, file_path in report_files:
                table.add_row(report_type, file_path)
                
            console.print(table)

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
        
        # Converte datas
        analyzer.current_df['RESOLUÇÃO'] = pd.to_datetime(analyzer.current_df['RESOLUÇÃO'], errors='coerce')
        
        # Mostra datas disponíveis
        datas_resolucao = analyzer.current_df[
            (analyzer.current_df['SITUAÇÃO'] == 'RESOLVIDO') & 
            (analyzer.current_df['RESOLUÇÃO'].notna())
        ]['RESOLUÇÃO'].dt.date.unique()
        
        console.print("\n[bold cyan]Datas com demandas resolvidas:[/bold cyan]")
        for data in sorted(datas_resolucao):
            console.print(f"- {data.strftime('%d/%m/%Y')}")
        
        # Análise para cada data em janeiro/2025
        for data in sorted(datas_resolucao):
            if data.year == 2025 and data.month == 1:
                console.print(f"\n[bold yellow]Analisando resoluções para {data.strftime('%d/%m/%Y')}[/bold yellow]")
                analyzer.analyze_resolutions_by_team(data)
        
        # Gera relatórios visuais
        analyzer.create_daily_report()
        
        console.print("\n[bold green]Análise concluída com sucesso![/bold green]")
            
    except Exception as e:
        logger.error(f"Erro durante a análise: {e}")
        console.print(f"[bold red]ERRO: {str(e)}[/bold red]")
        raise

if __name__ == "__main__":
    main()