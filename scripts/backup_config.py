"""
Configuração do sistema de backup e redundância
"""

# Configurações de Backup
BACKUP_CONFIG = {
    # Intervalo de sincronização em minutos
    'SYNC_INTERVAL': 5,
    
    # Configurações do SQLite
    'SQLITE': {
        'DB_FILE': 'data/backup.db',
        'AUTO_BACKUP': True,
        'BACKUP_INTERVAL': 30  # minutos
    },
    
    # Configurações do Excel
    'EXCEL': {
        'EXPORT_DIR': 'data/exports',
        'AUTO_EXPORT': True,
        'EXPORT_INTERVAL': 60  # minutos
    },
    
    # Cache em memória
    'CACHE': {
        'ENABLED': True,
        'MAX_AGE': 300,  # segundos
        'CLEANUP_INTERVAL': 600  # segundos
    },
    
    # Configurações de Fallback
    'FALLBACK': {
        'MAX_RETRIES': 3,
        'RETRY_DELAY': 5,  # segundos
        'AUTO_SWITCH': True
    }
}

# Status codes para monitoramento
STATUS_CODES = {
    'OK': 200,
    'SYNCING': 201,
    'USING_CACHE': 202,
    'USING_BACKUP': 203,
    'ERROR': 500,
    'GOOGLE_ERROR': 503
}

# Mensagens de status
STATUS_MESSAGES = {
    200: 'Sistema operando normalmente',
    201: 'Sincronizando dados...',
    202: 'Usando cache local',
    203: 'Usando backup SQLite',
    500: 'Erro interno do sistema',
    503: 'Google Sheets indisponível'
}

# Configurações de notificação
NOTIFICATION_CONFIG = {
    'ENABLED': True,
    'CHANNELS': ['email', 'slack'],
    'PRIORITY_LEVELS': ['low', 'medium', 'high', 'critical'],
    'THROTTLE_INTERVAL': 300  # segundos
}

# Métricas para monitoramento
METRICS = [
    'sync_status',
    'last_sync_time',
    'backup_status',
    'cache_hits',
    'error_count',
    'response_time'
]

# Limites para alertas
ALERT_THRESHOLDS = {
    'sync_delay': 600,  # segundos
    'error_rate': 0.05,  # 5%
    'response_time': 2.0,  # segundos
    'cache_miss_rate': 0.20  # 20%
}
