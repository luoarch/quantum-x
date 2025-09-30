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

# Configurações
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    # Startup
    print("🚀 Iniciando API FED-Selic...")
    app.state.start_time = time.time()
    app.state.request_count = 0
    
    # Inicializar modelos
    # TODO: Carregar modelos ML aqui
    
    yield
    
    # Shutdown
    print("🛑 Finalizando API FED-Selic...")

# Criar aplicação FastAPI
app = FastAPI(
    title="API FED-Selic Prediction",
    description="API para previsão probabilística da Selic condicionada a movimentos do Fed",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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

# Middleware para métricas básicas
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Rastrear métricas básicas"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Calcular latência
    latency = time.time() - start_time
    
    # Atualizar contadores
    app.state.request_count += 1
    
    # Adicionar headers de métricas
    response.headers["X-Response-Time"] = f"{latency:.3f}s"
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
        content=error_response.dict()
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
        content=error_response.dict()
    )

# Endpoint raiz
@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "API FED-Selic Prediction",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs",
        "health": "/health"
    }

# Endpoint de informações da API
@app.get("/info", tags=["Info"])
async def api_info():
    """Informações detalhadas da API"""
    uptime = time.time() - app.state.start_time
    
    return {
        "api": {
            "name": "FED-Selic Prediction API",
            "version": "1.0.0",
            "description": "API para previsão probabilística da Selic condicionada a movimentos do Fed"
        },
        "status": {
            "operational": True,
            "uptime_seconds": uptime,
            "request_count": app.state.request_count
        },
        "endpoints": {
            "prediction": "/predict/selic-from-fed",
            "batch_prediction": "/predict/selic-from-fed/batch",
            "health": "/health",
            "models": "/models/versions",
            "docs": "/docs"
        },
        "features": [
            "Previsão probabilística da Selic",
            "Suporte a múltiplos cenários",
            "Intervalos de confiança",
            "Mapeamento para reuniões do Copom",
            "Versionamento de modelos",
            "Rate limiting",
            "Autenticação por chave API"
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
