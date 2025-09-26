"""
Pipeline de Dados Automatizado
Conforme DRS seção 7.2 - Coleta automática a cada 6 horas
"""

from .data_pipeline import DataPipeline
from .data_validator import DataValidator
from .data_processor import DataProcessor

__all__ = [
    'DataPipeline',
    'DataValidator', 
    'DataProcessor'
]

__version__ = "1.0.0"
