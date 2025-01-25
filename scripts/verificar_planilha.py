import pandas as pd
import os

def verificar_planilha():
    # Caminho da planilha
    excel_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', '_DEMANDAS DE JANEIRO_2025.xlsx')
    
    # Carregar planilha
    print(f"\nVerificando planilha: {excel_path}")
    df = pd.read_excel(excel_path)
    
    # Mostrar informações
    print("\nInformações da planilha:")
    print("-" * 50)
    print(f"Número de linhas: {len(df)}")
    print(f"Número de colunas: {len(df.columns)}")
    print("\nColunas encontradas:")
    for col in df.columns:
        print(f"- {col}")
    
    # Mostrar primeiras linhas
    print("\nPrimeiras linhas da planilha:")
    print("-" * 50)
    print(df.head())

if __name__ == "__main__":
    try:
        verificar_planilha()
    except Exception as e:
        print(f"\nErro ao verificar planilha: {str(e)}")
