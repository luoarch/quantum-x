"""
Modelos de dados globais para TimescaleDB
Conforme DRS seção 2.1
"""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func

Base = declarative_base()

class GlobalData(Base):
    """Dados econômicos globais"""
    
    __tablename__ = 'global_data'
    __table_args__ = (
        Index('idx_global_data_country_indicator', 'country', 'indicator'),
        Index('idx_global_data_timestamp', 'timestamp'),
        {'schema': 'time_series'}
    )
    
    id = Column(Integer, primary_key=True)
    country = Column(String(3), nullable=False, comment='Código do país (ISO 3166-1 alpha-3)')
    indicator = Column(String(50), nullable=False, comment='Nome do indicador')
    value = Column(Numeric(15, 6), nullable=False, comment='Valor do indicador')
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, comment='Data da observação')
    source = Column(String(50), nullable=False, comment='Fonte dos dados')
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), comment='Data de criação do registro')

class BrazilData(Base):
    """Dados econômicos do Brasil"""
    
    __tablename__ = 'brazil_data'
    __table_args__ = (
        Index('idx_brazil_data_indicator', 'indicator'),
        Index('idx_brazil_data_timestamp', 'timestamp'),
        {'schema': 'time_series'}
    )
    
    id = Column(Integer, primary_key=True)
    indicator = Column(String(50), nullable=False, comment='Nome do indicador')
    value = Column(Numeric(15, 6), nullable=False, comment='Valor do indicador')
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, comment='Data da observação')
    source = Column(String(50), nullable=False, comment='Fonte dos dados')
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), comment='Data de criação do registro')

class Regime(Base):
    """Regimes econômicos identificados"""
    
    __tablename__ = 'regimes'
    __table_args__ = (
        Index('idx_regimes_timestamp', 'timestamp'),
        {'schema': 'time_series'}
    )
    
    id = Column(Integer, primary_key=True)
    regime_type = Column(String(50), nullable=False, comment='Tipo do regime')
    probability = Column(Numeric(5, 4), nullable=False, comment='Probabilidade do regime')
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, comment='Data da observação')
    model_version = Column(String(20), nullable=False, comment='Versão do modelo')
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), comment='Data de criação do registro')

class Spillover(Base):
    """Spillovers calculados"""
    
    __tablename__ = 'spillovers'
    __table_args__ = (
        Index('idx_spillovers_channel', 'channel'),
        Index('idx_spillovers_timestamp', 'timestamp'),
        {'schema': 'time_series'}
    )
    
    id = Column(Integer, primary_key=True)
    channel = Column(String(50), nullable=False, comment='Canal de spillover')
    impact_magnitude = Column(Numeric(10, 6), nullable=False, comment='Magnitude do impacto')
    confidence_interval_lower = Column(Numeric(10, 6), nullable=False, comment='Limite inferior do intervalo de confiança')
    confidence_interval_upper = Column(Numeric(10, 6), nullable=False, comment='Limite superior do intervalo de confiança')
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, comment='Data da observação')
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), comment='Data de criação do registro')

class Forecast(Base):
    """Previsões de indicadores"""
    
    __tablename__ = 'forecasts'
    __table_args__ = (
        Index('idx_forecasts_indicator', 'indicator'),
        Index('idx_forecasts_timestamp', 'timestamp'),
        {'schema': 'time_series'}
    )
    
    id = Column(Integer, primary_key=True)
    indicator = Column(String(50), nullable=False, comment='Nome do indicador')
    forecast_value = Column(Numeric(15, 6), nullable=False, comment='Valor previsto')
    confidence_interval_lower = Column(Numeric(15, 6), nullable=False, comment='Limite inferior do intervalo de confiança')
    confidence_interval_upper = Column(Numeric(15, 6), nullable=False, comment='Limite superior do intervalo de confiança')
    horizon_months = Column(Integer, nullable=False, comment='Horizonte de previsão em meses')
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, comment='Data da observação')
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), comment='Data de criação do registro')
