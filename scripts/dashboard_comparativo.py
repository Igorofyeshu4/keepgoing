import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output, State
from google_sheets_sync import GoogleSheetsSync
from datetime import datetime
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from pathlib import Path

class ExcelMonitor(FileSystemEventHandler):
    def __init__(self, dashboard):
        self.last_modified = time.time()
        self.cooldown = 2  # Tempo mínimo entre atualizações em segundos
        self.excel_path = "F:/demandstest/docs/_DEMANDAS DE JANEIRO_2025.xlsx"
        self.dashboard = dashboard
        self.modification_count = 0
        
    def on_modified(self, event):
        if event.src_path.endswith('.xlsx'):
            current_time = time.time()
            if current_time - self.last_modified > self.cooldown:
                self.last_modified = current_time
                self.modification_count += 1
                
                # Análise das mudanças
                try:
                    df_julio_novo = pd.read_excel(self.excel_path, sheet_name="DEMANDAS JULIO")
                    df_leandro_novo = pd.read_excel(self.excel_path, sheet_name="DEMANDA LEANDROADRIANO")
                    
                    # Compara com os dados anteriores
                    total_anterior_julio = len(self.dashboard.df_julio) if self.dashboard.df_julio is not None else 0
                    total_anterior_leandro = len(self.dashboard.df_leandro) if self.dashboard.df_leandro is not None else 0
                    
                    total_novo_julio = len(df_julio_novo)
                    total_novo_leandro = len(df_leandro_novo)
                    
                    # Atualiza os dados no dashboard
                    self.dashboard.df_julio = df_julio_novo
                    self.dashboard.df_leandro = df_leandro_novo
                    
                    # Mostra as mudanças
                    print(f"\n=== Atualização #{self.modification_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
                    print(f"Equipe Julio: {total_novo_julio - total_anterior_julio:+d} novas demandas")
                    print(f"Equipe Leandro: {total_novo_leandro - total_anterior_leandro:+d} novas demandas")
                    print("Status: Dashboard atualizado com sucesso!")
                    
                except Exception as e:
                    print(f"Erro ao analisar mudanças: {str(e)}")

class DemandDashboard:
    def __init__(self):
        self.app = Dash(__name__)
        self.excel_path = "F:/demandstest/docs/_DEMANDAS DE JANEIRO_2025.xlsx"
        self.df_julio = None
        self.df_leandro = None
        self.setup_file_monitor()
        self.load_initial_data()
        self.setup_layout()
        self.setup_callbacks()
        
    def load_initial_data(self):
        """Carrega os dados iniciais"""
        try:
            self.df_julio = pd.read_excel(self.excel_path, sheet_name="DEMANDAS JULIO")
            self.df_leandro = pd.read_excel(self.excel_path, sheet_name="DEMANDA LEANDROADRIANO")
            print("\n=== Dados Iniciais Carregados ===")
            print(f"Equipe Julio: {len(self.df_julio)} demandas")
            print(f"Equipe Leandro: {len(self.df_leandro)} demandas")
        except Exception as e:
            print(f"Erro ao carregar dados iniciais: {str(e)}")
        
    def setup_file_monitor(self):
        """Configura o monitoramento do arquivo Excel"""
        self.event_handler = ExcelMonitor(self)
        self.observer = Observer()
        watch_path = str(Path(self.excel_path).parent)
        self.observer.schedule(self.event_handler, watch_path, recursive=False)
        self.observer.start()
        print(f"\n=== Monitoramento Iniciado ===")
        print(f"Pasta monitorada: {watch_path}")
        print("Aguardando alterações no arquivo Excel...")
        
    def load_excel_data(self):
        try:
            # Carrega os dados das planilhas locais
            excel_path = "F:/demandstest/docs/_DEMANDAS DE JANEIRO_2025.xlsx"
            df_julio = pd.read_excel(excel_path, sheet_name="DEMANDAS JULIO")
            df_leandro = pd.read_excel(excel_path, sheet_name="DEMANDA LEANDROADRIANO")
            return df_julio, df_leandro
        except Exception as e:
            print(f"Erro ao carregar dados: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()
        
    def process_data(self, df):
        if df is None or df.empty:
            return pd.DataFrame()
            
        try:
            df = df.copy()
            df['DATA_RESOLUCAO'] = pd.to_datetime(df.iloc[:, 1])
            df['RESPONSAVEL'] = df.iloc[:, 10]
            df['STATUS'] = df.iloc[:, 11]
            df['TIPO'] = df.iloc[:, 3]
            
            # Filtra apenas resolvidos
            return df[df['STATUS'].str.upper() == 'RESOLVIDO']
        except Exception as e:
            print(f"Erro ao processar dados: {str(e)}")
            return pd.DataFrame()
    
    def create_daily_table(self, df):
        if df is None or df.empty:
            return pd.DataFrame()
            
        try:
            daily_data = df.groupby(['DATA_RESOLUCAO', 'RESPONSAVEL']).size().reset_index()
            daily_data.columns = ['Data', 'Responsável', 'Total Resolvido']
            daily_data['Data'] = daily_data['Data'].dt.strftime('%Y-%m-%d')
            return daily_data.sort_values(['Data', 'Responsável'])
        except Exception as e:
            print(f"Erro ao criar tabela diária: {str(e)}")
            return pd.DataFrame()
    
    def calculate_metrics(self, df_julio, df_leandro):
        try:
            if df_julio is None or df_leandro is None:
                return {
                    'total_julio': 0,
                    'total_leandro': 0,
                    'media_diaria_julio': 0,
                    'media_diaria_leandro': 0
                }
                
            metrics = {
                'total_julio': len(df_julio) if not df_julio.empty else 0,
                'total_leandro': len(df_leandro) if not df_leandro.empty else 0,
                'media_diaria_julio': len(df_julio) / df_julio['DATA_RESOLUCAO'].dt.date.nunique() if not df_julio.empty else 0,
                'media_diaria_leandro': len(df_leandro) / df_leandro['DATA_RESOLUCAO'].dt.date.nunique() if not df_leandro.empty else 0
            }
            return metrics
        except Exception as e:
            print(f"Erro ao calcular métricas: {str(e)}")
            return {
                'total_julio': 0,
                'total_leandro': 0,
                'media_diaria_julio': 0,
                'media_diaria_leandro': 0
            }
    
    def create_comparison_charts(self, df_julio, df_leandro):
        try:
            if df_julio is None or df_leandro is None:
                return go.Figure(), go.Figure(), go.Figure()
                
            # Gráfico de barras comparativo
            fig_comparison = go.Figure(data=[
                go.Bar(name='Equipe Julio', x=['Total Resolvido'], y=[len(df_julio)]),
                go.Bar(name='Equipe Leandro', x=['Total Resolvido'], y=[len(df_leandro)])
            ])
            fig_comparison.update_layout(
                title='Comparativo de Resoluções por Equipe',
                yaxis_title='Total de Demandas',
                showlegend=True
            )
            
            # Gráfico de linha temporal
            df_julio_daily = df_julio.groupby('DATA_RESOLUCAO').size().reset_index(name='Total')
            df_julio_daily['Equipe'] = 'Julio'
            df_leandro_daily = df_leandro.groupby('DATA_RESOLUCAO').size().reset_index(name='Total')
            df_leandro_daily['Equipe'] = 'Leandro'
            
            df_timeline = pd.concat([df_julio_daily, df_leandro_daily])
            fig_timeline = px.line(df_timeline, 
                                x='DATA_RESOLUCAO', 
                                y='Total',
                                color='Equipe',
                                title='Resoluções por Dia')
            fig_timeline.update_layout(
                xaxis_title='Data',
                yaxis_title='Total de Resoluções'
            )
            
            # Gráfico de pizza para tipos de demanda
            df_tipos_julio = df_julio.groupby('TIPO').size().reset_index(name='Total')
            df_tipos_julio['Equipe'] = 'Julio'
            df_tipos_leandro = df_leandro.groupby('TIPO').size().reset_index(name='Total')
            df_tipos_leandro['Equipe'] = 'Leandro'
            
            df_tipos = pd.concat([df_tipos_julio, df_tipos_leandro])
            fig_tipos = px.pie(df_tipos, 
                            values='Total', 
                            names='TIPO',
                            color='Equipe',
                            title='Distribuição por Tipo de Demanda')
            
            return fig_comparison, fig_timeline, fig_tipos
            
        except Exception as e:
            print(f"Erro ao criar gráficos: {str(e)}")
            return go.Figure(), go.Figure(), go.Figure()
    
    def setup_layout(self):
        self.app.layout = html.Div([
            html.H1("Dashboard Comparativo de Demandas", 
                   style={'textAlign': 'center', 'marginBottom': '30px'}),
            
            # Botão de sincronização
            html.Div([
                html.Button('Sincronizar com Google Sheets', 
                           id='sync-button',
                           style={'marginBottom': '20px'}),
                html.Div(id='sync-status')
            ], style={'textAlign': 'center'}),
            
            # Container de métricas
            html.Div(id='metrics-container', className='metrics-container'),
            
            # Gráficos
            html.Div([
                dcc.Graph(id='comparison-chart'),
                dcc.Graph(id='timeline-chart'),
                dcc.Graph(id='tipo-chart')
            ], className='charts-container'),
            
            # Tabelas
            html.Div([
                html.Div([
                    html.H3("Resoluções Diárias - Equipe Julio"),
                    dash_table.DataTable(
                        id='table-julio',
                        page_size=10,
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'},
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                        }
                    )
                ], className='table-section'),
                
                html.Div([
                    html.H3("Resoluções Diárias - Equipe Leandro"),
                    dash_table.DataTable(
                        id='table-leandro',
                        page_size=10,
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'},
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                        }
                    )
                ], className='table-section')
            ], className='tables-container'),
            
            # Componente de intervalo para atualização
            dcc.Interval(
                id='interval-component',
                interval=30*1000,  # Atualiza a cada 30 segundos
                n_intervals=0
            )
        ])
    
    def setup_callbacks(self):
        @self.app.callback(
            [
                Output('metrics-container', 'children'),
                Output('comparison-chart', 'figure'),
                Output('timeline-chart', 'figure'),
                Output('tipo-chart', 'figure'),
                Output('table-julio', 'data'),
                Output('table-julio', 'columns'),
                Output('table-leandro', 'data'),
                Output('table-leandro', 'columns')
            ],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            try:
                # Verifica se o arquivo foi modificado
                if hasattr(self.event_handler, 'last_modified'):
                    current_time = time.time()
                    if current_time - self.event_handler.last_modified < 1:
                        print("Atualizando dashboard com novos dados...")
                
                # Carrega e processa os dados
                df_julio, df_leandro = self.df_julio, self.df_leandro
                df_julio_proc = self.process_data(df_julio)
                df_leandro_proc = self.process_data(df_leandro)
                
                # Calcula métricas
                metrics = self.calculate_metrics(df_julio_proc, df_leandro_proc)
                
                # Cria os elementos de métrica
                metrics_div = html.Div([
                    html.Div([
                        html.H3("Equipe Julio"),
                        html.P(f"Total Resolvido: {metrics['total_julio']}"),
                        html.P(f"Média Diária: {metrics['media_diaria_julio']:.2f}")
                    ], className='metric-box'),
                    html.Div([
                        html.H3("Equipe Leandro"),
                        html.P(f"Total Resolvido: {metrics['total_leandro']}"),
                        html.P(f"Média Diária: {metrics['media_diaria_leandro']:.2f}")
                    ], className='metric-box')
                ])
                
                # Cria gráficos
                fig_comparison, fig_timeline, fig_tipos = self.create_comparison_charts(
                    df_julio_proc, df_leandro_proc)
                
                # Cria tabelas diárias
                daily_julio = self.create_daily_table(df_julio_proc)
                daily_leandro = self.create_daily_table(df_leandro_proc)
                
                # Prepara colunas para as tabelas
                columns = [{"name": i, "id": i} for i in ['Data', 'Responsável', 'Total Resolvido']]
                
                return (
                    metrics_div,
                    fig_comparison,
                    fig_timeline,
                    fig_tipos,
                    daily_julio.to_dict('records'),
                    columns,
                    daily_leandro.to_dict('records'),
                    columns
                )
                
            except Exception as e:
                print(f"Erro no callback de atualização: {str(e)}")
                empty_fig = go.Figure()
                empty_table = pd.DataFrame(columns=['Data', 'Responsável', 'Total Resolvido'])
                columns = [{"name": i, "id": i} for i in empty_table.columns]
                
                return (
                    html.Div("Erro ao carregar dados"),
                    empty_fig,
                    empty_fig,
                    empty_fig,
                    [],
                    columns,
                    [],
                    columns
                )
        
        @self.app.callback(
            Output('sync-status', 'children'),
            [Input('sync-button', 'n_clicks')],
            [State('sync-status', 'children')]
        )
        def sync_with_sheets(n_clicks, current_status):
            if n_clicks:
                try:
                    df_julio, df_leandro = self.load_excel_data()
                    sync = GoogleSheetsSync()
                    success = sync.sync_to_sheets(df_julio, df_leandro)
                    
                    if success:
                        return html.Div("Sincronização concluída com sucesso!", 
                                      style={'color': 'green'})
                    else:
                        return html.Div("Erro na sincronização", 
                                      style={'color': 'red'})
                except Exception as e:
                    print(f"Erro na sincronização: {str(e)}")
                    return html.Div(f"Erro: {str(e)}", 
                                  style={'color': 'red'})
            return current_status
    
    def run(self, debug=True):
        try:
            print("Dashboard iniciado. Monitorando alterações no arquivo Excel...")
            print(f"Acesse o dashboard em: http://localhost:8051")
            self.app.run_server(debug=debug, port=8051)
        except KeyboardInterrupt:
            print("\nEncerrando monitoramento...")
        finally:
            self.observer.stop()
            self.observer.join()
            print("Monitoramento encerrado.")

if __name__ == '__main__':
    dashboard = DemandDashboard()
    dashboard.run()
