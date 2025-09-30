"""
Endpoints de gerenciamento de modelos
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ...api.schemas import ModelVersion, StandardErrorResponse, ErrorCodes
from ...core.config import get_settings
from ...services.model_service import ModelService

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependência para obter serviço de modelos
def get_model_service() -> ModelService:
    """Obter serviço de modelos"""
    return ModelService()

@router.get(
    "/versions",
    response_model=List[ModelVersion],
    summary="Listar versões de modelos",
    description="Lista todas as versões de modelos disponíveis"
)
async def list_model_versions(
    include_inactive: bool = Query(False, description="Incluir versões inativas"),
    model_service: ModelService = Depends(get_model_service)
):
    """
    Listar versões de modelos disponíveis.
    
    - **include_inactive**: Incluir versões inativas na lista
    """
    try:
        versions = await model_service.list_versions(include_inactive=include_inactive)
        return versions
        
    except Exception as e:
        logger.error(f"Erro ao listar versões: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno ao listar versões de modelos",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.get(
    "/versions/{version}",
    response_model=ModelVersion,
    summary="Obter detalhes de versão",
    description="Obter detalhes de uma versão específica do modelo"
)
async def get_model_version(
    version: str,
    model_service: ModelService = Depends(get_model_service)
):
    """
    Obter detalhes de uma versão específica do modelo.
    
    - **version**: Versão do modelo
    """
    try:
        model_version = await model_service.get_version(version)
        
        if not model_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": ErrorCodes.MODEL_UNAVAILABLE,
                    "message": f"Versão {version} não encontrada",
                    "details": {"requested_version": version}
                }
            )
        
        return model_version
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter versão {version}: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno ao obter versão do modelo",
            details={"error": str(e), "version": version}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.get(
    "/active",
    response_model=ModelVersion,
    summary="Obter versão ativa",
    description="Obter detalhes da versão ativa do modelo"
)
async def get_active_model(
    model_service: ModelService = Depends(get_model_service)
):
    """
    Obter detalhes da versão ativa do modelo.
    """
    try:
        active_model = await model_service.get_active_model()
        
        if not active_model:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error_code": ErrorCodes.MODEL_UNAVAILABLE,
                    "message": "Nenhum modelo ativo encontrado",
                    "details": {"status": "no_active_model"}
                }
            )
        
        return active_model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter modelo ativo: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno ao obter modelo ativo",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.post(
    "/versions/{version}/activate",
    summary="Ativar versão",
    description="Ativar uma versão específica do modelo"
)
async def activate_model_version(
    version: str,
    model_service: ModelService = Depends(get_model_service)
):
    """
    Ativar uma versão específica do modelo.
    
    - **version**: Versão do modelo para ativar
    """
    try:
        success = await model_service.activate_version(version)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": ErrorCodes.MODEL_UNAVAILABLE,
                    "message": f"Versão {version} não encontrada ou não pode ser ativada",
                    "details": {"requested_version": version}
                }
            )
        
        return {
            "message": f"Versão {version} ativada com sucesso",
            "version": version,
            "activated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao ativar versão {version}: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno ao ativar versão do modelo",
            details={"error": str(e), "version": version}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.get(
    "/performance",
    summary="Métricas de performance",
    description="Métricas de performance dos modelos"
)
async def get_model_performance(
    version: Optional[str] = Query(None, description="Versão específica (opcional)"),
    model_service: ModelService = Depends(get_model_service)
):
    """
    Obter métricas de performance dos modelos.
    
    - **version**: Versão específica (opcional, se não informado retorna todas)
    """
    try:
        if version:
            performance = await model_service.get_version_performance(version)
            if not performance:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error_code": ErrorCodes.MODEL_UNAVAILABLE,
                        "message": f"Versão {version} não encontrada",
                        "details": {"requested_version": version}
                    }
                )
        else:
            performance = await model_service.get_all_performance()
        
        return performance
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter performance: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno ao obter métricas de performance",
            details={"error": str(e), "version": version}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.get(
    "/metadata",
    summary="Metadados dos modelos",
    description="Metadados gerais dos modelos"
)
async def get_model_metadata(
    model_service: ModelService = Depends(get_model_service)
):
    """
    Obter metadados gerais dos modelos.
    """
    try:
        metadata = await model_service.get_metadata()
        return metadata
        
    except Exception as e:
        logger.error(f"Erro ao obter metadados: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno ao obter metadados dos modelos",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.get(
    "/capabilities",
    summary="Capacidades dos modelos",
    description="Capacidades e limitações dos modelos"
)
async def get_model_capabilities(
    model_service: ModelService = Depends(get_model_service)
):
    """
    Obter capacidades e limitações dos modelos.
    """
    try:
        capabilities = await model_service.get_capabilities()
        return capabilities
        
    except Exception as e:
        logger.error(f"Erro ao obter capacidades: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno ao obter capacidades dos modelos",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )
