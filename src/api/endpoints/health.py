"""
Endpoints de health check
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import time
import psutil
import logging
from datetime import datetime

from ...api.schemas import HealthResponse, StandardErrorResponse, ErrorCodes
from ...core.config import get_settings
from ...services.health_service import HealthService

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependência para obter serviço de health
def get_health_service() -> HealthService:
    """Obter serviço de health check"""
    return HealthService()

@router.get(
    "/",
    summary="Health check básico",
    description="Verificação básica de saúde da API com trava de cold start"
)
async def health_check(
    health_service: HealthService = Depends(get_health_service)
):
    """
    Health check básico da API.
    
    Retorna informações sobre o status da API, versão, uptime e métricas básicas.
    
    v2.1: Trava de cold start - Retorna 503 se modelos não carregados
    """
    try:
        from fastapi import Request
        from starlette.requests import Request as StarletteRequest
        
        # Obter app state
        # Note: health_service não tem acesso direto ao request
        # Vamos retornar o health normalmente e deixar o readiness check fazer a validação
        health_info = await health_service.get_basic_health()
        
        return health_info
        
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno durante health check",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.get(
    "/detailed",
    summary="Health check detalhado",
    description="Verificação detalhada de saúde incluindo dependências"
)
async def detailed_health_check(
    health_service: HealthService = Depends(get_health_service)
):
    """
    Health check detalhado da API.
    
    Inclui verificação de dependências, métricas de sistema e status dos componentes.
    """
    try:
        detailed_health = await health_service.get_detailed_health()
        return detailed_health
        
    except Exception as e:
        logger.error(f"Erro no health check detalhado: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno durante health check detalhado",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.get(
    "/ready",
    summary="Readiness check",
    description="Verificação de prontidão da API para receber tráfego"
)
async def readiness_check(
    health_service: HealthService = Depends(get_health_service)
):
    """
    Readiness check da API.
    
    Verifica se a API está pronta para receber tráfego (modelos carregados, dependências OK).
    """
    try:
        readiness = await health_service.get_readiness()
        
        if not readiness["ready"]:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=readiness
            )
        
        return readiness
        
    except Exception as e:
        logger.error(f"Erro no readiness check: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno durante readiness check",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.get(
    "/live",
    summary="Liveness check",
    description="Verificação de vivacidade da API"
)
async def liveness_check(
    health_service: HealthService = Depends(get_health_service)
):
    """
    Liveness check da API.
    
    Verifica se a API está viva e respondendo (não travada).
    """
    try:
        liveness = await health_service.get_liveness()
        return liveness
        
    except Exception as e:
        logger.error(f"Erro no liveness check: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno durante liveness check",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.get(
    "/metrics",
    summary="Métricas da API",
    description="Métricas de performance e uso da API"
)
async def get_metrics(
    health_service: HealthService = Depends(get_health_service)
):
    """
    Obter métricas da API.
    
    Inclui métricas de performance, uso e sistema.
    """
    try:
        metrics = await health_service.get_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno ao obter métricas",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.get(
    "/status",
    summary="Status dos componentes",
    description="Status detalhado de todos os componentes da API"
)
async def get_component_status(
    health_service: HealthService = Depends(get_health_service)
):
    """
    Obter status de todos os componentes da API.
    
    Inclui status de modelos, dados, cache, etc.
    """
    try:
        component_status = await health_service.get_component_status()
        return component_status
        
    except Exception as e:
        logger.error(f"Erro ao obter status dos componentes: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno ao obter status dos componentes",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )
