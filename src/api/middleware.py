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
    """
    Middleware para logging estruturado de requisições
    v2.1: perf_counter, logs estruturados, request_id propagado
    """
    
    async def dispatch(self, request: Request, call_next):
        """Processar requisição e log estruturado"""
        start_perf = time.perf_counter()
        
        # Garantir request_id (já deve estar setado pelo RequestID middleware)
        request_id = getattr(request.state, 'request_id', 'unknown')
        client_ip = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log estruturado da requisição
        logger.info(
            "HTTP request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "user_agent": user_agent[:100],  # Truncar UA longo
                "action": "request_start"
            }
        )
        
        # Processar requisição
        response = await call_next(request)
        
        # Calcular latência precisa
        latency_ms = (time.perf_counter() - start_perf) * 1000
        
        # Log estruturado da resposta
        logger.info(
            "HTTP response",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": round(latency_ms, 2),
                "action": "request_complete",
                "success": 200 <= response.status_code < 400
            }
        )
        
        # Propagar request_id no header de resposta
        response.headers["X-Request-ID"] = request_id
        
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
        """
        Processar rate limiting
        v2.1: Retry-After header, logs estruturados
        """
        client_id = self._get_client_id(request)
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Verificar rate limit
        if self._is_rate_limited(client_id):
            # Calcular tempo até reset (próxima hora)
            now = time.time()
            reset_timestamp = int(now) + 3600
            retry_after_seconds = 3600  # 1 hora
            
            # Log estruturado
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "request_id": request_id,
                    "client_id": client_id[:8],
                    "limit": self.requests_per_hour,
                    "action": "rate_limit_exceeded"
                }
            )
            
            error_response = StandardErrorResponse(
                error_code=ErrorCodes.RATE_LIMITED,
                message=f"Rate limit excedido. Máximo {self.requests_per_hour} requests por hora.",
                details={
                    "limit": self.requests_per_hour,
                    "window": "1 hour",
                    "window_seconds": 3600,
                    "reset_time": datetime.utcnow() + timedelta(hours=1),
                    "retry_after_seconds": retry_after_seconds
                },
                request_id=request_id
            )
            
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_response.model_dump(mode='json')
            )
            
            # Headers de rate limiting (RFC 6585)
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_hour)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(reset_timestamp)
            response.headers["Retry-After"] = str(retry_after_seconds)
            response.headers["X-Request-ID"] = request_id
            
            return response
        
        # Registrar requisição
        self._record_request(client_id)
        
        # Processar requisição
        response = await call_next(request)
        
        # Adicionar headers de rate limit
        remaining = max(0, self.requests_per_hour - len(self.requests[client_id]))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 3600))
        
        return response

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware para autenticação por chave API
    v2.1: logs estruturados, headers propagados
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.valid_keys = set(self.settings.API_KEYS)
    
    async def dispatch(self, request: Request, call_next):
        """Processar autenticação"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Pular autenticação para endpoints públicos
        public_paths = ["/", "/info", "/health", "/ready", "/live", "/docs", "/redoc", "/openapi.json"]
        if request.url.path in public_paths:
            return await call_next(request)
        
        # Verificar chave API
        api_key = request.headers.get(self.settings.API_KEY_HEADER)
        
        if not api_key:
            logger.warning(
                "Authentication failed: missing API key",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "action": "auth_missing",
                    "error_type": "missing_key"
                }
            )
            
            error_response = StandardErrorResponse(
                error_code=ErrorCodes.AUTHENTICATION_FAILED,
                message="Chave API necessária",
                details={
                    "header": self.settings.API_KEY_HEADER,
                    "required": True
                },
                request_id=request_id
            )
            
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response.model_dump(mode='json')
            )
            response.headers["X-Request-ID"] = request_id
            return response
        
        if api_key not in self.valid_keys:
            logger.warning(
                "Authentication failed: invalid API key",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "key_prefix": api_key[:8],
                    "action": "auth_invalid",
                    "error_type": "invalid_key"
                }
            )
            
            error_response = StandardErrorResponse(
                error_code=ErrorCodes.AUTHENTICATION_FAILED,
                message="Chave API inválida",
                details={
                    "provided_key": api_key[:8] + "..." if len(api_key) > 8 else api_key
                },
                request_id=request_id
            )
            
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response.model_dump(mode='json')
            )
            response.headers["X-Request-ID"] = request_id
            return response
        
        # Log sucesso
        logger.info(
            "Authentication successful",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "key_prefix": api_key[:8],
                "action": "auth_success"
            }
        )
        
        # Adicionar informações de autenticação ao request
        request.state.api_key = api_key
        request.state.authenticated = True
        
        return await call_next(request)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para tratamento de erros
    v2.1: logs estruturados, request_id propagado
    """
    
    async def dispatch(self, request: Request, call_next):
        """Processar tratamento de erros"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        try:
            return await call_next(request)
        except HTTPException:
            # Re-raise HTTP exceptions (já tratadas)
            raise
        except Exception as e:
            # Log estruturado do erro
            logger.error(
                "Unhandled exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "exception_type": type(e).__name__,
                    "error": str(e),
                    "action": "unhandled_exception",
                    "error_type": "internal"
                },
                exc_info=True
            )
            
            # Resposta de erro
            error_response = StandardErrorResponse(
                error_code=ErrorCodes.INTERNAL_ERROR,
                message="Erro interno do servidor",
                details={
                    "exception_type": type(e).__name__,
                    "error": str(e)
                },
                request_id=request_id
            )
            
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump(mode='json')
            )
            response.headers["X-Request-ID"] = request_id
            
            return response

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
                content=error_response.model_dump(mode='json')
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
                content=error_response.model_dump(mode='json')
            )
        
        return await call_next(request)
