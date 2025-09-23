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
    
    # Application
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Data Collection
    DATA_UPDATE_INTERVAL: int = 3600  # 1 hora em segundos
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    
    # BCB API Configuration
    BCB_BASE_URL: str = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
    BCB_SERIES: dict = {
        'ipca': 433,      # IPCA mensal
        'selic': 432,     # Taxa Selic
        'cambio': 1,      # USD/BRL
        'prod_ind': 21859 # Produção Industrial
    }
    
    # OECD API Configuration
    OECD_BASE_URL: str = "https://stats.oecd.org/restsdmx/sdmx.ashx/GetData"
    OECD_COUNTRIES: list = ['BRA', 'USA', 'CHN', 'OECD']
    
    # IPEA API Configuration
    IPEA_BASE_URL: str = "http://www.ipeadata.gov.br/api/odata4"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instância global das configurações
settings = Settings()
