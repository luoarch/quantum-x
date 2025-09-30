"""
Serviço de health check
"""

import logging
import time
import psutil
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ..api.schemas import HealthResponse
from ..core.config import get_settings
from .model_service import ModelService
from .data_service import DataService

logger = logging.getLogger(__name__)

class HealthService:
    """Serviço para health checks"""
    
    def __init__(self):
        self.settings = get_settings()
        self.model_service = ModelService()
        self.data_service = DataService()
        self.start_time = time.time()
    
    async def get_basic_health(self) -> HealthResponse:
        """Obter health check básico"""
        try:
            uptime = time.time() - self.start_time
            
            # Verificar se modelo está disponível
            active_model = await self.model_service.get_active_model()
            model_version = active_model.version if active_model else "none"
            
            # Verificar dados
            data_summary = await self.data_service.get_data_summary()
            data_available = data_summary["combined_data"]["observations"] > 0
            
            # Determinar status
            if active_model and data_available:
                status = "healthy"
            elif active_model or data_available:
                status = "degraded"
            else:
                status = "unhealthy"
            
            return HealthResponse(
                status=status,
                version=self.settings.API_VERSION,
                model_version=model_version,
                uptime_seconds=uptime,
                latency_p50_ms=self._get_latency_p50(),
                latency_p95_ms=self._get_latency_p95(),
                requests_per_minute=self._get_requests_per_minute()
            )
            
        except Exception as e:
            logger.error(f"Erro no health check básico: {str(e)}", exc_info=True)
            
            return HealthResponse(
                status="unhealthy",
                version=self.settings.API_VERSION,
                model_version="error",
                uptime_seconds=time.time() - self.start_time,
                latency_p50_ms=None,
                latency_p95_ms=None,
                requests_per_minute=None
            )
    
    async def get_detailed_health(self) -> Dict[str, Any]:
        """Obter health check detalhado"""
        try:
            # Health básico
            basic_health = await self.get_basic_health()
            
            # Verificações de dependências
            dependencies = await self._check_dependencies()
            
            # Métricas de sistema
            system_metrics = self._get_system_metrics()
            
            # Status dos componentes
            components = await self._check_components()
            
            return {
                "status": basic_health.status,
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": basic_health.uptime_seconds,
                "version": basic_health.version,
                "model_version": basic_health.model_version,
                "dependencies": dependencies,
                "system": system_metrics,
                "components": components,
                "overall_health": self._calculate_overall_health(basic_health, dependencies, components)
            }
            
        except Exception as e:
            logger.error(f"Erro no health check detalhado: {str(e)}", exc_info=True)
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "overall_health": "unhealthy"
            }
    
    async def get_readiness(self) -> Dict[str, Any]:
        """Obter readiness check"""
        try:
            # Verificar se modelo está carregado
            active_model = await self.model_service.get_active_model()
            model_ready = active_model is not None
            
            # Verificar se dados estão disponíveis
            data_summary = await self.data_service.get_data_summary()
            data_ready = data_summary["combined_data"]["observations"] > 0
            
            # Verificar qualidade dos dados
            data_quality = await self.data_service.validate_data_quality()
            data_valid = data_quality["valid"]
            
            ready = model_ready and data_ready and data_valid
            
            return {
                "ready": ready,
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "model_loaded": model_ready,
                    "data_available": data_ready,
                    "data_valid": data_valid
                },
                "issues": [] if ready else [
                    "Modelo não carregado" if not model_ready else None,
                    "Dados não disponíveis" if not data_ready else None,
                    "Dados inválidos" if not data_valid else None
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro no readiness check: {str(e)}", exc_info=True)
            return {
                "ready": False,
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "model_loaded": False,
                    "data_available": False,
                    "data_valid": False
                },
                "issues": [f"Erro no readiness check: {str(e)}"]
            }
    
    async def get_liveness(self) -> Dict[str, Any]:
        """Obter liveness check"""
        try:
            # Verificações básicas de vivacidade
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent(interval=1)
            
            alive = memory_usage < 90 and cpu_usage < 95
            
            return {
                "alive": alive,
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": time.time() - self.start_time,
                "memory_usage_percent": memory_usage,
                "cpu_usage_percent": cpu_usage,
                "issues": [] if alive else [
                    "Alto uso de memória" if memory_usage >= 90 else None,
                    "Alto uso de CPU" if cpu_usage >= 95 else None
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro no liveness check: {str(e)}", exc_info=True)
            return {
                "alive": False,
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": time.time() - self.start_time,
                "error": str(e)
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas da API"""
        try:
            # Métricas básicas
            uptime = time.time() - self.start_time
            
            # Métricas de sistema
            system_metrics = self._get_system_metrics()
            
            # Métricas de dados
            data_summary = await self.data_service.get_data_summary()
            
            # Métricas de modelo
            active_model = await self.model_service.get_active_model()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": uptime,
                "system": system_metrics,
                "data": {
                    "total_observations": data_summary["combined_data"]["observations"],
                    "data_quality": await self.data_service.validate_data_quality()
                },
                "model": {
                    "active_version": active_model.version if active_model else None,
                    "is_loaded": active_model is not None
                },
                "api": {
                    "version": self.settings.API_VERSION,
                    "environment": "development"  # TODO: Obter do ambiente
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter métricas: {str(e)}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def get_component_status(self) -> Dict[str, Any]:
        """Obter status dos componentes"""
        try:
            components = {}
            
            # Status do modelo
            try:
                active_model = await self.model_service.get_active_model()
                components["model"] = {
                    "status": "healthy" if active_model else "unhealthy",
                    "version": active_model.version if active_model else None,
                    "loaded": active_model is not None
                }
            except Exception as e:
                components["model"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Status dos dados
            try:
                data_quality = await self.data_service.validate_data_quality()
                components["data"] = {
                    "status": "healthy" if data_quality["valid"] else "degraded",
                    "observations": data_quality["data_points"],
                    "issues": data_quality["issues"],
                    "warnings": data_quality["warnings"]
                }
            except Exception as e:
                components["data"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Status do cache (simulado)
            components["cache"] = {
                "status": "healthy",
                "size": 0,  # TODO: Implementar cache real
                "hit_rate": 0.0
            }
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "components": components,
                "overall_status": self._calculate_component_status(components)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status dos componentes: {str(e)}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "overall_status": "error"
            }
    
    async def _check_dependencies(self) -> Dict[str, Any]:
        """Verificar dependências"""
        dependencies = {}
        
        # Verificar dados
        try:
            data_summary = await self.data_service.get_data_summary()
            dependencies["data"] = {
                "status": "healthy" if data_summary["combined_data"]["observations"] > 0 else "unhealthy",
                "observations": data_summary["combined_data"]["observations"]
            }
        except Exception as e:
            dependencies["data"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Verificar modelo
        try:
            active_model = await self.model_service.get_active_model()
            dependencies["model"] = {
                "status": "healthy" if active_model else "unhealthy",
                "version": active_model.version if active_model else None
            }
        except Exception as e:
            dependencies["model"] = {
                "status": "error",
                "error": str(e)
            }
        
        return dependencies
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Obter métricas do sistema"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 2)
                },
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count()
                }
            }
        except Exception as e:
            logger.error(f"Erro ao obter métricas do sistema: {str(e)}")
            return {"error": str(e)}
    
    async def _check_components(self) -> Dict[str, Any]:
        """Verificar componentes"""
        return await self.get_component_status()
    
    def _calculate_overall_health(self, basic_health, dependencies, components) -> str:
        """Calcular saúde geral"""
        if basic_health.status == "unhealthy":
            return "unhealthy"
        
        # Verificar dependências
        for dep_name, dep_status in dependencies.items():
            if dep_status["status"] == "error":
                return "unhealthy"
            elif dep_status["status"] == "unhealthy":
                return "degraded"
        
        return "healthy"
    
    def _calculate_component_status(self, components) -> str:
        """Calcular status dos componentes"""
        statuses = [comp["status"] for comp in components.values()]
        
        if "error" in statuses:
            return "error"
        elif "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"
    
    def _get_latency_p50(self) -> Optional[float]:
        """Obter latência P50 (simulada)"""
        # TODO: Implementar métricas reais
        return 45.2
    
    def _get_latency_p95(self) -> Optional[float]:
        """Obter latência P95 (simulada)"""
        # TODO: Implementar métricas reais
        return 120.5
    
    def _get_requests_per_minute(self) -> Optional[float]:
        """Obter requests por minuto (simulado)"""
        # TODO: Implementar métricas reais
        return 15.3
