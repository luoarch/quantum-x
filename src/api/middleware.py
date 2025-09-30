"""
Middlewares da API
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib

from ..core.config import get_settings
from .schemas import StandardErrorResponse, ErrorCodes

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requisições"""
    
    async def dispatch(self, request: Request, call_next):
        """Processar requisição e log"""
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Log da requisição
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Processar requisição
        response = await call_next(request)
        
        # Calcular latência
        latency = time.time() - start_time
        
        # Log da resposta
        logger.info(
            f"Response {request_id}: {response.status_code} "
            f"in {latency:.3f}s"
        )
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting"""
    
    def __init__(self, app, requests_per_hour: int = 100):
        super().__init__(app)
        self.requests_per_hour = requests_per_hour
        self.requests: Dict[str, list] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """Obter ID único do cliente"""
        # Usar IP + User-Agent para identificar cliente
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        return hashlib.md5(f"{client_ip}:{user_agent}".encode()).hexdigest()
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """Verificar se cliente está rate limited"""
        now = time.time()
        hour_ago = now - 3600  # 1 hora atrás
        
        # Limpar requisições antigas
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id] 
                if req_time > hour_ago
            ]
        else:
            self.requests[client_id] = []
        
        # Verificar limite
        return len(self.requests[client_id]) >= self.requests_per_hour
    
    def _record_request(self, client_id: str):
        """Registrar requisição"""
        if client_id not in self.requests:
            self.requests[client_id] = []
        self.requests[client_id].append(time.time())
    
    async def dispatch(self, request: Request, call_next):
        """Processar rate limiting"""
        client_id = self._get_client_id(request)
        
        # Verificar rate limit
        if self._is_rate_limited(client_id):
            error_response = StandardErrorResponse(
                error_code=ErrorCodes.RATE_LIMITED,
                message=f"Rate limit excedido. Máximo {self.requests_per_hour} requests por hora.",
                details={
                    "limit": self.requests_per_hour,
                    "window": "1 hour",
                    "reset_time": datetime.utcnow() + timedelta(hours=1)
                },
                request_id=getattr(request.state, 'request_id', None)
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_response.dict()
            )
        
        # Registrar requisição
        self._record_request(client_id)
        
        # Processar requisição
        response = await call_next(request)
        
        # Adicionar headers de rate limit
        remaining = self.requests_per_hour - len(self.requests[client_id])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 3600))
        
        return response

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware para autenticação por chave API"""
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.valid_keys = set(self.settings.API_KEYS)
    
    async def dispatch(self, request: Request, call_next):
        """Processar autenticação"""
        # Pular autenticação para endpoints públicos
        if request.url.path in ["/", "/info", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Verificar chave API
        api_key = request.headers.get(self.settings.API_KEY_HEADER)
        
        if not api_key:
            error_response = StandardErrorResponse(
                error_code=ErrorCodes.AUTHENTICATION_FAILED,
                message="Chave API necessária",
                details={
                    "header": self.settings.API_KEY_HEADER,
                    "required": True
                },
                request_id=getattr(request.state, 'request_id', None)
            )
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response.dict()
            )
        
        if api_key not in self.valid_keys:
            error_response = StandardErrorResponse(
                error_code=ErrorCodes.AUTHENTICATION_FAILED,
                message="Chave API inválida",
                details={
                    "provided_key": api_key[:8] + "..." if len(api_key) > 8 else api_key
                },
                request_id=getattr(request.state, 'request_id', None)
            )
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response.dict()
            )
        
        # Adicionar informações de autenticação ao request
        request.state.api_key = api_key
        request.state.authenticated = True
        
        return await call_next(request)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware para tratamento de erros"""
    
    async def dispatch(self, request: Request, call_next):
        """Processar tratamento de erros"""
        try:
            return await call_next(request)
        except HTTPException:
            # Re-raise HTTP exceptions (já tratadas)
            raise
        except Exception as e:
            # Log do erro
            logger.error(f"Erro não tratado: {str(e)}", exc_info=True)
            
            # Resposta de erro
            error_response = StandardErrorResponse(
                error_code=ErrorCodes.INTERNAL_ERROR,
                message="Erro interno do servidor",
                details={
                    "exception_type": type(e).__name__,
                    "error": str(e)
                },
                request_id=getattr(request.state, 'request_id', None)
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.dict()
            )

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para headers de segurança"""
    
    async def dispatch(self, request: Request, call_next):
        """Adicionar headers de segurança"""
        response = await call_next(request)
        
        # Headers de segurança
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware para validação de requisições"""
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
    
    async def dispatch(self, request: Request, call_next):
        """Validar requisição"""
        # Validar tamanho do body
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 1024 * 1024:  # 1MB
            error_response = StandardErrorResponse(
                error_code=ErrorCodes.INVALID_REQUEST,
                message="Tamanho do body excede o limite de 1MB",
                request_id=getattr(request.state, 'request_id', None)
            )
            
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content=error_response.dict()
            )
        
        # Validar método HTTP
        if request.method not in ["GET", "POST", "PUT", "DELETE", "OPTIONS"]:
            error_response = StandardErrorResponse(
                error_code=ErrorCodes.INVALID_REQUEST,
                message=f"Método HTTP não suportado: {request.method}",
                request_id=getattr(request.state, 'request_id', None)
            )
            
            return JSONResponse(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                content=error_response.dict()
            )
        
        return await call_next(request)
