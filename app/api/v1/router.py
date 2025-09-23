"""
Router principal da API v1
"""

from fastapi import APIRouter
from app.api.v1.endpoints import data, signals

# Criar router principal
api_router = APIRouter()

# Incluir endpoints
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
