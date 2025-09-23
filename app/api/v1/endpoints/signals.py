"""
Endpoints para sinais de trading (placeholder)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db

router = APIRouter()


@router.get("/")
async def get_signals(db: Session = Depends(get_db)):
    """Lista sinais de trading (placeholder)"""
    return {
        "message": "Endpoint de sinais em desenvolvimento",
        "status": "coming_soon"
    }


@router.get("/health")
async def signals_health():
    """Health check do módulo de sinais"""
    return {
        "status": "healthy",
        "module": "signals",
        "version": "1.0.0"
    }
