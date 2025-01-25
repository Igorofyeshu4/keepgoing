import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Inicializar o app Dash com tema claro e moderno
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Função para carregar e processar dados
def load_data():
    df = pd.read_excel('../data/demandas.xlsx')
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    return df

# Layout do dashboard
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Dashboard de Análise de Demandas", 
                   className="text-center mb-4 mt-4",
                   style={'color': '#2c3e50'})
        ])
    ]),
    
    # Filtros
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Filtros", className="card-title"),
                    dcc.DatePickerRange(
                        id='date-range',
                        start_date=datetime.now().date() - timedelta(days=30),
                        end_date=datetime.now().date(),
                        display_format='DD/MM/YYYY'
                    ),
                    html.Div(className="mb-3"),
                    dcc.Dropdown(
                        id='group-filter',
                        placeholder='Selecione os Grupos',
                        multi=True
                    ),
                    html.Div(className="mb-3"),
                    dcc.Dropdown(
                        id='responsible-filter',
                        placeholder='Selecione os Responsáveis',
                        multi=True
                    )
                ])
            ], className="mb-4")
        ])
    ]),
    
    # KPIs principais
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Total Resolvidos", className="card-title text-center"),
                    html.H3(id="total-resolved", className="text-center")
                ])
            ])
        ]),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Taxa de Resolução", className="card-title text-center"),
                    html.H3(id="resolution-rate", className="text-center")
                ])
            ])
        ]),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Média Diária", className="card-title text-center"),
                    html.H3(id="daily-average", className="text-center")
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Gráficos
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Evolução Diária", className="card-title"),
                    dcc.Graph(id='daily-evolution')
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Desempenho por Grupo", className="card-title"),
                    dcc.Graph(id='group-performance')
                ])
            ])
        ], width=6)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Desempenho Individual", className="card-title"),
                    dcc.Graph(id='individual-performance')
                ])
            ])
        ])
    ])
], fluid=True, style={'backgroundColor': '#f8f9fa'})

# Callbacks para atualizar os filtros
@app.callback(
    [Output('group-filter', 'options'),
     Output('responsible-filter', 'options')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_filters(start_date, end_date):
    df = load_data()
    
    # Filtrar por data
    mask = (df['DATA'] >= start_date) & (df['DATA'] <= end_date)
    filtered_df = df.loc[mask]
    
    # Obter grupos e responsáveis únicos
    groups = sorted(filtered_df['GRUPO'].unique())
    responsibles = sorted(filtered_df['RESPONSÁVEL'].unique())
    
    group_options = [{'label': g, 'value': g} for g in groups if pd.notna(g)]
    responsible_options = [{'label': r, 'value': r} for r in responsibles if pd.notna(r)]
    
    return group_options, responsible_options

# Callback para atualizar KPIs
@app.callback(
    [Output('total-resolved', 'children'),
     Output('resolution-rate', 'children'),
     Output('daily-average', 'children')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('group-filter', 'value'),
     Input('responsible-filter', 'value')]
)
def update_kpis(start_date, end_date, selected_groups, selected_responsibles):
    df = load_data()
    
    # Aplicar filtros
    mask = (df['DATA'] >= start_date) & (df['DATA'] <= end_date)
    if selected_groups:
        mask &= df['GRUPO'].isin(selected_groups)
    if selected_responsibles:
        mask &= df['RESPONSÁVEL'].isin(selected_responsibles)
    
    filtered_df = df.loc[mask]
    
    # Calcular KPIs
    total_resolved = len(filtered_df[filtered_df['SITUAÇÃO'].str.lower() == 'resolvido'])
    resolution_rate = f"{(total_resolved / len(filtered_df) * 100):.1f}%"
    
    days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1
    daily_average = f"{total_resolved / days:.1f}"
    
    return f"{total_resolved:,}", resolution_rate, daily_average

# Callback para atualizar gráficos
@app.callback(
    [Output('daily-evolution', 'figure'),
     Output('group-performance', 'figure'),
     Output('individual-performance', 'figure')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('group-filter', 'value'),
     Input('responsible-filter', 'value')]
)
def update_graphs(start_date, end_date, selected_groups, selected_responsibles):
    df = load_data()
    
    # Aplicar filtros
    mask = (df['DATA'] >= start_date) & (df['DATA'] <= end_date)
    if selected_groups:
        mask &= df['GRUPO'].isin(selected_groups)
    if selected_responsibles:
        mask &= df['RESPONSÁVEL'].isin(selected_responsibles)
    
    filtered_df = df.loc[mask]
    
    # Gráfico de evolução diária
    daily_data = filtered_df.groupby('DATA').size().reset_index(name='count')
    daily_fig = px.line(daily_data, x='DATA', y='count',
                       title='Evolução Diária de Demandas',
                       template='plotly_white')
    daily_fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Quantidade",
        showlegend=False
    )
    
    # Gráfico de desempenho por grupo
    group_data = filtered_df.groupby('GRUPO').agg({
        'SITUAÇÃO': lambda x: (x.str.lower() == 'resolvido').sum()
    }).reset_index()
    group_fig = px.bar(group_data, x='GRUPO', y='SITUAÇÃO',
                      title='Desempenho por Grupo',
                      template='plotly_white')
    group_fig.update_layout(
        xaxis_title="Grupo",
        yaxis_title="Demandas Resolvidas",
        showlegend=False
    )
    
    # Gráfico de desempenho individual
    individual_data = filtered_df.groupby('RESPONSÁVEL').agg({
        'SITUAÇÃO': lambda x: (x.str.lower() == 'resolvido').sum()
    }).reset_index()
    individual_data = individual_data.sort_values('SITUAÇÃO', ascending=False).head(10)
    individual_fig = px.bar(individual_data, x='RESPONSÁVEL', y='SITUAÇÃO',
                          title='Top 10 - Desempenho Individual',
                          template='plotly_white')
    individual_fig.update_layout(
        xaxis_title="Responsável",
        yaxis_title="Demandas Resolvidas",
        showlegend=False
    )
    
    return daily_fig, group_fig, individual_fig

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
