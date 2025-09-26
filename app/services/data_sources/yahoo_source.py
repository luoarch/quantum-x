"""
Fonte de dados do Yahoo Finance (preços e OHLCV) via yfinance

Princípios SOLID:
- SRP: classe dedicada a coletar e validar dados de preços
- OCP: símbolos e parâmetros configuráveis
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Final, Mapping, TypedDict

import pandas as pd

from .base_source import DataSource

logger = logging.getLogger(__name__)


class YahooConfig(TypedDict, total=False):
    symbol: str
    period: str  # ex: "2y", "1y", "6mo"
    interval: str  # ex: "1d", "1wk", "1mo"


YAHOO_SYMBOLS: Dict[str, str] = {
    'BOVA11': 'BOVA11.SA',
    'IBOVESPA': '^BVSP',
    'VALE': 'VALE3.SA',
    'PETR': 'PETR4.SA',
    'BRL_USD': 'BRL=X'
}


class YahooSource(DataSource):
    """Fonte de preços do Yahoo Finance usando yfinance"""

    def __init__(self) -> None:
        super().__init__(name="YAHOO_FINANCE", priority=1)
        self._default_period: Final[str] = "2y"
        self._default_interval: Final[str] = "1mo"

        # Import tardio para não exigir dependência se não usada
        try:
            import yfinance as yf  # noqa: F401
            self._yf_available = True
        except Exception as exc:  # noqa: BLE001
            self._yf_available = False
            logger.warning(f"yfinance não disponível: {exc}. Instale com: pip install yfinance")

    async def fetch_data(self, series_config: Dict[str, object]) -> pd.DataFrame:  # type: ignore[override]
        if not self._yf_available:
            raise ImportError("Dependência yfinance ausente")

        config: YahooConfig = self._parse_config(series_config)

        # Executar em thread para não bloquear loop
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(None, self._fetch_sync, config)

        if df.empty:
            raise ValueError("Nenhum dado retornado do Yahoo Finance")

        # Padronizar colunas: date/value (close)
        out = df.reset_index().rename(columns={
            'Date': 'date',
            'Close': 'value'
        })
        if 'date' not in out.columns:
            # Alguns retornos usam índice datetime sem coluna Date
            out['date'] = pd.to_datetime(df.index)
        out['date'] = pd.to_datetime(out['date'], errors='coerce')
        out = out.dropna(subset=['date']).sort_values('date')

        # Metadados
        out['source'] = self.name
        out['series_name'] = config['symbol']
        out['series_code'] = YAHOO_SYMBOLS.get(config['symbol'], config['symbol'])
        out['unit'] = 'price'
        out['frequency'] = config.get('interval', self._default_interval)
        out['method'] = 'yfinance-api'

        self.mark_success()
        logger.info(f"✅ [Yahoo] {config['symbol']} - {len(out)} registros ({config.get('period', self._default_period)})")
        return out

    def validate_data(self, data: pd.DataFrame) -> bool:
        if data.empty:
            return False
        required = {'date', 'value', 'source'}
        if not required.issubset(set(data.columns)):
            return False
        if not data['date'].is_monotonic_increasing:
            return False
        if data['value'].isnull().mean() > 0.05:
            return False
        return True

    def _parse_config(self, raw: Dict[str, object]) -> YahooConfig:
        symbol_obj = raw.get('symbol') or raw.get('name')
        if not isinstance(symbol_obj, str):
            raise ValueError("Parâmetro 'symbol' é obrigatório para YahooSource")
        symbol_key = symbol_obj
        yf_symbol = YAHOO_SYMBOLS.get(symbol_key, symbol_key)

        period = raw.get('period') if isinstance(raw.get('period'), str) else self._default_period
        interval = raw.get('interval') if isinstance(raw.get('interval'), str) else self._default_interval

        return YahooConfig(symbol=symbol_key, period=period, interval=interval)

    def _fetch_sync(self, config: YahooConfig) -> pd.DataFrame:
        import yfinance as yf
        ticker = yf.Ticker(YAHOO_SYMBOLS.get(config['symbol'], config['symbol']))
        hist = ticker.history(period=config.get('period', self._default_period), interval=config.get('interval', self._default_interval))
        # Assegurar DataFrame
        if isinstance(hist, pd.DataFrame):
            return hist
        return pd.DataFrame()


