"""
Error Handler Service - Single Responsibility Principle
Serviço responsável por tratamento de erros
"""

from typing import Dict, Any
from datetime import datetime

from src.core.interfaces import IErrorHandler
from src.core.exceptions import (
    ValidationError, ModelError, DataError, PredictionError,
    ConfigurationError, ServiceUnavailableError, RateLimitError,
    CacheError, AuthenticationError, AuthorizationError
)

class ErrorHandlerService(IErrorHandler):
    """
    Serviço de tratamento de erros
    
    Responsabilidades:
    - Tratar erros de validação
    - Tratar erros de modelo
    - Tratar erros de dados
    - Logging de erros
    """
    
    def __init__(self, error_config: Dict[str, Any] = None):
        self.error_config = error_config or {}
        self.include_details = self.error_config.get('include_details', False)
        self.log_errors = self.error_config.get('log_errors', True)
    
    async def handle_validation_error(self, error: Exception) -> Dict[str, Any]:
        """Tratar erro de validação"""
        error_response = {
            "error_code": "VALIDATION_ERROR",
            "error_message": "Dados de entrada inválidos",
            "timestamp": datetime.now().isoformat()
        }
        
        if isinstance(error, ValidationError):
            error_response.update({
                "error_code": error.error_code,
                "error_message": error.message,
                "field": error.details.get("field"),
                "value": error.details.get("value")
            })
        
        if self.include_details:
            error_response["details"] = {
                "exception_type": type(error).__name__,
                "original_message": str(error)
            }
        
        if self.log_errors:
            await self._log_error("validation", error, error_response)
        
        return error_response
    
    async def handle_model_error(self, error: Exception) -> Dict[str, Any]:
        """Tratar erro de modelo"""
        error_response = {
            "error_code": "MODEL_ERROR",
            "error_message": "Erro no processamento do modelo",
            "timestamp": datetime.now().isoformat()
        }
        
        if isinstance(error, ModelError):
            error_response.update({
                "error_code": error.error_code,
                "error_message": error.message,
                "model_type": error.details.get("model_type"),
                "operation": error.details.get("operation")
            })
        
        if self.include_details:
            error_response["details"] = {
                "exception_type": type(error).__name__,
                "original_message": str(error)
            }
        
        if self.log_errors:
            await self._log_error("model", error, error_response)
        
        return error_response
    
    async def handle_data_error(self, error: Exception) -> Dict[str, Any]:
        """Tratar erro de dados"""
        error_response = {
            "error_code": "DATA_ERROR",
            "error_message": "Erro no processamento de dados",
            "timestamp": datetime.now().isoformat()
        }
        
        if isinstance(error, DataError):
            error_response.update({
                "error_code": error.error_code,
                "error_message": error.message,
                "source": error.details.get("source"),
                "operation": error.details.get("operation")
            })
        
        if self.include_details:
            error_response["details"] = {
                "exception_type": type(error).__name__,
                "original_message": str(error)
            }
        
        if self.log_errors:
            await self._log_error("data", error, error_response)
        
        return error_response
    
    async def handle_prediction_error(self, error: Exception) -> Dict[str, Any]:
        """Tratar erro de previsão"""
        error_response = {
            "error_code": "PREDICTION_ERROR",
            "error_message": "Erro na geração de previsão",
            "timestamp": datetime.now().isoformat()
        }
        
        if isinstance(error, PredictionError):
            error_response.update({
                "error_code": error.error_code,
                "error_message": error.message,
                "request_id": error.details.get("request_id"),
                "horizon": error.details.get("horizon")
            })
        
        if self.include_details:
            error_response["details"] = {
                "exception_type": type(error).__name__,
                "original_message": str(error)
            }
        
        if self.log_errors:
            await self._log_error("prediction", error, error_response)
        
        return error_response
    
    async def handle_generic_error(self, error: Exception) -> Dict[str, Any]:
        """Tratar erro genérico"""
        error_response = {
            "error_code": "INTERNAL_ERROR",
            "error_message": "Erro interno do servidor",
            "timestamp": datetime.now().isoformat()
        }
        
        # Mapear tipos de erro específicos
        if isinstance(error, ValidationError):
            return await self.handle_validation_error(error)
        elif isinstance(error, ModelError):
            return await self.handle_model_error(error)
        elif isinstance(error, DataError):
            return await self.handle_data_error(error)
        elif isinstance(error, PredictionError):
            return await self.handle_prediction_error(error)
        elif isinstance(error, ConfigurationError):
            error_response.update({
                "error_code": "CONFIGURATION_ERROR",
                "error_message": "Erro de configuração",
                "config_key": getattr(error, 'details', {}).get("config_key")
            })
        elif isinstance(error, ServiceUnavailableError):
            error_response.update({
                "error_code": "SERVICE_UNAVAILABLE",
                "error_message": "Serviço temporariamente indisponível",
                "service": getattr(error, 'details', {}).get("service"),
                "retry_after": getattr(error, 'details', {}).get("retry_after")
            })
        elif isinstance(error, RateLimitError):
            error_response.update({
                "error_code": "RATE_LIMIT_ERROR",
                "error_message": "Limite de requests excedido",
                "limit": getattr(error, 'details', {}).get("limit"),
                "reset_time": getattr(error, 'details', {}).get("reset_time")
            })
        elif isinstance(error, CacheError):
            error_response.update({
                "error_code": "CACHE_ERROR",
                "error_message": "Erro no sistema de cache",
                "operation": getattr(error, 'details', {}).get("operation"),
                "key": getattr(error, 'details', {}).get("key")
            })
        elif isinstance(error, AuthenticationError):
            error_response.update({
                "error_code": "AUTHENTICATION_ERROR",
                "error_message": "Erro de autenticação",
                "api_key": getattr(error, 'details', {}).get("api_key")
            })
        elif isinstance(error, AuthorizationError):
            error_response.update({
                "error_code": "AUTHORIZATION_ERROR",
                "error_message": "Erro de autorização",
                "resource": getattr(error, 'details', {}).get("resource"),
                "action": getattr(error, 'details', {}).get("action")
            })
        
        if self.include_details:
            error_response["details"] = {
                "exception_type": type(error).__name__,
                "original_message": str(error)
            }
        
        if self.log_errors:
            await self._log_error("generic", error, error_response)
        
        return error_response
    
    async def _log_error(self, error_type: str, error: Exception, error_response: Dict[str, Any]):
        """Log de erro"""
        # TODO: Implementar logging real
        print(f"ERROR_LOG: {error_type} - {error_response['error_code']} - {error_response['error_message']}")
    
    def get_error_suggestions(self, error_code: str) -> list:
        """Obter sugestões para erro específico"""
        suggestions_map = {
            "VALIDATION_ERROR": [
                "Verifique se todos os campos obrigatórios estão preenchidos",
                "Confirme se os valores estão dentro dos limites permitidos",
                "Verifique o formato das datas (ISO-8601)"
            ],
            "MODEL_ERROR": [
                "O modelo pode não estar treinado",
                "Verifique se há dados suficientes para a previsão",
                "Tente novamente em alguns minutos"
            ],
            "DATA_ERROR": [
                "Verifique se as fontes de dados estão disponíveis",
                "Confirme se os dados estão no formato correto",
                "Tente novamente mais tarde"
            ],
            "PREDICTION_ERROR": [
                "Verifique se os parâmetros de entrada estão corretos",
                "O modelo pode estar temporariamente indisponível",
                "Tente com horizontes diferentes"
            ],
            "RATE_LIMIT_ERROR": [
                "Aguarde antes de fazer nova requisição",
                "Considere usar previsões em lote",
                "Verifique seu plano de rate limiting"
            ],
            "AUTHENTICATION_ERROR": [
                "Verifique se a chave de API está correta",
                "Confirme se a chave não expirou",
                "Entre em contato com o suporte"
            ]
        }
        
        return suggestions_map.get(error_code, [
            "Tente novamente em alguns minutos",
            "Verifique os parâmetros de entrada",
            "Entre em contato com o suporte se o problema persistir"
        ])
