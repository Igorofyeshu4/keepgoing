import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
import joblib
import logging
import json
from datetime import datetime
from pathlib import Path
import unicodedata
from typing import Dict, List, Tuple
import difflib

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_corrections/logs/error_correction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ErrorAnalyzer:
    def __init__(self):
        self.base_path = Path('ml_corrections')
        self.error_patterns = {}
        self.correction_model = None
        self.vectorizer = None
        self.label_encoder = None
        
    def analyze_errors(self, df: pd.DataFrame, column: str) -> Dict:
        """Analisa erros em uma coluna específica do DataFrame."""
        errors = {
            'missing_values': df[column].isna().sum(),
            'invalid_format': 0,
            'inconsistent_values': set()
        }
        
        # Análise de valores não nulos
        valid_values = df[column].dropna()
        
        # Verifica formatos inválidos
        if column in ['DATA', 'RESOLUÇÃO']:
            errors['invalid_format'] = sum(pd.to_datetime(valid_values, errors='coerce').isna())
        
        # Verifica inconsistências nos valores
        if column == 'RESPONSÁVEL':
            values = valid_values.str.upper().str.strip()
            for val in values:
                normalized = self.normalize_text(val)
                if normalized != val:
                    errors['inconsistent_values'].add(val)
        
        return errors
    
    def normalize_text(self, text: str) -> str:
        """Normaliza um texto removendo acentos e padronizando formato."""
        if pd.isna(text):
            return text
        text = unicodedata.normalize('NFKD', str(text).strip().upper())
        return text.encode('ASCII', 'ignore').decode('ASCII')
    
    def generate_error_report(self, dfs: Dict[str, pd.DataFrame]) -> Dict:
        """Gera relatório de erros para todos os DataFrames."""
        report = {}
        
        for df_name, df in dfs.items():
            df_report = {}
            for column in df.columns:
                errors = self.analyze_errors(df, column)
                df_report[column] = {
                    'missing_values': int(errors['missing_values']),
                    'invalid_format': int(errors['invalid_format']),
                    'inconsistent_values': list(errors['inconsistent_values'])
                }
            report[df_name] = df_report
        
        # Salva o relatório
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.base_path / 'reports' / f'error_report_{timestamp}.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        
        return report

class AutoCorrection:
    def __init__(self):
        self.base_path = Path('ml_corrections')
        self.model_path = self.base_path / 'models'
        self.data_path = self.base_path / 'data'
        self.vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2,4))
        self.classifier = RandomForestClassifier(n_estimators=100)
        self.label_encoder = LabelEncoder()
        
    def prepare_training_data(self, error_examples: List[Tuple[str, str]]) -> Tuple:
        """Prepara dados de treinamento a partir de exemplos de erros e correções."""
        X = [error for error, _ in error_examples]
        y = [correction for _, correction in error_examples]
        
        # Codifica as classes
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Vetoriza os textos
        X_vectorized = self.vectorizer.fit_transform(X)
        
        return train_test_split(X_vectorized, y_encoded, test_size=0.2, random_state=42)
    
    def train_model(self, error_examples: List[Tuple[str, str]]):
        """Treina o modelo de correção automática."""
        logger.info("Iniciando treinamento do modelo...")
        
        X_train, X_test, y_train, y_test = self.prepare_training_data(error_examples)
        
        # Treina o classificador
        self.classifier.fit(X_train, y_train)
        
        # Avalia o modelo
        y_pred = self.classifier.predict(X_test)
        report = classification_report(y_test, y_pred)
        logger.info(f"Relatório de classificação:\n{report}")
        
        # Salva o modelo e componentes
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        joblib.dump(self.classifier, self.model_path / f'correction_model_{timestamp}.joblib')
        joblib.dump(self.vectorizer, self.model_path / f'vectorizer_{timestamp}.joblib')
        joblib.dump(self.label_encoder, self.model_path / f'label_encoder_{timestamp}.joblib')
    
    def suggest_correction(self, text: str) -> str:
        """Sugere correção para um texto com erro."""
        # Vetoriza o texto
        X = self.vectorizer.transform([text])
        
        # Prediz a classe
        y_pred = self.classifier.predict(X)
        
        # Decodifica a predição
        correction = self.label_encoder.inverse_transform(y_pred)[0]
        
        return correction
    
    def load_model(self, model_timestamp: str):
        """Carrega um modelo treinado específico."""
        self.classifier = joblib.load(self.model_path / f'correction_model_{model_timestamp}.joblib')
        self.vectorizer = joblib.load(self.model_path / f'vectorizer_{model_timestamp}.joblib')
        self.label_encoder = joblib.load(self.model_path / f'label_encoder_{model_timestamp}.joblib')

def create_error_examples(df: pd.DataFrame, column: str) -> List[Tuple[str, str]]:
    """Cria exemplos de erros e correções para treinamento."""
    examples = []
    values = df[column].dropna()
    
    for val in values:
        # Simula erros comuns para treinamento
        errors = [
            val.lower(),  # minúsculas
            val.upper(),  # maiúsculas
            ' ' + val + ' ',  # espaços extras
            val.replace('Ç', 'C').replace('Ã', 'A'),  # sem acentos
        ]
        
        for error in errors:
            if error != val:
                examples.append((error, val))
    
    return examples

def main():
    """Função principal para execução da análise de erros e treinamento do modelo."""
    try:
        # Carrega os DataFrames com encoding correto
        df_julio = pd.read_csv('docs/_DEMANDAS DE JANEIRO_2025 - DEMANDAS JULIO.csv', encoding='latin1')
        df_leandro = pd.read_csv('docs/_DEMANDAS DE JANEIRO_2025 - DEMANDA LEANDROADRIANO.csv', encoding='latin1')
        df_quitados = pd.read_csv('docs/_DEMANDAS DE JANEIRO_2025 - QUITADOS.csv', encoding='latin1')
        
        # Padroniza os nomes das colunas
        column_mapping = {
            'RESPONSAVEL': 'RESPONSÁVEL',
            'RESPONSÁVEL': 'RESPONSÁVEL',
            'RESOLUCAO': 'RESOLUÇÃO',
            'RESOLUÇÃO': 'RESOLUÇÃO',
            'SITUACAO': 'SITUAÇÃO',
            'SITUAÇÃO': 'SITUAÇÃO'
        }
        
        df_julio = df_julio.rename(columns=column_mapping)
        df_leandro = df_leandro.rename(columns=column_mapping)
        df_quitados = df_quitados.rename(columns=column_mapping)
        
        # Analisa erros
        analyzer = ErrorAnalyzer()
        report = analyzer.generate_error_report({
            'JULIO': df_julio,
            'LEANDRO': df_leandro,
            'QUITADOS': df_quitados
        })
        
        logger.info("Relatório de erros gerado com sucesso")
        
        # Cria exemplos para treinamento
        examples = []
        for df in [df_julio, df_leandro, df_quitados]:
            if 'RESPONSÁVEL' in df.columns:
                examples.extend(create_error_examples(df, 'RESPONSÁVEL'))
        
        if examples:
            # Treina modelo de correção
            correction_model = AutoCorrection()
            correction_model.train_model(examples)
            logger.info("Modelo de correção treinado com sucesso")
        else:
            logger.warning("Nenhum exemplo de treinamento encontrado")
        
        logger.info("Análise de erros e treinamento do modelo concluídos com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante o processamento: {str(e)}")
        raise

if __name__ == "__main__":
    main()
