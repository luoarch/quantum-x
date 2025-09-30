"""
Configuração da aplicação Quantum-X
Configurações centralizadas conforme requisitos
"""

import os
from typing import Dict, Any

# Configuração da API
API_CONFIG = {
    "version": "v1.0.0",
    "title": "Quantum-X: Spillover Intelligence FED-Selic",
    "description": "API de Previsão Probabilística da Selic Condicionada ao Fed",
    "max_requests_per_minute": int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60")),
    "max_requests_per_day": int(os.getenv("MAX_REQUESTS_PER_DAY", "1000")),
    "timeout_seconds": int(os.getenv("TIMEOUT_SECONDS", "30")),
    "enable_cors": os.getenv("ENABLE_CORS", "true").lower() == "true",
    "enable_metrics": os.getenv("ENABLE_METRICS", "true").lower() == "true",
    "enable_docs": os.getenv("ENABLE_DOCS", "true").lower() == "true"
}

# Configuração dos modelos
MODEL_CONFIG = {
    "local_projections": {
        "max_horizon": int(os.getenv("LP_MAX_HORIZON", "12")),
        "max_lags": int(os.getenv("LP_MAX_LAGS", "4")),
        "alpha": float(os.getenv("LP_ALPHA", "0.1")),
        "regularization": os.getenv("LP_REGULARIZATION", "ridge")
    },
    "bvar_minnesota": {
        "n_lags": int(os.getenv("BVAR_N_LAGS", "2")),
        "n_vars": int(os.getenv("BVAR_N_VARS", "2")),
        "n_simulations": int(os.getenv("BVAR_N_SIMULATIONS", "1000")),
        "minnesota_params": {
            "lambda1": float(os.getenv("BVAR_LAMBDA1", "0.1")),
            "lambda2": float(os.getenv("BVAR_LAMBDA2", "0.5")),
            "lambda3": float(os.getenv("BVAR_LAMBDA3", "1.0")),
            "lambda4": float(os.getenv("BVAR_LAMBDA4", "0.1")),
            "mu": float(os.getenv("BVAR_MU", "0.0")),
            "sigma": float(os.getenv("BVAR_SIGMA", "1.0"))
        }
    }
}

# Configuração de dados
DATA_CONFIG = {
    "fed_data_source": os.getenv("FED_DATA_SOURCE", "fred"),
    "selic_data_source": os.getenv("SELIC_DATA_SOURCE", "bcb"),
    "fred_api_key": os.getenv("FRED_API_KEY", ""),
    "bcb_api_url": os.getenv("BCB_API_URL", "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados"),
    "update_frequency": os.getenv("DATA_UPDATE_FREQUENCY", "daily"),
    "data_retention_days": int(os.getenv("DATA_RETENTION_DAYS", "365"))
}

# Configuração de cache
CACHE_CONFIG = {
    "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "default_ttl": int(os.getenv("CACHE_DEFAULT_TTL", "3600")),
    "model_cache_ttl": int(os.getenv("CACHE_MODEL_TTL", "86400"))
}

# Configuração de logging
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": os.getenv("LOG_FORMAT", "json"),
    "file": os.getenv("LOG_FILE"),
    "enable_request_logging": os.getenv("ENABLE_REQUEST_LOGGING", "true").lower() == "true"
}

# Configuração de métricas
METRICS_CONFIG = {
    "backend": os.getenv("METRICS_BACKEND", "prometheus"),
    "port": int(os.getenv("METRICS_PORT", "9090")),
    "enable_collection": os.getenv("ENABLE_METRICS_COLLECTION", "true").lower() == "true"
}

# Configuração de validação
VALIDATION_CONFIG = {
    "fed_move_bps_range": (-200, 200),
    "horizons_months_range": (1, 24),
    "max_batch_size": int(os.getenv("MAX_BATCH_SIZE", "10")),
    "fed_move_step": 25,  # Múltiplos de 25 bps conforme requisitos
    "max_future_days": int(os.getenv("MAX_FUTURE_DAYS", "30"))
}

# Configuração de estacionariedade
STATIONARITY_CONFIG = {
    "significance_level": float(os.getenv("STATIONARITY_SIGNIFICANCE", "0.05")),
    "max_lags": int(os.getenv("STATIONARITY_MAX_LAGS", "4")),
    "tests": ["adf", "kpss", "dfgls", "pp", "za"]
}

# Configuração de tratamento de erros
ERROR_HANDLING_CONFIG = {
    "include_details": os.getenv("ENVIRONMENT", "production") == "development",
    "log_errors": os.getenv("LOG_ERRORS", "true").lower() == "true",
    "notify_errors": os.getenv("NOTIFY_ERRORS", "false").lower() == "true"
}

# Configuração de processamento de dados
DATA_PROCESSING_CONFIG = {
    "outlier_threshold": float(os.getenv("OUTLIER_THRESHOLD", "3.0")),
    "outlier_treatment": os.getenv("OUTLIER_TREATMENT", "winsorize"),  # remove, cap, winsorize
    "max_lags": int(os.getenv("DATA_MAX_LAGS", "4"))
}

# Configuração de autenticação
AUTH_CONFIG = {
    "api_key_header": "X-API-Key",
    "valid_api_keys": os.getenv("VALID_API_KEYS", "").split(","),
    "enable_auth": os.getenv("ENABLE_AUTH", "true").lower() == "true"
}

# Configuração de rate limiting
RATE_LIMIT_CONFIG = {
    "max_requests_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
    "max_requests_per_day": int(os.getenv("RATE_LIMIT_PER_DAY", "1000")),
    "enable_rate_limiting": os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
}

# Configuração completa da aplicação
APP_CONFIG = {
    "api": API_CONFIG,
    "model": MODEL_CONFIG,
    "data": DATA_CONFIG,
    "cache": CACHE_CONFIG,
    "logging": LOGGING_CONFIG,
    "metrics": METRICS_CONFIG,
    "validation": VALIDATION_CONFIG,
    "stationarity": STATIONARITY_CONFIG,
    "error_handling": ERROR_HANDLING_CONFIG,
    "data_processing": DATA_PROCESSING_CONFIG,
    "auth": AUTH_CONFIG,
    "rate_limit": RATE_LIMIT_CONFIG
}

# Configuração de ambiente
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Configuração do servidor
SERVER_CONFIG = {
    "host": os.getenv("HOST", "0.0.0.0"),
    "port": int(os.getenv("PORT", "8000")),
    "workers": int(os.getenv("WORKERS", "1")),
    "reload": DEBUG
}

def get_config() -> Dict[str, Any]:
    """Obter configuração completa da aplicação"""
    return APP_CONFIG

def get_config_section(section: str) -> Dict[str, Any]:
    """Obter seção específica da configuração"""
    return APP_CONFIG.get(section, {})

def is_development() -> bool:
    """Verificar se está em ambiente de desenvolvimento"""
    return ENVIRONMENT == "development" or DEBUG

def is_production() -> bool:
    """Verificar se está em ambiente de produção"""
    return ENVIRONMENT == "production" and not DEBUG
