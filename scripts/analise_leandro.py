import pandas as pd
import os
from datetime import datetime

def analisar_demandas_leandro():
    try:
        # Carregar a planilha específica
        excel_path = "F:/demandstest/docs/_DEMANDAS DE JANEIRO_2025.xlsx"
        df = pd.read_excel(excel_path, sheet_name="DEMANDA LEANDROADRIANO")
        
        print("\n=== ANÁLISE INICIAL DOS DADOS ===")
        print("-" * 50)
        print(f"Total de linhas na planilha: {len(df)}")
        print(f"Colunas disponíveis: {len(df.columns)}")
        
        # Filtrar apenas resolvidos
        df_resolvido = df[df.iloc[:, 11].str.upper() == 'RESOLVIDO'].copy()
        
        # Converter data para datetime
        df_resolvido.iloc[:, 1] = pd.to_datetime(df_resolvido.iloc[:, 1], format='%Y-%m-%d', errors='coerce')
        
        # Remover linhas com datas nulas
        df_resolvido = df_resolvido.dropna(subset=[df_resolvido.columns[1]])
        
        # Agrupar por responsável e data
        por_dia = df_resolvido.groupby([df_resolvido.iloc[:, 10], df_resolvido.iloc[:, 1].dt.date]).size().reset_index()
        por_dia.columns = ['RESPONSÁVEL', 'RESOLUÇÃO', 'TOTAL_RESOLVIDOS']
        
        # Ordenar por data e responsável
        por_dia = por_dia.sort_values(['RESOLUÇÃO', 'RESPONSÁVEL'])
        por_dia = por_dia.reset_index(drop=True)
        
        # Filtrar apenas janeiro de 2025
        por_dia = por_dia[pd.to_datetime(por_dia['RESOLUÇÃO']).dt.year == 2025]
        por_dia = por_dia[pd.to_datetime(por_dia['RESOLUÇÃO']).dt.month == 1]
        
        # Análise por responsável
        print("\n=== ANÁLISE DE PRODUTIVIDADE - JANEIRO 2025 ===")
        print("\nResumo da Análise:")
        print("-" * 50)
        
        # Total geral de resoluções
        total_geral = por_dia['TOTAL_RESOLVIDOS'].sum()
        print(f"Total de demandas resolvidas em Janeiro/2025: {total_geral}")
        
        # Média diária geral
        dias_uteis = por_dia['RESOLUÇÃO'].nunique()
        media_diaria_geral = total_geral / dias_uteis if dias_uteis > 0 else 0
        print(f"Média diária geral: {media_diaria_geral:.1f} resoluções/dia")
        print(f"Dias úteis analisados: {dias_uteis}")
        
        # Análise por tipo de demanda (coluna 3)
        print("\nDistribuição por Tipo de Demanda:")
        print("-" * 50)
        tipos_demanda = df_resolvido.iloc[:, 3].value_counts()
        for tipo, count in tipos_demanda.items():
            print(f"{tipo}: {count} demandas")
        
        # Análise por responsável
        print("\nDesempenho Individual:")
        print("-" * 50)
        
        for responsavel in sorted(por_dia['RESPONSÁVEL'].unique()):
            dados_resp = por_dia[por_dia['RESPONSÁVEL'] == responsavel]
            total_resp = dados_resp['TOTAL_RESOLVIDOS'].sum()
            dias_ativos = len(dados_resp)
            media_diaria = total_resp / dias_ativos if dias_ativos > 0 else 0
            
            print(f"\n{responsavel}:")
            print(f"- Total de resoluções: {total_resp}")
            print(f"- Dias ativos: {dias_ativos}")
            print(f"- Média diária: {media_diaria:.1f}")
            print("\nHistórico de resoluções:")
            
            for _, row in dados_resp.iterrows():
                print(f"  {row['RESOLUÇÃO'].strftime('%d/%m/%Y')}: {row['TOTAL_RESOLVIDOS']} demandas")
        
        # Análise de status atual (coluna 11)
        print("\n=== ANÁLISE DE STATUS ===")
        print("-" * 50)
        status = df.iloc[:, 11].value_counts()
        for st, count in status.items():
            print(f"{st}: {count} demandas")
        
        # Ranking dos mais produtivos
        print("\n=== RANKING DE PRODUTIVIDADE ===")
        print("-" * 50)
        ranking = por_dia.groupby('RESPONSÁVEL')['TOTAL_RESOLVIDOS'].sum().sort_values(ascending=False)
        
        for i, (resp, total) in enumerate(ranking.items(), 1):
            dias = len(por_dia[por_dia['RESPONSÁVEL'] == resp])
            media = total / dias if dias > 0 else 0
            print(f"{i}º - {resp}: {total} resoluções (média: {media:.1f}/dia)")
        
        # Tabela detalhada
        print("\n=== QUANTIDADE DE DEMANDAS RESOLVIDAS POR DIA ===")
        print("-" * 50)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)
        print(por_dia.to_string(index=True))
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    analisar_demandas_leandro()
