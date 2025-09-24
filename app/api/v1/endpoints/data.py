"""
Endpoints para status e monitoramento de dados
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.robust_data_collector import RobustDataCollector
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status")
async def get_data_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Retorna o status dos dados e fontes
    """
    try:
        # Inicializar coletor
        collector = RobustDataCollector(db)
        
        # Obter status de saúde (método síncrono)
        health_status = collector._health_metrics
        
        return {
            "status": "success",
            "data_sources": {
                "bcb": {
                    "status": "active",
                    "last_success": health_status.get("bcb", {}).get("last_success"),
                    "last_failure": health_status.get("bcb", {}).get("last_failure"),
                    "total_requests": health_status.get("bcb", {}).get("total_requests", 0),
                    "successful_requests": health_status.get("bcb", {}).get("successful_requests", 0),
                    "failed_requests": health_status.get("bcb", {}).get("failed_requests", 0)
                },
                "oecd": {
                    "status": "active",
                    "last_success": health_status.get("oecd", {}).get("last_success"),
                    "last_failure": health_status.get("oecd", {}).get("last_failure"),
                    "total_requests": health_status.get("oecd", {}).get("total_requests", 0),
                    "successful_requests": health_status.get("oecd", {}).get("successful_requests", 0),
                    "failed_requests": health_status.get("oecd", {}).get("failed_requests", 0)
                },
                "fred": {
                    "status": "active",
                    "last_success": health_status.get("fred", {}).get("last_success"),
                    "last_failure": health_status.get("fred", {}).get("last_failure"),
                    "total_requests": health_status.get("fred", {}).get("total_requests", 0),
                    "successful_requests": health_status.get("fred", {}).get("successful_requests", 0),
                    "failed_requests": health_status.get("fred", {}).get("failed_requests", 0)
                }
            },
            "system_health": "healthy" if all(
                health_status.get(source, {}).get("failed_requests", 0) < 5 
                for source in ["bcb", "oecd", "fred"]
            ) else "degraded"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status de dados: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data_sources": {},
            "system_health": "error"
        }

@router.get("/health")
async def get_health_check() -> Dict[str, Any]:
    """
    Health check simples
    """
    return {
        "status": "healthy",
        "message": "Sistema funcionando",
        "timestamp": "2025-09-23T22:00:00Z"
    }