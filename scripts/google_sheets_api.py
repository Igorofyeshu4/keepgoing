from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
import pandas as pd
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from insights_api import insights_bp

app = Flask(__name__)
CORS(app)

# Registrar blueprint dos insights
app.register_blueprint(insights_bp)

# Se modificar estes escopos, delete o arquivo token.pickle
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# ID da planilha e range
SPREADSHEET_ID = 'seu_spreadsheet_id_aqui'
RANGE_NAME = 'Sheet1!A1:H1000'  # Ajuste conforme sua planilha

def get_google_sheets_service():
    creds = None
    # O arquivo token.pickle armazena os tokens de acesso e atualização do usuário
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # Se não há credenciais válidas disponíveis, permite que o usuário faça login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Salva as credenciais para a próxima execução
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    return service

def get_sheet_data():
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])

        if not values:
            return None

        # Converter para DataFrame
        df = pd.DataFrame(values[1:], columns=values[0])
        return df

    except Exception as e:
        print(f"Erro ao acessar Google Sheets: {str(e)}")
        return None

def process_data(df):
    if df is None:
        return None
        
    # Processar dados conforme necessário
    dados_processados = {
        'total_demandas': len(df),
        'demandas_resolvidas': len(df[df['STATUS'] == 'RESOLVIDO']),
        'por_responsavel': df.groupby('RESPONSAVEL').agg({
            'STATUS': ['count', lambda x: (x == 'RESOLVIDO').sum()]
        }).to_dict(),
        'por_grupo': df.groupby('GRUPO').agg({
            'STATUS': ['count', lambda x: (x == 'RESOLVIDO').sum()]
        }).to_dict(),
        'evolucao_diaria': df.groupby('DATA').size().to_dict()
    }
    
    return dados_processados

@app.route('/api/data')
def get_data():
    try:
        df = get_sheet_data()
        if df is None:
            return jsonify({'error': 'Erro ao carregar dados do Google Sheets'}), 500
            
        dados = process_data(df)
        return jsonify(dados)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update', methods=['POST'])
def update_data():
    try:
        df = get_sheet_data()
        if df is None:
            return jsonify({'error': 'Erro ao carregar dados do Google Sheets'}), 500
            
        # Processar e salvar análises
        dados = process_data(df)
        
        return jsonify({'message': 'Dados atualizados com sucesso'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
