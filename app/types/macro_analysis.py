"""
Tipos para análise macroeconômica
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class EconomicRegime(str, Enum):
    """Regimes econômicos suportados"""
    RECESSION = "RECESSION"
    RECOVERY = "RECOVERY" 
    EXPANSION = "EXPANSION"
    CONTRACTION = "CONTRACTION"
    UNKNOWN = "UNKNOWN"

class DataSource(str, Enum):
    """Fontes de dados suportadas"""
    BCB = "bcb"
    BACEN_SGS = "bacen_sgs"
    FRED = "fred"
    OECD = "oecd"
    YAHOO = "yahoo"
    IPEA = "ipea"
    WORLD_BANK = "worldbank"

@dataclass
class RegimeCharacteristics:
    """Características de um regime econômico"""
    name: str
    gdp_growth_range: Tuple[float, float]
    unemployment_range: Tuple[float, float]
    inflation_range: Tuple[float, float]
    cli_range: Tuple[float, float]
    vix_range: Tuple[float, float]
    description: str

@dataclass
class MacroAnalysisResult:
    """Resultado da análise macroeconômica"""
    current_regime: EconomicRegime
    regime_confidence: float
    data_quality: int
    analysis_timestamp: datetime
    regime_probabilities: Dict[EconomicRegime, float]
    regime_frequencies: Dict[EconomicRegime, float]
    indicators_used: List[str]
    model_metadata: Dict[str, Any]

@dataclass
class IndicatorData:
    """Dados de um indicador econômico"""
    name: str
    values: List[float]
    dates: List[datetime]
    source: DataSource
    frequency: str
    weight: float
    description: str

@dataclass
class RegimeSummary:
    """Resumo de um regime econômico"""
    regime: EconomicRegime
    probability: float
    frequency: float
    avg_probability: float
    max_probability: float

@dataclass
class CLIDataPoint:
    """Ponto de dados do CLI"""
    date: datetime
    value: float
    confidence: float
    regime: EconomicRegime

@dataclass
class TradingSignal:
    """Sinal de trading"""
    date: datetime
    signal: str  # BUY, SELL, HOLD
    strength: int  # 1-5
    confidence: float  # 0-100
    regime: EconomicRegime
    buy_probability: float
    sell_probability: float

@dataclass
class PerformanceMetrics:
    """Métricas de performance"""
    total_signals: int
    buy_signals: int
    sell_signals: int
    hold_signals: int
    avg_confidence: float
    avg_buy_probability: float
    avg_sell_probability: float
    regime_summary: List[RegimeSummary]
    hrp_metrics: Dict[str, float]

@dataclass
class AssetData:
    """Dados de um ativo"""
    ticker: str
    name: str
    price: float
    change: float
    change_percent: float
    allocation: float
    suggested_allocation: float
    current_price: float
    recommended_action: str

@dataclass
class DashboardData:
    """Dados completos do dashboard"""
    current_signal: TradingSignal
    recent_signals: List[TradingSignal]
    cli_data: List[CLIDataPoint]
    performance: PerformanceMetrics
    assets: List[AssetData]
    macro_analysis: MacroAnalysisResult
    last_update: datetime

# Tipos para APIs
class APIResponse[T]:
    """Resposta genérica da API"""
    success: bool
    data: Optional[T]
    error: Optional[str]
    timestamp: datetime

class HealthCheck:
    """Status de saúde do sistema"""
    status: str
    services: Dict[str, bool]
    last_check: datetime
    uptime: float
