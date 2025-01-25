import psutil
import requests
import logging
import time
import json
from datetime import datetime
import os
from pathlib import Path

# Configuração do logger
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'monitor.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

class SystemMonitor:
    def __init__(self):
        self.backend_url = 'http://localhost:5000'
        self.frontend_url = 'http://localhost:3002'
        self.thresholds = {
            'cpu_percent': 80,
            'memory_percent': 80,
            'response_time': 2.0  # segundos
        }
        self.anomaly_count = 0
        self.check_interval = 30  # segundos

    def check_process(self, process_name):
        """Verifica se um processo está rodando e seu consumo de recursos"""
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    return {
                        'pid': proc.pid,
                        'cpu_percent': proc.cpu_percent(),
                        'memory_percent': proc.memory_percent()
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return None

    def check_endpoint(self, url):
        """Verifica se um endpoint está respondendo"""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=5)
            response_time = time.time() - start_time
            return {
                'status_code': response.status_code,
                'response_time': response_time
            }
        except requests.RequestException:
            return None

    def log_anomaly(self, component, issue, details):
        """Registra uma anomalia no sistema"""
        self.anomaly_count += 1
        logging.warning(f"Anomalia #{self.anomaly_count} - {component}: {issue}")
        logging.warning(f"Detalhes: {json.dumps(details, indent=2)}")

        # Se houver muitas anomalias em sequência, aumenta o intervalo de checagem
        if self.anomaly_count > 5:
            self.check_interval = min(300, self.check_interval * 1.5)  # máximo 5 minutos
            logging.info(f"Intervalo de checagem aumentado para {self.check_interval}s")

    def monitor(self):
        """Executa o monitoramento contínuo"""
        logging.info("Iniciando monitoramento do sistema...")
        
        while True:
            try:
                # Verifica processos
                python_proc = self.check_process('python')
                node_proc = self.check_process('node')

                # Verifica endpoints
                backend_status = self.check_endpoint(self.backend_url)
                frontend_status = self.check_endpoint(self.frontend_url)

                # Analisa resultados
                if python_proc:
                    if python_proc['cpu_percent'] > self.thresholds['cpu_percent']:
                        self.log_anomaly('Backend', 'Alto uso de CPU', python_proc)
                    if python_proc['memory_percent'] > self.thresholds['memory_percent']:
                        self.log_anomaly('Backend', 'Alto uso de memória', python_proc)
                else:
                    self.log_anomaly('Backend', 'Processo não encontrado', {})

                if node_proc:
                    if node_proc['cpu_percent'] > self.thresholds['cpu_percent']:
                        self.log_anomaly('Frontend', 'Alto uso de CPU', node_proc)
                    if node_proc['memory_percent'] > self.thresholds['memory_percent']:
                        self.log_anomaly('Frontend', 'Alto uso de memória', node_proc)
                else:
                    self.log_anomaly('Frontend', 'Processo não encontrado', {})

                if backend_status:
                    if backend_status['response_time'] > self.thresholds['response_time']:
                        self.log_anomaly('Backend', 'Tempo de resposta alto', backend_status)
                else:
                    self.log_anomaly('Backend', 'Endpoint não responde', {})

                if frontend_status:
                    if frontend_status['response_time'] > self.thresholds['response_time']:
                        self.log_anomaly('Frontend', 'Tempo de resposta alto', frontend_status)
                else:
                    self.log_anomaly('Frontend', 'Endpoint não responde', {})

                # Se não houver anomalias, reseta o contador
                if self.anomaly_count == 0:
                    self.check_interval = 30  # reseta para o intervalo padrão

                time.sleep(self.check_interval)

            except Exception as e:
                logging.error(f"Erro no monitoramento: {str(e)}")
                time.sleep(self.check_interval)

if __name__ == '__main__':
    monitor = SystemMonitor()
    monitor.monitor()
