"""
Service Factory - Dependency Injection
Factory para criar e injetar dependências
"""

from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from src.core.interfaces import (
    IModelService, IDataRepository, IProbabilityEngine,
    IValidationService, ILoggingService, IMetricsService,
    ICacheService, IErrorHandler, IModelFactory,
    IConfigurationService, IDataProcessor, IStationarityService
)
from src.core.models import ModelConfiguration, APIConfiguration, DataConfiguration
from src.core.exceptions import ConfigurationError

# Importações das implementações (serão criadas)
from src.services.prediction_service import PredictionService
from src.repositories.data_repository import CompositeDataRepository, FedDataRepository, SelicDataRepository
from src.services.model_service import LocalProjectionsModelService, BVARMinnesotaModelService
from src.services.probability_engine import ProbabilityEngineService
from src.services.validation_service import ValidationService
from src.services.logging_service import LoggingService
from src.services.metrics_service import MetricsService
from src.services.cache_service import RedisCacheService
from src.services.error_handler import ErrorHandlerService
from src.services.stationarity_service import StationarityService
from src.services.data_processor import DataProcessorService

class ServiceFactory:
    """
    Factory para criação de serviços com injeção de dependência
    
    Responsabilidades:
    - Criar instâncias de serviços
    - Injetar dependências
    - Gerenciar configurações
    - Singleton pattern para serviços caros
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._instances = {}  # Cache de instâncias (Singleton)
        self._lock = asyncio.Lock()
    
    async def create_prediction_service(self) -> PredictionService:
        """Criar PredictionService com todas as dependências"""
        async with self._lock:
            if 'prediction_service' not in self._instances:
                # Criar dependências
                model_service = await self.create_model_service()
                data_repository = await self.create_data_repository()
                probability_engine = await self.create_probability_engine()
                validation_service = await self.create_validation_service()
                logging_service = await self.create_logging_service()
                metrics_service = await self.create_metrics_service()
                cache_service = await self.create_cache_service()
                error_handler = await self.create_error_handler()
                
                # Criar PredictionService
                self._instances['prediction_service'] = PredictionService(
                    model_service=model_service,
                    data_repository=data_repository,
                    probability_engine=probability_engine,
                    validation_service=validation_service,
                    logging_service=logging_service,
                    metrics_service=metrics_service,
                    cache_service=cache_service,
                    error_handler=error_handler
                )
            
            return self._instances['prediction_service']
    
    async def create_model_service(self, model_type: str = "local_projections") -> IModelService:
        """Criar serviço de modelo"""
        async with self._lock:
            cache_key = f'model_service_{model_type}'
            if cache_key not in self._instances:
                model_config = self.config.get('model', {})
                
                if model_type == "local_projections":
                    self._instances[cache_key] = LocalProjectionsModelService(
                        max_horizon=model_config.get('max_horizon', 12),
                        max_lags=model_config.get('max_lags', 4),
                        alpha=model_config.get('alpha', 0.1),
                        regularization=model_config.get('regularization', 'ridge')
                    )
                elif model_type == "bvar_minnesota":
                    self._instances[cache_key] = BVARMinnesotaModelService(
                        n_lags=model_config.get('n_lags', 2),
                        n_vars=model_config.get('n_vars', 2),
                        minnesota_params=model_config.get('minnesota_params', {}),
                        n_simulations=model_config.get('n_simulations', 1000)
                    )
                else:
                    raise ConfigurationError(f"Tipo de modelo não suportado: {model_type}")
            
            return self._instances[cache_key]
    
    async def create_data_repository(self) -> IDataRepository:
        """Criar repositório de dados"""
        async with self._lock:
            if 'data_repository' not in self._instances:
                data_config = self.config.get('data', {})
                
                # Criar repositórios específicos
                fed_repo = FedDataRepository(
                    fred_api_key=data_config.get('fred_api_key', '')
                )
                
                selic_repo = SelicDataRepository(
                    bcb_api_url=data_config.get('bcb_api_url', '')
                )
                
                # Criar repositório composto
                self._instances['data_repository'] = CompositeDataRepository(
                    fed_repo=fed_repo,
                    selic_repo=selic_repo
                )
            
            return self._instances['data_repository']
    
    async def create_probability_engine(self) -> IProbabilityEngine:
        """Criar engine de probabilidades"""
        async with self._lock:
            if 'probability_engine' not in self._instances:
                self._instances['probability_engine'] = ProbabilityEngineService(
                    discretization_step=self.config.get('probability', {}).get('step', 25),
                    confidence_levels=self.config.get('probability', {}).get('confidence_levels', [0.8, 0.95])
                )
            
            return self._instances['probability_engine']
    
    async def create_validation_service(self) -> IValidationService:
        """Criar serviço de validação"""
        async with self._lock:
            if 'validation_service' not in self._instances:
                self._instances['validation_service'] = ValidationService(
                    validation_rules=self.config.get('validation', {})
                )
            
            return self._instances['validation_service']
    
    async def create_logging_service(self) -> ILoggingService:
        """Criar serviço de logging"""
        async with self._lock:
            if 'logging_service' not in self._instances:
                logging_config = self.config.get('logging', {})
                self._instances['logging_service'] = LoggingService(
                    log_level=logging_config.get('level', 'INFO'),
                    log_format=logging_config.get('format', 'json'),
                    log_file=logging_config.get('file', None)
                )
            
            return self._instances['logging_service']
    
    async def create_metrics_service(self) -> IMetricsService:
        """Criar serviço de métricas"""
        async with self._lock:
            if 'metrics_service' not in self._instances:
                metrics_config = self.config.get('metrics', {})
                self._instances['metrics_service'] = MetricsService(
                    metrics_backend=metrics_config.get('backend', 'prometheus'),
                    metrics_port=metrics_config.get('port', 9090)
                )
            
            return self._instances['metrics_service']
    
    async def create_cache_service(self) -> ICacheService:
        """Criar serviço de cache"""
        async with self._lock:
            if 'cache_service' not in self._instances:
                cache_config = self.config.get('cache', {})
                self._instances['cache_service'] = RedisCacheService(
                    redis_url=cache_config.get('redis_url', 'redis://localhost:6379'),
                    default_ttl=cache_config.get('default_ttl', 3600)
                )
            
            return self._instances['cache_service']
    
    async def create_error_handler(self) -> IErrorHandler:
        """Criar handler de erros"""
        async with self._lock:
            if 'error_handler' not in self._instances:
                self._instances['error_handler'] = ErrorHandlerService(
                    error_config=self.config.get('error_handling', {})
                )
            
            return self._instances['error_handler']
    
    async def create_stationarity_service(self) -> IStationarityService:
        """Criar serviço de estacionariedade"""
        async with self._lock:
            if 'stationarity_service' not in self._instances:
                self._instances['stationarity_service'] = StationarityService(
                    significance_level=self.config.get('stationarity', {}).get('significance_level', 0.05),
                    max_lags=self.config.get('stationarity', {}).get('max_lags', 4)
                )
            
            return self._instances['stationarity_service']
    
    async def create_data_processor(self) -> IDataProcessor:
        """Criar processador de dados"""
        async with self._lock:
            if 'data_processor' not in self._instances:
                self._instances['data_processor'] = DataProcessorService(
                    processing_config=self.config.get('data_processing', {})
                )
            
            return self._instances['data_processor']
    
    async def create_configuration_service(self) -> IConfigurationService:
        """Criar serviço de configuração"""
        async with self._lock:
            if 'configuration_service' not in self._instances:
                self._instances['configuration_service'] = ConfigurationService(
                    config=self.config
                )
            
            return self._instances['configuration_service']
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Obter status de saúde de todos os serviços"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        
        # Verificar status de cada serviço
        services_to_check = [
            'prediction_service',
            'data_repository',
            'model_service_local_projections',
            'model_service_bvar_minnesota',
            'probability_engine',
            'validation_service',
            'logging_service',
            'metrics_service',
            'cache_service',
            'error_handler'
        ]
        
        for service_name in services_to_check:
            try:
                if service_name in self._instances:
                    health_status['services'][service_name] = {
                        'status': 'healthy',
                        'created_at': getattr(self._instances[service_name], 'created_at', None)
                    }
                else:
                    health_status['services'][service_name] = {
                        'status': 'not_initialized'
                    }
            except Exception as e:
                health_status['services'][service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return health_status
    
    async def cleanup(self):
        """Limpar instâncias (útil para testes)"""
        async with self._lock:
            for service in self._instances.values():
                if hasattr(service, 'cleanup'):
                    await service.cleanup()
            self._instances.clear()

class ConfigurationService(IConfigurationService):
    """Serviço de configuração"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def get_model_config(self, model_type: str) -> Dict[str, Any]:
        """Obter configuração do modelo"""
        return self.config.get('model', {}).get(model_type, {})
    
    async def get_api_config(self) -> Dict[str, Any]:
        """Obter configuração da API"""
        return self.config.get('api', {})
    
    async def get_data_config(self) -> Dict[str, Any]:
        """Obter configuração de dados"""
        return self.config.get('data', {})

# Factory global (Singleton)
_global_factory: Optional[ServiceFactory] = None

async def get_service_factory(config: Dict[str, Any] = None) -> ServiceFactory:
    """Obter factory global (Singleton)"""
    global _global_factory
    
    if _global_factory is None:
        if config is None:
            # Configuração padrão
            config = {
                'model': {
                    'max_horizon': 12,
                    'max_lags': 4,
                    'alpha': 0.1,
                    'regularization': 'ridge'
                },
                'data': {
                    'fred_api_key': '',
                    'bcb_api_url': 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados'
                },
                'cache': {
                    'redis_url': 'redis://localhost:6379',
                    'default_ttl': 3600
                },
                'logging': {
                    'level': 'INFO',
                    'format': 'json'
                },
                'metrics': {
                    'backend': 'prometheus',
                    'port': 9090
                }
            }
        
        _global_factory = ServiceFactory(config)
    
    return _global_factory

async def cleanup_global_factory():
    """Limpar factory global"""
    global _global_factory
    if _global_factory:
        await _global_factory.cleanup()
        _global_factory = None
