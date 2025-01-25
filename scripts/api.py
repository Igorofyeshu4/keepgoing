from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def home():
    return jsonify({"status": "API is running"})

def load_excel():
    excel_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'demandas.xlsx')
    if not os.path.exists(excel_path):
        return None
    return pd.read_excel(excel_path)

def save_excel(df):
    excel_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'demandas.xlsx')
    df.to_excel(excel_path, index=False)

@app.route('/api/demandas', methods=['GET'])
def get_demandas():
    try:
        df = load_excel()
        if df is None:
            return jsonify({"error": "Arquivo não encontrado"}), 404
            
        # Converter para lista de dicionários
        demandas = []
        for _, row in df.iterrows():
            demandas.append({
                'id': int(row.name),
                'data': row['DATA'].strftime('%Y-%m-%d'),
                'grupo': row['GRUPO'],
                'responsavel': row['RESPONSÁVEL'],
                'status': row['STATUS']
            })
            
        return jsonify(demandas)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/quitar/<int:demanda_id>', methods=['POST'])
def quitar_demanda(demanda_id):
    try:
        df = load_excel()
        if df is None:
            return jsonify({"error": "Arquivo não encontrado"}), 404
        
        # Atualizar status da demanda
        if demanda_id < len(df):
            df.at[demanda_id, 'STATUS'] = 'RESOLVIDO'
            save_excel(df)
            return jsonify({"message": "Demanda quitada com sucesso"})
        else:
            return jsonify({"error": "Demanda não encontrada"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        df = load_excel()
        if df is None:
            return jsonify({"error": "Arquivo não encontrado"}), 404
            
        # Parâmetros do filtro
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        grupo = request.args.get('grupo')
        responsavel = request.args.get('responsavel')
        
        # Aplicar filtros
        if start_date and end_date:
            df['DATA'] = pd.to_datetime(df['DATA'])
            df = df[(df['DATA'] >= start_date) & (df['DATA'] <= end_date)]
        
        if grupo and grupo != 'all':
            df = df[df['GRUPO'] == grupo]
            
        if responsavel and responsavel != 'all':
            df = df[df['RESPONSÁVEL'] == responsavel]
        
        # Processar dados
        df['DATA'] = pd.to_datetime(df['DATA'])
        evolucao_diaria = df.groupby('DATA').size().reset_index()
        evolucao_diaria.columns = ['data', 'quantidade']
        evolucao_diaria['data'] = evolucao_diaria['data'].dt.strftime('%Y-%m-%d')
        
        # Dados por grupo
        grupos = df['GRUPO'].unique()
        desempenho_grupo = []
        for grupo in grupos:
            df_grupo = df[df['GRUPO'] == grupo]
            resolvidos = len(df_grupo[df_grupo['STATUS'] == 'RESOLVIDO'])
            total = len(df_grupo)
            desempenho_grupo.append({
                'grupo': grupo,
                'resolvidos': resolvidos,
                'total': total,
                'taxa': round(resolvidos/total * 100, 2) if total > 0 else 0
            })
            
        # Dados por responsável
        responsaveis = df['RESPONSÁVEL'].unique()
        desempenho_responsavel = []
        for resp in responsaveis:
            df_resp = df[df['RESPONSÁVEL'] == resp]
            resolvidos = len(df_resp[df_resp['STATUS'] == 'RESOLVIDO'])
            total = len(df_resp)
            desempenho_responsavel.append({
                'responsavel': resp,
                'resolvidos': resolvidos, 
                'total': total,
                'taxa': round(resolvidos/total * 100, 2) if total > 0 else 0
            })
            
        return jsonify({
            'evolucao_diaria': evolucao_diaria.to_dict('records'),
            'desempenho_grupo': desempenho_grupo,
            'desempenho_responsavel': desempenho_responsavel,
            'total_demandas': len(df),
            'demandas_resolvidas': len(df[df['STATUS'] == 'RESOLVIDO']),
            'taxa_resolucao': round(len(df[df['STATUS'] == 'RESOLVIDO']) / len(df) * 100, 2) if len(df) > 0 else 0
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
