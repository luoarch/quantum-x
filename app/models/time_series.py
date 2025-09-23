"""
Modelos para séries temporais
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base
from datetime import datetime
from typing import Optional


class EconomicSeries(Base):
    """Modelo para séries econômicas coletadas"""
    __tablename__ = "economic_series"
    
    id = Column(Integer, primary_key=True, index=True)
    series_code = Column(String(50), nullable=False, index=True)  # Código da série (ex: IPCA, SELIC)
    series_name = Column(String(200), nullable=False)
    source = Column(String(50), nullable=False)  # BCB, OECD, IPEA
    country = Column(String(10), nullable=True)  # BRA, USA, etc.
    
    # Dados da série temporal
    date = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True)  # %, index, etc.
    
    # Metadados
    frequency = Column(String(20), nullable=True)  # monthly, quarterly, annual
    method = Column(String(50), nullable=True)  # python-bcb, OECD_CSV, OData4, etc.
    last_updated = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSONB, nullable=True)  # Dados brutos da API
    
    # Índices para performance
    __table_args__ = (
        Index('idx_series_date', 'series_code', 'date'),
        Index('idx_source_country', 'source', 'country'),
    )


class CLISeries(Base):
    """Modelo para séries CLI calculadas"""
    __tablename__ = "cli_series"
    
    id = Column(Integer, primary_key=True, index=True)
    country = Column(String(10), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    cli_value = Column(Float, nullable=False)
    cli_normalized = Column(Float, nullable=False)  # Normalizado (média 100)
    
    # Componentes do CLI
    factors = Column(JSONB, nullable=True)  # Fatores extraídos
    weights = Column(JSONB, nullable=True)  # Pesos otimizados
    
    # Metadados
    calculation_method = Column(String(50), nullable=False)  # oecd_standard, ml_optimized
    confidence_score = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Índices
    __table_args__ = (
        Index('idx_cli_country_date', 'country', 'date'),
    )


class TradingSignal(Base):
    """Modelo para sinais de trading gerados"""
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(String(100), nullable=False, unique=True, index=True)
    
    # Informações do sinal
    asset_class = Column(String(50), nullable=False)  # equity, bond, fx, commodity
    asset_name = Column(String(100), nullable=False)
    signal_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD
    signal_strength = Column(String(20), nullable=False)  # STRONG, MODERATE, WEAK
    
    # Valores numéricos
    strength_score = Column(Float, nullable=False)  # 0-1
    confidence = Column(Float, nullable=False)  # 0-1
    expected_return = Column(Float, nullable=True)
    position_size = Column(Float, nullable=True)  # 0-1
    
    # CLI que gerou o sinal
    cli_brazil = Column(Float, nullable=True)
    cli_global = Column(Float, nullable=True)
    
    # Explicação do sinal
    explanation = Column(Text, nullable=True)
    shap_values = Column(JSONB, nullable=True)
    
    # Metadados
    generated_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # active, expired, cancelled
    
    # Índices
    __table_args__ = (
        Index('idx_signal_asset_date', 'asset_class', 'generated_at'),
        Index('idx_signal_status', 'status', 'generated_at'),
    )


class DataCollectionLog(Base):
    """Log de coleta de dados"""
    __tablename__ = "data_collection_log"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)
    series_name = Column(String(50), nullable=False)  # Nome da série (ex: IPCA, SELIC)
    series_code = Column(String(50), nullable=True)  # Código da série (ex: 433, 432)
    status = Column(String(20), nullable=False)  # success, error, partial
    records_collected = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)  # segundos
    details = Column(JSONB, nullable=True)  # Detalhes da coleta
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    # Índices
    __table_args__ = (
        Index('idx_collection_source_date', 'source', 'collected_at'),
    )
