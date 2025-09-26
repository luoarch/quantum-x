"""
Tipos para Indicadores Macroeconômicos do Brasil
Conforme especificação do DRS seção 5.2.3
"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class RegimeSensitivity(BaseModel):
    """Sensibilidade de indicador a diferentes regimes"""
    global_recession: float = Field(..., description="Valor em recessão global")
    global_recovery: float = Field(..., description="Valor em recuperação global")
    global_expansion: float = Field(..., description="Valor em expansão global")
    global_contraction: float = Field(..., description="Valor em contração global")

class GDPForecast(BaseModel):
    """Previsão do PIB"""
    current_quarter: float = Field(..., description="PIB atual (trimestre)")
    next_quarter: float = Field(..., description="PIB próximo trimestre")
    confidence_interval: List[float] = Field(..., description="Intervalo de confiança [min, max]")
    regime_sensitivity: RegimeSensitivity = Field(..., description="Sensibilidade a regimes")

class InflationForecast(BaseModel):
    """Previsão da inflação"""
    current_month: float = Field(..., description="Inflação atual (mês)")
    forecast_12_months: float = Field(..., description="Previsão 12 meses")
    target_range: List[float] = Field(..., description="Meta de inflação [min, max]")
    spillover_contribution: float = Field(..., description="Contribuição dos spillovers")

class ExchangeRateForecast(BaseModel):
    """Previsão da taxa de câmbio"""
    current: float = Field(..., description="Taxa atual")
    forecast_3m: float = Field(..., description="Previsão 3 meses")
    volatility: float = Field(..., description="Volatilidade esperada")
    regime_conditional: Dict[str, float] = Field(..., description="Valores condicionais aos regimes")

class UnemploymentForecast(BaseModel):
    """Previsão do desemprego"""
    current: float = Field(..., description="Taxa atual")
    forecast_6m: float = Field(..., description="Previsão 6 meses")
    confidence_interval: List[float] = Field(..., description="Intervalo de confiança [min, max]")
    spillover_impact: float = Field(..., description="Impacto dos spillovers")

class InterestRateForecast(BaseModel):
    """Previsão da taxa de juros (SELIC)"""
    current: float = Field(..., description="Taxa atual")
    forecast_6m: float = Field(..., description="Previsão 6 meses")
    policy_direction: str = Field(..., description="Direção da política (hawkish, dovish, neutral)")
    spillover_pressure: float = Field(..., description="Pressão dos spillovers")

class BrazilIndicatorsForecast(BaseModel):
    """Previsões dos indicadores brasileiros"""
    gdp_growth: GDPForecast = Field(..., description="Previsão do PIB")
    inflation: InflationForecast = Field(..., description="Previsão da inflação")
    exchange_rate: ExchangeRateForecast = Field(..., description="Previsão do câmbio")
    unemployment: UnemploymentForecast = Field(..., description="Previsão do desemprego")
    interest_rate: InterestRateForecast = Field(..., description="Previsão da taxa de juros")
    last_updated: datetime = Field(..., description="Timestamp da última atualização")

class IndicatorAlert(BaseModel):
    """Alerta para indicador macroeconômico"""
    indicator_name: str = Field(..., description="Nome do indicador")
    current_value: float = Field(..., description="Valor atual")
    threshold_value: float = Field(..., description="Valor limite")
    alert_type: str = Field(..., description="Tipo de alerta (above, below, extreme)")
    severity: str = Field(..., description="Severidade (low, medium, high)")
    description: str = Field(..., description="Descrição do alerta")
    timestamp: datetime = Field(..., description="Timestamp do alerta")

class WebhookEvent(BaseModel):
    """Evento de webhook"""
    event_type: str = Field(..., description="Tipo do evento")
    timestamp: datetime = Field(..., description="Timestamp do evento")
    data: Dict = Field(..., description="Dados do evento")

class RegimeChangeEvent(WebhookEvent):
    """Evento de mudança de regime"""
    event_type: str = "regime_change"
    data: Dict = Field(..., description="Dados da mudança de regime")

class SpilloverAlertEvent(WebhookEvent):
    """Evento de alerta de spillover"""
    event_type: str = "spillover_alert"
    severity: str = Field(..., description="Severidade do alerta")
    data: Dict = Field(..., description="Dados do alerta de spillover")
