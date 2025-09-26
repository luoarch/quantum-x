"""
Router principal da API v1
"""

from fastapi import APIRouter
from app.api.v1.endpoints import data, signals, test, dashboard, dashboard_simple

# Criar router principal
api_router = APIRouter()

# Incluir endpoints
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(dashboard_simple.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(test.router, prefix="/test", tags=["test"])
