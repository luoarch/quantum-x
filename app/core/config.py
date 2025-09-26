"""
Configuração Central do Sistema - Global Economic Regime Analysis & Brazil Spillover Prediction
Baseado no Documento de Requisitos do Sistema (DRS) v1.0
"""

import os
from pathlib import Path
from typing import Dict, List, Any
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Configurações principais do sistema conforme DRS"""
    
    # === INFORMAÇÕES BÁSICAS ===
    APP_NAME: str = "Global Economic Regime Analysis & Brazil Spillover Prediction System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Sistema científico para análise de regimes econômicos globais e previsão de spillovers para o Brasil"
    
    # === BANCO DE DADOS ===
    DATABASE_URL: str = Field(
        default="postgresql://luoarch:postgres@localhost:5432/global_regime_analysis",
        description="URL do banco PostgreSQL com TimescaleDB"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="URL do Redis para cache"
    )
    
    # === APIS EXTERNAS ===
    FRED_API_KEY: str = Field(default="", description="API Key do FRED")
    OECD_API_KEY: str = Field(default="", description="API Key do OECD")
    WORLD_BANK_API_KEY: str = Field(default="", description="API Key do World Bank")
    YAHOO_FINANCE_ENABLED: bool = Field(default=True, description="Habilitar Yahoo Finance")
    
    # === CONFIGURAÇÕES DE ANÁLISE ===
    # Países conforme DRS (G7 + China + Brasil)
    GLOBAL_COUNTRIES: List[str] = Field(
        default=["USA", "DEU", "JPN", "GBR", "FRA", "ITA", "CAN", "CHN", "BRA"],
        description="Países para análise global"
    )
    
    # Número de regimes (2-6 conforme DRS)
    MIN_REGIMES: int = Field(default=2, description="Número mínimo de regimes")
    MAX_REGIMES: int = Field(default=6, description="Número máximo de regimes")
    
    # Horizonte de previsão (1-12 meses conforme DRS)
    FORECAST_HORIZON: int = Field(default=12, description="Horizonte de previsão em meses")
    
    # === CANAIS DE SPILLOVER ===
    SPILLOVER_CHANNELS: List[str] = Field(
        default=["trade", "commodity", "financial", "supply_chain"],
        description="Canais de spillover conforme DRS"
    )
    
    # === PERFORMANCE (RNF001-RNF010) ===
    API_RESPONSE_TIME_MS: int = Field(default=500, description="Tempo máximo de resposta da API (ms)")
    DASHBOARD_LOAD_TIME_S: int = Field(default=2, description="Tempo máximo de carregamento do dashboard (s)")
    ANALYSIS_EXECUTION_TIME_M: int = Field(default=30, description="Tempo máximo de execução da análise (min)")
    FORECAST_GENERATION_TIME_M: int = Field(default=5, description="Tempo máximo de geração de previsões (min)")
    
    # === DISPONIBILIDADE (RNF011-RNF015) ===
    UPTIME_SLA: float = Field(default=99.9, description="SLA de uptime (%)")
    BACKUP_FREQUENCY_H: int = Field(default=6, description="Frequência de backup (horas)")
    RECOVERY_TIME_M: int = Field(default=15, description="Tempo máximo de recuperação (min)")
    
    # === SEGURANÇA (RNF016-RNF025) ===
    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production", description="Chave secreta JWT")
    JWT_ALGORITHM: str = Field(default="HS256", description="Algoritmo JWT")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Expiração do token de acesso (min)")
    
    # === VALIDAÇÃO DE DADOS (RNF026-RNF035) ===
    MAX_MISSING_DATA_PERCENT: float = Field(default=10.0, description="Percentual máximo de dados faltantes (%)")
    OUTLIER_DETECTION_METHOD: str = Field(default="modified_zscore", description="Método de detecção de outliers")
    CROSS_VALIDATION_FOLDS: int = Field(default=5, description="Número de folds para validação cruzada")
    
    # === CONFIGURAÇÕES DE DESENVOLVIMENTO ===
    DEBUG: bool = Field(default=False, description="Modo debug")
    LOG_LEVEL: str = Field(default="INFO", description="Nível de log")
    HOST: str = Field(default="0.0.0.0", description="Host da aplicação")
    PORT: int = Field(default=8000, description="Porta da aplicação")
    
    # === CACHE ===
    CACHE_TTL_SECONDS: int = Field(default=3600, description="TTL do cache (segundos)")
    CACHE_REGIME_ANALYSIS_TTL: int = Field(default=1800, description="TTL do cache de análise de regimes (segundos)")
    CACHE_SPILLOVER_TTL: int = Field(default=900, description="TTL do cache de spillovers (segundos)")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instância global das configurações
settings = Settings()

# === CONFIGURAÇÕES ESPECÍFICAS POR MÓDULO ===

class DataSourceConfig:
    """Configurações das fontes de dados conforme DRS seção 7.1"""
    
    # Dados Globais
    FRED_SERIES = {
        "US_GDP": "GDP",
        "US_CPI": "CPIAUCSL", 
        "US_UNEMPLOYMENT": "UNRATE",
        "US_FED_RATE": "FEDFUNDS",
        "US_VIX": "VIXCLS"
    }
    
    OECD_SERIES = {
        "G7_LEADING_INDICATORS": "G7_LEADING_INDICATORS",
        "G7_GDP": "G7_GDP",
        "G7_CPI": "G7_CPI"
    }
    
    # Dados Brasil
    BCB_SERIES = {
        "IPCA": 433,
        "SELIC": 432,
        "CAMBIO": 1,
        "PROD_INDUSTRIAL": 21859,
        "PIB_MENSAL": 4380,
        "DESEMPREGO": 24369
    }

class ModelConfig:
    """Configurações dos modelos conforme DRS seção 3"""
    
    # RS-GVAR
    RS_GVAR_MAX_LAGS: int = 4
    RS_GVAR_CONVERGENCE_TOLERANCE: float = 1e-6
    RS_GVAR_MAX_ITERATIONS: int = 1000
    
    # Validação
    OUT_OF_SAMPLE_START_PERCENT: float = 0.8
    MIN_TRAINING_OBSERVATIONS: int = 100
    
    # Spillovers
    SPILLOVER_ELASTICITY_WINDOW: int = 24  # meses
    COMMODITY_WEIGHTS = {
        "iron_ore": 0.25,
        "soybeans": 0.20,
        "crude_oil": 0.15,
        "coffee": 0.10,
        "sugar": 0.08,
        "corn": 0.07,
        "beef": 0.05,
        "poultry": 0.05
    }

# Instâncias das configurações específicas
data_source_config = DataSourceConfig()
model_config = ModelConfig()