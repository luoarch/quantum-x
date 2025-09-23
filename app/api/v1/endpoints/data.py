"""
Endpoints para coleta e consulta de dados
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.robust_data_collector import RobustDataCollector
from app.models.time_series import EconomicSeries, DataCollectionLog
from app.schemas.data import DataCollectionResponse, SeriesDataResponse

router = APIRouter()


@router.post("/collect", response_model=DataCollectionResponse)
async def collect_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Inicia coleta de dados das APIs externas"""
    try:
        collector = RobustDataCollector(db)
        
        # Executar coleta em background
        result = await collector.collect_all_series()
        
        return DataCollectionResponse(
            status="success",
            message="Coleta de dados iniciada com sucesso",
            total_records=result.get('total_records', 0),
            sources=result.get('sources', {}),
            collected_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na coleta de dados: {str(e)}")


@router.get("/series", response_model=List[SeriesDataResponse])
async def get_series_data(
    source: Optional[str] = None,
    country: Optional[str] = None,
    series_name: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Consulta séries de dados econômicos"""
    try:
        query = db.query(EconomicSeries)
        
        # Aplicar filtros
        if source:
            query = query.filter(EconomicSeries.source == source)
        if country:
            query = query.filter(EconomicSeries.country == country)
        if series_name:
            query = query.filter(EconomicSeries.series_name.ilike(f"%{series_name}%"))
        
        # Ordenar por data decrescente e limitar
        series = query.order_by(EconomicSeries.date.desc()).limit(limit).all()
        
        return [
            SeriesDataResponse(
                id=item.id,
                series_code=item.series_code,
                series_name=item.series_name,
                source=item.source,
                country=item.country,
                date=item.date,
                value=item.value,
                unit=item.unit,
                frequency=item.frequency,
                last_updated=item.last_updated
            )
            for item in series
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar dados: {str(e)}")


@router.get("/series/{series_code}")
async def get_series_by_code(
    series_code: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Consulta série específica por código"""
    try:
        query = db.query(EconomicSeries).filter(EconomicSeries.series_code == series_code)
        
        # Aplicar filtros de data
        if start_date:
            query = query.filter(EconomicSeries.date >= start_date)
        if end_date:
            query = query.filter(EconomicSeries.date <= end_date)
        
        series = query.order_by(EconomicSeries.date.desc()).all()
        
        if not series:
            raise HTTPException(status_code=404, detail="Série não encontrada")
        
        return {
            "series_code": series_code,
            "series_name": series[0].series_name,
            "source": series[0].source,
            "country": series[0].country,
            "unit": series[0].unit,
            "frequency": series[0].frequency,
            "data_points": len(series),
            "data": [
                {
                    "date": item.date.isoformat(),
                    "value": item.value
                }
                for item in series
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar série: {str(e)}")


@router.get("/collection-log")
async def get_collection_log(
    source: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Consulta log de coleta de dados"""
    try:
        query = db.query(DataCollectionLog)
        
        # Aplicar filtros
        if source:
            query = query.filter(DataCollectionLog.source == source)
        if status:
            query = query.filter(DataCollectionLog.status == status)
        
        logs = query.order_by(DataCollectionLog.collected_at.desc()).limit(limit).all()
        
        return [
            {
                "id": log.id,
                "source": log.source,
                "series_code": log.series_code,
                "status": log.status,
                "records_collected": log.records_collected,
                "error_message": log.error_message,
                "execution_time": log.execution_time,
                "collected_at": log.collected_at.isoformat()
            }
            for log in logs
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar log: {str(e)}")


@router.get("/stats")
async def get_data_stats(db: Session = Depends(get_db)):
    """Estatísticas dos dados coletados"""
    try:
        # Contar registros por fonte
        bcb_count = db.query(EconomicSeries).filter(EconomicSeries.source == "BCB").count()
        oecd_count = db.query(EconomicSeries).filter(EconomicSeries.source == "OECD").count()
        ipea_count = db.query(EconomicSeries).filter(EconomicSeries.source == "IPEA").count()
        
        # Última coleta
        last_collection = db.query(DataCollectionLog).order_by(
            DataCollectionLog.collected_at.desc()
        ).first()
        
        # Séries disponíveis
        series_list = db.query(EconomicSeries.series_name, EconomicSeries.source).distinct().all()
        
        return {
            "total_records": bcb_count + oecd_count + ipea_count,
            "by_source": {
                "BCB": bcb_count,
                "OECD": oecd_count,
                "IPEA": ipea_count
            },
            "available_series": [
                {"name": item.series_name, "source": item.source}
                for item in series_list
            ],
            "last_collection": {
                "source": last_collection.source if last_collection else None,
                "status": last_collection.status if last_collection else None,
                "collected_at": last_collection.collected_at.isoformat() if last_collection else None,
                "records": last_collection.records_collected if last_collection else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar estatísticas: {str(e)}")
