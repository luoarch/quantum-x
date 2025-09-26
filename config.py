"""
Configurações do Sistema de Spillovers
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

class Config:
    """Configurações do sistema"""
    
    # FRED API
    FRED_API_KEY: Optional[str] = os.getenv('FRED_API_KEY')
    
    # Configurações de dados
    DATA_START_DATE: str = "1990-01-01"
    DATA_END_DATE: str = "2025-09-30"
    
    # Configurações de validação
    VALIDATION_FOLDS: int = 5
    CONFIDENCE_LEVEL: float = 0.95
    
    # Configurações de logging
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Configurações do modelo
    VAR_LAGS: int = 12
    NN_HIDDEN_LAYERS: tuple = (50, 25)
    SIMPLE_WEIGHT: float = 0.4
    COMPLEX_WEIGHT: float = 0.6
    RANDOM_STATE: int = 42
    
    @classmethod
    def validate_fred_api(cls) -> bool:
        """Validar se FRED API está configurada"""
        return cls.FRED_API_KEY is not None and len(cls.FRED_API_KEY) > 0
    
    @classmethod
    def get_fred_api_key(cls) -> str:
        """Obter FRED API key"""
        if not cls.validate_fred_api():
            raise ValueError(
                "FRED_API_KEY não configurada. "
                "Configure com: export FRED_API_KEY='sua_chave_aqui'"
            )
        return cls.FRED_API_KEY
