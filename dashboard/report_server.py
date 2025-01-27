from flask import Flask, jsonify, render_template, request
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

app = Flask(__name__)

def load_data():
    """Carrega e processa os dados do CSV"""
    try:
        # Tenta diferentes encodings
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv('docs/_DEMANDAS DE JANEIRO_2025 - DEMANDAS JULIO.csv', encoding=encoding)
                break
            except:
                continue
                
        if df is None:
            raise ValueError("Não foi possível ler o arquivo")
            
        # Identifica a coluna de resolução
        resolucao_col = None
        for col in df.columns:
            try:
                sample = df[col].dropna().iloc[0] if not df[col].empty else None
                if sample and isinstance(sample, str) and len(sample.split('/')) == 3:
                    resolucao_col = col
                    break
            except:
                continue
                
        if resolucao_col is None:
            raise ValueError("Coluna de resolução não encontrada")
            
        # Renomeia colunas
        column_mapping = {
            resolucao_col: 'resolucao',
            'RESPONSÁVEL': 'responsavel',
            'RESPONS�VEL': 'responsavel',
            'RESPONSAVEL': 'responsavel',
            'SITUAÇÃO': 'situacao',
            'SITUACAO': 'situacao',
            'STATUS': 'situacao'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Converte data
        df['resolucao'] = pd.to_datetime(df['resolucao'], format='%d/%m/%Y', errors='coerce')
        
        return df
        
    except Exception as e:
        print(f"Erro ao carregar dados: {str(e)}")
        return None

def process_data(df, date_range='week', team='all', status='all'):
    """Processa os dados conforme os filtros"""
    try:
        # Filtra por data
        today = datetime.now()
        if date_range == 'today':
            df = df[df['resolucao'].dt.date == today.date()]
        elif date_range == 'week':
            start_date = today - timedelta(days=7)
            df = df[df['resolucao'] >= start_date]
        elif date_range == 'month':
            start_date = today - timedelta(days=30)
            df = df[df['resolucao'] >= start_date]
            
        # Filtra por equipe
        if team != 'all':
            df = df[df['responsavel'] == team]
            
        # Filtra por status
        if status != 'all':
            status_map = {
                'resolved': ['RESOLVIDO', 'APROVADO', 'CONCLUÍDO'],
                'pending': ['PENDENTE', 'EM ANÁLISE', 'EM ANDAMENTO']
            }
            df = df[df['situacao'].isin(status_map.get(status, []))]
            
        return df
        
    except Exception as e:
        print(f"Erro ao processar dados: {str(e)}")
        return None

def calculate_metrics(df):
    """Calcula métricas para o dashboard"""
    try:
        total = len(df)
        resolved = len(df[df['situacao'].isin(['RESOLVIDO', 'APROVADO', 'CONCLUÍDO'])])
        days = (df['resolucao'].max() - df['resolucao'].min()).days + 1
        daily_avg = resolved / max(days, 1)
        efficiency = resolved / total if total > 0 else 0
        
        # Dados diários
        daily_data = df.groupby(df['resolucao'].dt.date).size().reset_index()
        daily_data.columns = ['date', 'count']
        
        # Dados por equipe
        team_data = df.groupby('responsavel').agg({
            'situacao': 'count',
            'resolucao': lambda x: len(x[x.isin(['RESOLVIDO', 'APROVADO', 'CONCLUÍDO'])])
        }).reset_index()
        
        team_data.columns = ['team', 'total', 'resolved']
        team_data['pending'] = team_data['total'] - team_data['resolved']
        team_data['efficiency'] = team_data['resolved'] / team_data['total']
        team_data['daily_avg'] = team_data['resolved'] / max(days, 1)
        team_data['weekly_avg'] = team_data['daily_avg'] * 7
        
        return {
            'total': total,
            'resolved': resolved,
            'dailyAverage': daily_avg,
            'efficiency': efficiency,
            'dailyData': {
                'dates': daily_data['date'].tolist(),
                'resolved': daily_data['count'].tolist()
            },
            'teamData': {
                'teams': team_data['team'].tolist(),
                'resolved': team_data['resolved'].tolist(),
                'pending': team_data['pending'].tolist()
            },
            'teamDetails': team_data.to_dict('records')
        }
        
    except Exception as e:
        print(f"Erro ao calcular métricas: {str(e)}")
        return None

@app.route('/')
def index():
    """Renderiza a página principal"""
    return render_template('report.html')

@app.route('/api/demands')
def get_demands():
    """API para obter dados das demandas"""
    try:
        date_range = request.args.get('dateRange', 'week')
        team = request.args.get('team', 'all')
        status = request.args.get('status', 'all')
        
        df = load_data()
        if df is None:
            return jsonify({'error': 'Erro ao carregar dados'}), 500
            
        filtered_df = process_data(df, date_range, team, status)
        if filtered_df is None:
            return jsonify({'error': 'Erro ao processar dados'}), 500
            
        metrics = calculate_metrics(filtered_df)
        if metrics is None:
            return jsonify({'error': 'Erro ao calcular métricas'}), 500
            
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
