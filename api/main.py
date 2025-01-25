from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from datetime import datetime
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def carregar_dados():
    """Carrega e processa os dados do arquivo Excel"""
    try:
        excel_path = "F:/demandstest/docs/_DEMANDAS DE JANEIRO_2025.xlsx"
        
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {excel_path}")
        
        # Carregar dados mantendo os nomes originais das colunas
        df = pd.read_excel(excel_path)
        
        # Converter datas
        if 'RESOLUÇÃO' in df.columns:
            df['RESOLUÇÃO'] = pd.to_datetime(df['RESOLUÇÃO'], errors='coerce')
        
        return df
    except Exception as e:
        print(f"Erro ao carregar dados: {str(e)}")
        raise

def analisar_dados(df):
    """Realiza análise das demandas resolvidas por responsável"""
    try:
        # Lista de nomes alvo
        nomes_alvo = [
            "ADRIANO", "LUARA", "ANA GESSICA", "FELIPE", "JULIANE", "POLIANA",
            "THALISSON", "IGOR", "MATHEUS", "ALINE", "NUNO", "ELISANGELA", "YURI", "ANA LIDIA"
        ]
        
        # Filtrar apenas demandas resolvidas
        df_resolvido = df[df['SITUAÇÃO'].str.upper() == 'RESOLVIDO'].copy()
        
        # Inicializar resultados
        resultados = []
        
        # Processar cada responsável
        for nome in nomes_alvo:
            # Filtrar demandas do responsável
            df_resp = df_resolvido[df_resolvido['RESPONSÁVEL'].str.upper() == nome]
            
            if not df_resp.empty:
                total_demandas = len(df_resp)
                dias_unicos = df_resp['RESOLUÇÃO'].dt.date.nunique()
                total_ctt = df_resp['CTT'].sum()  # Soma dos números CTT
                
                # Calcular médias
                media_diaria = round(total_demandas / dias_unicos, 2) if dias_unicos > 0 else 0
                media_semanal = round(total_demandas / (dias_unicos / 7), 2) if dias_unicos > 0 else 0
                
                resultados.append({
                    'RESPONSAVEL': nome,
                    'TOTAL_DEMANDAS': total_demandas,
                    'TOTAL_CTT': total_ctt,
                    'MEDIA_DIARIA': media_diaria,
                    'MEDIA_SEMANAL': media_semanal,
                    'DIAS_TRABALHADOS': dias_unicos
                })
        
        # Ordenar resultados por total de CTT
        resultados = sorted(resultados, key=lambda x: x['TOTAL_CTT'], reverse=True)
        
        # Gerar texto formatado
        analise = ["=== ANÁLISE DE DEMANDAS RESOLVIDAS POR RESPONSÁVEL ===\n"]
        analise.append("RESPONSÁVEL | TOTAL DEMANDAS | TOTAL CTT | MÉDIA DIÁRIA | MÉDIA SEMANAL | DIAS TRABALHADOS")
        analise.append("-" * 90)
        
        for r in resultados:
            linha = f"{r['RESPONSAVEL']:<15} | {r['TOTAL_DEMANDAS']:>13} | {r['TOTAL_CTT']:>9} | {r['MEDIA_DIARIA']:>12.2f} | {r['MEDIA_SEMANAL']:>12.2f} | {r['DIAS_TRABALHADOS']:>15}"
            analise.append(linha)
        
        # Adicionar totais
        total_demandas = sum(r['TOTAL_DEMANDAS'] for r in resultados)
        total_ctt = sum(r['TOTAL_CTT'] for r in resultados)
        analise.append("-" * 90)
        analise.append(f"TOTAL          | {total_demandas:>13} | {total_ctt:>9} |")
        
        return "\n".join(analise)
    except Exception as e:
        return f"Erro ao analisar dados: {str(e)}\nColunas disponíveis: {', '.join(df.columns)}"

@app.get("/")
async def root():
    """Página inicial com análise de dados"""
    try:
        df = carregar_dados()
        analise_texto = analisar_dados(df)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Análise de Demandas</title>
                <style>
                    body {{
                        font-family: monospace;
                        padding: 20px;
                        line-height: 1.6;
                        background-color: #f5f5f5;
                    }}
                    pre {{
                        background-color: white;
                        padding: 20px;
                        border-radius: 5px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        overflow-x: auto;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }}
                </style>
            </head>
            <body>
                <h1>Análise de Demandas por Responsável</h1>
                <pre>{analise_texto}</pre>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        print(f"Erro na rota /: {str(e)}")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Erro</title>
            </head>
            <body>
                <h1>Erro ao carregar análise</h1>
                <p>Detalhes: {str(e)}</p>
            </body>
        </html>
        """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
