"""
Rate Limit Middleware - Single Responsibility Principle
Middleware responsável por controle de taxa de requests
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting
    
    Responsabilidades:
    - Controlar taxa de requests por minuto/dia
    - Aplicar limites por chave de API
    - Retornar headers de rate limit
    """
    
    def __init__(self, 
                 app, 
                 max_requests_per_minute: int = 60,
                 max_requests_per_day: int = 1000):
        super().__init__(app)
        self.max_requests_per_minute = max_requests_per_minute
        self.max_requests_per_day = max_requests_per_day
        
        # Armazenamento de requests por chave de API
        self.requests_per_minute: Dict[str, deque] = defaultdict(lambda: deque())
        self.requests_per_day: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Lock para thread safety
        self._lock = asyncio.Lock()
    
    async def dispatch(self, request: Request, call_next):
        """Processar request com rate limiting"""
        
        # Rotas que não precisam de rate limiting
        public_routes = ["/", "/health", "/docs", "/redoc", "/openapi.json"]
        if request.url.path in public_routes:
            return await call_next(request)
        
        # Obter chave de API
        api_key = request.headers.get("X-API-Key", "anonymous")
        
        # Verificar rate limits
        async with self._lock:
            if not await self._check_rate_limits(api_key):
                # Calcular tempo de reset
                reset_time = self._calculate_reset_time(api_key)
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "error_message": "Limite de requests excedido",
                        "retry_after": reset_time
                    },
                    headers={
                        "X-RateLimit-Limit": str(self.max_requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(reset_time)
                    }
                )
        
        # Processar request
        response = await call_next(request)
        
        # Adicionar headers de rate limit
        await self._add_rate_limit_headers(response, api_key)
        
        return response
    
    async def _check_rate_limits(self, api_key: str) -> bool:
        """Verificar se request está dentro dos limites"""
        now = datetime.now()
        
        # Limpar requests antigos
        self._cleanup_old_requests(api_key, now)
        
        # Verificar limite por minuto
        if len(self.requests_per_minute[api_key]) >= self.max_requests_per_minute:
            return False
        
        # Verificar limite por dia
        if len(self.requests_per_day[api_key]) >= self.max_requests_per_day:
            return False
        
        # Registrar request
        self.requests_per_minute[api_key].append(now)
        self.requests_per_day[api_key].append(now)
        
        return True
    
    def _cleanup_old_requests(self, api_key: str, now: datetime):
        """Limpar requests antigos"""
        # Limpar requests de mais de 1 minuto
        minute_ago = now - timedelta(minutes=1)
        while (self.requests_per_minute[api_key] and 
               self.requests_per_minute[api_key][0] < minute_ago):
            self.requests_per_minute[api_key].popleft()
        
        # Limpar requests de mais de 1 dia
        day_ago = now - timedelta(days=1)
        while (self.requests_per_day[api_key] and 
               self.requests_per_day[api_key][0] < day_ago):
            self.requests_per_day[api_key].popleft()
    
    def _calculate_reset_time(self, api_key: str) -> int:
        """Calcular tempo de reset em segundos"""
        now = datetime.now()
        
        # Verificar qual limite foi excedido
        if len(self.requests_per_minute[api_key]) >= self.max_requests_per_minute:
            # Reset em 1 minuto
            oldest_request = self.requests_per_minute[api_key][0]
            reset_time = oldest_request + timedelta(minutes=1)
            return int((reset_time - now).total_seconds())
        
        elif len(self.requests_per_day[api_key]) >= self.max_requests_per_day:
            # Reset em 1 dia
            oldest_request = self.requests_per_day[api_key][0]
            reset_time = oldest_request + timedelta(days=1)
            return int((reset_time - now).total_seconds())
        
        return 0
    
    async def _add_rate_limit_headers(self, response, api_key: str):
        """Adicionar headers de rate limit à response"""
        now = datetime.now()
        
        # Calcular requests restantes
        remaining_minute = max(0, self.max_requests_per_minute - len(self.requests_per_minute[api_key]))
        remaining_day = max(0, self.max_requests_per_day - len(self.requests_per_day[api_key]))
        
        # Calcular tempo de reset
        reset_time = self._calculate_reset_time(api_key)
        
        # Adicionar headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.max_requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining_minute)
        response.headers["X-RateLimit-Limit-Day"] = str(self.max_requests_per_day)
        response.headers["X-RateLimit-Remaining-Day"] = str(remaining_day)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

class RateLimitConfig:
    """Configuração de rate limiting"""
    
    def __init__(self):
        self.limits = {
            "free": {
                "requests_per_minute": 10,
                "requests_per_day": 100
            },
            "premium": {
                "requests_per_minute": 100,
                "requests_per_day": 1000
            },
            "enterprise": {
                "requests_per_minute": 1000,
                "requests_per_day": 10000
            }
        }
    
    def get_limits_for_key(self, api_key: str) -> Dict[str, int]:
        """Obter limites para chave de API específica"""
        # TODO: Implementar lógica real baseada na chave de API
        # Por enquanto, retornar limites padrão
        return self.limits["premium"]
