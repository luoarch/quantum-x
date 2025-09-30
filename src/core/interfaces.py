"""
Interfaces e Contratos - Dependency Inversion Principle
Definições abstratas para inversão de dependência
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from datetime import datetime

class IDataRepository(ABC):
    """Interface para repositórios de dados"""
    
    @abstractmethod
    async def get_fed_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Obter dados do Fed"""
        pass
    
    @abstractmethod
    async def get_selic_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Obter dados da Selic/Copom"""
        pass
    
    @abstractmethod
    async def get_copom_calendar(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Obter calendário do Copom"""
        pass

class IModelService(ABC):
    """Interface para serviços de modelo"""
    
    @abstractmethod
    async def train_model(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Treinar modelo"""
        pass
    
    @abstractmethod
    async def predict(self, fed_shock: float, horizon_months: List[int]) -> Dict[str, Any]:
        """Fazer previsão"""
        pass
    
    @abstractmethod
    async def evaluate_model(self) -> Dict[str, Any]:
        """Avaliar modelo"""
        pass

class IStationarityService(ABC):
    """Interface para testes de estacionariedade"""
    
    @abstractmethod
    async def test_stationarity(self, series: pd.Series) -> Dict[str, Any]:
        """Testar estacionariedade"""
        pass
    
    @abstractmethod
    async def detect_structural_breaks(self, series: pd.Series) -> Dict[str, Any]:
        """Detectar quebras estruturais"""
        pass

class IProbabilityEngine(ABC):
    """Interface para engine de probabilidades"""
    
    @abstractmethod
    async def convert_to_probabilities(self, 
                                     forecasts: Dict[str, Any], 
                                     copom_calendar: pd.DataFrame) -> Dict[str, Any]:
        """Converter previsões em probabilidades"""
        pass
    
    @abstractmethod
    async def discretize_movements(self, 
                                 movements: List[float], 
                                 step: int = 25) -> List[Dict[str, Any]]:
        """Discretizar movimentos em múltiplos de 25 bps"""
        pass

class IValidationService(ABC):
    """Interface para validação de dados"""
    
    @abstractmethod
    async def validate_fed_data(self, data: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validar dados do Fed"""
        pass
    
    @abstractmethod
    async def validate_selic_data(self, data: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validar dados da Selic"""
        pass
    
    @abstractmethod
    async def validate_prediction_request(self, request: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validar request de previsão"""
        pass

class ILoggingService(ABC):
    """Interface para logging"""
    
    @abstractmethod
    async def log_prediction_request(self, request_id: str, request: Dict[str, Any]) -> None:
        """Log de request de previsão"""
        pass
    
    @abstractmethod
    async def log_prediction_response(self, request_id: str, response: Dict[str, Any]) -> None:
        """Log de response de previsão"""
        pass
    
    @abstractmethod
    async def log_error(self, request_id: str, error: Exception) -> None:
        """Log de erro"""
        pass

class IMetricsService(ABC):
    """Interface para métricas"""
    
    @abstractmethod
    async def record_prediction_latency(self, request_id: str, latency_ms: float) -> None:
        """Registrar latência de previsão"""
        pass
    
    @abstractmethod
    async def record_model_performance(self, model_version: str, metrics: Dict[str, float]) -> None:
        """Registrar performance do modelo"""
        pass
    
    @abstractmethod
    async def get_health_metrics(self) -> Dict[str, Any]:
        """Obter métricas de saúde"""
        pass

class IModelFactory(ABC):
    """Interface para factory de modelos"""
    
    @abstractmethod
    async def create_lp_model(self, config: Dict[str, Any]) -> IModelService:
        """Criar modelo Local Projections"""
        pass
    
    @abstractmethod
    async def create_bvar_model(self, config: Dict[str, Any]) -> IModelService:
        """Criar modelo BVAR Minnesota"""
        pass
    
    @abstractmethod
    async def get_model_by_version(self, version: str) -> IModelService:
        """Obter modelo por versão"""
        pass

class IConfigurationService(ABC):
    """Interface para configuração"""
    
    @abstractmethod
    async def get_model_config(self, model_type: str) -> Dict[str, Any]:
        """Obter configuração do modelo"""
        pass
    
    @abstractmethod
    async def get_api_config(self) -> Dict[str, Any]:
        """Obter configuração da API"""
        pass
    
    @abstractmethod
    async def get_data_config(self) -> Dict[str, Any]:
        """Obter configuração de dados"""
        pass

class IDataProcessor(ABC):
    """Interface para processamento de dados"""
    
    @abstractmethod
    async def align_fed_selic_data(self, 
                                 fed_data: pd.DataFrame, 
                                 selic_data: pd.DataFrame) -> pd.DataFrame:
        """Alinhar dados Fed-Selic"""
        pass
    
    @abstractmethod
    async def create_lag_features(self, 
                                data: pd.DataFrame, 
                                max_lags: int) -> pd.DataFrame:
        """Criar features de lag"""
        pass
    
    @abstractmethod
    async def detect_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """Detectar e tratar outliers"""
        pass

class ICacheService(ABC):
    """Interface para cache"""
    
    @abstractmethod
    async def get_cached_prediction(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Obter previsão do cache"""
        pass
    
    @abstractmethod
    async def cache_prediction(self, 
                             cache_key: str, 
                             prediction: Dict[str, Any], 
                             ttl_seconds: int) -> None:
        """Cachear previsão"""
        pass
    
    @abstractmethod
    async def invalidate_model_cache(self, model_version: str) -> None:
        """Invalidar cache do modelo"""
        pass

class IErrorHandler(ABC):
    """Interface para tratamento de erros"""
    
    @abstractmethod
    async def handle_validation_error(self, error: Exception) -> Dict[str, Any]:
        """Tratar erro de validação"""
        pass
    
    @abstractmethod
    async def handle_model_error(self, error: Exception) -> Dict[str, Any]:
        """Tratar erro de modelo"""
        pass
    
    @abstractmethod
    async def handle_data_error(self, error: Exception) -> Dict[str, Any]:
        """Tratar erro de dados"""
        pass
