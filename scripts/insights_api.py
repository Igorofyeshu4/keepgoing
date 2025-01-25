from flask import Blueprint, jsonify, request
from datetime import datetime
import json
import os

insights_bp = Blueprint('insights', __name__)

# Arquivo para armazenar os insights
INSIGHTS_FILE = 'data/insights.json'

def load_insights():
    if not os.path.exists(INSIGHTS_FILE):
        return []
    try:
        with open(INSIGHTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_insights(insights):
    os.makedirs(os.path.dirname(INSIGHTS_FILE), exist_ok=True)
    with open(INSIGHTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)

@insights_bp.route('/api/insights', methods=['GET'])
def get_insights():
    insights = load_insights()
    return jsonify(insights)

@insights_bp.route('/api/insights', methods=['POST'])
def add_insight():
    insight = request.json
    insights = load_insights()
    
    new_insight = {
        'id': len(insights) + 1,
        'titulo': insight['titulo'],
        'descricao': insight['descricao'],
        'categoria': insight['categoria'],
        'impacto': insight['impacto'],
        'acoes': insight['acoes'],
        'autor': insight.get('autor', 'Anônimo'),
        'data': datetime.now().isoformat(),
        'likes': 0,
        'comentarios': []
    }
    
    insights.insert(0, new_insight)
    save_insights(insights)
    return jsonify(new_insight)

@insights_bp.route('/api/insights/<int:insight_id>/like', methods=['POST'])
def like_insight(insight_id):
    insights = load_insights()
    for insight in insights:
        if insight['id'] == insight_id:
            insight['likes'] = insight.get('likes', 0) + 1
            save_insights(insights)
            return jsonify(insight)
    return jsonify({'error': 'Insight não encontrado'}), 404

@insights_bp.route('/api/insights/<int:insight_id>/comment', methods=['POST'])
def add_comment(insight_id):
    comment = request.json
    insights = load_insights()
    for insight in insights:
        if insight['id'] == insight_id:
            novo_comentario = {
                'id': len(insight.get('comentarios', [])) + 1,
                'texto': comment['texto'],
                'autor': comment.get('autor', 'Anônimo'),
                'data': datetime.now().isoformat()
            }
            if 'comentarios' not in insight:
                insight['comentarios'] = []
            insight['comentarios'].append(novo_comentario)
            save_insights(insights)
            return jsonify(novo_comentario)
    return jsonify({'error': 'Insight não encontrado'}), 404

# Dados iniciais de exemplo
INITIAL_INSIGHTS = [
    {
        'id': 1,
        'titulo': 'Performance Equipe Julio',
        'descricao': 'Com 140 demandas resolvidas, a equipe mostra um bom desempenho em resolução, mas há espaço para melhorar o número de pendentes.',
        'categoria': 'PERFORMANCE',
        'impacto': 'ALTO',
        'acoes': 'Implementar sistema de priorização para reduzir pendências.',
        'autor': 'Gestor 1',
        'data': '2025-01-17T00:00:00',
        'likes': 3,
        'comentarios': []
    },
    {
        'id': 2,
        'titulo': 'Análise Pendências Receptivo',
        'descricao': 'Equipe Adriano/Leandro tem pendências receptivo mais altas (161), indicando possíveis atrasos na resposta inicial aos clientes.',
        'categoria': 'PENDENCIAS',
        'impacto': 'ALTO',
        'acoes': 'Revisar processo de triagem inicial e resposta ao cliente.',
        'autor': 'Analista 1',
        'data': '2025-01-17T00:00:00',
        'likes': 5,
        'comentarios': []
    }
]

# Inicializar dados se não existirem
if not os.path.exists(INSIGHTS_FILE):
    save_insights(INITIAL_INSIGHTS)
