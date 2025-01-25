import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime

# Configurar o estilo dos gráficos
plt.style.use('default')
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

def gerar_dados_reais():
    # Dados do relatório de 10/01/2025
    dados = {
        'Equipe Julio': {
            'Resolvidos': 140,
            'Pendentes Receptivo': 102,
            'Pendentes Ativo': 701,
            'Prioridades': 3,
            'Análises do Dia': 3,
            'Total Análises': 49,
            'Quitados': 9,
            'Aprovados': 2,
            'Receptivo': 0
        },
        'Equipe Adriano/Leandro': {
            'Resolvidos': 130,
            'Pendentes Receptivo': 161,
            'Pendentes Ativo': 482,
            'Prioridades': 1,
            'Análises do Dia': 20,
            'Total Análises': 32,
            'Quitados': 16,
            'Aprovados': 5,
            'Receptivo': 1
        }
    }
    
    totalizadores = {
        'Quitados': 26,
        'Quitados Cliente': 1,
        'Quitado Aprovado': 0,
        'Aprovados': 91,
        'Aprovados Duplos': 6
    }
    
    return dados, totalizadores

def gerar_grafico_comparativo_equipes():
    print("Gerando gráfico comparativo entre equipes...")
    dados, _ = gerar_dados_reais()
    
    # Selecionar métricas principais para comparação
    metricas = ['Resolvidos', 'Pendentes Receptivo', 'Pendentes Ativo', 'Análises do Dia']
    
    # Preparar dados para o gráfico
    equipes = list(dados.keys())
    x = np.arange(len(metricas))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plotar barras para cada equipe
    valores_julio = [dados['Equipe Julio'][m] for m in metricas]
    valores_leandro = [dados['Equipe Adriano/Leandro'][m] for m in metricas]
    
    rects1 = ax.bar(x - width/2, valores_julio, width, label='Equipe Julio', color='#3498db')
    rects2 = ax.bar(x + width/2, valores_leandro, width, label='Equipe Adriano/Leandro', color='#9b59b6')
    
    # Personalizar o gráfico
    ax.set_title('Comparativo de Desempenho entre Equipes', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(metricas, rotation=45)
    ax.legend()
    
    # Adicionar valores sobre as barras
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{int(height)}',
                       xy=(rect.get_x() + rect.get_width()/2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom')
    
    autolabel(rects1)
    autolabel(rects2)
    
    plt.tight_layout()
    plt.savefig('docs/images/reports/comparativo_equipes.png', dpi=300, bbox_inches='tight')
    plt.close()

def gerar_grafico_totalizadores():
    print("Gerando gráfico de totalizadores...")
    _, totalizadores = gerar_dados_reais()
    
    # Criar gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Preparar dados
    metricas = list(totalizadores.keys())
    valores = list(totalizadores.values())
    
    # Criar barras horizontais
    colors = ['#27ae60', '#2ecc71', '#16a085', '#f1c40f', '#f39c12']
    bars = ax.barh(metricas, valores, color=colors)
    
    # Personalizar o gráfico
    ax.set_title('Totalizadores Gerais', pad=20)
    ax.invert_yaxis()  # Inverter eixo y para melhor visualização
    
    # Adicionar valores nas barras
    for i, v in enumerate(valores):
        ax.text(v + 0.5, i, str(v), va='center')
    
    plt.tight_layout()
    plt.savefig('docs/images/reports/totalizadores.png', dpi=300, bbox_inches='tight')
    plt.close()

def gerar_grafico_pendencias():
    print("Gerando gráfico de pendências...")
    dados, _ = gerar_dados_reais()
    
    # Preparar dados
    equipes = list(dados.keys())
    pendentes_receptivo = [dados[e]['Pendentes Receptivo'] for e in equipes]
    pendentes_ativo = [dados[e]['Pendentes Ativo'] for e in equipes]
    
    # Criar gráfico de pizza duplo
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
    
    # Gráfico de Pendentes Receptivo
    ax1.pie(pendentes_receptivo, labels=equipes, autopct='%1.1f%%',
            colors=['#3498db', '#9b59b6'])
    ax1.set_title('Distribuição de Pendentes Receptivo')
    
    # Gráfico de Pendentes Ativo
    ax2.pie(pendentes_ativo, labels=equipes, autopct='%1.1f%%',
            colors=['#3498db', '#9b59b6'])
    ax2.set_title('Distribuição de Pendentes Ativo')
    
    plt.tight_layout()
    plt.savefig('docs/images/reports/distribuicao_pendencias.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    print("Gerando gráficos do relatório...")
    
    # Criar diretório se não existir
    import os
    os.makedirs('docs/images/reports', exist_ok=True)
    
    # Gerar todos os gráficos
    gerar_grafico_comparativo_equipes()
    gerar_grafico_totalizadores()
    gerar_grafico_pendencias()
    
    print("Gráficos gerados com sucesso!")
