"""
Endpoints de gerenciamento de modelos
v2.1 FINAL - Governança perfeita com contratos explícitos
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

# Import completo de schemas
from ...api.schemas import StandardErrorResponse, ErrorCodes, ModelVersion
from ...core.config import get_settings
from ...services.model_service import get_model_service, ModelService

logger = logging.getLogger(__name__)
router = APIRouter()

def get_service() -> ModelService:
    """Obter serviço de modelos (singleton thread-safe)"""
    return get_model_service()

@router.get(
    "/versions",
    response_model=List[Dict[str, Any]],  # Retorna dicts, não ModelVersion
    summary="Listar versões de modelos",
    description="Lista todas as versões de modelos disponíveis com metadados completos",
    responses={
        200: {"description": "Lista de versões retornada com sucesso"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    }
)
async def list_model_versions(
    include_inactive: bool = Query(False, description="Incluir versões inativas"),
    response: Response,
    model_service: ModelService = Depends(get_service)
):
    """Listar todas as versões disponíveis"""
    try:
        versions = model_service.list_versions(include_inactive=include_inactive)
        
        # Header padronizado
        active = model_service.get_active_version()
        if active:
            response.headers["X-Active-Model-Version"] = active
        
        # Log estruturado
        logger.info(
            "Listagem de versões",
            extra={
                "action": "list_versions",
                "n_versions": len(versions),
                "include_inactive": include_inactive,
                "active_version": active,
                "success": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return versions
        
    except Exception as e:
        logger.error(
            "Erro ao listar versões",
            exc_info=True,
            extra={"action": "list_versions", "success": False, "error_type": type(e).__name__}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": ErrorCodes.INTERNAL_ERROR, "message": "Erro ao listar versões"}
        )

@router.get(
    "/versions/{version}",
    response_model=Dict[str, Any],
    summary="Obter detalhes de versão",
    description="Obter detalhes completos de uma versão específica do modelo",
    responses={
        200: {"description": "Detalhes da versão"},
        404: {"model": StandardErrorResponse, "description": "Versão não encontrada"},
        422: {"model": StandardErrorResponse, "description": "Formato de versão inválido"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    }
)
async def get_model_version(
    version: str,
    response: Response,
    model_service: ModelService = Depends(get_service)
):
    """Obter detalhes de versão específica"""
    try:
        # Sanitização
        if not version.startswith("v"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "validation_error",
                    "message": "Formato de versão inválido (deve começar com 'v')",
                    "details": {"received": version, "expected_format": "v1.0.0"}
                }
            )
        
        model_version = model_service.get_version(version)
        
        if not model_version:
            logger.warning(
                f"Versão {version} não encontrada",
                extra={"action": "get_version", "version": version, "success": False}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": ErrorCodes.MODEL_UNAVAILABLE,
                    "message": f"Versão {version} não encontrada"
                }
            )
        
        # Headers padronizados
        active = model_service.get_active_version()
        if active:
            response.headers["X-Active-Model-Version"] = active
        response.headers["X-Requested-Version"] = version
        
        # Log estruturado
        logger.info(
            "Detalhes de versão obtidos",
            extra={"action": "get_version", "version": version, "active": active, "success": True}
        )
        
        return model_version
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao obter versão {version}",
            exc_info=True,
            extra={"action": "get_version", "version": version, "success": False, "error_type": type(e).__name__}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": ErrorCodes.INTERNAL_ERROR, "message": "Erro interno"}
        )

@router.get(
    "/active",
    response_model=Dict[str, Any],
    summary="Obter versão ativa",
    description="Obter detalhes da versão ativa do modelo",
    responses={
        200: {"description": "Versão ativa retornada"},
        503: {"model": StandardErrorResponse, "description": "Nenhum modelo ativo"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    }
)
async def get_active_model(
    response: Response,
    model_service: ModelService = Depends(get_service)
):
    """Obter versão ativa do modelo"""
    try:
        active_version_str = model_service.get_active_version()
        
        if not active_version_str:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error_code": ErrorCodes.MODEL_UNAVAILABLE,
                    "message": "Nenhum modelo ativo encontrado"
                }
            )
        
        active_model = model_service.get_version(active_version_str)
        
        # Header padronizado
        response.headers["X-Active-Model-Version"] = active_version_str
        
        # Log estruturado
        logger.info(
            "Versão ativa obtida",
            extra={"action": "get_active", "version": active_version_str, "success": True}
        )
        
        return active_model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Erro ao obter modelo ativo",
            exc_info=True,
            extra={"action": "get_active", "success": False, "error_type": type(e).__name__}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": ErrorCodes.INTERNAL_ERROR, "message": "Erro interno"}
        )

@router.post(
    "/versions/{version}/activate",
    summary="Ativar versão do modelo",
    description="Ativar uma versão específica do modelo (operação idempotente)",
    responses={
        200: {"description": "Versão ativada com sucesso (ou já estava ativa)"},
        404: {"model": StandardErrorResponse, "description": "Versão não encontrada"},
        409: {"model": StandardErrorResponse, "description": "Conflito: self-check falhou"},
        422: {"model": StandardErrorResponse, "description": "Formato de versão inválido"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    }
)
async def activate_model_version(
    version: str,
    response: Response,
    model_service: ModelService = Depends(get_service)
):
    """
    Ativar versão específica (idempotente)
    
    - Retorna 200 mesmo se já ativa (idempotente)
    - Retorna 404 se versão não existe
    - Retorna 409 se existe mas falha self-check
    """
    try:
        # Sanitização
        if not version.startswith("v"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error_code": "validation_error", "message": "Formato de versão inválido"}
            )
        
        # Idempotência
        active = model_service.get_active_version()
        if active == version:
            logger.info(
                "Versão já ativa (idempotente)",
                extra={"action": "activate", "version": version, "idempotent": True, "success": True}
            )
            
            response.headers["X-Active-Model-Version"] = version
            
            return {
                "message": f"Versão {version} já está ativa",
                "version": version,
                "idempotent": True,
                "activated_at": datetime.utcnow().isoformat() + 'Z'
            }
        
        # Ativar
        success = model_service.set_active_version(version)
        
        if not success:
            # Distinguir 404 vs 409
            exists = model_service.get_version(version)
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error_code": ErrorCodes.MODEL_UNAVAILABLE, "message": f"Versão {version} não encontrada"}
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error_code": "activation_conflict", "message": f"Versão {version} falhou no self-check"}
                )
        
        # Sucesso
        logger.info(
            "Versão ativada",
            extra={"action": "activate", "version": version, "previous": active, "success": True}
        )
        
        response.headers["X-Active-Model-Version"] = version
        
        return {
            "message": f"Versão {version} ativada com sucesso",
            "version": version,
            "previous_version": active,
            "activated_at": datetime.utcnow().isoformat() + 'Z'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao ativar {version}",
            exc_info=True,
            extra={"action": "activate", "version": version, "success": False, "error_type": type(e).__name__}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": ErrorCodes.INTERNAL_ERROR, "message": "Erro interno"}
        )

@router.get(
    "/capabilities",
    summary="Capacidades dos modelos",
    description="Capacidades e limitações dos modelos (estáticas e dinâmicas)",
    responses={
        200: {"description": "Capacidades dos modelos"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    }
)
async def get_model_capabilities(
    include_dynamic: bool = Query(True, description="Incluir informações dinâmicas do modelo carregado"),
    response: Response,
    model_service: ModelService = Depends(get_service)
):
    """Obter capacidades"""
    try:
        capabilities = model_service.get_capabilities(include_dynamic=include_dynamic)
        
        # Header padronizado
        if include_dynamic and 'dynamic' in capabilities:
            active = capabilities['dynamic'].get('active_version')
            if active:
                response.headers["X-Active-Model-Version"] = active
        elif not include_dynamic:
            active = model_service.get_active_version()
            if active:
                response.headers["X-Active-Model-Version"] = active
        
        # Log
        logger.info(
            "Capabilities obtidas",
            extra={"action": "get_capabilities", "include_dynamic": include_dynamic, "success": True}
        )
        
        return capabilities
        
    except Exception as e:
        logger.error(
            "Erro ao obter capabilities",
            exc_info=True,
            extra={"action": "get_capabilities", "success": False, "error_type": type(e).__name__}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": ErrorCodes.INTERNAL_ERROR, "message": "Erro interno"}
        )

@router.get(
    "/cache",
    summary="Informações do cache",
    description="Informações sobre modelos em cache (diagnóstico)",
    responses={
        200: {"description": "Informações do cache"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    }
)
async def get_cache_info(
    response: Response,
    model_service: ModelService = Depends(get_service)
):
    """Obter informações do cache"""
    try:
        cache_info = model_service.get_cache_info()
        
        # Header padronizado em TODOS os endpoints
        active = model_service.get_active_version()
        if active:
            response.headers["X-Active-Model-Version"] = active
        
        # Log
        logger.info(
            "Cache info obtida",
            extra={
                "action": "get_cache_info",
                "cache_size": cache_info['cache_size'],
                "max_size": cache_info['max_cache_size'],
                "active": active,
                "success": True
            }
        )
        
        return cache_info
        
    except Exception as e:
        logger.error(
            "Erro ao obter cache info",
            exc_info=True,
            extra={"action": "get_cache_info", "success": False, "error_type": type(e).__name__}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": ErrorCodes.INTERNAL_ERROR, "message": "Erro interno"}
        )
