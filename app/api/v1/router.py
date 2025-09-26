"""
Router principal da API v1
Conforme especificação do DRS seção 5.1
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    global_regimes,
    brazil_spillovers, 
    brazil_indicators,
    data_pipeline,
    dashboard, dashboard_simple, dashboard_advanced, 
    macro_analysis, regime_analysis, scientific_validation
)

# Criar router principal
api_router = APIRouter()

# === ENDPOINTS PRINCIPAIS CONFORME DRS ===
# RF001-RF020: Análise de Regimes Globais
api_router.include_router(global_regimes.router, prefix="/global-regimes", tags=["global-regimes"])

# RF021-RF040: Spillovers Brasil  
api_router.include_router(brazil_spillovers.router, prefix="/brazil-spillovers", tags=["brazil-spillovers"])

# RF041-RF050: Indicadores Brasil
api_router.include_router(brazil_indicators.router, prefix="/brazil-indicators", tags=["brazil-indicators"])

# RF051-RF070: API e Integração
api_router.include_router(data_pipeline.router, prefix="/data-pipeline", tags=["data-pipeline"])

# === ENDPOINTS LEGACY (A SEREM REMOVIDOS) ===
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(dashboard_simple.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(dashboard_advanced.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(macro_analysis.router, prefix="/macro", tags=["macro-analysis"])
api_router.include_router(regime_analysis.router, prefix="/api/v1", tags=["regime-analysis"])
api_router.include_router(scientific_validation.router, prefix="/api/v1", tags=["scientific-validation"])
