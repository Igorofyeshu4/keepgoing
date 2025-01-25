"""
Dashboard de Análise de Demandas

Este dashboard fornece uma interface interativa para análise de demandas,
incluindo KPIs, gráficos e filtros.

Funcionalidades:
- Filtros por data, grupo e status
- KPIs principais (total, em progresso, concluídas, pendentes)
- Gráficos de distribuição por status e grupo
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Dados de exemplo
def generate_sample_data(n_demands=150):
    """Gera dados de exemplo para o dashboard"""
    np.random.seed(42)
    
    # Datas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dates = [start_date + timedelta(days=x) for x in range(31)]
    
    # Status
    status_options = ['Pendente', 'Em Progresso', 'Concluído']
    status_weights = [0.1, 0.3, 0.6]
    
    # Grupos
    groups = ['A', 'B', 'C']
    
    data = {
        'Data': np.random.choice(dates, n_demands),
        'Status': np.random.choice(status_options, n_demands, p=status_weights),
        'Grupo': np.random.choice(groups, n_demands),
        'Responsavel': [f'Pessoa {i}' for i in np.random.randint(1, 6, n_demands)]
    }
    
    return pd.DataFrame(data)

# Carrega dados
df = generate_sample_data()

# Inicializa o app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout do sidebar
sidebar = html.Div(
    [
        html.H2("Filtros", className="display-6"),
        html.Hr(),
        html.P("Selecione o período:"),
        dcc.DatePickerRange(
            id='date-picker',
            start_date=df['Data'].min(),
            end_date=df['Data'].max(),
            display_format='DD/MM/YYYY',
            className="mb-3"
        ),
        html.P("Selecione o grupo:"),
        dcc.Dropdown(
            id='group-dropdown',
            options=[{'label': g, 'value': g} for g in sorted(df['Grupo'].unique())],
            className="mb-3"
        ),
        html.P("Status:"),
        dcc.Checklist(
            id='status-checklist',
            options=[{'label': f' {s}', 'value': s} for s in sorted(df['Status'].unique())],
            value=list(df['Status'].unique())
        )
    ],
    style={
        'position': 'fixed',
        'top': 0,
        'left': 0,
        'bottom': 0,
        'width': '250px',
        'padding': '20px',
        'background-color': '#f8f9fa'
    }
)

# Layout principal
content = html.Div(
    [
        html.H1("Dashboard de Demandas", className="text-center mb-4"),
        
        # KPI Cards
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Total Demandas", className="card-title"),
                    html.H2(id="total-demands", className="card-text text-primary")
                ])
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Em Progresso", className="card-title"),
                    html.H2(id="in-progress", className="card-text text-warning")
                ])
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Concluídas", className="card-title"),
                    html.H2(id="completed", className="card-text text-success")
                ])
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Pendentes", className="card-title"),
                    html.H2(id="pending", className="card-text text-danger")
                ])
            ]), width=3),
        ], className="mb-4"),

        # Gráficos
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Distribuição por Status"),
                        dcc.Graph(id='status-graph')
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Demandas por Grupo"),
                        dcc.Graph(id='group-graph')
                    ])
                ])
            ], width=6),
        ])
    ],
    style={
        'margin-left': '250px',
        'padding': '20px'
    }
)

# Layout completo
app.layout = html.Div([sidebar, content])

# Callbacks
@app.callback(
    [Output('total-demands', 'children'),
     Output('in-progress', 'children'),
     Output('completed', 'children'),
     Output('pending', 'children'),
     Output('status-graph', 'figure'),
     Output('group-graph', 'figure')],
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('group-dropdown', 'value'),
     Input('status-checklist', 'value')]
)
def update_dashboard(start_date, end_date, selected_group, selected_status):
    """Atualiza todos os elementos do dashboard com base nos filtros"""
    
    # Filtra dados
    mask = df['Status'].isin(selected_status if selected_status else [])
    if start_date and end_date:
        mask &= (df['Data'] >= start_date) & (df['Data'] <= end_date)
    if selected_group:
        mask &= (df['Grupo'] == selected_group)
    
    filtered_df = df[mask]
    
    # Calcula KPIs
    total = len(filtered_df)
    in_progress = len(filtered_df[filtered_df['Status'] == 'Em Progresso'])
    completed = len(filtered_df[filtered_df['Status'] == 'Concluído'])
    pending = len(filtered_df[filtered_df['Status'] == 'Pendente'])
    
    # Gráfico de status
    status_counts = filtered_df['Status'].value_counts()
    fig_status = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        hole=0.3,
        title='Distribuição por Status'
    )
    
    # Gráfico de grupos
    group_counts = filtered_df['Grupo'].value_counts()
    fig_group = px.bar(
        x=group_counts.index,
        y=group_counts.values,
        title='Demandas por Grupo',
        labels={'x': 'Grupo', 'y': 'Quantidade'}
    )
    
    return total, in_progress, completed, pending, fig_status, fig_group

if __name__ == '__main__':
    app.run_server(debug=True)
