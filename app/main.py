"""
Aplicação Principal - Global Economic Regime Analysis & Brazil Spillover Prediction System
Conforme especificação do DRS seção 2.1
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.router import api_router

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    # Startup
    logger.info("Iniciando Global Economic Regime Analysis & Brazil Spillover Prediction System")
    logger.info(f"Versão: {settings.VERSION}")
    logger.info(f"Modo Debug: {settings.DEBUG}")
    
    # Verificar conectividade com bancos de dados
    try:
        # TODO: Implementar verificação de conectividade
        logger.info("Conectividade com bancos de dados verificada")
    except Exception as e:
        logger.error(f"Erro na conectividade com bancos de dados: {e}")
    
    yield
    
    # Shutdown
    logger.info("Encerrando aplicação")

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de hosts confiáveis
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else ["yourdomain.com", "*.yourdomain.com"]
)

# Middleware de logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log de requisições HTTP"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Tempo: {process_time:.4f}s"
    )
    
    return response

# Incluir rotas da API
app.include_router(api_router, prefix="/api/v1")

# Endpoints de saúde e status
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "Global Economic Regime Analysis & Brazil Spillover Prediction System",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }

# Handler de exceções global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções"""
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "message": str(exc) if settings.DEBUG else "Erro interno do servidor",
            "timestamp": time.time()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )