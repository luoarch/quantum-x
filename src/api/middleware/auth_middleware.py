"""
Auth Middleware - Single Responsibility Principle
Middleware responsável por autenticação e autorização
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import os

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware de autenticação
    
    Responsabilidades:
    - Validar chaves de API
    - Aplicar controle de acesso
    - Logging de eventos de segurança
    """
    
    def __init__(self, app, api_key_header: str = "X-API-Key"):
        super().__init__(app)
        self.api_key_header = api_key_header
        self.valid_api_keys = self._load_valid_api_keys()
        self.security = HTTPBearer(auto_error=False)
    
    def _load_valid_api_keys(self) -> set:
        """Carregar chaves de API válidas"""
        # Em produção, carregar de banco de dados ou serviço de secrets
        api_keys = os.getenv("VALID_API_KEYS", "").split(",")
        return {key.strip() for key in api_keys if key.strip()}
    
    async def dispatch(self, request: Request, call_next):
        """Processar request com autenticação"""
        
        # Rotas que não precisam de autenticação
        public_routes = ["/", "/health", "/docs", "/redoc", "/openapi.json"]
        if request.url.path in public_routes:
            return await call_next(request)
        
        # Verificar chave de API
        api_key = request.headers.get(self.api_key_header)
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "MISSING_API_KEY",
                    "error_message": f"Chave de API necessária no header {self.api_key_header}"
                }
            )
        
        if api_key not in self.valid_api_keys:
            # Log de evento de segurança
            await self._log_security_event("invalid_api_key", {
                "api_key": api_key[:8] + "...",  # Log apenas parte da chave
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "endpoint": request.url.path
            })
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "INVALID_API_KEY",
                    "error_message": "Chave de API inválida"
                }
            )
        
        # Adicionar informações de autenticação ao request
        request.state.authenticated = True
        request.state.api_key = api_key
        
        return await call_next(request)
    
    async def _log_security_event(self, event_type: str, details: dict):
        """Log de evento de segurança"""
        # TODO: Implementar logging real de eventos de segurança
        print(f"SECURITY_EVENT: {event_type} - {details}")

class APIKeyValidator:
    """Validador de chaves de API"""
    
    def __init__(self, valid_keys: set):
        self.valid_keys = valid_keys
    
    def validate(self, api_key: str) -> bool:
        """Validar chave de API"""
        return api_key in self.valid_keys
    
    def get_key_info(self, api_key: str) -> Optional[dict]:
        """Obter informações da chave de API"""
        if not self.validate(api_key):
            return None
        
        # TODO: Implementar obtenção real de informações da chave
        return {
            "key_id": api_key[:8],
            "permissions": ["read", "predict"],
            "rate_limit": 1000,
            "expires_at": None
        }
