import pandas as pd
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import os

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dashboard_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Classe responsável pelo processamento e análise de dados do CSV."""
    
    EXPECTED_COLUMNS = {
        'resolucao': ['RESOLUCAO', 'DATA', 'DATA RESOLUCAO', 'DT_RESOLUCAO', 'RESOLU'],
        'responsavel': ['RESPONSAVEL', 'RESP', 'ATENDENTE', 'ATEND', 'RESPONS'],
        'situacao': ['SITUACAO', 'STATUS', 'SITU', 'UNNAMED: 9', '  ']
    }
    
    TEAM_MAPPING = {
        'JULIO': ['JULIO'],
        'LEANDRO': ['LEANDRO'],
        'ADRIANO': ['ADRIANO']
    }
    
    def __init__(self, data_dir: str = 'docs'):
        """Inicializa o processador de dados.
        
        Args:
            data_dir: Diretório contendo os arquivos CSV
        """
        self.data_dir = Path(data_dir).resolve()  # Converte para caminho absoluto
        self.column_mapping = {}
        self.debug_info = {}
        
        # Log de informações do diretório
        logger.info(f"Inicializado com diretório de dados: {self.data_dir}")
        logger.info(f"Diretório existe: {self.data_dir.exists()}")
        logger.info(f"Diretório é absoluto: {self.data_dir.is_absolute()}")
        
        # Verifica se o diretório existe
        if not self.data_dir.exists():
            logger.error(f"Diretório não encontrado: {self.data_dir}")
            raise FileNotFoundError(f"Diretório não encontrado: {self.data_dir}")
            
        # Lista arquivos CSV disponíveis
        csv_files = list(self.data_dir.glob('*.csv'))
        logger.info(f"Arquivos CSV encontrados: {[f.name for f in csv_files]}")
        
        if not csv_files:
            logger.warning(f"Nenhum arquivo CSV encontrado em: {self.data_dir}")
            
    def analyze_csv_structure(self, file_path: Path) -> Dict:
        """Analisa a estrutura do CSV e retorna informações detalhadas."""
        logger.info(f"Analisando estrutura do arquivo: {file_path}")
        logger.info(f"Arquivo existe: {file_path.exists()}")
        
        if not file_path.exists():
            error_msg = f"Arquivo não encontrado: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        try:
            # Tenta diferentes encodings
            last_error = None
            for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']:
                try:
                    logger.info(f"Tentando ler com encoding {encoding}")
                    df = pd.read_csv(file_path, encoding=encoding, nrows=5)
                    
                    info = {
                        'encoding': encoding,
                        'columns': df.columns.tolist(),
                        'dtypes': df.dtypes.apply(str).to_dict(),
                        'sample_data': df.head(1).to_dict('records'),
                        'null_counts': df.isnull().sum().to_dict(),
                        'file_size': os.path.getsize(file_path),
                        'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }
                    
                    logger.info(f"Sucesso com encoding {encoding}")
                    logger.info(f"Colunas encontradas: {info['columns']}")
                    
                    # Salva informações para debug
                    debug_file = file_path.with_suffix('.debug.json')
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        json.dump(info, f, indent=2, ensure_ascii=False)
                        
                    return info
                    
                except Exception as e:
                    last_error = e
                    logger.warning(f"Falha ao tentar encoding {encoding}: {str(e)}")
                    continue
                    
            if last_error:
                raise ValueError(f"Não foi possível determinar o encoding correto do arquivo. Último erro: {str(last_error)}")
            
        except Exception as e:
            logger.error(f"Erro ao analisar estrutura do CSV {file_path}: {str(e)}")
            raise
            
    def identify_columns(self, columns: List[str]) -> Dict[str, str]:
        """Identifica as colunas do CSV e mapeia para os nomes padronizados."""
        mapping = {}
        logger.info(f"Identificando colunas: {columns}")
        
        for col in columns:
            col_upper = str(col).upper().strip()
            logger.info(f"Analisando coluna: {col} (upper: {col_upper})")
            
            # Procura em cada categoria de coluna esperada
            for target, possible_names in self.EXPECTED_COLUMNS.items():
                if any(name in col_upper for name in possible_names):
                    mapping[col] = target
                    logger.info(f"Coluna {col} mapeada para {target}")
                    break
                    
        logger.info(f"Mapeamento final: {mapping}")
        return mapping
        
    def process_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """Processa o DataFrame aplicando limpezas e transformações necessárias."""
        try:
            logger.info("Iniciando processamento do DataFrame")
            logger.info(f"Colunas originais: {df.columns.tolist()}")
            
            # Copia o DataFrame para não modificar o original
            df = df.copy()
            
            # Converte colunas para string onde necessário
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].fillna('NÃO INFORMADO')
                    df[col] = df[col].astype(str)
                    logger.info(f"Coluna {col} convertida para string")
            
            # Aplica o mapeamento de colunas
            self.column_mapping = self.identify_columns(df.columns)
            df = df.rename(columns=self.column_mapping)
            logger.info(f"Colunas após mapeamento: {df.columns.tolist()}")
            
            # Processa data de resolução
            if 'resolucao' in df.columns:
                df['resolucao'] = pd.to_datetime(df['resolucao'], format='%d/%m/%Y', errors='coerce')
                logger.info("Data de resolução processada")
                
            # Processa responsável e equipe
            if 'responsavel' in df.columns:
                df['responsavel'] = df['responsavel'].fillna('NÃO INFORMADO')
                df['responsavel'] = df['responsavel'].astype(str).str.strip().str.upper()
                df['equipe'] = df['responsavel'].apply(self._map_to_team)
                logger.info("Responsável e equipe processados")
                
            # Processa situação
            if 'situacao' in df.columns:
                df['situacao'] = df['situacao'].fillna('NÃO INFORMADO')
                df['situacao'] = df['situacao'].astype(str).str.strip().str.upper()
                logger.info("Situação processada")
                
            # Remove linhas com datas nulas
            df = df.dropna(subset=['resolucao'])
            logger.info(f"Linhas após remoção de datas nulas: {len(df)}")
            
            # Coleta informações de debug
            debug_info = {
                'total_rows': len(df),
                'columns_present': df.columns.tolist(),
                'null_counts': df.isnull().sum().to_dict(),
                'unique_values': {
                    'responsavel': df['responsavel'].unique().tolist() if 'responsavel' in df.columns else [],
                    'situacao': df['situacao'].unique().tolist() if 'situacao' in df.columns else [],
                    'equipe': df['equipe'].unique().tolist() if 'equipe' in df.columns else []
                }
            }
            
            logger.info("Processamento do DataFrame concluído com sucesso")
            return df, debug_info
            
        except Exception as e:
            logger.error(f"Erro ao processar DataFrame: {str(e)}")
            raise
            
    def _map_to_team(self, responsavel: str) -> str:
        """Mapeia um responsável para sua equipe."""
        for team, members in self.TEAM_MAPPING.items():
            if responsavel in members:
                return team
        return 'OUTROS'
        
    def load_and_process_file(self, file_name: str) -> Optional[pd.DataFrame]:
        """Carrega e processa um arquivo CSV."""
        try:
            logger.info(f"Iniciando processamento do arquivo: {file_name}")
            
            # Verifica se o arquivo existe
            file_path = self.data_dir / file_name
            logger.info(f"Caminho completo: {file_path}")
            logger.info(f"Arquivo existe: {file_path.exists()}")
            
            if not file_path.exists():
                logger.error(f"Arquivo não encontrado: {file_path}")
                return None
            
            # Analisa estrutura do arquivo
            structure_info = self.analyze_csv_structure(file_path)
            logger.info(f"Estrutura do arquivo analisada: {structure_info['encoding']}")
            
            # Carrega o arquivo com o encoding correto
            df = pd.read_csv(file_path, encoding=structure_info['encoding'])
            logger.info(f"Arquivo carregado com sucesso. Shape: {df.shape}")
            
            # Processa os dados
            processed_df, debug_info = self.process_dataframe(df)
            
            # Salva informações de debug
            self.debug_info = {
                'file_name': file_name,
                'structure': structure_info,
                'processing': debug_info,
                'timestamp': datetime.now().isoformat()
            }
            
            debug_file = file_path.with_suffix('.processed.json')
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(self.debug_info, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Arquivo {file_name} processado com sucesso")
            return processed_df
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file_name}: {str(e)}")
            return None
            
    def get_debug_info(self) -> Dict:
        """Retorna as informações de debug coletadas durante o processamento."""
        return self.debug_info
