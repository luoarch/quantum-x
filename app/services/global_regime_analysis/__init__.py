"""
Módulo de Análise de Regimes Globais
Implementa RF001-RF020 conforme DRS
"""

from .rs_gvar_model import RSGVARModel
from .regime_identification import GlobalRegimeIdentifier
from .regime_validation import GlobalRegimeValidator
from .regime_forecasting import GlobalRegimeForecaster

__all__ = [
    'RSGVARModel',
    'GlobalRegimeIdentifier', 
    'GlobalRegimeValidator',
    'GlobalRegimeForecaster'
]

__version__ = "1.0.0"
