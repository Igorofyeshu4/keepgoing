import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import os
import warnings
import re

def capture_excel_warnings():
    """Captura warnings do Excel e retorna informações sobre células com erro."""
    cell_errors = []
    
    def warning_handler(message, category, filename, lineno, file=None, line=None):
        if category == UserWarning and "is marked as a date but the serial value" in str(message):
            # Extrair informações do warning
            match = re.search(r"Cell ([A-Z]+\d+).*serial value (\d+\.\d+)", str(message))
            if match:
                cell_ref, serial_value = match.groups()
                cell_errors.append({
                    'cell': cell_ref,
                    'value': float(serial_value)
                })
    
    warnings.showwarning = warning_handler
    return cell_errors

def normalize_column_name(col):
    """Normaliza o nome da coluna para evitar problemas de codificação."""
    replacements = {
        "RESOLUÇÃO": "RESOLUCAO",
        "SITUAÇÃO": "SITUACAO",
        "CÓDIGO": "CODIGO",
        "ESCRITÓRIO": "ESCRITORIO",
        "ANÁLISE": "ANALISE"
    }
    return replacements.get(col, col)

def load_data(file_path, sheet_names=None):
    """Carrega os dados do arquivo Excel."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    if sheet_names is None:
        sheet_names = ["DEMANDAS JULIO", "DEMANDA LEANDROADRIANO", "QUITADOS"]
    
    # Configurar captura de warnings
    cell_errors = capture_excel_warnings()
    
    # Valores que não devem ser convertidos para data
    non_date_values = {6620035.0}  # Adicionar outros valores conforme necessário
    
    dfs = {}
    for sheet in sheet_names:
        try:
            # Carregar o Excel
            df = pd.read_excel(file_path, sheet_name=sheet)
            
            # Normalizar nomes das colunas
            df.columns = [normalize_column_name(col) if isinstance(col, str) else col for col in df.columns]
            
            # Identificar colunas de data
            date_columns = [col for col in df.columns if "DATA" in str(col).upper() or "RESOLUCAO" in str(col).upper()]
            
            for col in date_columns:
                try:
                    # Identificar valores que são números grandes (não datas)
                    numeric_mask = pd.to_numeric(df[col], errors='coerce').isin(non_date_values)
                    
                    # Manter os valores originais para os números grandes
                    original_values = df[col].copy()
                    
                    # Tentar converter para datetime
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    
                    # Restaurar os valores originais onde eram números grandes
                    df.loc[numeric_mask, col] = original_values[numeric_mask]
                    
                except Exception as e:
                    print(f"Aviso ao processar coluna {col}: {str(e)}")
            
            dfs[sheet] = df
            print(f"\nCarregados {len(df)} registros da aba {sheet}")
            print(f"Colunas encontradas: {', '.join(df.columns)}")
            
            # Mostrar alguns exemplos de valores nas colunas de data
            for col in date_columns:
                sample_vals = df[col].dropna().sample(min(5, len(df[col].dropna()))).tolist()
                if sample_vals:
                    print(f"\nExemplos de valores em {col}:")
                    for val in sample_vals:
                        print(f"  {val} (tipo: {type(val)})")
                
        except Exception as e:
            print(f"Erro ao carregar aba {sheet}: {str(e)}")
    
    return dfs, cell_errors

def analyze_data_quality(df):
    """Analisa a qualidade dos dados em um DataFrame."""
    quality_report = {
        "total_rows": len(df),
        "columns": {},
        "missing_data": {},
        "data_types": {},
        "unique_values": {}
    }
    
    for col in df.columns:
        # Contagem de valores nulos
        null_count = df[col].isnull().sum()
        null_percentage = (null_count / len(df)) * 100
        
        # Tipo de dados
        dtype = str(df[col].dtype)
        
        # Valores únicos
        unique_count = df[col].nunique()
        
        quality_report["columns"][col] = {
            "null_count": int(null_count),
            "null_percentage": float(null_percentage),
            "dtype": dtype,
            "unique_values": int(unique_count)
        }
        
        # Adicionar aos totais por tipo
        if dtype not in quality_report["data_types"]:
            quality_report["data_types"][dtype] = 0
        quality_report["data_types"][dtype] += 1
        
        # Registrar colunas com dados faltantes
        if null_count > 0:
            quality_report["missing_data"][col] = {
                "count": int(null_count),
                "percentage": float(null_percentage)
            }
    
    return quality_report

def analyze_status_columns(df):
    """Analisa as colunas de status e situação."""
    status_report = {}
    
    # Procurar colunas relacionadas a status
    status_columns = [col for col in df.columns if "STATUS" in str(col).upper() or "SITUACAO" in str(col).upper()]
    
    for col in status_columns:
        status_counts = df[col].value_counts()
        status_report[col] = status_counts.to_dict()
    
    return status_report

def analyze_quitados_Janeiro(df):
    """Analisa os registros quitados em Janeiro."""
    if "SITUACAO" not in df.columns or "RESOLUCAO" not in df.columns:
        return None
    
    # Filtrar registros de Janeiro/2025
    janeiro_2025 = df[
        (df["RESOLUCAO"].dt.year == 2025) & 
        (df["RESOLUCAO"].dt.month == 1)
    ]
    
    quitados = janeiro_2025[janeiro_2025["SITUACAO"].str.contains("QUITADO", na=False, case=False)]
    
    return {
        "total_janeiro": len(janeiro_2025),
        "total_quitados": len(quitados),
        "percentual_quitados": (len(quitados) / len(janeiro_2025) * 100) if len(janeiro_2025) > 0 else 0
    }

def analyze_formulas_columns(df):
    """Analisa as colunas que podem conter fórmulas (O a S)."""
    formula_cols = df.columns[14:19] if len(df.columns) >= 19 else []  # Colunas O a S (0-based index)
    
    analysis = {}
    for col in formula_cols:
        if col in df.columns:
            # Estatísticas básicas para valores numéricos
            numeric_stats = df[col].describe().to_dict() if pd.api.types.is_numeric_dtype(df[col]) else None
            
            # Valores únicos para não numéricos
            unique_values = df[col].value_counts().to_dict() if not pd.api.types.is_numeric_dtype(df[col]) else None
            
            analysis[col] = {
                "dtype": str(df[col].dtype),
                "numeric_stats": numeric_stats,
                "unique_values": unique_values,
                "null_count": int(df[col].isnull().sum())
            }
    
    return analysis

def analyze_date_errors(df, sheet_name, cell_errors):
    """Analisa erros em datas e retorna um DataFrame com os problemas encontrados."""
    date_errors = []
    
    # Adicionar erros capturados dos warnings do Excel
    for error in cell_errors:
        # Extrair linha e coluna da referência da célula
        col_letter = ''.join(filter(str.isalpha, error['cell']))
        row_num = int(''.join(filter(str.isdigit, error['cell'])))
        
        date_errors.append({
            'Sheet': sheet_name,
            'Linha': row_num,
            'Coluna': 'RESOLUCAO' if col_letter == 'B' else 'DATA',  # Assumindo que coluna B é RESOLUCAO
            'Valor_Original': str(error['value']),
            'Erro': 'Valor de data fora dos limites do Excel',
            'Sugestao_Correcao': 'Verificar e corrigir o formato da data'
        })
    
    # Identificar colunas de data
    date_columns = [col for col in df.columns if "DATA" in str(col).upper() or "RESOLUCAO" in str(col).upper()]
    
    for col in date_columns:
        # Converter para datetime preservando os erros
        original_values = df[col].copy()
        try:
            # Verificar valores numéricos muito grandes (erro comum no Excel)
            if pd.api.types.is_numeric_dtype(df[col]):
                large_values_mask = df[col] > 50000  # Valores muito grandes para datas do Excel
                for idx in df[large_values_mask].index:
                    # Verificar se já não foi reportado pelos warnings
                    if not any(e['Linha'] == idx + 2 and e['Coluna'] == col for e in date_errors):
                        date_errors.append({
                            'Sheet': sheet_name,
                            'Linha': idx + 2,
                            'Coluna': col,
                            'Valor_Original': str(df.loc[idx, col]),
                            'Erro': 'Valor numérico fora dos limites para data do Excel',
                            'Sugestao_Correcao': 'Verificar se o valor está correto e converter para formato de data válido'
                        })
            
            converted_dates = pd.to_datetime(df[col], errors='coerce')
            
            # Identificar linhas com problemas de conversão
            problem_mask = pd.isna(converted_dates) & df[col].notna()
            if problem_mask.any():
                problem_rows = df[problem_mask]
                for idx, row in problem_rows.iterrows():
                    # Verificar se já não foi reportado
                    if not any(e['Linha'] == idx + 2 and e['Coluna'] == col for e in date_errors):
                        date_errors.append({
                            'Sheet': sheet_name,
                            'Linha': idx + 2,
                            'Coluna': col,
                            'Valor_Original': str(row[col]),
                            'Erro': 'Data inválida',
                            'Sugestao_Correcao': 'Verificar formato da data'
                        })
            
            # Verificar datas fora dos limites razoáveis
            valid_dates_mask = converted_dates.notna()
            valid_dates = converted_dates[valid_dates_mask]
            
            # Definir limites razoáveis (ex: entre 2020 e 2025)
            min_date = pd.Timestamp('2020-01-01')
            max_date = pd.Timestamp('2025-12-31')
            
            out_of_bounds_mask = (valid_dates < min_date) | (valid_dates > max_date)
            if out_of_bounds_mask.any():
                problem_dates = valid_dates[out_of_bounds_mask]
                for idx, date in problem_dates.items():
                    # Verificar se já não foi reportado
                    if not any(e['Linha'] == idx + 2 and e['Coluna'] == col for e in date_errors):
                        date_errors.append({
                            'Sheet': sheet_name,
                            'Linha': idx + 2,
                            'Coluna': col,
                            'Valor_Original': str(original_values[idx]),
                            'Erro': 'Data fora dos limites',
                            'Sugestao_Correcao': f'Data deve estar entre {min_date.date()} e {max_date.date()}'
                        })
                    
        except Exception as e:
            print(f"Erro ao processar coluna {col}: {str(e)}")
    
    return pd.DataFrame(date_errors)

def export_date_errors_to_csv(file_path):
    """Exporta erros de data para um arquivo CSV."""
    try:
        # Carregar dados
        dfs, cell_errors = load_data(file_path)
        
        # Analisar erros de data em cada planilha
        all_errors = []
        for sheet_name, df in dfs.items():
            errors_df = analyze_date_errors(df, sheet_name, cell_errors)
            if not errors_df.empty:
                all_errors.append(errors_df)
        
        if all_errors:
            # Combinar todos os erros
            combined_errors = pd.concat(all_errors, ignore_index=True)
            
            # Exportar para CSV
            output_file = 'erros_datas.csv'
            combined_errors.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\nErros de data exportados para {output_file}")
            print(f"Total de erros encontrados: {len(combined_errors)}")
            
            # Exibir resumo dos erros
            print("\nResumo dos erros por tipo:")
            print(combined_errors['Erro'].value_counts())
            print("\nResumo dos erros por planilha:")
            print(combined_errors['Sheet'].value_counts())
        else:
            print("\nNenhum erro de data encontrado!")
            
    except Exception as e:
        print(f"Erro ao processar arquivo: {str(e)}")
        import traceback
        traceback.print_exc()

def generate_quality_report(dfs):
    """Gera um relatório completo de qualidade dos dados."""
    report = []
    report.append("=== RELATÓRIO DE QUALIDADE DOS DADOS ===\n")
    
    for sheet_name, df in dfs.items():
        report.append(f"\n=== {sheet_name} ===")
        
        # Análise de qualidade geral
        quality = analyze_data_quality(df)
        report.append(f"\nTotal de registros: {quality['total_rows']}")
        
        report.append("\nColunas com dados faltantes:")
        for col, stats in quality["missing_data"].items():
            report.append(f"  {col}: {stats['count']} registros ({stats['percentage']:.1f}%)")
        
        # Análise de status
        status = analyze_status_columns(df)
        if status:
            report.append("\nDistribuição de Status:")
            for col, counts in status.items():
                report.append(f"\n  {col}:")
                for status, count in counts.items():
                    if pd.notna(status):  # Ignorar valores NaN
                        report.append(f"    {status}: {count}")
        
        # Análise de quitados (Janeiro)
        if sheet_name in ["DEMANDAS JULIO", "DEMANDA LEANDROADRIANO"]:
            quitados = analyze_quitados_Janeiro(df)
            if quitados:
                report.append(f"\nAnálise de Quitados (Janeiro/2025):")
                report.append(f"  Total de registros: {quitados['total_janeiro']}")
                report.append(f"  Total quitados: {quitados['total_quitados']}")
                report.append(f"  Percentual quitados: {quitados['percentual_quitados']:.1f}%")
        
        # Análise de fórmulas
        formulas = analyze_formulas_columns(df)
        if formulas:
            report.append("\nAnálise das Colunas O a S:")
            for col, stats in formulas.items():
                report.append(f"\n  {col} ({stats['dtype']}):")
                if stats['numeric_stats']:
                    report.append(f"    Média: {stats['numeric_stats'].get('mean', 'N/A')}")
                    report.append(f"    Máximo: {stats['numeric_stats'].get('max', 'N/A')}")
                    report.append(f"    Mínimo: {stats['numeric_stats'].get('min', 'N/A')}")
                if stats['unique_values']:
                    report.append("    Valores únicos:")
                    for val, count in list(stats['unique_values'].items())[:5]:  # Mostrar apenas os 5 primeiros
                        if pd.notna(val):  # Ignorar valores NaN
                            report.append(f"      {val}: {count}")
    
    return "\n".join(report)

def analyze_daily_by_collaborator(df, date):
    """
    Analisa o desempenho diário de cada colaborador em uma data específica.
    
    Args:
        df: DataFrame com os dados
        date: Data para análise (str ou datetime)
    """
    # Converter data para datetime se necessário
    if isinstance(date, str):
        date = pd.to_datetime(date).normalize()
    else:
        date = pd.to_datetime(date).normalize()
    
    # Identificar coluna de data (DATA ou RESOLUCAO)
    date_col = 'DATA'
    if 'RESOLUCAO' in df.columns:
        date_col = 'RESOLUCAO'
    
    # Filtrar dados pela data
    df_date = df[pd.to_datetime(df[date_col]).dt.normalize() == date]
    
    if df_date.empty:
        print(f"\nNão há dados para a data {date.strftime('%Y-%m-%d')}.")
        return
    
    # Identificar coluna de responsável
    resp_col = None
    for col in ['RESPONSAVEL', 'CONSULTOR', 'RESPONSÁVEL']:
        if col in df.columns:
            resp_col = col
            break
    
    if not resp_col:
        print("\nNão foi encontrada coluna de responsável nesta planilha.")
        return
    
    # Análise por responsável
    results = []
    for resp in df_date[resp_col].unique():
        if pd.isna(resp):
            continue
            
        df_resp = df_date[df_date[resp_col] == resp]
        
        # Contagem de status
        status_counts = df_resp['SITUACAO'].value_counts()
        
        # Identificar os status disponíveis
        status_map = {
            'RESOLVIDO': ['RESOLVIDO', 'QUITADO'],
            'PENDENTE': ['PENDENTE', 'EM ANDAMENTO'],
            'ANALISE': ['ANALISE', 'EM ANÁLISE']
        }
        
        results.append({
            'Responsavel': resp,
            'Resolvidos': sum(status_counts.get(s, 0) for s in status_map['RESOLVIDO']),
            'Pendentes': sum(status_counts.get(s, 0) for s in status_map['PENDENTE']),
            'Analise': sum(status_counts.get(s, 0) for s in status_map['ANALISE']),
            'Total': len(df_resp)
        })
    
    # Converter para DataFrame para melhor visualização
    results_df = pd.DataFrame(results)
    
    if not results_df.empty:
        print(f"\nAnálise por Colaborador - {date.strftime('%Y-%m-%d')}:")
        for _, row in results_df.iterrows():
            print(f"\n{row['Responsavel']}:")
            print(f"  Resolvidos: {row['Resolvidos']}")
            print(f"  Pendentes: {row['Pendentes']}")
            print(f"  Em Análise: {row['Analise']}")
            print(f"  Total: {row['Total']}")
    
    return results_df

def analyze_daily_by_team(dfs, date):
    """
    Analisa o desempenho diário de cada equipe em uma data específica.
    
    Args:
        dfs: Dicionário com DataFrames das equipes
        date: Data para análise (str ou datetime)
    """
    # Converter data para datetime se necessário
    if isinstance(date, str):
        date = pd.to_datetime(date).normalize()
    else:
        date = pd.to_datetime(date).normalize()
    
    print(f"\nAnálise por Equipe - {date.strftime('%Y-%m-%d')}:")
    
    results = {}
    for team_name, df in dfs.items():
        # Identificar coluna de data (DATA ou RESOLUCAO)
        date_col = 'DATA'
        if 'RESOLUCAO' in df.columns:
            date_col = 'RESOLUCAO'
        
        # Filtrar dados pela data
        df_date = df[pd.to_datetime(df[date_col]).dt.normalize() == date]
        
        if df_date.empty:
            print(f"\n{team_name}: Não há dados para esta data.")
            continue
        
        # Contagem de status
        status_counts = df_date['SITUACAO'].value_counts()
        
        # Identificar os status disponíveis
        status_map = {
            'RESOLVIDO': ['RESOLVIDO', 'QUITADO'],
            'PENDENTE': ['PENDENTE', 'EM ANDAMENTO'],
            'ANALISE': ['ANALISE', 'EM ANÁLISE']
        }
        
        results[team_name] = {
            'Resolvidos': sum(status_counts.get(s, 0) for s in status_map['RESOLVIDO']),
            'Pendentes': sum(status_counts.get(s, 0) for s in status_map['PENDENTE']),
            'Analise': sum(status_counts.get(s, 0) for s in status_map['ANALISE']),
            'Total': len(df_date)
        }
        
        print(f"\n{team_name}:")
        print(f"  Resolvidos: {results[team_name]['Resolvidos']}")
        print(f"  Pendentes: {results[team_name]['Pendentes']}")
        print(f"  Em Análise: {results[team_name]['Analise']}")
        print(f"  Total: {results[team_name]['Total']}")
    
    return results

def show_available_dates(dfs):
    """Mostra as datas disponíveis em cada planilha."""
    print("\nDatas disponíveis em cada planilha:")
    for sheet_name, df in dfs.items():
        print(f"\n{sheet_name}:")
        
        # Verificar datas na coluna DATA
        if 'DATA' in df.columns:
            dates = pd.to_datetime(df['DATA'], errors='coerce').dt.normalize()
            dates = dates.dropna().unique()
            dates = sorted(dates)
            print("  Coluna DATA:")
            for date in dates[-5:]:  # Mostrar apenas as 5 últimas datas
                print(f"    {date.strftime('%Y-%m-%d')}")
        
        # Verificar datas na coluna RESOLUCAO
        if 'RESOLUCAO' in df.columns:
            dates = pd.to_datetime(df['RESOLUCAO'], errors='coerce').dt.normalize()
            dates = dates.dropna().unique()
            dates = sorted(dates)
            print("  Coluna RESOLUCAO:")
            for date in dates[-5:]:  # Mostrar apenas as 5 últimas datas
                print(f"    {date.strftime('%Y-%m-%d')}")

def create_consolidated_dataframe(dfs, date):
    """
    Cria um DataFrame consolidado com métricas de todos os colaboradores.
    
    Args:
        dfs: Dicionário com DataFrames das equipes
        date: Data para análise
    
    Returns:
        DataFrame consolidado
    """
    all_data = []
    
    for team_name, df in dfs.items():
        # Identificar coluna de data
        date_col = 'DATA'
        if 'RESOLUCAO' in df.columns:
            date_col = 'RESOLUCAO'
            
        # Identificar coluna de responsável
        resp_col = None
        for col in ['RESPONSAVEL', 'CONSULTOR', 'RESPONSÁVEL']:
            if col in df.columns:
                resp_col = col
                break
                
        if not resp_col:
            continue
            
        # Filtrar dados pela data
        df_date = df[pd.to_datetime(df[date_col]).dt.normalize() == date]
        
        if df_date.empty:
            continue
            
        # Análise por responsável
        for resp in df_date[resp_col].unique():
            if pd.isna(resp):
                continue
                
            df_resp = df_date[df_date[resp_col] == resp]
            
            # Contagem de status
            status_counts = df_resp['SITUACAO'].value_counts()
            
            # Mapear diferentes status
            status_map = {
                'RESOLVIDO': ['RESOLVIDO'],
                'PENDENTE': ['PENDENTE', 'EM ANDAMENTO'],
                'ANALISE': ['ANALISE', 'EM ANÁLISE'],
                'QUITADO': ['QUITADO'],
                'APROVADO': ['APROVADO']
            }
            
            # Contar ocorrências de cada status
            metrics = {
                'Resolvidos': sum(status_counts.get(s, 0) for s in status_map['RESOLVIDO']),
                'Pendentes': sum(status_counts.get(s, 0) for s in status_map['PENDENTE']),
                'Analisados': sum(status_counts.get(s, 0) for s in status_map['ANALISE']),
                'Quitados': sum(status_counts.get(s, 0) for s in status_map['QUITADO']),
                'Aprovados': sum(status_counts.get(s, 0) for s in status_map['APROVADO'])
            }
            
            all_data.append({
                'Data': date,
                'Nome': resp,
                'Equipe': team_name,
                **metrics
            })
    
    if not all_data:
        return pd.DataFrame()
    
    # Criar DataFrame
    df_consolidated = pd.DataFrame(all_data)
    
    # Converter data para datetime
    df_consolidated['Data'] = pd.to_datetime(df_consolidated['Data'])
    
    return df_consolidated

def analyze_daily_metrics(file_path, dates):
    """
    Realiza análise diária para uma lista de datas.
    
    Args:
        file_path: Caminho para o arquivo Excel
        dates: Lista de datas para análise
    """
    try:
        # Carregar dados
        dfs, _ = load_data(file_path)
        
        # Mostrar datas disponíveis
        show_available_dates(dfs)
        print("\nRealizando análise para as datas solicitadas...")
        
        # DataFrame para armazenar dados consolidados
        all_data = []
        
        # Para cada data
        for date in dates:
            print(f"\n{'='*50}")
            print(f"Análise para {date}")
            print('='*50)
            
            # Análise por equipe
            team_results = analyze_daily_by_team(dfs, date)
            
            # Análise por colaborador para cada equipe
            for team_name, df in dfs.items():
                print(f"\n{'-'*30}")
                print(f"Detalhamento {team_name}")
                print(f"{'-'*30}")
                analyze_daily_by_collaborator(df, date)
            
            # Criar DataFrame consolidado para esta data
            df_date = create_consolidated_dataframe(dfs, pd.to_datetime(date))
            if not df_date.empty:
                all_data.append(df_date)
        
        # Consolidar todos os dados
        if all_data:
            df_all = pd.concat(all_data, ignore_index=True)
            
            # Calcular métricas totais por colaborador
            print("\nMétricas Totais por Colaborador:")
            metrics = ['Resolvidos', 'Pendentes', 'Analisados', 'Quitados', 'Aprovados']
            totals = df_all.groupby(['Nome', 'Equipe'])[metrics].sum().reset_index()
            
            # Ordenar por total de resolvidos
            totals = totals.sort_values('Resolvidos', ascending=False)
            
            for _, row in totals.iterrows():
                print(f"\n{row['Nome']} ({row['Equipe']}):")
                for metric in metrics:
                    if row[metric] > 0:  # Só mostrar métricas com valores
                        print(f"  {metric}: {row[metric]}")
            
            # Salvar DataFrame consolidado
            output_file = os.path.join(os.path.dirname(file_path), 'metricas_colaboradores.csv')
            df_all.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\nDados consolidados salvos em: {output_file}")
            
    except Exception as e:
        print(f"Erro ao analisar métricas diárias: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Análise de qualidade dos dados de demandas.')
    parser.add_argument('file_path', help='Caminho para o arquivo Excel de dados')
    parser.add_argument('--analise', choices=['qualidade', 'datas', 'diaria'], default='qualidade',
                      help='Tipo de análise a ser realizada')
    parser.add_argument('--datas', nargs='+', help='Datas para análise diária (formato YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    try:
        if args.analise == 'datas':
            # Analisar e exportar erros de data
            export_date_errors_to_csv(args.file_path)
        elif args.analise == 'diaria':
            if not args.datas:
                # Se não foram especificadas datas, usar os últimos 3 dias
                today = datetime.now()
                dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(3)]
            else:
                dates = args.datas
            
            analyze_daily_metrics(args.file_path, dates)
        else:
            # Carregar dados
            dfs, _ = load_data(args.file_path)
            
            # Gerar relatório de qualidade
            quality_report = generate_quality_report(dfs)
            print("\n" + quality_report)
        
    except Exception as e:
        print(f"Erro ao processar os dados: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
