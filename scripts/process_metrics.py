"""
Processamento de métricas a partir da planilha de demandas
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

class DemandMetricsProcessor:
    def __init__(self, excel_file):
        self.df = pd.read_excel(excel_file)
        self.df['DATA'] = pd.to_datetime(self.df['DATA'])
        self.today = datetime.now().date()
        self.equipes = {
            'julio': [
                'POLIANA', 'THALISSON', 'BRUNO MARIANO', 'ALANA', 'ISABELLA',
                'BRUNA RAQUEL', 'FABIANA', 'LETICIA', 'MONYZA', 'VICTOR ADRIANO',
                'ELISANGELA', 'ELIZABETE', 'ADRIANO', 'ALINE', 'NUNO', 'MATHEUS',
                'YURI', 'FELIPE', 'ANA LIDIA', 'JULIANE', 'IGOR', 'LUARA',
                'ANA GESSICA', 'GEOVANNA'
            ],
            'leandro': [
                'ALINE', 'MATHEUS', 'VITORIA', 'VICTOR ADRIANO', 'NUNO', 'KATIA',
                'YURI', 'ELIZABETE', 'MONYZA', 'FABIANA', 'ISABELLA', 'LETICIA',
                'BRUNO MARIANO', 'ALANA', 'ADRIANO', 'ITAYNNARA', 'AMANDA SANTANA',
                'MARIA BRUNA', 'EDIANE', 'GREICY', 'JULIANA', 'IZABEL',
                'ALINE SALVADOR', 'SOFIA', 'JULIA', 'GEOVANNA', 'FELIPE'
            ]
        }

    def process_metrics(self):
        """Processa todas as métricas e retorna o resultado em formato JSON"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'geral': self.get_metricas_gerais(),
            'julio': self.get_metricas_equipe('julio'),
            'leandro': self.get_metricas_equipe('leandro'),
            'insights': self.generate_insights()
        }
        
        # Criar diretório data se não existir
        os.makedirs('data', exist_ok=True)
        
        # Salvar métricas em JSON
        with open('data/metrics.json', 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        return metrics

    def get_metricas_gerais(self):
        """Calcula métricas gerais do sistema"""
        total_demandas = len(self.df)
        resolvidas = len(self.df[self.df['STATUS'] == 'RESOLVIDO'])
        
        return {
            'total_demandas': total_demandas,
            'resolvidas': resolvidas,
            'taxa_geral': round((resolvidas / total_demandas) * 100, 1),
            'total_receptivo': len(self.df[self.df['TIPO'] == 'RECEPTIVO']),
            'total_ativo': len(self.df[self.df['TIPO'] == 'ATIVO'])
        }

    def get_metricas_equipe(self, equipe_nome):
        """Calcula métricas para uma equipe específica"""
        equipe_df = self.df[self.df['RESPONSÁVEL'].isin(self.equipes[equipe_nome])]
        
        # Métricas básicas
        total = len(equipe_df)
        resolvidas = len(equipe_df[equipe_df['STATUS'] == 'RESOLVIDO'])
        
        # Métricas por tipo
        receptivo = len(equipe_df[equipe_df['TIPO'] == 'RECEPTIVO'])
        ativo = len(equipe_df[equipe_df['TIPO'] == 'ATIVO'])
        pendentes_receptivo = len(equipe_df[
            (equipe_df['TIPO'] == 'RECEPTIVO') & 
            (equipe_df['STATUS'] != 'RESOLVIDO')
        ])
        pendentes_ativo = len(equipe_df[
            (equipe_df['TIPO'] == 'ATIVO') & 
            (equipe_df['STATUS'] != 'RESOLVIDO')
        ])
        
        # Métricas por dia
        demandas_dia = equipe_df.groupby(equipe_df['DATA'].dt.date).size().to_dict()
        demandas_dia = {k.isoformat(): v for k, v in demandas_dia.items()}
        
        # Métricas por responsável
        responsaveis = {}
        for resp in self.equipes[equipe_nome]:
            resp_df = equipe_df[equipe_df['RESPONSÁVEL'] == resp]
            if len(resp_df) > 0:
                resp_resolvidas = len(resp_df[resp_df['STATUS'] == 'RESOLVIDO'])
                dias_ativos = len(resp_df['DATA'].dt.date.unique())
                responsaveis[resp] = {
                    'total': len(resp_df),
                    'resolvidas': resp_resolvidas,
                    'taxa_resolucao': round((resp_resolvidas / len(resp_df)) * 100, 1),
                    'media_diaria': round(len(resp_df) / max(dias_ativos, 1), 1),
                    'dias_ativos': dias_ativos,
                    'receptivo': len(resp_df[resp_df['TIPO'] == 'RECEPTIVO']),
                    'ativo': len(resp_df[resp_df['TIPO'] == 'ATIVO'])
                }
        
        return {
            'total': total,
            'resolvidas': resolvidas,
            'taxa_resolucao': round((resolvidas / total) * 100, 1) if total > 0 else 0,
            'receptivo': receptivo,
            'ativo': ativo,
            'pendentes_receptivo': pendentes_receptivo,
            'pendentes_ativo': pendentes_ativo,
            'demandas_dia': demandas_dia,
            'responsaveis': responsaveis
        }

    def generate_insights(self):
        """Gera insights baseados nas métricas"""
        insights = []
        
        # Analisar cada equipe
        for equipe_nome in ['julio', 'leandro']:
            equipe_metrics = self.get_metricas_equipe(equipe_nome)
            
            # Verificar taxa de resolução geral da equipe
            if equipe_metrics['taxa_resolucao'] < 30:
                insights.append({
                    'equipe': f'Equipe {equipe_nome.title()}',
                    'insight': f'Taxa de resolução baixa: {equipe_metrics["taxa_resolucao"]}%',
                    'acao': 'Verificar gargalos e distribuir demandas',
                    'impacto': 'ALTO'
                })
            
            # Analisar métricas por responsável
            for resp, metricas in equipe_metrics['responsaveis'].items():
                # Alta carga diária
                if metricas['media_diaria'] > 10:
                    insights.append({
                        'equipe': f'Equipe {equipe_nome.title()}',
                        'responsavel': resp,
                        'insight': f'Alta carga diária: {metricas["media_diaria"]} demandas/dia',
                        'acao': 'Redistribuir demandas',
                        'impacto': 'ALTO'
                    })
                
                # Baixa taxa de resolução individual
                if metricas['taxa_resolucao'] < 25:
                    insights.append({
                        'equipe': f'Equipe {equipe_nome.title()}',
                        'responsavel': resp,
                        'insight': f'Baixa taxa de resolução: {metricas["taxa_resolucao"]}%',
                        'acao': 'Verificar dificuldades e oferecer suporte',
                        'impacto': 'MEDIO'
                    })
                
                # Desbalanceamento entre receptivo e ativo
                total = metricas['receptivo'] + metricas['ativo']
                if total > 5:  # Apenas para quem tem volume significativo
                    if metricas['receptivo'] / total > 0.8:
                        insights.append({
                            'equipe': f'Equipe {equipe_nome.title()}',
                            'responsavel': resp,
                            'insight': 'Concentração alta em demandas receptivas',
                            'acao': 'Balancear com demandas ativas',
                            'impacto': 'MEDIO'
                        })
                    elif metricas['ativo'] / total > 0.8:
                        insights.append({
                            'equipe': f'Equipe {equipe_nome.title()}',
                            'responsavel': resp,
                            'insight': 'Concentração alta em demandas ativas',
                            'acao': 'Balancear com demandas receptivas',
                            'impacto': 'MEDIO'
                        })
        
        return insights

def main():
    # Encontrar o arquivo Excel mais recente no diretório docs
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
    excel_files = [f for f in os.listdir(docs_dir) if f.startswith('_DEMANDAS') and f.endswith('.xlsx')]
    if not excel_files:
        raise FileNotFoundError("Nenhum arquivo de demandas encontrado no diretório docs/")
    
    latest_file = max(excel_files, key=lambda x: os.path.getmtime(os.path.join(docs_dir, x)))
    excel_path = os.path.join(docs_dir, latest_file)
    
    # Processar métricas
    processor = DemandMetricsProcessor(excel_path)
    metrics = processor.process_metrics()
    
    print(f"Métricas processadas com sucesso. Arquivo gerado: data/metrics.json")
    print(f"\nResumo das métricas:")
    print(f"Total de demandas: {metrics['geral']['total_demandas']}")
    print(f"Taxa de resolução geral: {metrics['geral']['taxa_geral']}%")
    print(f"Insights gerados: {len(metrics['insights'])}")

if __name__ == '__main__':
    main()
