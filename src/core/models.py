"""
Domain Models - Single Responsibility Principle
Modelos de domínio para o sistema FED-Selic
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import pandas as pd
from collections import defaultdict

class ModelType(str, Enum):
    """Tipos de modelo disponíveis"""
    LOCAL_PROJECTIONS = "local_projections"
    BVAR_MINNESOTA = "bvar_minnesota"
    HYBRID = "hybrid"

class PredictionConfidence(str, Enum):
    """Níveis de confiança da previsão"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class FedMoveDirection(str, Enum):
    """Direção do movimento do Fed"""
    HAWKISH = 1      # Aumento de juros
    NEUTRAL = 0      # Manutenção
    DOVISH = -1      # Redução de juros

@dataclass
class FedDecision:
    """Decisão do Fed"""
    date: datetime
    move_bps: int
    direction: FedMoveDirection
    surprise_bps: Optional[int] = None
    expected_bps: Optional[int] = None
    
    def __post_init__(self):
        """Validação pós-inicialização"""
        if self.move_bps % 25 != 0:
            raise ValueError("move_bps deve ser múltiplo de 25")
        
        if self.surprise_bps is not None and abs(self.surprise_bps) > 100:
            raise ValueError("surprise_bps deve estar entre -100 e 100")

@dataclass
class CopomMeeting:
    """Reunião do Copom"""
    date: datetime
    expected_move_bps: int
    probability: float
    confidence_interval_80: tuple = (0, 0)
    confidence_interval_95: tuple = (0, 0)
    
    def __post_init__(self):
        """Validação pós-inicialização"""
        if not 0 <= self.probability <= 1:
            raise ValueError("probability deve estar entre 0 e 1")

@dataclass
class SelicPrediction:
    """Previsão da Selic"""
    expected_move_bps: int
    horizon_months: str
    prob_move_within_next_copom: float
    confidence_level: PredictionConfidence
    per_meeting: List[CopomMeeting] = field(default_factory=list)
    distribution: List[Dict[str, Any]] = field(default_factory=list)
    confidence_intervals: Dict[str, List[int]] = field(default_factory=dict)
    rationale: str = ""
    limitations: Optional[str] = None

@dataclass
class ModelMetadata:
    """Metadados do modelo"""
    version: str
    model_type: ModelType
    trained_at: datetime
    data_hash: str
    methodology: str
    n_observations: int
    r_squared: Optional[float] = None
    backtest_metrics: Optional[Dict[str, float]] = None
    hyperparameters: Optional[Dict[str, Any]] = None

@dataclass
class PredictionRequest:
    """Request de previsão"""
    fed_decision: FedDecision
    horizons_months: List[int]
    model_version: str = "latest"
    regime_hint: str = "normal"
    request_id: Optional[str] = None
    
    def __post_init__(self):
        """Validação pós-inicialização"""
        if not self.horizons_months:
            raise ValueError("horizons_months não pode estar vazio")
        
        if any(h < 1 or h > 24 for h in self.horizons_months):
            raise ValueError("horizons_months deve estar entre 1 e 24")

@dataclass
class PredictionResponse:
    """Response de previsão"""
    prediction: SelicPrediction
    model_metadata: ModelMetadata
    request_id: str
    processing_time_ms: float
    cache_hit: bool = False

@dataclass
class ModelPerformance:
    """Performance do modelo"""
    model_version: str
    r_squared: float
    mae: float  # Mean Absolute Error
    rmse: float  # Root Mean Square Error
    coverage_80: float
    coverage_95: float
    brier_score: float
    calibration_score: float
    evaluated_at: datetime

@dataclass
class DataQuality:
    """Qualidade dos dados"""
    source: str
    completeness: float
    consistency: float
    timeliness: float
    accuracy: float
    overall_score: float
    issues: List[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.now)

@dataclass
class StationarityTestResult:
    """Resultado de teste de estacionariedade"""
    series_name: str
    is_stationary: bool
    adf_pvalue: float
    kpss_pvalue: float
    dfgls_pvalue: Optional[float] = None
    pp_pvalue: Optional[float] = None
    za_pvalue: Optional[float] = None
    confidence_level: float = 0.95
    methodology: str = "Elliott et al. (1996)"
    recommendations: List[str] = field(default_factory=list)

@dataclass
class StructuralBreakResult:
    """Resultado de detecção de quebra estrutural"""
    series_name: str
    has_breaks: bool
    break_dates: List[datetime] = field(default_factory=list)
    break_probabilities: List[float] = field(default_factory=list)
    methodology: str = "Zivot-Andrews"
    confidence_level: float = 0.95

@dataclass
class ModelConfiguration:
    """Configuração do modelo"""
    model_type: ModelType
    max_horizon: int = 12
    max_lags: int = 4
    alpha: float = 0.1
    regularization: str = "ridge"
    significance_level: float = 0.05
    n_simulations: int = 1000
    minnesota_params: Optional[Dict[str, float]] = None

@dataclass
class APIConfiguration:
    """Configuração da API"""
    version: str = "v1.0.0"
    max_requests_per_minute: int = 60
    max_requests_per_day: int = 1000
    cache_ttl_seconds: int = 3600
    timeout_seconds: int = 30
    enable_cors: bool = True
    enable_metrics: bool = True

@dataclass
class DataConfiguration:
    """Configuração de dados"""
    fed_data_source: str = "fred"
    selic_data_source: str = "bcb"
    update_frequency: str = "daily"
    data_retention_days: int = 365
    backup_frequency: str = "weekly"
    validation_rules: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthStatus:
    """Status de saúde do sistema"""
    status: str
    version: str
    model_version: str
    uptime_seconds: float
    latency_p50_ms: Optional[float] = None
    latency_p95_ms: Optional[float] = None
    requests_per_minute: Optional[float] = None
    error_rate: Optional[float] = None
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class ErrorDetails:
    """Detalhes de erro"""
    error_code: str
    error_message: str
    error_type: str
    field: Optional[str] = None
    value: Optional[Any] = None
    suggestions: List[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class BatchPredictionRequest:
    """Request de previsões em lote"""
    scenarios: List[PredictionRequest]
    batch_id: Optional[str] = None
    
    def __post_init__(self):
        """Validação pós-inicialização"""
        if not self.scenarios:
            raise ValueError("scenarios não pode estar vazio")
        
        if len(self.scenarios) > 10:
            raise ValueError("Máximo de 10 cenários por lote")

@dataclass
class BatchPredictionResponse:
    """Response de previsões em lote"""
    predictions: List[PredictionResponse]
    batch_metadata: Dict[str, Any]
    batch_id: str
    processing_time_ms: float
    success_count: int
    error_count: int = 0
    errors: List[ErrorDetails] = field(default_factory=list)
