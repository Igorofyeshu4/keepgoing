import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def processar_planilha():
    # Encontrar o arquivo Excel mais recente
    base_dir = os.path.dirname(os.path.dirname(__file__))
    excel_files = [f for f in os.listdir(base_dir) if f.endswith('.xlsx') and 'DEMANDAS' in f]
    if not excel_files:
        raise FileNotFoundError("Nenhum arquivo de demandas encontrado")
    
    latest_file = max(excel_files)
    excel_path = os.path.join(base_dir, latest_file)
    
    # Carregar dados da planilha
    df = pd.read_excel(excel_path)
    
    # Renomear colunas para nomes significativos
    df.columns = ['ID', 'DATA', 'DEMANDA', 'RESPONSAVEL', 'STATUS', 'RESOLUCAO', 'OBSERVACAO', 'PRIORIDADE']
    
    # Converter colunas de data
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    df['RESOLUCAO'] = pd.to_datetime(df['RESOLUCAO'], errors='coerce')
    
    # Classificar grupos
    def classificar_grupo(responsavel):
        if pd.isna(responsavel):
            return 'Outros'
        responsavel = str(responsavel).lower()
        if responsavel in ['julio', 'antunis']:
            return 'Grupo Julio'
        elif responsavel in ['leandro', 'adriano']:
            return 'Grupo Leandro/Adriano'
        return 'Outros'
    
    df['GRUPO'] = df['RESPONSAVEL'].apply(classificar_grupo)
    
    # Adicionar coluna de tipo (mantendo compatibilidade)
    df['TIPO'] = 'RECEPTIVO'  # Podemos ajustar isso conforme necessário
    
    return df

def analisar_dados():
    df = processar_planilha()
    
    # Cálculos gerais
    total_demandas = df['DEMANDA'].sum()
    total_resolvidas = df[df['STATUS'] == 'RESOLVIDO']['DEMANDA'].sum()
    taxa_resolucao = (total_resolvidas / total_demandas * 100) if total_demandas > 0 else 0
    total_receptivo = df[df['TIPO'] == 'RECEPTIVO']['DEMANDA'].sum()
    total_ativo = df[df['TIPO'] == 'ATIVO']['DEMANDA'].sum()
    
    # Gerar insights
    insights = []
    
    # Insights por equipe
    for grupo in df['GRUPO'].unique():
        df_grupo = df[df['GRUPO'] == grupo]
        total_grupo = df_grupo['DEMANDA'].sum()
        resolvidas_grupo = df_grupo[df_grupo['STATUS'] == 'RESOLVIDO']['DEMANDA'].sum()
        receptivo_grupo = df_grupo[df_grupo['TIPO'] == 'RECEPTIVO']['DEMANDA'].sum()
        
        insights.append({
            'equipe': grupo,
            'insight': f'Total de {int(resolvidas_grupo)} demandas resolvidas',
            'impacto': 'ALTO'
        })
        
        insights.append({
            'equipe': grupo,
            'insight': f'Possui {int(total_grupo - resolvidas_grupo)} pendências receptivo',
            'impacto': 'MEDIO'
        })
        
        insights.append({
            'equipe': grupo,
            'insight': f'Total de {int(receptivo_grupo)} demandas receptivas',
            'impacto': 'INFORMATIVO'
        })
    
    return {
        'total_demandas': int(total_demandas),
        'total_resolvidas': int(total_resolvidas),
        'taxa_resolucao': round(taxa_resolucao, 1),
        'total_receptivo': int(total_receptivo),
        'total_ativo': int(total_ativo),
        'insights': insights
    }

def analisar_dados_por_pessoa():
    df = processar_planilha()
    
    # Período de análise (30 dias)
    periodo_dias = 30
    
    resultados = {}
    
    # Análise por pessoa
    for pessoa in df['RESPONSAVEL'].unique():
        df_pessoa = df[df['RESPONSAVEL'] == pessoa]
        
        # Cálculos básicos
        total_demandas = df_pessoa['DEMANDA'].sum()
        resolvidas = df_pessoa[df_pessoa['STATUS'] == 'RESOLVIDO']['DEMANDA'].sum()
        percentual = (resolvidas / total_demandas * 100) if total_demandas > 0 else 0
        media_diaria = total_demandas / periodo_dias
        
        # Receptivo/Ativo
        receptivo = df_pessoa[df_pessoa['TIPO'] == 'RECEPTIVO']['DEMANDA'].sum()
        ativo = df_pessoa[df_pessoa['TIPO'] == 'ATIVO']['DEMANDA'].sum()
        
        # Pico de demandas
        pico_data = df_pessoa.loc[df_pessoa['DEMANDA'].idxmax()]
        
        # Determinar equipe
        equipe = 'julio' if pessoa in ['JAIRANE', 'ANA GESSICA', 'FELIPE'] else 'adriano'
        
        resultados[pessoa] = {
            'equipe': equipe,
            'total': int(total_demandas),
            'resolvidas': int(resolvidas),
            'percentual': round(percentual, 1),
            'mediadiaria': round(media_diaria, 1),
            'receptivo': int(receptivo),
            'ativo': int(ativo),
            'pico': {
                'quantidade': int(pico_data['DEMANDA']),
                'data': pico_data['DATA'].strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    
    return resultados

def gerar_metricas_por_responsavel():
    df = processar_planilha()
    
    # Agrupar por responsável
    metricas_por_responsavel = {}
    
    for responsavel in df['RESPONSAVEL'].unique():
        df_resp = df[df['RESPONSAVEL'] == responsavel]
        
        # Calcular métricas básicas
        total_demandas = df_resp['DEMANDA'].sum()
        resolvidas = df_resp[df_resp['STATUS'] == 'RESOLVIDO']['DEMANDA'].sum()
        taxa_resolucao = (resolvidas / total_demandas * 100) if total_demandas > 0 else 0
        
        # Calcular receptivo/ativo
        receptivo = df_resp[df_resp['TIPO'] == 'RECEPTIVO']['DEMANDA'].sum()
        ativo = df_resp[df_resp['TIPO'] == 'ATIVO']['DEMANDA'].sum()
        
        # Calcular média diária
        dias_ativos = len(df_resp['DATA'].unique())
        media_diaria = total_demandas / dias_ativos if dias_ativos > 0 else 0
        
        # Encontrar pico de demandas
        demandas_por_dia = df_resp.groupby('DATA')['DEMANDA'].sum()
        pico_data = demandas_por_dia.idxmax()
        pico_quantidade = demandas_por_dia.max()
        
        # Determinar equipe
        equipe = df_resp['GRUPO'].iloc[0]
        
        # Organizar métricas
        if equipe not in metricas_por_responsavel:
            metricas_por_responsavel[equipe] = {}
            
        metricas_por_responsavel[equipe][responsavel] = {
            'total_demandas': int(total_demandas),
            'resolvidas': int(resolvidas),
            'taxa_resolucao': round(taxa_resolucao, 1),
            'media_diaria': round(media_diaria, 1),
            'dias_ativos': dias_ativos,
            'receptivo': int(receptivo),
            'ativo': int(ativo),
            'pico_data': pico_data,
            'pico_quantidade': int(pico_quantidade),
            'demandas_por_dia': demandas_por_dia.to_dict()
        }
    
    return metricas_por_responsavel

if __name__ == "__main__":
    try:
        print("\nProcessando planilha...")
        metricas = analisar_dados()
        
        print("\nMétricas Principais:")
        print(f"Total de Demandas: {metricas['total_demandas']}")
        print(f"Total Resolvidas: {metricas['total_resolvidas']}")
        print(f"Taxa de Resolução: {metricas['taxa_resolucao']}%")
        print(f"Total Receptivo: {metricas['total_receptivo']}")
        print(f"Total Ativo: {metricas['total_ativo']}")
        
        print(f"\nInsights gerados: {len(metricas['insights'])}")
        
        print("\nPrincipais Insights:")
        for insight in metricas['insights']:
            print(f"- {insight['equipe']}: {insight['insight']} (Impacto: {insight['impacto']})")
        
        print("\nMétricas por Responsável:")
        metricas_resp = gerar_metricas_por_responsavel()
        for equipe, responsaveis in metricas_resp.items():
            print(f"\n{equipe}:")
            for resp, dados in responsaveis.items():
                print(f"\n{resp}:")
                print(f"  Total Demandas: {dados['total_demandas']}")
                print(f"  Resolvidas: {dados['resolvidas']} ({dados['taxa_resolucao']}%)")
                print(f"  Média Diária: {dados['media_diaria']} em {dados['dias_ativos']} dias")
                print(f"  Receptivo/Ativo: {dados['receptivo']}/{dados['ativo']}")
                print(f"  Pico: {dados['pico_quantidade']} demandas em {dados['pico_data']}")
        
        print("\nMétricas por Pessoa:")
        metricas_pessoa = analisar_dados_por_pessoa()
        for pessoa, dados in metricas_pessoa.items():
            print(f"\n{pessoa}:")
            print(f"  Total Demandas: {dados['total']}")
            print(f"  Resolvidas: {dados['resolvidas']} ({dados['percentual']}%)")
            print(f"  Média Diária: {dados['mediadiaria']}")
            print(f"  Receptivo/Ativo: {dados['receptivo']}/{dados['ativo']}")
            print(f"  Pico: {dados['pico']['quantidade']} demandas em {dados['pico']['data']}")
        
    except Exception as e:
        print(f"\nErro durante a análise: {str(e)}")
