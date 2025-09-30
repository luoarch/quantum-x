"""
Health Controller - Single Responsibility Principle
Controller responsável pelos endpoints de saúde e monitoramento
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from datetime import datetime

from src.core.models import HealthStatus
from src.api.schemas import HealthResponse

class HealthController:
    """
    Controller para endpoints de saúde
    
    Responsabilidades:
    - GET /health
    - GET /health/detailed
    - Monitoramento do sistema
    """
    
    def __init__(self):
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configurar rotas do controller"""
        
        @self.router.get(
            "/health",
            response_model=HealthResponse,
            status_code=status.HTTP_200_OK,
            summary="Health Check Básico",
            description="Verificação básica de saúde do sistema"
        )
        async def health_check(service_factory = Depends()):
            """Health check básico"""
            try:
                # Obter métricas de saúde
                metrics_service = await service_factory.create_metrics_service()
                health_metrics = await metrics_service.get_health_metrics()
                
                # Determinar status
                system_status = health_metrics.get("status", "unknown")
                
                return HealthResponse(
                    status=system_status,
                    version="v1.0.0",
                    model_version="v1.0.0",  # TODO: Obter versão atual do modelo
                    uptime_seconds=health_metrics.get("uptime_seconds", 0),
                    latency_p50_ms=health_metrics.get("latency", {}).get("p50_ms"),
                    latency_p95_ms=health_metrics.get("latency", {}).get("p95_ms"),
                    requests_per_minute=health_metrics.get("throughput", {}).get("requests_per_minute")
                )
                
            except Exception as e:
                return HealthResponse(
                    status="unhealthy",
                    version="v1.0.0",
                    model_version="unknown",
                    uptime_seconds=0
                )
        
        @self.router.get(
            "/health/detailed",
            response_model=Dict[str, Any],
            status_code=status.HTTP_200_OK,
            summary="Health Check Detalhado",
            description="Verificação detalhada de saúde do sistema com métricas completas"
        )
        async def detailed_health_check(service_factory = Depends()):
            """Health check detalhado"""
            try:
                # Obter métricas detalhadas
                metrics_service = await service_factory.create_metrics_service()
                health_metrics = await metrics_service.get_health_metrics()
                
                # Obter status dos serviços
                service_status = await service_factory.get_health_status()
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "system": health_metrics,
                    "services": service_status,
                    "checks": {
                        "database": "healthy",  # TODO: Implementar check real
                        "cache": "healthy",     # TODO: Implementar check real
                        "external_apis": "healthy"  # TODO: Implementar check real
                    }
                }
                
            except Exception as e:
                return {
                    "timestamp": datetime.now().isoformat(),
                    "status": "unhealthy",
                    "error": str(e),
                    "system": {"status": "error"},
                    "services": {},
                    "checks": {
                        "database": "error",
                        "cache": "error",
                        "external_apis": "error"
                    }
                }
        
        @self.router.get(
            "/health/latency",
            response_model=Dict[str, Any],
            status_code=status.HTTP_200_OK,
            summary="Métricas de Latência",
            description="Obter distribuição de latência do sistema"
        )
        async def latency_metrics(
            hours: int = 1,
            service_factory = Depends()
        ):
            """Métricas de latência"""
            try:
                metrics_service = await service_factory.create_metrics_service()
                latency_dist = await metrics_service.get_latency_distribution(hours)
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "period_hours": hours,
                    "latency_distribution": latency_dist
                }
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "METRICS_ERROR",
                        "error_message": f"Erro ao obter métricas de latência: {str(e)}"
                    }
                )
        
        @self.router.get(
            "/health/model-performance",
            response_model=Dict[str, Any],
            status_code=status.HTTP_200_OK,
            summary="Performance dos Modelos",
            description="Obter métricas de performance dos modelos"
        )
        async def model_performance_metrics(
            model_version: str = None,
            metric_name: str = "r_squared",
            service_factory = Depends()
        ):
            """Métricas de performance dos modelos"""
            try:
                metrics_service = await service_factory.create_metrics_service()
                
                if model_version:
                    # Performance de modelo específico
                    trends = await metrics_service.get_model_performance_trends(
                        model_version, metric_name
                    )
                    return {
                        "timestamp": datetime.now().isoformat(),
                        "model_version": model_version,
                        "metric_name": metric_name,
                        "trends": trends
                    }
                else:
                    # Performance de todos os modelos
                    health_metrics = await metrics_service.get_health_metrics()
                    return {
                        "timestamp": datetime.now().isoformat(),
                        "model_performance": health_metrics.get("model_performance", {})
                    }
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "METRICS_ERROR",
                        "error_message": f"Erro ao obter métricas de performance: {str(e)}"
                    }
                )
