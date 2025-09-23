"""
Módulo de Backtesting
Implementa backtesting rigoroso com dados históricos reais
"""

from .historical_backtester import HistoricalBacktester
from .performance_analyzer import PerformanceAnalyzer
from .asset_simulator import AssetSimulator

__all__ = [
    'HistoricalBacktester',
    'PerformanceAnalyzer', 
    'AssetSimulator'
]