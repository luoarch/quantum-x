"""
Quantum-X: Spillover Intelligence FED-Selic
API Principal - Arquitetura SOLID e Modular

Baseado em:
- Local Projections (Jordà, 2005)
- BVAR Minnesota (Litterman, 1986)
- Validação científica rigorosa
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

from src.api.controllers.prediction_controller import PredictionController
from src.api.controllers.health_controller import HealthController
from src.api.controllers.model_controller import ModelController
from src.api.middleware.auth_middleware import AuthMiddleware
from src.api.middleware.rate_limit_middleware import RateLimitMiddleware
from src.api.middleware.logging_middleware import LoggingMiddleware
from src.factories.service_factory import get_service_factory, cleanup_global_factory
from src.core.exceptions import QuantumXException
from src.core.models import APIConfiguration

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuração da aplicação
APP_CONFIG = {
    'api': {
        'version': 'v1.0.0',
        'title': 'Quantum-X: Spillover Intelligence FED-Selic',
        'description': 'API de Previsão Probabilística da Selic Condicionada ao Fed',
        'max_requests_per_minute': 60,
        'max_requests_per_day': 1000,
        'timeout_seconds': 30,
        'enable_cors': True,
        'enable_metrics': True
    },
    'model': {
        'max_horizon': 12,
        'max_lags': 4,
        'alpha': 0.1,
        'regularization': 'ridge',
        'minnesota_params': {
            'lambda1': 0.1,
            'lambda2': 0.5,
            'lambda3': 1.0,
            'lambda4': 0.1,
            'mu': 0.0,
            'sigma': 1.0
        }
    },
    'data': {
        'fred_api_key': os.getenv('FRED_API_KEY', ''),
        'bcb_api_url': 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados',
        'update_frequency': 'daily',
        'data_retention_days': 365
    },
    'cache': {
        'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
        'default_ttl': 3600,
        'model_cache_ttl': 86400
    },
    'logging': {
        'level': os.getenv('LOG_LEVEL', 'INFO'),
        'format': 'json',
        'file': os.getenv('LOG_FILE', None)
    },
    'metrics': {
        'backend': 'prometheus',
        'port': int(os.getenv('METRICS_PORT', '9090'))
    },
    'validation': {
        'fed_move_bps_range': (-200, 200),
        'horizons_months_range': (1, 24),
        'max_batch_size': 10
    },
    'stationarity': {
        'significance_level': 0.05,
        'max_lags': 4,
        'tests': ['adf', 'kpss', 'dfgls', 'pp', 'za']
    },
    'error_handling': {
        'include_details': os.getenv('ENVIRONMENT', 'production') == 'development',
        'log_errors': True,
        'notify_errors': False
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    logger.info("🚀 Iniciando Quantum-X API...")
    
    # Inicializar factory de serviços
    factory = await get_service_factory(APP_CONFIG)
    app.state.service_factory = factory
    
    # Verificar saúde dos serviços
    health_status = await factory.get_health_status()
    logger.info(f"📊 Status dos serviços: {health_status}")
    
    yield
    
    # Cleanup
    logger.info("🛑 Finalizando Quantum-X API...")
    await cleanup_global_factory()

# Criar aplicação FastAPI
app = FastAPI(
    title=APP_CONFIG['api']['title'],
    description=APP_CONFIG['api']['description'],
    version=APP_CONFIG['api']['version'],
    lifespan=lifespan,
    docs_url="/docs" if APP_CONFIG['api'].get('enable_docs', True) else None,
    redoc_url="/redoc" if APP_CONFIG['api'].get('enable_docs', True) else None
)

# Middleware
if APP_CONFIG['api']['enable_cors']:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção, especificar origens
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, 
                  max_requests_per_minute=APP_CONFIG['api']['max_requests_per_minute'])
app.add_middleware(AuthMiddleware)

# Dependency para obter factory de serviços
async def get_service_factory_dependency():
    """Dependency para obter factory de serviços"""
    return app.state.service_factory

# Incluir controllers
app.include_router(
    PredictionController().router,
    prefix="/api/v1",
    tags=["Previsões"]
)

app.include_router(
    HealthController().router,
    prefix="/api/v1",
    tags=["Saúde"]
)

app.include_router(
    ModelController().router,
    prefix="/api/v1",
    tags=["Modelos"]
)

# Exception handlers globais
@app.exception_handler(QuantumXException)
async def quantum_x_exception_handler(request, exc: QuantumXException):
    """Handler para exceções do domínio"""
    return HTTPException(
        status_code=400,
        detail={
            "error_code": exc.error_code,
            "error_message": exc.message,
            "error_details": exc.details
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handler para exceções gerais"""
    logger.error(f"Erro não tratado: {str(exc)}", exc_info=True)
    return HTTPException(
        status_code=500,
        detail={
            "error_code": "INTERNAL_ERROR",
            "error_message": "Erro interno do servidor",
            "error_details": {"exception": str(exc)} if APP_CONFIG['error_handling']['include_details'] else {}
        }
    )

# Rota raiz
@app.get("/")
async def root():
    """Rota raiz da API"""
    return {
        "name": "Quantum-X: Spillover Intelligence FED-Selic",
        "version": APP_CONFIG['api']['version'],
        "description": "API de Previsão Probabilística da Selic Condicionada ao Fed",
        "status": "operational",
        "endpoints": {
            "predictions": "/api/v1/predict/selic-from-fed",
            "health": "/api/v1/health",
            "models": "/api/v1/models/versions",
            "docs": "/docs"
        }
    }

# Health check básico
@app.get("/health")
async def health_check():
    """Health check básico"""
    return {"status": "healthy", "version": APP_CONFIG['api']['version']}

if __name__ == "__main__":
    # Configuração do servidor
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    
    logger.info(f"🌐 Iniciando servidor em {host}:{port}")
    logger.info(f"👥 Workers: {workers}")
    logger.info(f"📚 Documentação: http://{host}:{port}/docs")
    
    # Executar servidor
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        reload=os.getenv("ENVIRONMENT", "production") == "development",
        log_level=APP_CONFIG['logging']['level'].lower()
    )
