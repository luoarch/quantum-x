"""
Configurações da aplicação
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # API
    API_TITLE: str = "FED-Selic Prediction API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API para previsão probabilística da Selic condicionada a movimentos do Fed"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")  # development, staging, production
    
    # Servidor
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["*"],
        env="ALLOWED_ORIGINS"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"],
        env="ALLOWED_HOSTS"
    )
    
    # Autenticação
    API_KEY_HEADER: str = "X-API-Key"
    API_KEYS: List[str] = Field(
        default=["dev-key-123", "test-key-456"],
        env="API_KEYS"
    )
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 hora
    
    # Modelos
    DEFAULT_MODEL_VERSION: str = "v1.0.0"
    MODEL_CACHE_SIZE: int = Field(default=5, env="MODEL_CACHE_SIZE")
    
    # Dados
    DATA_DIR: str = Field(default="data", env="DATA_DIR")
    FED_SELIC_DATA_PATH: str = "raw/fed_selic_combined.csv"
    FED_DETAILED_DATA_PATH: str = "raw/fed_detailed_data.csv"
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Observabilidade
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    ENABLE_TRACING: bool = Field(default=True, env="ENABLE_TRACING")
    
    # Redis (para cache e rate limiting)
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    
    # Validação
    MAX_BATCH_SIZE: int = Field(default=100, env="MAX_BATCH_SIZE")
    MAX_HORIZONS: int = Field(default=12, env="MAX_HORIZONS")
    MIN_HORIZONS: int = Field(default=1, env="MIN_HORIZONS")
    
    # Modelo ML
    DEFAULT_METHODOLOGY: str = "LP primary, BVAR fallback"
    CONFIDENCE_LEVELS: List[float] = [0.80, 0.95]
    DISCRETIZATION_BPS: int = 25
    
    # Performance
    MAX_LATENCY_MS: int = Field(default=250, env="MAX_LATENCY_MS")
    TIMEOUT_SECONDS: int = Field(default=30, env="TIMEOUT_SECONDS")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar campos extras

# Instância global das configurações
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Obter configurações da aplicação"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reload_settings():
    """Recarregar configurações"""
    global _settings
    _settings = None
    return get_settings()
