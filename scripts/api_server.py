from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
from datetime import datetime
import os

app = FastAPI()

# Configurar CORS para permitir requisições do Google Apps Script
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caminho do arquivo Excel
EXCEL_PATH = "F:/demandstest/docs/_DEMANDAS DE JANEIRO_2025.xlsx"

# Lista de valores válidos para o status
VALID_STATUS = ["PENDENTE", "PRIORIDADE", "RESOLVIDO", "ANÁLISE", "RECEPTIVO", "PRIORIDADE TOTAL"]

def validate_data(data):
    """Valida os dados recebidos"""
    errors = []
    for idx, row in enumerate(data):
        # Verifica o status
        status = row.get('STATUS')
        if status and status not in VALID_STATUS:
            errors.append(f"Linha {idx + 1}: Status inválido '{status}'. Valores permitidos: {', '.join(VALID_STATUS)}")
    return errors

@app.post("/update_demandas")
async def update_demandas(request: Request):
    try:
        # Recebe os dados JSON
        data = await request.json()
        
        # Registra a atualização
        print(f"\n=== Atualização via Google Sheets {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
        print(f"Dados recebidos: {len(data)} registros")
        
        # Valida os dados
        errors = validate_data(data)
        if errors:
            error_msg = "\n".join(errors)
            print(f"Erros de validação:\n{error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Converte para DataFrame
        df = pd.DataFrame(data)
        
        # Identifica a equipe baseado nos dados
        if 'EQUIPE' in df.columns:
            df_julio = df[df['EQUIPE'] == 'Julio']
            df_leandro = df[df['EQUIPE'] == 'Leandro']
            
            # Backup do arquivo existente
            if os.path.exists(EXCEL_PATH):
                backup_path = EXCEL_PATH.replace('.xlsx', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
                try:
                    os.rename(EXCEL_PATH, backup_path)
                    print(f"Backup criado: {backup_path}")
                except Exception as e:
                    print(f"Erro ao criar backup: {str(e)}")
            
            # Salva em Excel
            try:
                with pd.ExcelWriter(EXCEL_PATH) as writer:
                    df_julio.to_excel(writer, sheet_name='DEMANDAS JULIO', index=False)
                    df_leandro.to_excel(writer, sheet_name='DEMANDA LEANDROADRIANO', index=False)
                
                print(f"Equipe Julio: {len(df_julio)} demandas")
                print(f"Equipe Leandro: {len(df_leandro)} demandas")
                print("Status: Dados atualizados com sucesso!")
                
                return {
                    "status": "success",
                    "message": "Dados atualizados com sucesso",
                    "details": {
                        "julio_count": len(df_julio),
                        "leandro_count": len(df_leandro)
                    }
                }
            except Exception as e:
                print(f"Erro ao salvar Excel: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="Campo EQUIPE não encontrado nos dados")
            
    except Exception as e:
        print(f"Erro na atualização: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def start_api():
    import uvicorn
    print("\n=== Iniciando Servidor API ===")
    print("Endereço: http://localhost:8052")
    print("Valores válidos para STATUS:", ", ".join(VALID_STATUS))
    uvicorn.run(app, host="0.0.0.0", port=8052)

if __name__ == "__main__":
    start_api()
