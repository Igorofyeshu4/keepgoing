import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
from ..models.metrics import DailyMetrics
from ..config import settings
import gc

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        """Inicializa o serviço de dados"""
        self.df = None
        self.dfs = {}
        self._load_data()
    
    def _load_data(self):
        """Carrega dados do CSV e Excel com otimização de memória"""
        try:
            # Carregar CSV com tipos otimizados
            csv_dtypes = {
                'Data': 'datetime64[ns]',
                'Equipe': 'category',
                'Colaborador': 'category',
                'Métrica': 'category',
                'Valor': 'float32'
            }
            
            self.df = pd.read_csv(
                f'{settings.DATA_DIR}/{settings.METRICS_FILE}',
                dtype=csv_dtypes,
                parse_dates=['Data']
            )
            
            # Carregar Excel com chunks
            excel_path = f'{settings.DATA_DIR}/{settings.DEMANDS_FILE}'
            self.dfs = {}
            
            with pd.ExcelFile(excel_path) as xls:
                for sheet_name in xls.sheet_names:
                    try:
                        # Definir tipos de dados otimizados
                        dtypes = {
                            'CTT': 'category',
                            'CONTRATO': 'category',
                            'SITUACAO': 'category',
                            'SITUAÇÃO': 'category',
                            'ATIVO/RECEPTIVO': 'category',
                            'EQUIPE': 'category',
                            'NOME': 'category',
                            'PRIORIDADE': 'category'
                        }
                        
                        # Carregar planilha em chunks
                        chunks = []
                        for chunk in pd.read_excel(xls, sheet_name=sheet_name, dtype=dtypes, chunksize=1000):
                            # Padronizar nomes das colunas
                            chunk.columns = chunk.columns.str.strip().str.upper()
                            
                            # Converter datas
                            date_columns = ['DATA', 'RESOLUCAO', 'Data']
                            for col in date_columns:
                                if col in chunk.columns:
                                    chunk[col] = pd.to_datetime(chunk[col], errors='coerce')
                            
                            chunks.append(chunk)
                        
                        # Concatenar chunks
                        if chunks:
                            self.dfs[sheet_name] = pd.concat(chunks, ignore_index=True)
                            # Limpar chunks para liberar memória
                            chunks.clear()
                            gc.collect()
                        
                        logger.info(f"Planilha {sheet_name} carregada com sucesso")
                        
                    except Exception as e:
                        logger.error(f"Erro ao carregar planilha {sheet_name}: {str(e)}")
                        continue
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {str(e)}")
            raise
    
    def get_situacao_column(self, df: pd.DataFrame) -> Optional[str]:
        """Identifica a coluna de situação no DataFrame"""
        possible_columns = ['SITUACAO', 'SITUAÇÃO', 'STATUS', 'ESTADO']
        for col in possible_columns:
            if col in df.columns:
                return col
        return None
    
    def get_daily_metrics(self, date: datetime, team: Optional[str] = None) -> DailyMetrics:
        """Calcula métricas diárias para uma data específica"""
        try:
            metrics = {
                'date': date,
                'team': team,
                'resolvidos': 0,
                'pendente_ativo': 0,
                'pendente_receptivo': 0,
                'prioridade': 0,
                'prioridade_total': 0,
                'soma_prioridades': 0,
                'analise': 0,
                'analise_dia': 0,
                'receptivo': 0,
                'quitado_cliente': 0,
                'quitado': 0,
                'aprovados': 0
            }
            
            for sheet_name, df in self.dfs.items():
                if df.empty:
                    continue
                
                # Criar cópia local para evitar SettingWithCopyWarning
                df_temp = df.copy()
                
                # Filtrar por equipe
                if team:
                    equipe_col = next((col for col in df_temp.columns if 'EQUIPE' in col.upper()), None)
                    if equipe_col:
                        df_temp = df_temp[df_temp[equipe_col].astype(str).str.upper() == team.upper()]
                
                # Identificar coluna de situação
                situacao_col = self.get_situacao_column(df_temp)
                if not situacao_col:
                    continue
                
                # Filtrar por data
                date_mask = pd.Series(False, index=df_temp.index)
                date_columns = ['DATA', 'RESOLUCAO', 'Data']
                
                for col in date_columns:
                    if col in df_temp.columns:
                        if pd.api.types.is_datetime64_any_dtype(df_temp[col]):
                            date_mask |= (df_temp[col].dt.date == date.date())
                
                df_date = df_temp[date_mask]
                if df_date.empty:
                    continue
                
                # Calcular métricas
                situacao = df_date[situacao_col].astype(str).str.upper()
                
                # Resolvidos
                metrics['resolvidos'] += situacao.str.contains('RESOLVID|FINALIZADO|CONCLUÍDO', na=False).sum()
                
                # Análise
                analise_mask = situacao.str.contains('ANALIS|ANÁLISE', na=False)
                metrics['analise'] += analise_mask.sum()
                
                # Quitados
                metrics['quitado'] += situacao.str.contains('QUITAD', na=False).sum()
                
                # Aprovados
                metrics['aprovados'] += situacao.str.contains('APROVAD', na=False).sum()
                
                # Pendentes e Receptivo
                if 'ATIVO/RECEPTIVO' in df_date.columns:
                    ativo_receptivo = df_date['ATIVO/RECEPTIVO'].astype(str).str.upper()
                    pendente_mask = situacao.str.contains('PENDENT', na=False)
                    
                    ativo_mask = ativo_receptivo.str.contains('ATIVO', na=False)
                    receptivo_mask = ativo_receptivo.str.contains('RECEPTIVO', na=False)
                    
                    metrics['pendente_ativo'] += (pendente_mask & ativo_mask).sum()
                    metrics['pendente_receptivo'] += (pendente_mask & receptivo_mask).sum()
                    metrics['receptivo'] += receptivo_mask.sum()
                
                # Limpar variáveis temporárias
                del df_temp, df_date
                gc.collect()
            
            return DailyMetrics(**metrics)
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas: {str(e)}")
            raise
    
    def get_teams(self) -> List[str]:
        """Retorna lista de equipes disponíveis"""
        teams = set()
        
        try:
            # Buscar em todas as planilhas
            for df in self.dfs.values():
                equipe_col = next((col for col in df.columns if 'EQUIPE' in col.upper()), None)
                if equipe_col:
                    teams.update(df[equipe_col].dropna().unique())
            
            return sorted(list(teams))
            
        except Exception as e:
            logger.error(f"Erro ao buscar equipes: {str(e)}")
            raise
    
    def get_date_range(self) -> Tuple[datetime, datetime]:
        """Retorna o intervalo de datas disponível nos dados"""
        try:
            min_date = datetime.max
            max_date = datetime.min
            
            # Verificar todas as planilhas
            for df in self.dfs.values():
                date_columns = ['DATA', 'RESOLUCAO', 'Data']
                
                for col in date_columns:
                    if col in df.columns and pd.api.types.is_datetime64_any_dtype(df[col]):
                        col_min = df[col].min()
                        col_max = df[col].max()
                        
                        if pd.notna(col_min) and col_min < min_date:
                            min_date = col_min
                        if pd.notna(col_max) and col_max > max_date:
                            max_date = col_max
            
            return min_date, max_date
            
        except Exception as e:
            logger.error(f"Erro ao buscar intervalo de datas: {str(e)}")
            raise
