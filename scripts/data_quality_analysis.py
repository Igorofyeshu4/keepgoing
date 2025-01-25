import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import os

def load_data(file_path, sheet_name="DEMANDAS JULIO"):
    """Carrega os dados do arquivo Excel."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    # Carregar a aba específica
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    print(f"\nColunas encontradas na aba {sheet_name}:")
    for i, col in enumerate(df.columns):
        print(f"Coluna {i}: {col}")
    
    print("\nPrimeiras 5 linhas do DataFrame:")
    print(df.head())
    
    # Tentar converter colunas de data
    for col in df.columns:
        if "DATA" in str(col).upper():
            try:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
                print(f"\nColuna {col} convertida para datetime")
            except:
                print(f"Não foi possível converter a coluna {col} para datetime")
    
    return df

def analyze_data_types(df):
    """Analisa os tipos de dados de cada coluna."""
    return df.dtypes

def get_unique_values(df, column_name):
    """Retorna valores únicos de uma coluna específica."""
    if column_name in df.columns:
        values = sorted(df[column_name].dropna().unique())
        return [str(v) for v in values]  # Converter para string para melhor exibição
    return []

def count_resolutions_by_person(df, date):
    """Conta resoluções por pessoa em uma data específica."""
    try:
        # Usar a coluna de resolução
        date_col = "RESOLUÇÃO"
        if date_col not in df.columns:
            print("Coluna de resolução não encontrada")
            return {}
        
        print(f"\nUsando coluna de data: {date_col}")
        
        # Filtrar por data
        daily_data = df[df[date_col].dt.date == date]
        print(f"\nRegistros encontrados para a data {date}: {len(daily_data)}")
        
        if len(daily_data) == 0:
            return {}
        
        # Usar a coluna de responsável
        resp_col = "RESPONSÁVEL"
        if resp_col not in df.columns:
            print("Coluna de responsável não encontrada")
            return {}
        
        print(f"Usando coluna de responsável: {resp_col}")
        
        # Contar resoluções
        resolutions = daily_data[resp_col].value_counts()
        
        # Converter para dicionário
        results = {}
        for name, count in resolutions.items():
            clean_name = str(name).strip()
            if clean_name and clean_name.lower() != "nan":
                results[clean_name] = count
        
        return results
    except Exception as e:
        print(f"Erro ao contar resoluções: {str(e)}")
        return {}

def format_results(results):
    """Formata os resultados para exibição."""
    if not results:
        return "Nenhum resultado encontrado para esta data"
    
    output = []
    total = 0
    for name, count in sorted(results.items()):
        output.append(f"{name}: {count}")
        total += count
    output.append(f"TOTAL: {total}")
    return "\n".join(output)

def show_available_dates(df, date_col):
    """Mostra as datas disponíveis em uma coluna de data."""
    if date_col not in df.columns:
        print(f"Coluna {date_col} não encontrada")
        return
    
    dates = sorted(df[date_col].dt.date.unique())
    print(f"\nDatas disponíveis em {date_col}:")
    for date in dates:
        count = len(df[df[date_col].dt.date == date])
        print(f"{date.strftime('%d/%m/%Y')}: {count} registros")

def main():
    parser = argparse.ArgumentParser(description='Análise de qualidade dos dados de demandas.')
    parser.add_argument('file_path', help='Caminho para o arquivo Excel de dados')
    parser.add_argument('--date', help='Data para análise (formato: DD/MM/YYYY). Se não especificada, usa o dia anterior.')
    parser.add_argument('--sheet', help='Nome da aba do Excel para análise. Padrão: DEMANDAS JULIO', default="DEMANDAS JULIO")
    
    args = parser.parse_args()
    
    try:
        # Carregar dados
        df = load_data(args.file_path, args.sheet)
        
        # Mostrar datas disponíveis
        show_available_dates(df, "RESOLUÇÃO")
        
        # Analisar tipos de dados
        print("\nTipos de dados das colunas:")
        print(analyze_data_types(df))
        
        # Procurar coluna de status
        status_col = None
        for col in df.columns:
            if "STATUS" in str(col).upper():
                status_col = col
                break
        
        if status_col:
            print(f"\nValores únicos na coluna de status ({status_col}):")
            status_values = get_unique_values(df, status_col)
            print("\n".join(status_values))
        else:
            print("\nColuna de status não encontrada")
        
        # Procurar coluna de responsável
        resp_col = None
        for col in df.columns:
            if any(term in str(col).upper() for term in ["RESPONSÁVEL", "RESPONSAVEL", "ATENDENTE"]):
                resp_col = col
                break
        
        if resp_col:
            print(f"\nValores únicos na coluna de responsável ({resp_col}):")
            resp_values = get_unique_values(df, resp_col)
            print("\n".join(resp_values))
        else:
            print("\nColuna de responsável não encontrada")
        
        # Análise para uma data específica
        if args.date:
            analysis_date = datetime.strptime(args.date, "%d/%m/%Y").date()
        else:
            analysis_date = datetime.now().date() - timedelta(days=1)
        
        results = count_resolutions_by_person(df, analysis_date)
        
        print(f"\nResultados para {analysis_date.strftime('%d/%m/%Y')}:")
        print(format_results(results))
        
    except Exception as e:
        print(f"Erro ao processar os dados: {str(e)}")

if __name__ == "__main__":
    main()
