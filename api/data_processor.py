import pandas as pd
from datetime import datetime
import os

def load_and_process_data(excel_file):
    # Read the Excel file
    df = pd.read_excel(excel_file, header=0)
    
    # Rename columns to meaningful names
    df.columns = ['ID', 'DATA', 'DEMANDA', 'RESPONSAVEL', 'STATUS', 'RESOLUCAO', 'OBSERVACAO', 'PRIORIDADE']
    
    # Convert date columns
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    df['RESOLUCAO'] = pd.to_datetime(df['RESOLUCAO'], errors='coerce')
    
    # Create group classification
    def classify_group(responsavel):
        if responsavel.lower() in ['julio', 'antunis']:
            return 'Grupo Julio'
        elif responsavel.lower() in ['leandro', 'adriano']:
            return 'Grupo Leandro/Adriano'
        return 'Outros'
    
    df['GRUPO'] = df['RESPONSAVEL'].apply(classify_group)
    
    # Filter only resolved demands
    df_resolved = df[df['STATUS'].str.lower() == 'resolvido'].copy()
    
    # Group data by date and group
    daily_by_group = df_resolved.groupby([df_resolved['RESOLUCAO'].dt.date, 'GRUPO']).size().reset_index()
    daily_by_group.columns = ['DATA', 'GRUPO', 'TOTAL']
    
    # Group data by date and responsible
    daily_by_responsible = df_resolved.groupby([df_resolved['RESOLUCAO'].dt.date, 'RESPONSAVEL']).size().reset_index()
    daily_by_responsible.columns = ['DATA', 'RESPONSAVEL', 'TOTAL']
    
    return {
        'by_group': daily_by_group.to_dict('records'),
        'by_responsible': daily_by_responsible.to_dict('records')
    }

def get_latest_data():
    # Get the most recent Excel file in the directory
    excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and 'DEMANDAS' in f]
    if not excel_files:
        return None
    
    latest_file = max(excel_files)
    return load_and_process_data(latest_file)

if __name__ == '__main__':
    data = get_latest_data()
    print(data)
