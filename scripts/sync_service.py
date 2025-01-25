"""
Serviço de sincronização com redundância e fallback automático
"""

import time
import sqlite3
import pandas as pd
import json
import logging
from datetime import datetime
from backup_config import BACKUP_CONFIG, STATUS_CODES, STATUS_MESSAGES
from google_sheets_api import get_sheet_data

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SyncService:
    def __init__(self):
        self.status = STATUS_CODES['OK']
        self.last_sync = None
        self.cache = {}
        self.error_count = 0
        self.setup_database()
        
    def setup_database(self):
        """Inicializa o banco SQLite para backup"""
        conn = sqlite3.connect(BACKUP_CONFIG['SQLITE']['DB_FILE'])
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS demands
                    (id TEXT PRIMARY KEY, data TEXT, timestamp DATETIME)''')
        conn.commit()
        conn.close()
        
    def update_cache(self, data):
        """Atualiza o cache em memória"""
        self.cache = {
            'data': data,
            'timestamp': datetime.now().timestamp(),
            'status': self.status
        }
        
    def save_to_sqlite(self, data):
        """Salva os dados no SQLite"""
        conn = sqlite3.connect(BACKUP_CONFIG['SQLITE']['DB_FILE'])
        timestamp = datetime.now().isoformat()
        
        # Converter dados para JSON
        data_json = json.dumps(data)
        
        # Salvar no SQLite
        conn.execute('INSERT OR REPLACE INTO demands VALUES (?, ?, ?)',
                    ('latest', data_json, timestamp))
        conn.commit()
        conn.close()
        
    def export_to_excel(self, data):
        """Exporta os dados para Excel"""
        if BACKUP_CONFIG['EXCEL']['AUTO_EXPORT']:
            try:
                df = pd.DataFrame(data)
                filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                filepath = f"{BACKUP_CONFIG['EXCEL']['EXPORT_DIR']}/{filename}"
                df.to_excel(filepath, index=False)
                logging.info(f"Dados exportados para {filepath}")
            except Exception as e:
                logging.error(f"Erro ao exportar para Excel: {e}")
                
    def get_backup_data(self):
        """Recupera dados do backup SQLite"""
        conn = sqlite3.connect(BACKUP_CONFIG['SQLITE']['DB_FILE'])
        c = conn.cursor()
        c.execute('SELECT data FROM demands WHERE id = ? ORDER BY timestamp DESC LIMIT 1',
                 ('latest',))
        result = c.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
        
    def sync(self):
        """Sincroniza dados com fallback automático"""
        try:
            # Tentar Google Sheets
            data = get_sheet_data()
            if data is not None:
                self.status = STATUS_CODES['OK']
                self.error_count = 0
                self.update_cache(data)
                self.save_to_sqlite(data)
                self.export_to_excel(data)
                self.last_sync = datetime.now()
                logging.info("Sincronização com Google Sheets bem sucedida")
                return data
                
        except Exception as e:
            self.error_count += 1
            logging.error(f"Erro ao sincronizar com Google Sheets: {e}")
            
            # Tentar cache
            if self.cache and (datetime.now().timestamp() - self.cache['timestamp']) < BACKUP_CONFIG['CACHE']['MAX_AGE']:
                self.status = STATUS_CODES['USING_CACHE']
                logging.info("Usando dados do cache")
                return self.cache['data']
                
            # Tentar SQLite
            backup_data = self.get_backup_data()
            if backup_data:
                self.status = STATUS_CODES['USING_BACKUP']
                logging.info("Usando dados do backup SQLite")
                return backup_data
                
        self.status = STATUS_CODES['ERROR']
        logging.error("Todos os métodos de recuperação falharam")
        return None
        
    def get_status(self):
        """Retorna status atual do serviço"""
        return {
            'code': self.status,
            'message': STATUS_MESSAGES[self.status],
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'error_count': self.error_count
        }

def main():
    service = SyncService()
    interval = BACKUP_CONFIG['SYNC_INTERVAL'] * 60  # converter para segundos
    
    while True:
        try:
            data = service.sync()
            if data:
                status = service.get_status()
                logging.info(f"Status: {status['message']}")
            time.sleep(interval)
            
        except KeyboardInterrupt:
            logging.info("Serviço de sincronização finalizado")
            break
            
        except Exception as e:
            logging.error(f"Erro no serviço de sincronização: {e}")
            time.sleep(BACKUP_CONFIG['FALLBACK']['RETRY_DELAY'])

if __name__ == "__main__":
    main()
