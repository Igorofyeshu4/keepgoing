import pytest
import pandas as pd
import sys
import os

# Adiciona o diretório de scripts ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from dashboard_comparativo import DemandDashboard

@pytest.fixture
def dashboard():
    return DemandDashboard()

def test_process_data(dashboard):
    # Cria um DataFrame de teste
    data = {
        'DATA': ['2025-01-01', '2025-01-01', '2025-01-02'],
        'STATUS': ['RESOLVIDO', 'PENDENTE', 'RESOLVIDO'],
        'RESPONSÁVEL': ['João', 'Maria', 'João']
    }
    df = pd.DataFrame(data)
    
    # Processa os dados
    result = dashboard.process_data(df)
    
    # Verifica se o resultado é um DataFrame
    assert isinstance(result, pd.DataFrame)
    
    # Verifica se as colunas necessárias estão presentes
    assert 'DATA' in result.columns
    assert 'STATUS' in result.columns
    assert 'RESPONSÁVEL' in result.columns

def test_calculate_metrics(dashboard):
    # Cria DataFrames de teste
    data_julio = {
        'DATA': ['2025-01-01', '2025-01-01'],
        'STATUS': ['RESOLVIDO', 'RESOLVIDO']
    }
    data_leandro = {
        'DATA': ['2025-01-01', '2025-01-01', '2025-01-01'],
        'STATUS': ['RESOLVIDO', 'RESOLVIDO', 'RESOLVIDO']
    }
    
    df_julio = pd.DataFrame(data_julio)
    df_leandro = pd.DataFrame(data_leandro)
    
    # Calcula métricas
    metrics = dashboard.calculate_metrics(df_julio, df_leandro)
    
    # Verifica os resultados
    assert metrics['total_julio'] == 2
    assert metrics['total_leandro'] == 3
    assert metrics['media_diaria_julio'] > 0
    assert metrics['media_diaria_leandro'] > 0

def test_create_daily_table(dashboard):
    # Cria um DataFrame de teste
    data = {
        'DATA': ['2025-01-01', '2025-01-01', '2025-01-02'],
        'STATUS': ['RESOLVIDO', 'RESOLVIDO', 'RESOLVIDO'],
        'RESPONSÁVEL': ['João', 'Maria', 'João']
    }
    df = pd.DataFrame(data)
    
    # Cria tabela diária
    result = dashboard.create_daily_table(df)
    
    # Verifica se o resultado é um DataFrame
    assert isinstance(result, pd.DataFrame)
    
    # Verifica se as colunas necessárias estão presentes
    assert 'Data' in result.columns
    assert 'Total Resolvido' in result.columns
