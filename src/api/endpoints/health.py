"""
Endpoints de health check
v2.1 FINAL - Readiness/Liveness com governança completa
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ...api.schemas import HealthResponse, StandardErrorResponse, ErrorCodes
from ...core.config import get_settings
from ...services.health_service import get_health_service_singleton

logger = logging.getLogger(__name__)
router = APIRouter()

def get_health_service():
    """Obter serviço de health check (singleton)"""
    return get_health_service_singleton()

@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="Health check básico",
    description="Verificação básica de saúde com trava de cold start",
    responses={
        200: {"description": "API saudável e modelos carregados"},
        503: {"description": "Modelos não carregados (cold start)"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    }
)
async def health_check(
    request: Request,
    response: Response,
    health_service = Depends(get_health_service)
):
    """
    Health check com cold start gate
    
    Retorna 503 se modelos não estiverem carregados no app.state
    """
    try:
        # Método síncrono - SEM await
        basic = health_service.get_basic_health()
        
        # Cold start gate: verificar se modelos estão carregados
        model_lp = getattr(request.app.state, "model_lp", None)
        model_bvar = getattr(request.app.state, "model_bvar", None)
        models_loaded = model_lp is not None or model_bvar is not None
        
        # Enriquecer com info de modelos
        basic_dict = basic.model_dump() if hasattr(basic, 'model_dump') else basic
        basic_dict["models_loaded"] = models_loaded
        
        # Headers
        model_version = getattr(request.app.state, "model_version", "none")
        response.headers["X-Active-Model-Version"] = model_version
        response.headers["X-Models-Loaded"] = str(models_loaded)
        
        # Retornar 503 se modelos não carregados
        if not models_loaded:
            logger.warning(
                "Health check: modelos não carregados (cold start)",
                extra={"action": "health", "models_loaded": False, "status": 503}
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=basic_dict,
                headers=response.headers
            )
        
        # Log estruturado
        logger.info(
            "Health check OK",
            extra={
                "action": "health",
                "models_loaded": True,
                "model_version": model_version,
                "status": "healthy",
                "success": True
            }
        )
        
        return basic_dict
        
    except Exception as e:
        logger.error(
            "Erro no health check",
            exc_info=True,
            extra={"action": "health", "success": False, "error_type": type(e).__name__}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "message": "Erro interno durante health check"
            }
        )

@router.get(
    "/detailed",
    summary="Health check detalhado",
    description="Verificação detalhada incluindo dependências e componentes",
    responses={
        200: {"description": "Status detalhado da API"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    }
)
async def detailed_health_check(
    response: Response,
    health_service: HealthService = Depends(get_health_service)
):
    """Health check detalhado"""
    try:
        # Método síncrono - SEM await
        detailed_health = health_service.get_detailed_health()
        
        # Headers
        if "model_version" in detailed_health:
            response.headers["X-Active-Model-Version"] = detailed_health["model_version"]
        
        logger.info(
            "Health check detalhado",
            extra={"action": "health_detailed", "success": True}
        )
        
        return detailed_health
        
    except Exception as e:
        logger.error(
            "Erro no health check detalhado",
            exc_info=True,
            extra={"action": "health_detailed", "success": False, "error_type": type(e).__name__}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": ErrorCodes.INTERNAL_ERROR, "message": "Erro interno"}
        )

@router.get(
    "/ready",
    summary="Readiness probe",
    description="Verificação de prontidão para Kubernetes (modelos carregados, deps OK)",
    responses={
        200: {"description": "Pronto para receber tráfego"},
        503: {"model": StandardErrorResponse, "description": "Não pronto (aguardar)"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    }
)
async def readiness_check(
    response: Response,
    health_service: HealthService = Depends(get_health_service)
):
    """
    Readiness probe (Kubernetes-compatible)
    
    Retorna 503 até que modelos estejam carregados e dependências OK
    """
    try:
        # Método síncrono - SEM await
        readiness = health_service.get_readiness()
        
        # Headers de governança (padronizados)
        if "active_version" in readiness:
            response.headers["X-Active-Model-Version"] = readiness["active_version"]
        if "uptime_seconds" in readiness:
            response.headers["X-Uptime-Seconds"] = str(round(readiness["uptime_seconds"], 2))
        if "models_loaded" in readiness:
            response.headers["X-Models-Loaded"] = str(readiness["models_loaded"])
        
        # Log estruturado
        logger.info(
            "Readiness check",
            extra={
                "action": "readiness",
                "ready": readiness.get("ready", False),
                "models_loaded": readiness.get("models_loaded", False),
                "success": True
            }
        )
        
        # Retornar 503 se não pronto
        if not readiness.get("ready", False):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=readiness,
                headers=response.headers
            )
        
        return readiness
        
    except Exception as e:
        logger.error(
            "Erro no readiness check",
            exc_info=True,
            extra={"action": "readiness", "success": False, "error_type": type(e).__name__}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": ErrorCodes.INTERNAL_ERROR, "message": "Erro interno"}
        )

@router.get(
    "/live",
    summary="Liveness probe",
    description="Verificação de vivacidade para Kubernetes (resposta rápida, sem I/O)",
    responses={
        200: {"description": "API viva e respondendo"},
        500: {"model": StandardErrorResponse, "description": "API travada"}
    }
)
async def liveness_check(
    health_service: HealthService = Depends(get_health_service)
):
    """
    Liveness probe (Kubernetes-compatible)
    
    Sempre retorna 200 rapidamente se API está rodando.
    NÃO consulta dependências externas.
    """
    try:
        # Liveness minimalista - sem I/O externo (síncrono)
        liveness = health_service.get_liveness()
        
        logger.debug(
            "Liveness check",
            extra={"action": "liveness", "alive": True}
        )
        
        return liveness
        
    except Exception as e:
        logger.error(
            "Erro no liveness check (API travada?)",
            exc_info=True,
            extra={"action": "liveness", "alive": False, "error_type": type(e).__name__}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": ErrorCodes.INTERNAL_ERROR, "message": "API travada"}
        )

@router.get(
    "/metrics",
    summary="Métricas Prometheus",
    description="Métricas de performance (latência p50/p95/p99), uso e sistema (CPU%, RSS MB)",
    responses={
        200: {"description": "Métricas atuais (unidades no payload)"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    }
)
async def get_metrics(
    response: Response,
    health_service: HealthService = Depends(get_health_service)
):
    """
    Métricas Prometheus-compatible
    
    Inclui: latências, throughput, códigos de erro, CPU, memória
    """
    try:
        # Método síncrono - SEM await
        metrics = health_service.get_metrics()
        
        # Headers
        if "model_version" in metrics:
            response.headers["X-Active-Model-Version"] = metrics["model_version"]
        
        logger.info(
            "Métricas obtidas",
            extra={
                "action": "get_metrics",
                "n_metrics": len(metrics),
                "success": True
            }
        )
        
        return metrics
        
    except Exception as e:
        logger.error(
            "Erro ao obter métricas",
            exc_info=True,
            extra={"action": "get_metrics", "success": False, "error_type": type(e).__name__}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": ErrorCodes.INTERNAL_ERROR, "message": "Erro ao obter métricas"}
        )

@router.get(
    "/status",
    summary="Status dos componentes",
    description="Status detalhado: modelos, dados, cache (com evidências de rastreabilidade)",
    responses={
        200: {"description": "Status de todos os componentes"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    }
)
async def get_component_status(
    response: Response,
    health_service: HealthService = Depends(get_health_service)
):
    """
    Status detalhado dos componentes
    
    Inclui: models (versão, hash), data (last_update), cache (size)
    """
    try:
        # Método síncrono - SEM await
        component_status = health_service.get_component_status()
        
        # Headers de evidência
        if "models" in component_status and "active_version" in component_status["models"]:
            response.headers["X-Active-Model-Version"] = component_status["models"]["active_version"]
        
        logger.info(
            "Status dos componentes",
            extra={
                "action": "component_status",
                "n_components": len(component_status),
                "success": True
            }
        )
        
        return component_status
        
    except Exception as e:
        logger.error(
            "Erro ao obter status dos componentes",
            exc_info=True,
            extra={"action": "component_status", "success": False, "error_type": type(e).__name__}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": ErrorCodes.INTERNAL_ERROR, "message": "Erro interno"}
        )
