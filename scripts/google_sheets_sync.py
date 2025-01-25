import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
from datetime import datetime
import os
import socket

class GoogleSheetsSync:
    def __init__(self):
        self.API_KEY = 'AIzaSyB572fFyJG66uOPkk33OYzxheJdyxy97fc'
        self.setup_credentials()
        
    def find_free_port(self):
        """Encontra uma porta livre para usar"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
        
    def setup_credentials(self):
        """Configura as credenciais do Google Sheets usando OAuth2"""
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = None
        token_path = 'f:/demandstest/token.json'
        creds_path = 'f:/demandstest/credentials.json'
        
        # Carrega credenciais existentes se disponíveis
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
        # Se não há credenciais válidas, solicita autorização
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=self.find_free_port())
                
            # Salva as credenciais para a próxima execução
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        try:
            # Configura o cliente gspread com as credenciais OAuth2 e API Key
            self.client = gspread.authorize(creds)
            print("Conectado com sucesso ao Google Sheets")
            
        except Exception as e:
            print(f"Erro na configuração das credenciais: {str(e)}")
            raise e
        
    def process_dataframe(self, df):
        """Processa o DataFrame para incluir apenas as colunas necessárias"""
        df = df.copy()
        df['DATA_RESOLUCAO'] = pd.to_datetime(df.iloc[:, 1]).dt.strftime('%Y-%m-%d')
        df['RESPONSAVEL'] = df.iloc[:, 10]
        df['STATUS'] = df.iloc[:, 11]
        df['TIPO'] = df.iloc[:, 3]
        
        # Filtra apenas resolvidos
        df = df[df['STATUS'].str.upper() == 'RESOLVIDO']
        
        # Agrupa por data e responsável
        grouped = df.groupby(['DATA_RESOLUCAO', 'RESPONSAVEL']).size().reset_index()
        grouped.columns = ['DATA_RESOLUCAO', 'RESPONSAVEL', 'TOTAL_RESOLVIDOS']
        
        return grouped.sort_values(['DATA_RESOLUCAO', 'RESPONSAVEL'])
        
    def sync_to_sheets(self, df_julio, df_leandro):
        """Sincroniza os dataframes com o Google Sheets"""
        try:
            # ID da planilha compartilhada
            spreadsheet_id = '1E5-M0jmv9ielF1ySuPn19g5NtUJvbrcIFtcze-VgY3I'
            
            try:
                spreadsheet = self.client.open_by_key(spreadsheet_id)
            except Exception as e:
                print(f"Erro ao abrir planilha. Tentando criar nova: {str(e)}")
                spreadsheet = self.client.create('Demandas Dashboard')
                spreadsheet.share('maiaowm2@gmail.com', perm_type='user', role='writer')
            
            # Processa os dados
            df_julio_proc = self.process_dataframe(df_julio)
            df_leandro_proc = self.process_dataframe(df_leandro)
            
            # Sincroniza dados processados
            self._update_worksheet(spreadsheet, 'RESUMO_JULIO', df_julio_proc)
            self._update_worksheet(spreadsheet, 'RESUMO_LEANDRO', df_leandro_proc)
            
            # Sincroniza dados originais
            self._update_worksheet(spreadsheet, 'DEMANDAS JULIO', df_julio)
            self._update_worksheet(spreadsheet, 'DEMANDA LEANDROADRIANO', df_leandro)
            
            print(f"Dados sincronizados com sucesso em {datetime.now()}")
            return True
            
        except Exception as e:
            print(f"Erro ao sincronizar com Google Sheets: {str(e)}")
            return False
    
    def _update_worksheet(self, spreadsheet, sheet_name, df):
        """Atualiza uma worksheet específica com os dados do DataFrame"""
        try:
            # Tenta obter a worksheet existente ou cria uma nova
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except:
                worksheet = spreadsheet.add_worksheet(sheet_name, 1000, 100)
            
            # Converte o DataFrame para lista de listas
            data = [df.columns.values.tolist()] + df.values.tolist()
            
            # Limpa a worksheet atual
            worksheet.clear()
            
            # Atualiza com os novos dados
            worksheet.update('A1', data)
            
            # Formata o cabeçalho
            worksheet.format('A1:Z1', {
                "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.8},
                "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True}
            })
            
            # Ajusta automaticamente a largura das colunas
            worksheet.columns_auto_resize(0, len(df.columns))
            
        except Exception as e:
            print(f"Erro ao atualizar worksheet {sheet_name}: {str(e)}")
            raise e

def main():
    # Exemplo de uso
    sync = GoogleSheetsSync()
    
    # Carrega dados do Excel local
    excel_path = "F:/demandstest/docs/_DEMANDAS DE JANEIRO_2025.xlsx"
    df_julio = pd.read_excel(excel_path, sheet_name="DEMANDAS JULIO")
    df_leandro = pd.read_excel(excel_path, sheet_name="DEMANDA LEANDROADRIANO")
    
    # Sincroniza com Google Sheets
    sync.sync_to_sheets(df_julio, df_leandro)

if __name__ == "__main__":
    main()
