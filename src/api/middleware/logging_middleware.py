"""
Logging Middleware - Single Responsibility Principle
Middleware responsável por logging de requests e responses
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any
import time
import uuid
from datetime import datetime

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware de logging
    
    Responsabilidades:
    - Log de requests HTTP
    - Log de responses HTTP
    - Métricas de latência
    - Rastreamento de requests
    """
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next):
        """Processar request com logging"""
        
        # Gerar ID único para o request
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Timestamp de início
        start_time = time.time()
        
        # Log do request
        if self.log_requests:
            await self._log_request(request, request_id)
        
        # Processar request
        try:
            response = await call_next(request)
            
            # Calcular latência
            processing_time = (time.time() - start_time) * 1000  # ms
            
            # Log da response
            if self.log_responses:
                await self._log_response(request, response, request_id, processing_time)
            
            # Adicionar headers de rastreamento
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time"] = f"{processing_time:.2f}ms"
            
            return response
            
        except Exception as e:
            # Log de erro
            processing_time = (time.time() - start_time) * 1000
            await self._log_error(request, e, request_id, processing_time)
            raise
    
    async def _log_request(self, request: Request, request_id: str):
        """Log do request"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "http_request",
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "api_key": request.headers.get("X-API-Key", "N/A")[:8] + "..." if request.headers.get("X-API-Key") else "N/A"
        }
        
        # Log estruturado
        print(f"REQUEST: {request_id} - {request.method} {request.url.path}")
    
    async def _log_response(self, request: Request, response: Response, 
                          request_id: str, processing_time: float):
        """Log da response"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "http_response",
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "processing_time_ms": processing_time,
            "response_size": len(response.body) if hasattr(response, 'body') else 0,
            "api_key": request.headers.get("X-API-Key", "N/A")[:8] + "..." if request.headers.get("X-API-Key") else "N/A"
        }
        
        # Log estruturado
        print(f"RESPONSE: {request_id} - {response.status_code} - {processing_time:.2f}ms")
    
    async def _log_error(self, request: Request, error: Exception, 
                        request_id: str, processing_time: float):
        """Log de erro"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "http_error",
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "processing_time_ms": processing_time,
            "api_key": request.headers.get("X-API-Key", "N/A")[:8] + "..." if request.headers.get("X-API-Key") else "N/A"
        }
        
        # Log estruturado
        print(f"ERROR: {request_id} - {type(error).__name__} - {str(error)}")

class RequestTracer:
    """Rastreador de requests para auditoria"""
    
    def __init__(self):
        self.active_requests: Dict[str, Dict[str, Any]] = {}
    
    def start_request(self, request_id: str, request: Request):
        """Iniciar rastreamento de request"""
        self.active_requests[request_id] = {
            "start_time": datetime.now(),
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "api_key": request.headers.get("X-API-Key", "N/A")[:8] + "..."
        }
    
    def end_request(self, request_id: str, response: Response, processing_time: float):
        """Finalizar rastreamento de request"""
        if request_id in self.active_requests:
            self.active_requests[request_id].update({
                "end_time": datetime.now(),
                "status_code": response.status_code,
                "processing_time_ms": processing_time
            })
            
            # Remover do tracking ativo
            del self.active_requests[request_id]
    
    def get_active_requests(self) -> Dict[str, Dict[str, Any]]:
        """Obter requests ativos"""
        return self.active_requests.copy()
