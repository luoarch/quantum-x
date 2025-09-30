"""
Model Controller - Single Responsibility Principle
Controller responsável pelos endpoints de modelos
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime

from src.core.models import ModelVersion, ModelMetadata
from src.api.schemas import ModelVersion as ModelVersionSchema

class ModelController:
    """
    Controller para endpoints de modelos
    
    Responsabilidades:
    - GET /models/versions
    - GET /models/{version}
    - GET /models/{version}/performance
    - Gerenciamento de versões de modelo
    """
    
    def __init__(self):
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configurar rotas do controller"""
        
        @self.router.get(
            "/models/versions",
            response_model=List[ModelVersionSchema],
            status_code=status.HTTP_200_OK,
            summary="Listar Versões de Modelos",
            description="Lista todas as versões de modelos disponíveis com metadados"
        )
        async def list_model_versions(service_factory = Depends()):
            """Listar versões de modelos"""
            try:
                # TODO: Implementar obtenção real de versões de modelos
                # Por enquanto, retornar versão mock
                mock_versions = [
                    ModelVersionSchema(
                        version="v1.0.0",
                        trained_at="2025-09-25T12:00:00Z",
                        data_hash="sha256:abcd1234...",
                        methodology="LP primary, BVAR fallback",
                        n_observations=20,
                        r_squared=0.65,
                        backtest_metrics={
                            "coverage_80": 0.85,
                            "coverage_95": 0.92,
                            "brier_score": 0.15
                        }
                    )
                ]
                
                return mock_versions
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "MODEL_ERROR",
                        "error_message": f"Erro ao listar versões: {str(e)}"
                    }
                )
        
        @self.router.get(
            "/models/{version}",
            response_model=ModelVersionSchema,
            status_code=status.HTTP_200_OK,
            summary="Obter Detalhes do Modelo",
            description="Obter detalhes de uma versão específica do modelo"
        )
        async def get_model_details(
            version: str,
            service_factory = Depends()
        ):
            """Obter detalhes de modelo específico"""
            try:
                # TODO: Implementar obtenção real de detalhes do modelo
                if version != "v1.0.0":
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "error_code": "MODEL_NOT_FOUND",
                            "error_message": f"Modelo {version} não encontrado"
                        }
                    )
                
                return ModelVersionSchema(
                    version=version,
                    trained_at="2025-09-25T12:00:00Z",
                    data_hash="sha256:abcd1234...",
                    methodology="LP primary, BVAR fallback",
                    n_observations=20,
                    r_squared=0.65,
                    backtest_metrics={
                        "coverage_80": 0.85,
                        "coverage_95": 0.92,
                        "brier_score": 0.15
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "MODEL_ERROR",
                        "error_message": f"Erro ao obter detalhes do modelo: {str(e)}"
                    }
                )
        
        @self.router.get(
            "/models/{version}/performance",
            response_model=Dict[str, Any],
            status_code=status.HTTP_200_OK,
            summary="Performance do Modelo",
            description="Obter métricas de performance de uma versão específica"
        )
        async def get_model_performance(
            version: str,
            service_factory = Depends()
        ):
            """Obter performance de modelo específico"""
            try:
                # Obter métricas de performance
                metrics_service = await service_factory.create_metrics_service()
                health_metrics = await metrics_service.get_health_metrics()
                
                model_performance = health_metrics.get("model_performance", {})
                
                if version not in model_performance:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "error_code": "MODEL_NOT_FOUND",
                            "error_message": f"Performance do modelo {version} não encontrada"
                        }
                    )
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "model_version": version,
                    "performance": model_performance[version]
                }
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "METRICS_ERROR",
                        "error_message": f"Erro ao obter performance do modelo: {str(e)}"
                    }
                )
        
        @self.router.get(
            "/models/{version}/trends",
            response_model=Dict[str, Any],
            status_code=status.HTTP_200_OK,
            summary="Tendências do Modelo",
            description="Obter tendências de performance de uma versão específica"
        )
        async def get_model_trends(
            version: str,
            metric_name: str = "r_squared",
            service_factory = Depends()
        ):
            """Obter tendências de modelo específico"""
            try:
                # Obter tendências de performance
                metrics_service = await service_factory.create_metrics_service()
                trends = await metrics_service.get_model_performance_trends(
                    version, metric_name
                )
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "model_version": version,
                    "metric_name": metric_name,
                    "trends": trends
                }
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "METRICS_ERROR",
                        "error_message": f"Erro ao obter tendências do modelo: {str(e)}"
                    }
                )
        
        @self.router.post(
            "/models/{version}/retrain",
            response_model=Dict[str, Any],
            status_code=status.HTTP_202_ACCEPTED,
            summary="Retreinar Modelo",
            description="Iniciar retreinamento de uma versão específica do modelo"
        )
        async def retrain_model(
            version: str,
            service_factory = Depends()
        ):
            """Retreinar modelo específico"""
            try:
                # TODO: Implementar retreinamento real do modelo
                # Por enquanto, retornar confirmação mock
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "model_version": version,
                    "status": "retraining_initiated",
                    "message": "Retreinamento iniciado em background",
                    "estimated_completion": "2025-09-25T14:00:00Z"
                }
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "TRAINING_ERROR",
                        "error_message": f"Erro ao iniciar retreinamento: {str(e)}"
                    }
                )
