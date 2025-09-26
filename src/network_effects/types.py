"""
Type definitions for Network Effects - Type Safety First
"""
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np

class PredictionOutcome(Enum):
    """Resultado da predição para tracking"""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"

@dataclass(frozen=True)
class ClientPrediction:
    """Dados de uma predição de cliente - Immutable"""
    client_id: str
    timestamp: datetime
    input_data: Dict[str, float]  # fed_rate, selic
    prediction: float
    uncertainty: float
    is_outlier: bool
    high_uncertainty: bool
    model_version: str
    
@dataclass(frozen=True)
class ClientFeedback:
    """Feedback do cliente sobre predição - Immutable"""
    client_id: str
    prediction_id: str
    actual_outcome: Optional[float]
    feedback_score: Optional[float]  # 1-10 rating
    was_accurate: Optional[bool]
    timestamp: datetime

@dataclass(frozen=True)
class NetworkMetrics:
    """Métricas de network effects - Immutable"""
    total_clients: int
    total_predictions: int
    accuracy_improvement: float
    model_version: str
    last_retrain: datetime
    network_effect_strength: float

@dataclass(frozen=True)
class RetrainConfig:
    """Configuração para retreinamento - Immutable"""
    min_clients: int = 10
    min_predictions: int = 100
    retrain_frequency_days: int = 30
    accuracy_threshold: float = 0.05  # 5% improvement required
    max_retrain_attempts: int = 3

# Type aliases para clareza
ClientId = str
PredictionId = str
ModelVersion = str
AccuracyScore = float
NetworkStrength = float
