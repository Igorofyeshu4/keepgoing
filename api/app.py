from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import sys
import os
import logging
from flask import request

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adiciona o diretório de scripts ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from analise_dados import analisar_dados, gerar_metricas_por_responsavel

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "API de Análise de Demandas"})

@app.route('/api/metrics/summary', methods=['GET'])
def get_metrics_summary():
    try:
        logger.info("Processando requisição de métricas resumidas")
        metricas = analisar_dados()
        return jsonify({
            'total_demandas': metricas['total_demandas'],
            'total_resolvidas': metricas['total_resolvidas'],
            'taxa_resolucao': metricas['taxa_resolucao'],
            'total_receptivo': metricas['total_receptivo'],
            'total_ativo': metricas['total_ativo'],
            'insights': metricas['insights']
        })
    except Exception as e:
        logger.error(f"Erro ao processar métricas resumidas: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/metrics/team', methods=['GET'])
def get_team_metrics():
    try:
        logger.info("Processando requisição de métricas por equipe")
        metricas_responsavel = gerar_metricas_por_responsavel()
        
        teams = {
            'julio': {
                'name': 'Equipe Julio',
                'members': [],
                'total_demandas': 0,
                'total_resolvidas': 0,
                'total_receptivo': 0,
                'total_ativo': 0
            },
            'leandro': {
                'name': 'Equipe Leandro/Adriano',
                'members': [],
                'total_demandas': 0,
                'total_resolvidas': 0,
                'total_receptivo': 0,
                'total_ativo': 0
            }
        }
        
        for equipe, dados in metricas_responsavel.items():
            for responsavel, metricas in dados.items():
                member = {
                    'name': responsavel,
                    'total_demandas': metricas['total_demandas'],
                    'demandas_resolvidas': metricas['resolvidas'],
                    'taxa_resolucao': metricas['taxa_resolucao'],
                    'media_diaria': metricas['media_diaria'],
                    'receptivo': metricas['receptivo'],
                    'ativo': metricas['ativo'],
                    'pico_demandas': {
                        'data': metricas['pico_data'].strftime('%Y-%m-%d'),
                        'quantidade': metricas['pico_quantidade']
                    }
                }
                
                team_key = 'julio' if equipe == 'Equipe Julio' else 'leandro'
                teams[team_key]['members'].append(member)
                teams[team_key]['total_demandas'] += metricas['total_demandas']
                teams[team_key]['total_resolvidas'] += metricas['resolvidas']
                teams[team_key]['total_receptivo'] += metricas['receptivo']
                teams[team_key]['total_ativo'] += metricas['ativo']
        
        return jsonify({'teams': list(teams.values())})
    except Exception as e:
        logger.error(f"Erro ao processar métricas por equipe: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/metrics/daily', methods=['GET'])
def get_daily_metrics():
    try:
        logger.info("Processando requisição de métricas diárias")
        metricas_responsavel = gerar_metricas_por_responsavel()
        daily_stats = []
        
        # Agregar estatísticas diárias
        for equipe, dados in metricas_responsavel.items():
            for responsavel, metricas in dados.items():
                if 'demandas_por_dia' in metricas:
                    for data, quantidade in metricas['demandas_por_dia'].items():
                        daily_stats.append({
                            'date': data.strftime('%Y-%m-%d'),
                            'completed': quantidade
                        })
        
        return jsonify({
            'daily_stats': daily_stats
        })
    except Exception as e:
        logger.error(f"Erro ao processar métricas diárias: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.after_request
def after_request(response):
    logger.info(f"{request.method} {request.path} - Status: {response.status_code}")
    return response

if __name__ == '__main__':
    logger.info("Iniciando servidor Flask na porta 5000...")
    app.run(debug=True, port=5000)
