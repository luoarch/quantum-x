"""
Módulo de Previsões para o Brasil
Implementa RF041-RF050 conforme DRS
"""

from .macro_indicators_forecaster import MacroIndicatorsForecaster
from .regime_conditional_forecaster import RegimeConditionalForecaster
from .alert_system import AlertSystem

__all__ = [
    'MacroIndicatorsForecaster',
    'RegimeConditionalForecaster',
    'AlertSystem'
]

__version__ = "1.0.0"
