import json
from analise_dados import analisar_dados_por_pessoa
import os

def gerar_json_pessoas():
    try:
        # Obter dados das pessoas
        dados = analisar_dados_por_pessoa()
        
        # Criar diretório data se não existir
        os.makedirs('docs/data', exist_ok=True)
        
        # Salvar dados em JSON
        with open('docs/data/metricas_pessoas.json', 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
            
        print("Arquivo JSON gerado com sucesso!")
        
    except Exception as e:
        print(f"Erro ao gerar JSON: {str(e)}")

if __name__ == "__main__":
    gerar_json_pessoas()
