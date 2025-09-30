"""
Custom Exceptions - Single Responsibility Principle
Exceções específicas do domínio FED-Selic
"""

from typing import Any

class QuantumXException(Exception):
    """Exceção base do sistema Quantum-X"""
    def __init__(self, message: str, error_code: str = "QUANTUM_X_ERROR", details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(QuantumXException):
    """Erro de validação de dados"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": value}
        )

class DataError(QuantumXException):
    """Erro relacionado a dados"""
    def __init__(self, message: str, source: str = None, operation: str = None):
        super().__init__(
            message=message,
            error_code="DATA_ERROR",
            details={"source": source, "operation": operation}
        )

class ModelError(QuantumXException):
    """Erro relacionado a modelos"""
    def __init__(self, message: str, model_type: str = None, operation: str = None):
        super().__init__(
            message=message,
            error_code="MODEL_ERROR",
            details={"model_type": model_type, "operation": operation}
        )

class PredictionError(QuantumXException):
    """Erro relacionado a previsões"""
    def __init__(self, message: str, request_id: str = None, horizon: int = None):
        super().__init__(
            message=message,
            error_code="PREDICTION_ERROR",
            details={"request_id": request_id, "horizon": horizon}
        )

class ConfigurationError(QuantumXException):
    """Erro de configuração"""
    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key}
        )

class ServiceUnavailableError(QuantumXException):
    """Serviço indisponível"""
    def __init__(self, message: str, service: str = None, retry_after: int = None):
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service, "retry_after": retry_after}
        )

class RateLimitError(QuantumXException):
    """Erro de limite de taxa"""
    def __init__(self, message: str, limit: int = None, reset_time: int = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details={"limit": limit, "reset_time": reset_time}
        )

class CacheError(QuantumXException):
    """Erro de cache"""
    def __init__(self, message: str, operation: str = None, key: str = None):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details={"operation": operation, "key": key}
        )

class AuthenticationError(QuantumXException):
    """Erro de autenticação"""
    def __init__(self, message: str, api_key: str = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details={"api_key": api_key}
        )

class AuthorizationError(QuantumXException):
    """Erro de autorização"""
    def __init__(self, message: str, resource: str = None, action: str = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details={"resource": resource, "action": action}
        )

class ModelVersionNotFoundError(QuantumXException):
    """Versão do modelo não encontrada"""
    def __init__(self, message: str, version: str = None):
        super().__init__(
            message=message,
            error_code="MODEL_VERSION_NOT_FOUND",
            details={"version": version}
        )

class InsufficientDataError(QuantumXException):
    """Dados insuficientes"""
    def __init__(self, message: str, required: int = None, available: int = None):
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_DATA",
            details={"required": required, "available": available}
        )

class StationarityTestError(QuantumXException):
    """Erro em teste de estacionariedade"""
    def __init__(self, message: str, series_name: str = None, test_type: str = None):
        super().__init__(
            message=message,
            error_code="STATIONARITY_TEST_ERROR",
            details={"series_name": series_name, "test_type": test_type}
        )

class StructuralBreakError(QuantumXException):
    """Erro em detecção de quebra estrutural"""
    def __init__(self, message: str, series_name: str = None, method: str = None):
        super().__init__(
            message=message,
            error_code="STRUCTURAL_BREAK_ERROR",
            details={"series_name": series_name, "method": method}
        )

class ProbabilityEngineError(QuantumXException):
    """Erro no engine de probabilidades"""
    def __init__(self, message: str, operation: str = None):
        super().__init__(
            message=message,
            error_code="PROBABILITY_ENGINE_ERROR",
            details={"operation": operation}
        )

class DataRepositoryError(QuantumXException):
    """Erro no repositório de dados"""
    def __init__(self, message: str, source: str = None, query: str = None):
        super().__init__(
            message=message,
            error_code="DATA_REPOSITORY_ERROR",
            details={"source": source, "query": query}
        )

class ModelTrainingError(QuantumXException):
    """Erro no treinamento do modelo"""
    def __init__(self, message: str, model_type: str = None, stage: str = None):
        super().__init__(
            message=message,
            error_code="MODEL_TRAINING_ERROR",
            details={"model_type": model_type, "stage": stage}
        )

class ModelEvaluationError(QuantumXException):
    """Erro na avaliação do modelo"""
    def __init__(self, message: str, model_version: str = None, metric: str = None):
        super().__init__(
            message=message,
            error_code="MODEL_EVALUATION_ERROR",
            details={"model_version": model_version, "metric": metric}
        )

class ExternalServiceError(QuantumXException):
    """Erro em serviço externo"""
    def __init__(self, message: str, service: str = None, status_code: int = None):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "status_code": status_code}
        )

class TimeoutError(QuantumXException):
    """Erro de timeout"""
    def __init__(self, message: str, operation: str = None, timeout_seconds: int = None):
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            details={"operation": operation, "timeout_seconds": timeout_seconds}
        )

class ConcurrencyError(QuantumXException):
    """Erro de concorrência"""
    def __init__(self, message: str, resource: str = None):
        super().__init__(
            message=message,
            error_code="CONCURRENCY_ERROR",
            details={"resource": resource}
        )

class ResourceNotFoundError(QuantumXException):
    """Recurso não encontrado"""
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None):
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )

class BusinessLogicError(QuantumXException):
    """Erro de lógica de negócio"""
    def __init__(self, message: str, rule: str = None):
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            details={"rule": rule}
        )
