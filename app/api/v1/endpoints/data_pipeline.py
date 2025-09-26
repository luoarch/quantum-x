"""
Endpoints para Monitoramento do Pipeline de Dados
Conforme DRS seção 5.2 - API RESTful Completa
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime

from app.core.scheduler import DataScheduler
from app.services.data_pipeline.data_pipeline import DataPipeline

router = APIRouter()

# Instâncias globais (em produção, usar injeção de dependência)
scheduler = DataScheduler()
data_pipeline = DataPipeline()

@router.get("/status")
async def get_pipeline_status() -> Dict[str, Any]:
    """
    Obter status do pipeline de dados
    
    Returns:
        Status atual do pipeline e agendador
    """
    try:
        # Status do agendador
        scheduler_status = scheduler.get_scheduler_status()
        
        # Status do pipeline
        cached_data = data_pipeline.get_cached_data()
        pipeline_status = {
            'has_cached_data': cached_data is not None,
            'last_update': cached_data.get('timestamp').isoformat() if cached_data else None,
            'data_age_hours': None
        }
        
        if cached_data and cached_data.get('timestamp'):
            age_seconds = (datetime.now() - cached_data['timestamp']).total_seconds()
            pipeline_status['data_age_hours'] = age_seconds / 3600
        
        return {
            'pipeline': pipeline_status,
            'scheduler': scheduler_status,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")

@router.post("/collect")
async def trigger_data_collection() -> Dict[str, Any]:
    """
    Executar coleta manual de dados
    
    Returns:
        Resultado da coleta de dados
    """
    try:
        result = await scheduler.run_manual_collection()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na coleta de dados: {str(e)}")

@router.post("/analyze-regimes")
async def trigger_regime_analysis() -> Dict[str, Any]:
    """
    Forçar análise de regimes
    
    Returns:
        Resultado da análise de regimes
    """
    try:
        result = await scheduler.force_regime_analysis()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise de regimes: {str(e)}")

@router.get("/data-quality")
async def get_data_quality() -> Dict[str, Any]:
    """
    Obter métricas de qualidade dos dados
    
    Returns:
        Métricas de qualidade dos dados
    """
    try:
        cached_data = data_pipeline.get_cached_data()
        
        if not cached_data:
            raise HTTPException(status_code=404, detail="Nenhum dado em cache")
        
        data_quality = cached_data.get('data_quality', {})
        
        return {
            'data_quality': data_quality,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter qualidade dos dados: {str(e)}")

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Verificação de saúde do pipeline
    
    Returns:
        Status de saúde do sistema
    """
    try:
        # Verificar se agendador está funcionando
        scheduler_status = scheduler.get_scheduler_status()
        scheduler_healthy = scheduler_status['is_running']
        
        # Verificar se há dados recentes
        cached_data = data_pipeline.get_cached_data()
        data_healthy = cached_data is not None
        
        if cached_data and cached_data.get('timestamp'):
            age_hours = (datetime.now() - cached_data['timestamp']).total_seconds() / 3600
            data_healthy = age_hours < 8  # Dados devem ter menos de 8 horas
        
        overall_healthy = scheduler_healthy and data_healthy
        
        return {
            'healthy': overall_healthy,
            'scheduler_healthy': scheduler_healthy,
            'data_healthy': data_healthy,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
