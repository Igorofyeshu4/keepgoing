from pydantic import BaseModel
from datetime import datetime

class DailyMetrics(BaseModel):
    """Modelo para métricas diárias"""
    date: datetime
    team: str | None = None
    resolvidos: int = 0
    pendente_ativo: int = 0
    pendente_receptivo: int = 0
    prioridade: int = 0
    prioridade_total: int = 0
    soma_prioridades: float = 0
    analise: int = 0
    analise_dia: int = 0
    receptivo: int = 0
    quitado_cliente: int = 0
    quitado: int = 0
    aprovados: int = 0

    class Config:
        from_attributes = True
