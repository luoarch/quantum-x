"""
Módulo de Geração de Sinais de Trading
Implementa algoritmos para gerar sinais baseados em CLI e séries econômicas
"""

from .cli_calculator import CLICalculator
from .signal_generator import SignalGenerator
from .ml_optimizer import MLOptimizer
from .position_sizing import PositionSizing

__all__ = [
    'CLICalculator',
    'SignalGenerator', 
    'MLOptimizer',
    'PositionSizing'
]
