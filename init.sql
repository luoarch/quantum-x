-- Script de inicialização do banco de dados
-- Global Economic Regime Analysis & Brazil Spillover Prediction System
-- Conforme especificação do DRS seção 2.1

-- Habilitar extensão TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Criar schema para séries temporais
CREATE SCHEMA IF NOT EXISTS time_series;

-- Tabela para dados globais
CREATE TABLE IF NOT EXISTS time_series.global_data (
    id SERIAL PRIMARY KEY,
    country VARCHAR(3) NOT NULL,
    indicator VARCHAR(50) NOT NULL,
    value DECIMAL(15,6) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Criar hypertable para dados globais
SELECT create_hypertable('time_series.global_data', 'timestamp');

-- Tabela para dados do Brasil
CREATE TABLE IF NOT EXISTS time_series.brazil_data (
    id SERIAL PRIMARY KEY,
    indicator VARCHAR(50) NOT NULL,
    value DECIMAL(15,6) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Criar hypertable para dados do Brasil
SELECT create_hypertable('time_series.brazil_data', 'timestamp');

-- Tabela para regimes identificados
CREATE TABLE IF NOT EXISTS time_series.regimes (
    id SERIAL PRIMARY KEY,
    regime_type VARCHAR(50) NOT NULL,
    probability DECIMAL(5,4) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Criar hypertable para regimes
SELECT create_hypertable('time_series.regimes', 'timestamp');

-- Tabela para spillovers
CREATE TABLE IF NOT EXISTS time_series.spillovers (
    id SERIAL PRIMARY KEY,
    channel VARCHAR(50) NOT NULL,
    impact_magnitude DECIMAL(10,6) NOT NULL,
    confidence_interval_lower DECIMAL(10,6) NOT NULL,
    confidence_interval_upper DECIMAL(10,6) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Criar hypertable para spillovers
SELECT create_hypertable('time_series.spillovers', 'timestamp');

-- Tabela para previsões
CREATE TABLE IF NOT EXISTS time_series.forecasts (
    id SERIAL PRIMARY KEY,
    indicator VARCHAR(50) NOT NULL,
    forecast_value DECIMAL(15,6) NOT NULL,
    confidence_interval_lower DECIMAL(15,6) NOT NULL,
    confidence_interval_upper DECIMAL(15,6) NOT NULL,
    horizon_months INTEGER NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Criar hypertable para previsões
SELECT create_hypertable('time_series.forecasts', 'timestamp');

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_global_data_country_indicator 
ON time_series.global_data (country, indicator);

CREATE INDEX IF NOT EXISTS idx_global_data_timestamp 
ON time_series.global_data (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_brazil_data_indicator 
ON time_series.brazil_data (indicator);

CREATE INDEX IF NOT EXISTS idx_brazil_data_timestamp 
ON time_series.brazil_data (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_regimes_timestamp 
ON time_series.regimes (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_spillovers_channel 
ON time_series.spillovers (channel);

CREATE INDEX IF NOT EXISTS idx_spillovers_timestamp 
ON time_series.spillovers (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_forecasts_indicator 
ON time_series.forecasts (indicator);

CREATE INDEX IF NOT EXISTS idx_forecasts_timestamp 
ON time_series.forecasts (timestamp DESC);

-- Políticas de retenção de dados (manter 5 anos)
SELECT add_retention_policy('time_series.global_data', INTERVAL '5 years');
SELECT add_retention_policy('time_series.brazil_data', INTERVAL '5 years');
SELECT add_retention_policy('time_series.regimes', INTERVAL '5 years');
SELECT add_retention_policy('time_series.spillovers', INTERVAL '5 years');
SELECT add_retention_policy('time_series.forecasts', INTERVAL '5 years');

-- Comentários nas tabelas
COMMENT ON TABLE time_series.global_data IS 'Dados econômicos globais de países G7 + China + Brasil';
COMMENT ON TABLE time_series.brazil_data IS 'Dados econômicos específicos do Brasil';
COMMENT ON TABLE time_series.regimes IS 'Regimes econômicos identificados pelo modelo RS-GVAR';
COMMENT ON TABLE time_series.spillovers IS 'Spillovers calculados via 4 canais de transmissão';
COMMENT ON TABLE time_series.forecasts IS 'Previsões de indicadores macroeconômicos brasileiros';
