"""
API principal para previsão da Selic condicionada ao Fed
"""

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid
from datetime import datetime
from typing import Dict, Any

from .schemas import (
    PredictionRequest, PredictionResponse, BatchPredictionRequest, BatchPredictionResponse,
    HealthResponse, ModelVersion, StandardErrorResponse, ErrorCodes
)
from .middleware import (
    RequestLoggingMiddleware, 
    RateLimitMiddleware, 
    AuthenticationMiddleware,
    ErrorHandlingMiddleware
)
from .endpoints import prediction, health, models
from ..core.config import get_settings
from ..services.model_service import get_model_service

# Configurações
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    # Startup
    print("🚀 Iniciando API FED-Selic...")
    print("="*70)
    app.state.start_time = time.time()
    app.state.request_count = 0
    app.state.models_loaded = False  # Flag de estado dos modelos
    
    # Inicializar modelos REAIS
    print("\n📦 Carregando modelos...")
    try:
        model_service = get_model_service()
        
        # Carregar versão mais recente
        lp, bvar, metadata = model_service.load_model("latest")
        
        # Armazenar no app state
        app.state.model_lp = lp
        app.state.model_bvar = bvar
        app.state.model_metadata = metadata
        app.state.model_version = metadata.get('version', 'unknown')
        app.state.models_loaded = True  # Modelos carregados com sucesso
        
        print(f"✅ Modelos carregados:")
        print(f"   Versão: {app.state.model_version}")
        print(f"   Data hash: {metadata.get('data_hash', 'N/A')[:60]}...")
        print(f"   BVAR estável: {getattr(bvar, 'stable', 'N/A')}")
        print(f"   LP horizontes: {len(lp.models) if hasattr(lp, 'models') else 'N/A'}")
        
    except Exception as e:
        print(f"⚠️  Erro ao carregar modelos: {e}")
        print(f"   API continuará mas sem modelos carregados")
        app.state.model_lp = None
        app.state.model_bvar = None
        app.state.model_metadata = {}
        app.state.model_version = "none"
        app.state.models_loaded = False
        app.state.model_load_error = repr(e)  # Para diagnóstico
    
    print("="*70)
    print("✅ API pronta para receber requisições!\n")
    
    yield
    
    # Shutdown
    print("\n🛑 Finalizando API FED-Selic...")
    
    # Limpar cache de modelos
    if hasattr(app.state, 'model_lp'):
        app.state.model_lp = None
    if hasattr(app.state, 'model_bvar'):
        app.state.model_bvar = None
    
    print("✅ Recursos liberados")

# Criar aplicação FastAPI
# Desabilitar docs em produção por segurança
docs_url = "/docs" if settings.ENVIRONMENT != "production" else None
redoc_url = "/redoc" if settings.ENVIRONMENT != "production" else None

app = FastAPI(
    title="API FED-Selic Prediction",
    description="API para previsão probabilística da Selic condicionada a movimentos do Fed",
    version=settings.API_VERSION,
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Incluir routers
app.include_router(prediction.router, prefix="/predict", tags=["Prediction"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(models.router, prefix="/models", tags=["Models"])

# Middleware para adicionar request ID
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Adicionar ID único para cada requisição"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response

# Middleware para headers padrão de governança
@app.middleware("http")
async def add_standard_headers(request: Request, call_next):
    """
    Adicionar headers padrão em todas as respostas
    v2.1: X-API-Version, X-Active-Model-Version, X-Environment
    """
    response = await call_next(request)
    
    # Headers de governança
    response.headers["X-API-Version"] = settings.API_VERSION
    response.headers["X-Environment"] = settings.ENVIRONMENT
    
    # Versão do modelo (se disponível)
    model_version = getattr(request.app.state, "model_version", "none")
    response.headers["X-Active-Model-Version"] = model_version
    
    return response

# Middleware para métricas básicas
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """
    Rastrear métricas básicas
    v2.1: perf_counter para precisão, formato ms
    """
    start_perf = time.perf_counter()
    
    response = await call_next(request)
    
    # Calcular latência precisa em ms
    latency_ms = (time.perf_counter() - start_perf) * 1000
    
    # Atualizar contadores (com fallback seguro)
    if not hasattr(app.state, 'request_count'):
        app.state.request_count = 0
    app.state.request_count += 1
    
    # Adicionar headers de métricas (precisão 1 casa decimal)
    response.headers["X-Response-Time"] = f"{latency_ms:.1f}ms"
    response.headers["X-Request-Count"] = str(app.state.request_count)
    
    return response

# Handler de exceções global
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler para exceções HTTP"""
    request_id = getattr(request.state, 'request_id', None)
    
    error_response = StandardErrorResponse(
        error_code=exc.detail.get("error_code", "http_error") if isinstance(exc.detail, dict) else "http_error",
        message=exc.detail.get("message", str(exc.detail)) if isinstance(exc.detail, dict) else str(exc.detail),
        details=exc.detail.get("details") if isinstance(exc.detail, dict) else None,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções gerais"""
    request_id = getattr(request.state, 'request_id', None)
    
    error_response = StandardErrorResponse(
        error_code=ErrorCodes.INTERNAL_ERROR,
        message="Erro interno do servidor",
        details={"exception_type": type(exc).__name__},
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )

# Endpoint raiz
@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "API FED-Selic Prediction",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "docs": "/docs" if settings.ENVIRONMENT != "production" else None,
        "health": "/health"
    }

# Endpoint de informações da API
@app.get("/info", tags=["Info"])
async def api_info():
    """Informações detalhadas da API"""
    start_time = getattr(app.state, 'start_time', time.time())
    uptime = time.time() - start_time
    
    # Incluir versão do modelo carregado e possível erro
    model_version = getattr(app.state, 'model_version', 'none')
    model_metadata = getattr(app.state, 'model_metadata', {})
    models_loaded = getattr(app.state, 'models_loaded', False)
    model_load_error = getattr(app.state, 'model_load_error', None)
    
    return {
        "api": {
            "name": "FED-Selic Prediction API",
            "version": settings.API_VERSION,
            "environment": settings.ENVIRONMENT,
            "description": "API para previsão probabilística da Selic condicionada a movimentos do Fed"
        },
        "status": {
            "operational": True,
            "uptime_seconds": round(uptime, 2),
            "request_count": getattr(app.state, 'request_count', 0),
            "models_loaded": models_loaded
        },
        "model": {
            "version": model_version,
            "loaded": models_loaded,
            "data_hash": model_metadata.get('data_hash', 'N/A')[:64] + '...' if model_metadata.get('data_hash') else 'N/A',
            "n_observations": model_metadata.get('n_observations', 0),
            "methodology": model_metadata.get('methodology', 'N/A'),
            "load_error": model_load_error
        },
        "endpoints": {
            "prediction": "/predict/selic-from-fed",
            "batch_prediction": "/predict/selic-from-fed/batch",
            "health": "/health",
            "models": "/models/versions",
            "docs": "/docs",
            "info": "/info"
        },
        "features": [
            "Previsão probabilística da Selic",
            "Suporte a múltiplos cenários",
            "Intervalos de confiança 80% e 95%",
            "Discretização em 25 bps",
            "Mapeamento para reuniões do Copom",
            "Versionamento de modelos",
            "Rate limiting",
            "Autenticação por chave API",
            "Cache LRU de modelos",
            "Self-check de integridade"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
