"""
Tipos para Análise de Regimes Globais
Conforme especificação do DRS seção 5.2.1
"""

from typing import Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class RegimeType(str, Enum):
    """Tipos de regimes econômicos globais"""
    GLOBAL_RECESSION = "GLOBAL_RECESSION"
    GLOBAL_RECOVERY = "GLOBAL_RECOVERY" 
    GLOBAL_EXPANSION = "GLOBAL_EXPANSION"
    GLOBAL_CONTRACTION = "GLOBAL_CONTRACTION"
    GLOBAL_STRESS = "GLOBAL_STRESS"
    GLOBAL_CALM = "GLOBAL_CALM"

class RegimeCharacteristics(BaseModel):
    """Características de um regime econômico"""
    duration_months: int = Field(..., description="Duração típica do regime em meses")
    typical_indicators: Dict[str, List[float]] = Field(..., description="Indicadores típicos do regime")
    volatility_level: str = Field(..., description="Nível de volatilidade (low, medium, high)")
    risk_appetite: str = Field(..., description="Apetite ao risco (low, medium, high)")

class CurrentRegimeResponse(BaseModel):
    """Resposta do endpoint /global-regimes/current"""
    current_regime: RegimeType = Field(..., description="Regime atual identificado")
    regime_probabilities: Dict[RegimeType, float] = Field(..., description="Probabilidades de cada regime")
    regime_characteristics: RegimeCharacteristics = Field(..., description="Características do regime atual")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nível de confiança da identificação")
    last_updated: datetime = Field(..., description="Timestamp da última atualização")

class MonthlyForecast(BaseModel):
    """Previsão mensal de regime"""
    month: int = Field(..., ge=1, le=12, description="Mês da previsão")
    most_likely_regime: RegimeType = Field(..., description="Regime mais provável")
    regime_probabilities: Dict[RegimeType, float] = Field(..., description="Probabilidades de cada regime")
    confidence_interval: List[float] = Field(..., description="Intervalo de confiança [min, max]")

class RegimeForecastResponse(BaseModel):
    """Resposta do endpoint /global-regimes/forecast"""
    forecast_horizon: int = Field(..., description="Horizonte de previsão em meses")
    monthly_forecast: List[MonthlyForecast] = Field(..., description="Previsões mensais")
    scenario_analysis: Dict[str, float] = Field(..., description="Análise de cenários")

class ModelPerformance(BaseModel):
    """Performance do modelo de regimes"""
    out_of_sample_accuracy: float = Field(..., ge=0.0, le=1.0, description="Acurácia fora da amostra")
    regime_identification_score: float = Field(..., ge=0.0, le=1.0, description="Score de identificação de regimes")
    transition_prediction_score: float = Field(..., ge=0.0, le=1.0, description="Score de previsão de transições")

class RegimeValidationResponse(BaseModel):
    """Resposta do endpoint /global-regimes/validation"""
    model_performance: ModelPerformance = Field(..., description="Performance do modelo")
    last_validation: datetime = Field(..., description="Data da última validação")
    next_validation: datetime = Field(..., description="Data da próxima validação")
    model_version: str = Field(..., description="Versão do modelo")

class GlobalShock(BaseModel):
    """Choque econômico global"""
    shock_type: str = Field(..., description="Tipo do choque")
    magnitude: float = Field(..., description="Magnitude do choque")
    affected_countries: List[str] = Field(..., description="Países afetados")
    duration_months: int = Field(..., description="Duração esperada em meses")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança na estimativa")
