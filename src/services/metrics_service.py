"""
Metrics Service - Single Responsibility Principle
Serviço responsável por métricas e observabilidade
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

from src.core.interfaces import IMetricsService

class MetricsService(IMetricsService):
    """
    Serviço de métricas e observabilidade
    
    Responsabilidades:
    - Métricas de latência
    - Métricas de performance do modelo
    - Métricas de saúde do sistema
    - Observabilidade para auditoria
    """
    
    def __init__(self, 
                 metrics_backend: str = "prometheus",
                 metrics_port: int = 9090):
        self.metrics_backend = metrics_backend
        self.metrics_port = metrics_port
        
        # Métricas em memória (para simplicidade)
        self.latency_metrics = deque(maxlen=1000)  # Últimas 1000 latências
        self.model_performance = {}  # Performance por versão do modelo
        self.request_counts = defaultdict(int)  # Contadores de requests
        self.error_counts = defaultdict(int)  # Contadores de erros
        self.start_time = time.time()
        
        # Thread safety
        self._lock = threading.Lock()
    
    async def record_prediction_latency(self, request_id: str, latency_ms: float) -> None:
        """Registrar latência de previsão"""
        with self._lock:
            self.latency_metrics.append({
                'request_id': request_id,
                'latency_ms': latency_ms,
                'timestamp': datetime.now()
            })
    
    async def record_model_performance(self, model_version: str, metrics: Dict[str, float]) -> None:
        """Registrar performance do modelo"""
        with self._lock:
            if model_version not in self.model_performance:
                self.model_performance[model_version] = {
                    'r_squared': [],
                    'mae': [],
                    'rmse': [],
                    'coverage_80': [],
                    'coverage_95': [],
                    'brier_score': [],
                    'last_updated': datetime.now()
                }
            
            for metric_name, value in metrics.items():
                if metric_name in self.model_performance[model_version]:
                    self.model_performance[model_version][metric_name].append(value)
                    # Manter apenas últimas 100 medições
                    if len(self.model_performance[model_version][metric_name]) > 100:
                        self.model_performance[model_version][metric_name] = \
                            self.model_performance[model_version][metric_name][-100:]
            
            self.model_performance[model_version]['last_updated'] = datetime.now()
    
    async def record_request_count(self, endpoint: str, status_code: int) -> None:
        """Registrar contagem de requests"""
        with self._lock:
            key = f"{endpoint}_{status_code}"
            self.request_counts[key] += 1
    
    async def record_error_count(self, error_type: str) -> None:
        """Registrar contagem de erros"""
        with self._lock:
            self.error_counts[error_type] += 1
    
    async def get_health_metrics(self) -> Dict[str, Any]:
        """Obter métricas de saúde do sistema"""
        with self._lock:
            current_time = datetime.now()
            uptime_seconds = time.time() - self.start_time
            
            # Calcular métricas de latência
            if self.latency_metrics:
                latencies = [m['latency_ms'] for m in self.latency_metrics]
                latency_p50 = self._percentile(latencies, 50)
                latency_p95 = self._percentile(latencies, 95)
                latency_p99 = self._percentile(latencies, 99)
                avg_latency = sum(latencies) / len(latencies)
            else:
                latency_p50 = latency_p95 = latency_p99 = avg_latency = 0.0
            
            # Calcular requests por minuto
            recent_requests = [m for m in self.latency_metrics 
                             if m['timestamp'] > current_time - timedelta(minutes=1)]
            requests_per_minute = len(recent_requests)
            
            # Calcular taxa de erro
            total_requests = sum(self.request_counts.values())
            total_errors = sum(self.error_counts.values())
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0.0
            
            # Status geral
            status = "healthy"
            if error_rate > 10:  # Mais de 10% de erro
                status = "degraded"
            elif error_rate > 25:  # Mais de 25% de erro
                status = "unhealthy"
            elif latency_p95 > 1000:  # P95 > 1s
                status = "degraded"
            
            return {
                "status": status,
                "uptime_seconds": uptime_seconds,
                "latency": {
                    "p50_ms": latency_p50,
                    "p95_ms": latency_p95,
                    "p99_ms": latency_p99,
                    "avg_ms": avg_latency
                },
                "throughput": {
                    "requests_per_minute": requests_per_minute,
                    "total_requests": total_requests
                },
                "errors": {
                    "error_rate_percent": error_rate,
                    "total_errors": total_errors,
                    "error_breakdown": dict(self.error_counts)
                },
                "model_performance": self._get_model_performance_summary(),
                "timestamp": current_time.isoformat()
            }
    
    def _get_model_performance_summary(self) -> Dict[str, Any]:
        """Obter resumo da performance dos modelos"""
        summary = {}
        
        for model_version, metrics in self.model_performance.items():
            if not any(metrics[key] for key in ['r_squared', 'mae', 'rmse']):
                continue
            
            summary[model_version] = {
                "r_squared_avg": self._safe_average(metrics['r_squared']),
                "mae_avg": self._safe_average(metrics['mae']),
                "rmse_avg": self._safe_average(metrics['rmse']),
                "coverage_80_avg": self._safe_average(metrics['coverage_80']),
                "coverage_95_avg": self._safe_average(metrics['coverage_95']),
                "brier_score_avg": self._safe_average(metrics['brier_score']),
                "last_updated": metrics['last_updated'].isoformat(),
                "n_measurements": len(metrics['r_squared'])
            }
        
        return summary
    
    def _safe_average(self, values: list) -> float:
        """Calcular média de forma segura"""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def _percentile(self, data: list, percentile: int) -> float:
        """Calcular percentil"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def get_latency_distribution(self, hours: int = 1) -> Dict[str, Any]:
        """Obter distribuição de latência das últimas N horas"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_latencies = [m['latency_ms'] for m in self.latency_metrics 
                              if m['timestamp'] > cutoff_time]
            
            if not recent_latencies:
                return {"error": "Nenhuma métrica de latência disponível"}
            
            return {
                "count": len(recent_latencies),
                "min_ms": min(recent_latencies),
                "max_ms": max(recent_latencies),
                "avg_ms": sum(recent_latencies) / len(recent_latencies),
                "p50_ms": self._percentile(recent_latencies, 50),
                "p90_ms": self._percentile(recent_latencies, 90),
                "p95_ms": self._percentile(recent_latencies, 95),
                "p99_ms": self._percentile(recent_latencies, 99)
            }
    
    async def get_model_performance_trends(self, model_version: str, 
                                         metric_name: str = "r_squared") -> Dict[str, Any]:
        """Obter tendências de performance do modelo"""
        with self._lock:
            if model_version not in self.model_performance:
                return {"error": f"Modelo {model_version} não encontrado"}
            
            metrics = self.model_performance[model_version].get(metric_name, [])
            if not metrics:
                return {"error": f"Métrica {metric_name} não disponível para {model_version}"}
            
            return {
                "model_version": model_version,
                "metric_name": metric_name,
                "values": metrics,
                "count": len(metrics),
                "latest": metrics[-1] if metrics else None,
                "trend": self._calculate_trend(metrics)
            }
    
    def _calculate_trend(self, values: list) -> str:
        """Calcular tendência dos valores"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Usar regressão linear simples
        n = len(values)
        x = list(range(n))
        y = values
        
        # Calcular coeficiente angular
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "no_trend"
        
        slope = numerator / denominator
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "degrading"
        else:
            return "stable"
    
    async def cleanup(self):
        """Cleanup do serviço"""
        with self._lock:
            self.latency_metrics.clear()
            self.model_performance.clear()
            self.request_counts.clear()
            self.error_counts.clear()
