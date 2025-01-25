import pandas as pd
import datetime
from typing import Dict, List
import numpy as np
from pandas.api.types import is_datetime64_any_dtype
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import smtplib
import os

def validate_date(date_value) -> str:
    """Valida e formata datas, retornando uma string no formato YYYY-MM-DD"""
    try:
        if pd.isna(date_value):
            return None
        if isinstance(date_value, (int, float)):
            if date_value > 50000:  # Valor muito alto para ser uma data válida
                return None
        date_obj = pd.to_datetime(date_value)
        if date_obj.year < 2020 or date_obj.year > 2030:  # Intervalo razoável de anos
            return None
        return date_obj.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return None

def clean_contract_number(contract: any) -> str:
    """Limpa e formata números de contrato"""
    try:
        if pd.isna(contract):
            return 'N/A'
        return str(int(float(str(contract).replace('.', ''))))
    except (ValueError, TypeError):
        return str(contract)

def format_summary_table(data: Dict[str, int], title: str) -> str:
    """Formata uma tabela de resumo usando caracteres ASCII"""
    headers = ['Metricas', 'Valores']
    rows = []
    
    icon_map = {
        'Resolvidos': '[OK]',
        'Pendentes Receptivo': '[PR]',
        'Pendentes Ativo': '[PA]',
        'Prioridades': '[!]',
        'Análises do Dia': '[AD]',
        'Total Análises': '[TA]',
        'Quitados': '[Q]',
        'Aprovados': '[A]',
        'Receptivo': '[R]',
        'Quitados Cliente': '[QC]',
        'Quitado Aprovado': '[QA]',
        'Aprovados Duplos': '[AD]',
        'Campos Não Preenchidos': '[X]'
    }
    
    for metric, value in data.items():
        if isinstance(value, dict):  # Para campos não preenchidos
            for sub_metric, sub_value in value.items():
                icon = '[X]'
                metric_name = f"{icon} {sub_metric}"
                rows.append([metric_name, sub_value])
        else:
            if isinstance(value, float):
                value = f"{value:.1f}"
            icon = icon_map.get(metric, '')
            metric_name = f"{icon} {metric}" if icon else metric
            rows.append([metric_name, value])
    
    table = "+" + "-" * 30 + "+" + "-" * 10 + "+\n"
    table += "| {:<28} | {:>8} |\n".format(headers[0], headers[1])
    table += "+" + "-" * 30 + "+" + "-" * 10 + "+\n"
    
    for row in rows:
        if isinstance(row[1], (int, float)):
            if row[1] > 0:
                table += "| {:<28} | {:>8} |\n".format(row[0], row[1])
        else:
            table += "| {:<28} | {:>8} |\n".format(row[0], row[1])
    
    table += "+" + "-" * 30 + "+" + "-" * 10 + "+"
    
    return f"\n{title}\n{table}"

def calculate_resolution_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Calcula métricas de resolução"""
    if 'DATA_RESOLUCAO' in df.columns and 'DATA_CRIACAO' in df.columns:
        df['DATA_RESOLUCAO'] = pd.to_datetime(df['DATA_RESOLUCAO'])
        df['DATA_CRIACAO'] = pd.to_datetime(df['DATA_CRIACAO'])
        resolvidos = df[df['SITUAÇÃO'].str.lower() == 'resolvido']
        
        if not resolvidos.empty:
            tempo_medio = (resolvidos['DATA_RESOLUCAO'] - resolvidos['DATA_CRIACAO']).mean()
            return {
                'tempo_medio_resolucao': tempo_medio.days,
                'taxa_conclusao': len(resolvidos) / len(df) * 100
            }
    
    return {
        'tempo_medio_resolucao': 0,
        'taxa_conclusao': 0
    }

def send_email_report(report_path: str, summary_path: str, graphs_dir: str):
    """Envia relatório por email"""
    try:
        # Configurações de email (ajuste conforme necessário)
        sender_email = "seu_email@exemplo.com"
        receiver_email = "destinatario@exemplo.com"
        password = "sua_senha"  # Use variáveis de ambiente na produção
        
        msg = MIMEMultipart()
        msg['Subject'] = f'Relatório de Análise Diária - {datetime.datetime.now().strftime("%Y-%m-%d")}'
        msg['From'] = sender_email
        msg['To'] = receiver_email
        
        # Corpo do email
        with open(summary_path, 'r', encoding='utf-8') as f:
            body = f.read()
        msg.attach(MIMEText(body, 'plain'))
        
        # Anexos
        files_to_attach = [
            (report_path, 'Relatorio_Analise_Diaria.csv'),
            (os.path.join(graphs_dir, 'status_distribution.png'), 'status_distribution.png'),
            (os.path.join(graphs_dir, 'group_comparison.png'), 'group_comparison.png')
        ]
        
        for filepath, filename in files_to_attach:
            with open(filepath, 'rb') as f:
                part = MIMEApplication(f.read(), Name=filename)
                part['Content-Disposition'] = f'attachment; filename="{filename}"'
                msg.attach(part)
        
        # Enviando email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
            
        print("Relatório enviado por email com sucesso!")
        
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")

def process_group_data(df: pd.DataFrame, grupo_nome: str) -> tuple[List[Dict], Dict[str, int], Dict[str, Dict[str, int]]]:
    report_data = []
    
    # Limpando e validando dados
    df['DATA'] = df['DATA'].apply(validate_date)
    df['CTT'] = df['CTT'].apply(clean_contract_number)
    
    # Removendo linhas com datas inválidas
    df = df.dropna(subset=['DATA'])
    
    # Calculando métricas de resolução
    resolution_metrics = calculate_resolution_metrics(df)
    
    # Agrupando por responsável
    responsaveis = df['RESPONSÁVEL'].unique()
    responsavel_metricas = {}
    
    for responsavel in responsaveis:
        df_resp = df[df['RESPONSÁVEL'] == responsavel]
        
        # Verificando campos obrigatórios
        campos_vazios = {
            'RESPONSÁVEL': df_resp['RESPONSÁVEL'].isna().sum(),
            'Q.A': df_resp['Q.A'].isna().sum() if 'Q.A' in df_resp.columns else len(df_resp),
            'DATA': df_resp['DATA'].isna().sum(),
            'SITUAÇÃO': df_resp['SITUAÇÃO'].isna().sum()
        }
        
        # Verificando status específicos
        status_count = {
            'Quitados': len(df_resp[df_resp['SITUAÇÃO'].str.lower() == 'quitado']) if not df_resp.empty else 0,
            'Quitados Cliente': len(df_resp[df_resp['SITUAÇÃO'].str.lower() == 'quitado cliente']) if not df_resp.empty else 0,
            'Aprovados': len(df_resp[df_resp['SITUAÇÃO'].str.lower() == 'aprovado']) if not df_resp.empty else 0,
            'Resolvidos': len(df_resp[df_resp['SITUAÇÃO'].str.lower() == 'resolvido']) if not df_resp.empty else 0,
            'Pendentes': len(df_resp[df_resp['SITUAÇÃO'].str.lower() == 'pendente']) if not df_resp.empty else 0,
            'Análises do Dia': len(df_resp[df_resp['DATA'] == datetime.datetime.now().strftime('%Y-%m-%d')]) if not df_resp.empty else 0
        }
        
        # Calculando porcentagem de campos preenchidos
        total_registros = len(df_resp) if not df_resp.empty else 1
        preenchimento = {
            'Campos Vazios': {
                'Responsável': f"{(campos_vazios['RESPONSÁVEL']/total_registros)*100:.1f}%",
                'Q.A': f"{(campos_vazios['Q.A']/total_registros)*100:.1f}%",
                'Data': f"{(campos_vazios['DATA']/total_registros)*100:.1f}%",
                'Situação': f"{(campos_vazios['SITUAÇÃO']/total_registros)*100:.1f}%"
            }
        }
        
        responsavel_metricas[responsavel] = {
            **status_count,
            'Total Registros': total_registros,
            'Campos Não Preenchidos': preenchimento['Campos Vazios']
        }
    
    try:
        metricas = {
            'Resolvidos': len(df[df['SITUAÇÃO'].str.lower() == 'resolvido']),
            'Pendentes Receptivo': len(df[
                (df['SITUAÇÃO'].str.lower() == 'pendente') & 
                (df['ATIVO/RECEPTIVO'].str.lower() == 'receptivo')
            ]),
            'Pendentes Ativo': len(df[
                (df['SITUAÇÃO'].str.lower() == 'pendente') & 
                (df['ATIVO/RECEPTIVO'].str.lower() == 'ativo')
            ]),
            'Quitados': len(df[df['SITUAÇÃO'].str.lower() == 'quitado']),
            'Aprovados': len(df[df['SITUAÇÃO'].str.lower() == 'aprovado']),
            'Análises do Dia': len(df[df['DATA'] == datetime.datetime.now().strftime('%Y-%m-%d')]),
            'Total Análises': len(df),
            'Receptivo': len(df[df['ATIVO/RECEPTIVO'].str.lower() == 'receptivo']),
            'Prioridades': len(df[df['PRIORIDADE'].str.lower() == 'alta']) if 'PRIORIDADE' in df.columns else 0,
            'Quitados Cliente': len(df[df['SITUAÇÃO'].str.lower() == 'quitado cliente']) if 'SITUAÇÃO' in df.columns else 0,
            'Quitado Aprovado': len(df[df['SITUAÇÃO'].str.lower() == 'quitado aprovado']) if 'SITUAÇÃO' in df.columns else 0,
            'Aprovados Duplos': len(df[df['SITUAÇÃO'].str.lower() == 'aprovado duplo']) if 'SITUAÇÃO' in df.columns else 0
        }
        
    except Exception as e:
        print(f"Erro ao processar métricas para {grupo_nome}: {str(e)}")
        return [], {}, {}
    
    # Criando entradas para o relatório
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    
    for status, count in metricas.items():
        if isinstance(count, (int, float)) and count > 0:
            report_data.append({
                'data': datetime.datetime.now().strftime('%Y-%m-%d'),
                'grupo': grupo_nome,
                'status': status,
                'ultima_atualizacao': timestamp,
                'quantidade': float(count)
            })
    
    return report_data, metricas, responsavel_metricas

def process_excel_to_csv():
    try:
        output_dir = 'f:/demandstest/public/reports'
        os.makedirs(output_dir, exist_ok=True)
        
        pd.options.mode.chained_assignment = None
        
        excel_path = 'f:/demandstest/docs/_DEMANDAS DE JANEIRO_2025.xlsx'
        df_julio = pd.read_excel(excel_path, sheet_name='DEMANDAS JULIO')
        df_leandro = pd.read_excel(excel_path, sheet_name='DEMANDA LEANDROADRIANO')
        
        hoje = datetime.datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n=== RELATÓRIO GERAL DE DEMANDAS ({hoje}) ===\n")
        
        # Processando Grupo Julio
        print("\n[EQUIPE JULIO]")
        julio_data, julio_metrics, julio_resp = process_group_data(df_julio, 'Grupo Julio')
        print(format_summary_table(julio_metrics, ""))
        
        # Mostrando métricas por responsável do Grupo Julio
        print("\nDetalhamento por Responsável:")
        for resp, metricas in julio_resp.items():
            print(f"\n[{resp}]")
            print(format_summary_table(metricas, ""))
        
        # Processando Grupo Leandro e Adriano
        print("\n[EQUIPE ADRIANO/LEANDRO]")
        leandro_data, leandro_metrics, leandro_resp = process_group_data(df_leandro, 'Grupo Leandro e Adriano')
        print(format_summary_table(leandro_metrics, ""))
        
        # Mostrando métricas por responsável do Grupo Leandro/Adriano
        print("\nDetalhamento por Responsável:")
        for resp, metricas in leandro_resp.items():
            print(f"\n[{resp}]")
            print(format_summary_table(metricas, ""))
        
        # Calculando totais
        total_metrics = {}
        for metric in set(julio_metrics.keys()) | set(leandro_metrics.keys()):
            total_metrics[metric] = julio_metrics.get(metric, 0) + leandro_metrics.get(metric, 0)
        
        print("\n[TOTALIZADORES]")
        print(format_summary_table(total_metrics, ""))
        
        # Salvando relatórios e visualizações
        all_report_data = []
        all_report_data.extend(julio_data)
        all_report_data.extend(leandro_data)
        
        df_report = pd.DataFrame(all_report_data)
        df_report = df_report.sort_values(['grupo', 'status'])
        
        csv_path = os.path.join(output_dir, 'Relatorio_Analise_Diaria.csv')
        df_report.to_csv(csv_path, index=False, encoding='utf-8')
        
        # Salvando resumo em texto
        summary_path = os.path.join(output_dir, 'Resumo_Analise_Diaria.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"RELATÓRIO GERAL DE DEMANDAS - {hoje}\n\n")
            
            # Grupo Julio
            f.write("\n[EQUIPE JULIO]\n")
            for resp, metricas in julio_resp.items():
                f.write(f"\n[{resp}]\n")
                for metric, value in metricas.items():
                    f.write(f"{metric}: {value}\n")
            
            # Grupo Leandro/Adriano
            f.write("\n[EQUIPE ADRIANO/LEANDRO]\n")
            for resp, metricas in leandro_resp.items():
                f.write(f"\n[{resp}]\n")
                for metric, value in metricas.items():
                    f.write(f"{metric}: {value}\n")
            
            # Totalizadores
            f.write("\n[TOTALIZADORES]\n")
            for metric, value in total_metrics.items():
                f.write(f"{metric}: {value}\n")
        
        print(f"\nRelatório detalhado gerado em: {csv_path}")
        print(f"Resumo salvo em: {summary_path}")
        
    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")

if __name__ == "__main__":
    process_excel_to_csv()
