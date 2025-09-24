"""
Configurações da aplicação
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Database
    DATABASE_URL: str = "postgresql://luoarch:postgres@localhost:5432/quantum_x_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Keys
    BCB_API_KEY: Optional[str] = None
    OECD_API_KEY: Optional[str] = None
    TRADING_ECONOMICS_API_KEY: Optional[str] = None
    FRED_API_KEY: Optional[str] = "90157114039846fe14d8993faa2f11c7"  # Federal Reserve API key
    
    # Application
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Data Collection
    DATA_UPDATE_INTERVAL: int = 3600  # 1 hora em segundos
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    
    # Data Sources Configuration
    BCB_BASE_URL: str = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
    IPEA_BASE_URL: str = "http://www.ipeadata.gov.br/api/odata4"
    OECD_BASE_URL: str = "https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI/.M.LI...AA...H"
    TRADING_ECONOMICS_BASE_URL: str = "https://api.tradingeconomics.com"
    
    # Rate Limiting
    OECD_RATE_LIMIT: float = 5.0  # segundos entre requisições (OECD limitou a 20/hora)
    BCB_RATE_LIMIT: float = 2.0
    IPEA_RATE_LIMIT: float = 3.0
    
    # Series Configuration
    BCB_SERIES: dict = {
        "ipca": 433,
        "selic": 432,
        "pib": 4380,
        "cambio": 1
    }
    
    IPEA_SERIES: dict = {
        "desemprego": "PNADC12_TDESOC12",
        "cambio": "BM12_TJOVER12"
    }
    
    OECD_COUNTRIES: list = ['BRA', 'USA', 'CHN', 'OECD', 'EA19', 'DEU', 'GBR']
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instância global das configurações
settings = Settings()
