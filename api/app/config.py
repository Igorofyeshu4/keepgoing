from pydantic_settings import BaseSettings
from typing import Optional
import os
import yaml
from pathlib import Path

class Settings(BaseSettings):
    """Configurações da aplicação"""
    # Configurações da API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Demandas API"
    
    # Configurações do servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # Caminhos dos arquivos
    DATA_DIR: str = "docs"
    METRICS_FILE: str = "metricas_colaboradores.csv"
    DEMANDS_FILE: str = "_DEMANDAS DE JANEIRO_2025.xlsx"
    
    def __init__(self):
        super().__init__()
        self.load_yaml_config()
    
    def load_yaml_config(self):
        """Carrega configurações do arquivo YAML"""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Atualizar configurações
            if 'api' in config:
                self.HOST = config['api'].get('host', self.HOST)
                self.PORT = config['api'].get('port', self.PORT)
                self.RELOAD = config['api'].get('reload', self.RELOAD)
            
            if 'data' in config:
                self.DATA_DIR = config['data'].get('data_dir', self.DATA_DIR)
                self.METRICS_FILE = config['data'].get('metrics_file', self.METRICS_FILE)
                self.DEMANDS_FILE = config['data'].get('demands_file', self.DEMANDS_FILE)

    class Config:
        case_sensitive = True

settings = Settings()
