"""
Network Effects Module - SOLID Architecture
Captura dados dos clientes para melhorar modelo para todos
"""

from .client_tracker import ClientTracker
from .prediction_logger import PredictionLogger
from .model_improver import ModelImprover
from .network_analytics import NetworkAnalytics

__all__ = [
    'ClientTracker',
    'PredictionLogger', 
    'ModelImprover',
    'NetworkAnalytics'
]
