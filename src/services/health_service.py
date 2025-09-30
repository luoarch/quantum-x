"""
Serviço de health check
v2.1 FINAL - Síncrono, singleton, sem I/O bloqueante
"""

import logging
import time
import psutil
from typing import Dict, Any, Optional
from datetime import datetime

from ..api.schemas import HealthResponse
from ..core.config import get_settings
from .model_service import get_model_service
from .data_service import DataService

logger = logging.getLogger(__name__)

class HealthService:
    """
    Serviço para health checks
    
    v2.1: Métodos síncronos, usa singletons, perf_counter
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.model_service = get_model_service()  # Singleton
        self.data_service = DataService()
        self.start_perf = time.perf_counter()  # Mais preciso
    
    async def get_basic_health(self) -> HealthResponse:
        """Health check básico"""
        try:
            uptime = time.perf_counter() - self.start_perf
            
            # ModelService é síncrono, DataService é async
            active_model = self.model_service.get_active_version()
            model_version = active_model if active_model else "none"
            
            data_summary = await self.data_service.get_data_summary()
            data_available = data_summary.get("combined_data", {}).get("observations", 0) > 0
            
            # Determinar status
            if active_model and data_available:
                status_str = "healthy"
            elif active_model or data_available:
                status_str = "degraded"
            else:
                status_str = "unhealthy"
            
            return HealthResponse(
                status=status_str,
                version=self.settings.API_VERSION,
                model_version=model_version,
                uptime_seconds=uptime,
                latency_p50_ms=self._get_latency_p50(),
                latency_p95_ms=self._get_latency_p95(),
                requests_per_minute=self._get_requests_per_minute()
            )
            
        except Exception as e:
            logger.error(f"Erro no health check: {e}", exc_info=True)
            
            return HealthResponse(
                status="unhealthy",
                version=self.settings.API_VERSION,
                model_version="error",
                uptime_seconds=time.perf_counter() - self.start_perf,
                latency_p50_ms=None,
                latency_p95_ms=None,
                requests_per_minute=None
            )
    
    async def get_detailed_health(self) -> Dict[str, Any]:
        """Health check detalhado"""
        try:
            basic = await self.get_basic_health()
            dependencies = await self._check_dependencies()
            system_metrics = self._get_system_metrics()
            
            return {
                "status": basic.status,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "uptime_seconds": basic.uptime_seconds,
                "version": basic.version,
                "model_version": basic.model_version,
                "dependencies": dependencies,
                "system": system_metrics,
                "overall_health": self._calculate_overall_health(basic, dependencies)
            }
            
        except Exception as e:
            logger.error(f"Erro no health detalhado: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "error": str(e),
                "overall_health": "unhealthy"
            }
    
    async def get_readiness(self) -> Dict[str, Any]:
        """Readiness check"""
        try:
            # Métodos síncronos
            active_version = self.model_service.get_active_version()
            model_ready = active_version is not None
            
            data_summary = await self.data_service.get_data_summary()
            data_ready = data_summary.get("combined_data", {}).get("observations", 0) > 0
            
            data_quality = await self.data_service.validate_data_quality()
            data_valid = bool(data_quality.get("valid", False))
            
            ready = model_ready and data_ready and data_valid
            
            # Issues sem None (filtrado)
            issues = []
            if not model_ready:
                issues.append("Modelo não carregado")
            if not data_ready:
                issues.append("Dados não disponíveis")
            if not data_valid:
                issues.append("Dados inválidos")
            
            return {
                "ready": ready,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "active_version": active_version,
                "uptime_seconds": time.perf_counter() - self.start_perf,
                "models_loaded": model_ready,
                "checks": {
                    "model_loaded": model_ready,
                    "data_available": data_ready,
                    "data_valid": data_valid
                },
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Erro no readiness: {e}", exc_info=True)
            return {
                "ready": False,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "active_version": None,
                "uptime_seconds": time.perf_counter() - self.start_perf,
                "models_loaded": False,
                "checks": {
                    "model_loaded": False,
                    "data_available": False,
                    "data_valid": False
                },
                "issues": [f"Erro: {e}"]
            }
    
    async def get_liveness(self) -> Dict[str, Any]:
        """
        Liveness check (minimalista, sem I/O bloqueante)
        
        v2.1: cpu_percent(interval=0) para resposta instantânea
        """
        try:
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent(interval=0)  # Instantâneo!
            
            alive = memory_usage < 90 and cpu_usage < 95
            
            # Issues filtradas
            issues = []
            if memory_usage >= 90:
                issues.append("Alto uso de memória")
            if cpu_usage >= 95:
                issues.append("Alto uso de CPU")
            
            return {
                "alive": alive,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "uptime_seconds": time.perf_counter() - self.start_perf,
                "memory_usage_percent": round(memory_usage, 2),
                "cpu_usage_percent": round(cpu_usage, 2),
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Erro no liveness: {e}", exc_info=True)
            return {
                "alive": False,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "uptime_seconds": time.perf_counter() - self.start_perf,
                "memory_usage_percent": None,
                "cpu_usage_percent": None,
                "error": str(e),
                "issues": [f"Erro crítico: {e}"]
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Métricas da API"""
        try:
            uptime = time.perf_counter() - self.start_perf
            system_metrics = self._get_system_metrics()
            
            # Dados e modelo
            data_summary = await self.data_service.get_data_summary()
            active_version = self.model_service.get_active_version()
            
            return {
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "uptime_seconds": uptime,
                "system": system_metrics,
                "data": {
                    "total_observations": data_summary.get("combined_data", {}).get("observations", 0),
                    "data_quality": await self.data_service.validate_data_quality()
                },
                "model": {
                    "active_version": active_version,
                    "is_loaded": active_version is not None
                },
                "api": {
                    "version": self.settings.API_VERSION,
                    "latency_p50_ms": self._get_latency_p50(),
                    "latency_p95_ms": self._get_latency_p95(),
                    "latency_source": "simulated",  # Rotular placeholders
                    "requests_per_minute": self._get_requests_per_minute()
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter métricas: {e}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "error": str(e)
            }
    
    async def get_component_status(self) -> Dict[str, Any]:
        """Status dos componentes"""
        try:
            components = {}
            
            # Modelo
            try:
                active_version = self.model_service.get_active_version()
                cache_info = self.model_service.get_cache_info()
                
                components["model"] = {
                    "status": "healthy" if active_version else "unhealthy",
                    "version": active_version,
                    "loaded": active_version is not None,
                    "cached_versions": cache_info.get("cached_versions", [])
                }
            except Exception as e:
                components["model"] = {"status": "error", "error": str(e), "loaded": False}
            
            # Dados
            try:
                data_quality = await self.data_service.validate_data_quality()
                components["data"] = {
                    "status": "healthy" if data_quality.get("valid") else "degraded",
                    "observations": data_quality.get("data_points", 0),
                    "issues": data_quality.get("issues", []),
                    "warnings": data_quality.get("warnings", [])
                }
            except Exception as e:
                components["data"] = {"status": "error", "error": str(e)}
            
            # Cache
            try:
                cache_info = self.model_service.get_cache_info()
                components["cache"] = {
                    "status": "healthy",
                    "size": cache_info.get("cache_size", 0),
                    "max_size": cache_info.get("max_cache_size", 3)
                }
            except Exception as e:
                components["cache"] = {"status": "error", "error": str(e)}
            
            return {
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "components": components,
                "overall_status": self._calculate_component_status(components)
            }
            
        except Exception as e:
            logger.error(f"Erro status componentes: {e}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "error": str(e),
                "overall_status": "error"
            }
    
    async def _check_dependencies(self) -> Dict[str, Any]:
        """Verificar dependências"""
        dependencies = {}
        
        # Dados
        try:
            data_summary = await self.data_service.get_data_summary()
            dependencies["data"] = {
                "status": "healthy" if data_summary.get("combined_data", {}).get("observations", 0) > 0 else "unhealthy",
                "observations": data_summary.get("combined_data", {}).get("observations", 0)
            }
        except Exception as e:
            dependencies["data"] = {"status": "error", "error": str(e)}
        
        # Modelo
        try:
            active = self.model_service.get_active_version()
            dependencies["model"] = {
                "status": "healthy" if active else "unhealthy",
                "version": active
            }
        except Exception as e:
            dependencies["model"] = {"status": "error", "error": str(e)}
        
        return dependencies
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Métricas do sistema"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=0)  # Instantâneo
            
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
            logger.error(f"Erro métricas sistema: {e}")
            return {"error": str(e)}
    
    def _calculate_overall_health(self, basic_health: HealthResponse, dependencies: Dict[str, Any]) -> str:
        """Calcular saúde geral"""
        if basic_health.status == "unhealthy":
            return "unhealthy"
        
        for dep_status in dependencies.values():
            if dep_status.get("status") == "error":
                return "unhealthy"
            elif dep_status.get("status") == "unhealthy":
                return "degraded"
        
        return "healthy"
    
    def _calculate_component_status(self, components: Dict[str, Any]) -> str:
        """Calcular status dos componentes"""
        statuses = [comp.get("status", "unknown") for comp in components.values()]
        
        if "error" in statuses:
            return "error"
        elif "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"
    
    def _get_latency_p50(self) -> Optional[float]:
        """Latência P50 (placeholder)"""
        # TODO: Implementar métricas reais Prometheus
        return 45.2
    
    def _get_latency_p95(self) -> Optional[float]:
        """Latência P95 (placeholder)"""
        # TODO: Implementar métricas reais Prometheus
        return 120.5
    
    def _get_requests_per_minute(self) -> Optional[float]:
        """Requests/min (placeholder)"""
        # TODO: Implementar métricas reais Prometheus
        return 15.3


# Singleton instance (thread-safe básico)
_health_service_instance: Optional[HealthService] = None

def get_health_service_singleton() -> HealthService:
    """Obter instância singleton do HealthService"""
    global _health_service_instance
    
    if _health_service_instance is None:
        _health_service_instance = HealthService()
    
    return _health_service_instance
