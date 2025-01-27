import pandas as pd
import joblib
from pathlib import Path
import logging
from datetime import datetime
from rich.console import Console
from rich.table import Table
import glob
import os

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_corrections/logs/corrections_applied.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
console = Console()

class DataCorrector:
    def __init__(self):
        self.base_path = Path('ml_corrections')
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.load_latest_model()
    
    def load_latest_model(self):
        """Carrega o modelo mais recente da pasta models."""
        try:
            # Encontra os arquivos mais recentes
            model_files = glob.glob(str(self.base_path / 'models' / 'correction_model_*.joblib'))
            if not model_files:
                raise FileNotFoundError("Nenhum modelo encontrado!")
            
            # Pega o arquivo mais recente
            latest_model = max(model_files, key=os.path.getctime)
            timestamp = latest_model.split('correction_model_')[-1].replace('.joblib', '')
            
            # Carrega os componentes do modelo
            self.model = joblib.load(self.base_path / 'models' / f'correction_model_{timestamp}.joblib')
            self.vectorizer = joblib.load(self.base_path / 'models' / f'vectorizer_{timestamp}.joblib')
            self.label_encoder = joblib.load(self.base_path / 'models' / f'label_encoder_{timestamp}.joblib')
            
            logger.info(f"Modelo carregado com sucesso: {timestamp}")
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {str(e)}")
            raise
    
    def correct_value(self, value):
        """Corrige um valor usando o modelo treinado."""
        if pd.isna(value):
            return value
        
        try:
            # Vetoriza o texto
            X = self.vectorizer.transform([str(value)])
            
            # Prediz a classe
            y_pred = self.model.predict(X)
            
            # Decodifica a predição
            correction = self.label_encoder.inverse_transform(y_pred)[0]
            
            return correction
            
        except Exception as e:
            logger.warning(f"Não foi possível corrigir o valor '{value}': {str(e)}")
            return value
    
    def correct_dataframe(self, df, columns_to_correct):
        """Aplica correções a colunas específicas do DataFrame."""
        df_corrected = df.copy()
        corrections_made = []
        
        for column in columns_to_correct:
            if column not in df.columns:
                logger.warning(f"Coluna {column} não encontrada no DataFrame")
                continue
            
            logger.info(f"Corrigindo coluna: {column}")
            
            # Aplica correções
            for idx, value in df[column].items():
                original = str(value)
                corrected = self.correct_value(value)
                
                if original != corrected:
                    corrections_made.append({
                        'Linha': idx,
                        'Coluna': column,
                        'Valor Original': original,
                        'Valor Corrigido': corrected
                    })
                    df_corrected.at[idx, column] = corrected
        
        return df_corrected, corrections_made
    
    def save_corrections_report(self, corrections, output_file):
        """Salva um relatório das correções realizadas."""
        if not corrections:
            logger.info("Nenhuma correção necessária")
            return
        
        # Cria tabela rica para exibição
        table = Table(title="Correções Realizadas")
        table.add_column("Linha", style="cyan")
        table.add_column("Coluna", style="magenta")
        table.add_column("Valor Original", style="red")
        table.add_column("Valor Corrigido", style="green")
        
        for correction in corrections:
            table.add_row(
                str(correction['Linha']),
                correction['Coluna'],
                correction['Valor Original'],
                correction['Valor Corrigido']
            )
        
        # Exibe na tela
        console.print(table)
        
        # Salva em CSV
        pd.DataFrame(corrections).to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"Relatório de correções salvo em: {output_file}")

class AutoCorrection:
    def __init__(self):
        self.corrector = DataCorrector()
    
    def correct_data(self, df):
        """
        Aplica correções automáticas ao DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame a ser corrigido
            
        Returns:
            pd.DataFrame: DataFrame com as correções aplicadas
        """
        try:
            # Lista de colunas para corrigir
            columns_to_correct = ['RESPONSÁVEL', 'SITUAÇÃO']
            
            # Aplica correções usando o DataCorrector
            df_corrected, _ = self.corrector.correct_dataframe(df, columns_to_correct)
            
            # Padroniza os nomes das colunas
            column_mapping = {
                'RESPONSAVEL': 'RESPONSÁVEL',
                'RESOLUCAO': 'RESOLUÇÃO',
                'SITUACAO': 'SITUAÇÃO'
            }
            df_corrected.rename(columns=column_mapping, inplace=True)
            
            return df_corrected
            
        except Exception as e:
            logger.error(f"Erro ao aplicar correções: {str(e)}")
            return df  # Retorna o DataFrame original em caso de erro

def main():
    """Função principal para aplicar correções em novos dados."""
    try:
        # Inicializa o corretor
        corrector = DataCorrector()
        
        # Carrega novos dados (exemplo com os mesmos arquivos)
        df = pd.read_csv('docs/_DEMANDAS DE JANEIRO_2025 - DEMANDAS JULIO.csv', encoding='latin1')
        
        # Define colunas para corrigir
        columns_to_correct = ['RESPONSÁVEL', 'RESPONSAVEL']  # Inclui variações do nome
        
        # Aplica correções
        df_corrected, corrections = corrector.correct_dataframe(df, columns_to_correct)
        
        # Gera timestamp para os arquivos
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Salva o DataFrame corrigido
        output_path = Path('ml_corrections/data')
        df_corrected.to_csv(output_path / f'dados_corrigidos_{timestamp}.csv', 
                           index=False, encoding='utf-8-sig')
        
        # Salva e exibe relatório de correções
        corrector.save_corrections_report(
            corrections,
            output_path / f'relatorio_correcoes_{timestamp}.csv'
        )
        
        logger.info("Processo de correção concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante a correção: {str(e)}")
        raise

if __name__ == "__main__":
    main()
