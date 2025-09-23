"""
Quantum X - CLI Trading Signal Generator
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router
from app.core.scheduler import start_scheduler, stop_scheduler

# Carregar variáveis de ambiente
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    await init_db()
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


# Criar instância do FastAPI
app = FastAPI(
    title="Quantum X - CLI Trading Signal Generator",
    description="Sistema de geração de sinais de trading baseado em indicadores de ciclo de negócios",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas da API
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "Quantum X - CLI Trading Signal Generator",
        "version": "1.0.0",
        "status": "active"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: implementar verificação real
        "redis": "connected"      # TODO: implementar verificação real
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
