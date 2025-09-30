"""
Tipos de dados para o sistema FED-Selic
Baseado na estrutura dos dados reais baixados
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from datetime import datetime
from enum import Enum

@dataclass
class EconomicDataPoint:
    """Ponto de dados econômico mensal"""
    date: datetime
    fed_rate: float
    selic: float
    fed_change: Optional[float] = None
    selic_change: Optional[float] = None
    spillover: Optional[float] = None
    spillover_change: Optional[float] = None

@dataclass
class DataMetadata:
    """Metadados dos dados"""
    created_at: datetime
    observations: int
    start_date: datetime
    end_date: datetime
    columns: List[str]
    source: str

@dataclass
class DataSet:
    """Conjunto completo de dados"""
    metadata: DataMetadata
    data: List[EconomicDataPoint]

class FedMoveDirection(Enum):
    """Direção do movimento do Fed"""
    INCREASE = 1
    DECREASE = -1
    NO_CHANGE = 0

class RegimeHint(Enum):
    """Dicas de regime econômico"""
    NORMAL = "normal"
    CRISIS = "crisis"
    HIGH_INFLATION = "high_inflation"
    LOW_INFLATION = "low_inflation"
    RECESSION = "recession"
    EXPANSION = "expansion"

@dataclass
class PredictionRequest:
    """Requisição de previsão"""
    fed_decision_date: datetime
    fed_move_dir: FedMoveDirection
    fed_move_bps: int
    fed_surprise_bps: Optional[int] = None
    regime_flags: Optional[List[RegimeHint]] = None

@dataclass
class CopomMeetingPrediction:
    """Previsão para reunião do Copom"""
    date: datetime
    delta_bps: int
    probability: float

@dataclass
class DistributionEntry:
    """Entrada da distribuição de probabilidades"""
    horizon_months: int
    probability: float
    expected_move_bps: int

@dataclass
class PredictionResponse:
    """Resposta da previsão"""
    expected_move_bps: int
    horizon_months: int
    prob_move_within_next_copom: float
    ci80_bps: tuple[float, float]  # (lower, upper)
    ci95_bps: tuple[float, float]  # (lower, upper)
    path_by_meeting: List[CopomMeetingPrediction]
    rationale: str
    model_metadata: Dict[str, Union[str, int, float]]
    disclaimer: str

@dataclass
class ModelMetadata:
    """Metadados do modelo"""
    model_type: str
    data_window_start: datetime
    data_window_end: datetime
    model_version: str
    training_date: datetime
    performance_metrics: Dict[str, float]

@dataclass
class HealthStatus:
    """Status de saúde do sistema"""
    status: str
    timestamp: datetime
    model_status: str
    data_freshness: str
    api_version: str

@dataclass
class ErrorDetails:
    """Detalhes de erro"""
    error_code: str
    error_message: str
    error_type: str
    field: Optional[str] = None
    value: Optional[Union[str, int, float]] = None
    suggestions: Optional[List[str]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.timestamp is None:
            self.timestamp = datetime.now()

# Tipos para análise de dados
@dataclass
class CorrelationAnalysis:
    """Análise de correlação"""
    fed_selic_correlation: float
    spillover_correlation: float
    period: str
    significance_level: float

@dataclass
class StationarityTest:
    """Teste de estacionariedade"""
    variable: str
    test_name: str
    statistic: float
    p_value: float
    is_stationary: bool
    critical_values: Dict[str, float]

@dataclass
class StructuralBreakTest:
    """Teste de quebra estrutural"""
    variable: str
    break_date: Optional[datetime]
    confidence_level: float
    test_statistic: float
    p_value: float

# Tipos para modelos
@dataclass
class LocalProjectionsConfig:
    """Configuração do modelo Local Projections"""
    max_lags: int
    horizons: List[int]
    shrinkage_parameter: float
    bootstrap_samples: int

@dataclass
class BVARConfig:
    """Configuração do modelo BVAR"""
    variables: List[str]
    lags: int
    lambda1: float  # Overall shrinkage
    lambda2: float  # Cross-variable shrinkage
    minnesota_prior: bool

@dataclass
class ModelConfig:
    """Configuração geral do modelo"""
    model_type: str  # "local_projections" ou "bvar"
    lp_config: Optional[LocalProjectionsConfig] = None
    bvar_config: Optional[BVARConfig] = None
    data_preprocessing: Dict[str, Union[bool, str, float]] = None
    
    def __post_init__(self):
        if self.data_preprocessing is None:
            self.data_preprocessing = {
                "detrend": True,
                "standardize": True,
                "handle_outliers": True
            }

# Tipos para validação
@dataclass
class ValidationResult:
    """Resultado de validação"""
    is_valid: bool
    errors: List[ErrorDetails]
    warnings: List[str]
    suggestions: List[str]

@dataclass
class BacktestResult:
    """Resultado de backtest"""
    period_start: datetime
    period_end: datetime
    accuracy: float
    mae: float  # Mean Absolute Error
    rmse: float  # Root Mean Square Error
    directional_accuracy: float
    calibration_score: float

# Tipos para API
@dataclass
class BatchPredictionRequest:
    """Requisição de previsão em lote"""
    requests: List[PredictionRequest]
    batch_id: Optional[str] = None

@dataclass
class BatchPredictionResponse:
    """Resposta de previsão em lote"""
    batch_id: str
    results: List[PredictionResponse]
    processing_time: float
    success_count: int
    error_count: int

# Constantes úteis
SELIC_DISCRETIZATION = 25  # Múltiplos de 25 bps
COPOM_MEETINGS_PER_YEAR = 8
MAX_HORIZON_MONTHS = 24
MIN_OBSERVATIONS = 20

# Períodos históricos importantes
HISTORICAL_PERIODS = {
    "crisis_2008": (datetime(2008, 1, 1), datetime(2009, 12, 31)),
    "covid_2020": (datetime(2020, 1, 1), datetime(2021, 12, 31)),
    "inflation_2021": (datetime(2021, 1, 1), datetime(2022, 12, 31)),
    "recent": (datetime(2020, 1, 1), datetime.now())
}
