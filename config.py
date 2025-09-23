"""
Configuração Consolidada - Quantum X Trading Signals
Centraliza todas as configurações do sistema
"""

import os
from pathlib import Path
from typing import Dict, Any

# Diretório base do projeto
BASE_DIR = Path(__file__).parent

class Config:
    """Configurações principais do sistema"""
    
    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql://luoarch:postgres@localhost:5432/quantum_x_db"
    )
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # APIs Externas
    BCB_API_KEY = os.getenv("BCB_API_KEY", "")
    OECD_API_KEY = os.getenv("OECD_API_KEY", "")
    TRADING_ECONOMICS_API_KEY = os.getenv("TRADING_ECONOMICS_API_KEY", "")
    
    # Aplicação
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # Sistema de Trading
    CONFIDENCE_THRESHOLD = 0.6
    MAX_POSITION_SIZE = 0.8
    MAX_DRAWDOWN = 0.15
    
    # Markov-Switching
    N_REGIMES = 4
    REGIME_NAMES = ['RECESSION', 'RECOVERY', 'EXPANSION', 'CONTRACTION']
    
    # HRP
    HRP_LOOKBACK = 252  # 1 ano de dados
    HRP_REBALANCE_FREQ = 30  # Rebalanceamento mensal
    
    # Backtesting
    BACKTEST_START_DATE = "2010-01-01"
    BACKTEST_END_DATE = "2025-12-31"
    
    # Séries BCB
    BCB_SERIES = {
        'ipca': 433,
        'selic': 432,
        'cambio': 1,
        'prod_industrial': 21859,
        'pib_mensal': 4380,
        'desemprego': 24369
    }
    
    # Países OECD
    OECD_COUNTRIES = ['BRA', 'USA', 'CHN', 'OECD']
    
    # Ativos para Backtesting
    ASSETS = {
        'tesouro_ipca_2045': {
            'ticker': 'TESOURO_IPCA',
            'duration': 20,
            'type': 'bond'
        },
        'bova11': {
            'ticker': 'BOVA11',
            'type': 'equity'
        }
    }

class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    LOG_LEVEL = "INFO"

# Configuração baseada no ambiente
def get_config() -> Config:
    """Retorna configuração baseada no ambiente"""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()

# Instância global
config = get_config()
