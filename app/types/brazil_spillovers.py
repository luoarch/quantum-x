"""
Tipos para Análise de Spillovers Brasil
Conforme especificação do DRS seção 5.2.2
"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class SpilloverChannel(str, Enum):
    """Canais de spillover conforme DRS"""
    TRADE = "trade_channel"
    COMMODITY = "commodity_channel"
    FINANCIAL = "financial_channel"
    SUPPLY_CHAIN = "supply_chain_channel"

class ChannelImpact(BaseModel):
    """Impacto de um canal específico"""
    impact_magnitude: float = Field(..., description="Magnitude do impacto")
    key_drivers: List[str] = Field(..., description="Principais drivers do impacto")
    affected_sectors: List[str] = Field(..., description="Setores afetados")

class CommodityImpact(BaseModel):
    """Impacto de commodities específicas"""
    iron_ore: float = Field(..., description="Impacto do minério de ferro")
    soybeans: float = Field(..., description="Impacto da soja")
    crude_oil: float = Field(..., description="Impacto do petróleo")
    coffee: float = Field(..., description="Impacto do café")
    sugar: float = Field(..., description="Impacto do açúcar")
    corn: float = Field(..., description="Impacto do milho")
    beef: float = Field(..., description="Impacto da carne bovina")
    poultry: float = Field(..., description="Impacto da carne de frango")

class ChannelDetails(BaseModel):
    """Detalhes de um canal de spillover"""
    trade_channel: Optional[ChannelImpact] = Field(None, description="Detalhes do canal comercial")
    commodity_channel: Optional[CommodityImpact] = Field(None, description="Detalhes do canal de commodities")
    financial_channel: Optional[ChannelImpact] = Field(None, description="Detalhes do canal financeiro")
    supply_chain_channel: Optional[ChannelImpact] = Field(None, description="Detalhes do canal de cadeias globais")

class AggregateSpillover(BaseModel):
    """Spillover agregado para o Brasil"""
    total_impact: float = Field(..., description="Impacto total agregado")
    impact_breakdown: Dict[SpilloverChannel, float] = Field(..., description="Decomposição por canal")
    confidence_interval: List[float] = Field(..., description="Intervalo de confiança [min, max]")

class CurrentSpilloverResponse(BaseModel):
    """Resposta do endpoint /brazil-spillovers/current"""
    aggregate_spillover: AggregateSpillover = Field(..., description="Spillover agregado")
    channel_details: ChannelDetails = Field(..., description="Detalhes por canal")
    last_updated: datetime = Field(..., description="Timestamp da última atualização")

class SpilloverForecast(BaseModel):
    """Previsão de spillover para um mês"""
    month: int = Field(..., ge=1, le=12, description="Mês da previsão")
    expected_impact: float = Field(..., description="Impacto esperado")
    channel_breakdown: Dict[SpilloverChannel, float] = Field(..., description="Decomposição por canal")
    confidence_interval: List[float] = Field(..., description="Intervalo de confiança [min, max]")

class SpilloverForecastResponse(BaseModel):
    """Resposta do endpoint /brazil-spillovers/forecast"""
    spillover_forecast: List[SpilloverForecast] = Field(..., description="Previsões de spillover")
    horizon_months: int = Field(..., description="Horizonte de previsão em meses")

class SpilloverAlert(BaseModel):
    """Alerta de spillover anômalo"""
    alert_id: str = Field(..., description="ID único do alerta")
    severity: str = Field(..., description="Severidade (low, medium, high, critical)")
    channel: SpilloverChannel = Field(..., description="Canal afetado")
    impact_magnitude: float = Field(..., description="Magnitude do impacto")
    affected_regions: List[str] = Field(..., description="Regiões afetadas")
    timestamp: datetime = Field(..., description="Timestamp do alerta")
    description: str = Field(..., description="Descrição do alerta")
