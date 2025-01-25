from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from ...services.data_service import DataService
from ...models.metrics import DailyMetrics

router = APIRouter()

@router.get("/daily", response_model=DailyMetrics)
async def get_daily_metrics(
    date: datetime,
    team: Optional[str] = None,
    data_service: DataService = Depends()
):
    """
    Retorna métricas diárias para uma data específica
    
    Args:
        date: Data para buscar métricas
        team: Equipe específica (opcional)
        data_service: Serviço de dados (injetado automaticamente)
    """
    try:
        return data_service.get_daily_metrics(date, team)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teams", response_model=List[str])
async def get_teams(data_service: DataService = Depends()):
    """
    Retorna lista de equipes disponíveis
    """
    try:
        return data_service.get_teams()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/date-range")
async def get_date_range(data_service: DataService = Depends()):
    """
    Retorna o intervalo de datas disponível nos dados
    """
    try:
        start_date, end_date = data_service.get_date_range()
        return {
            "start_date": start_date,
            "end_date": end_date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
