"""
Fonte dedicada do BACEN (SGS) usando API oficial

Princípios SOLID:
- SRP: classe lida apenas com coleta/validação da API SGS
- OCP: mapeamentos e parâmetros configuráveis sem alterar chamadas
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Final, Literal, TypedDict, Mapping, Tuple, cast

import httpx
import pandas as pd

from .base_source import DataSource


logger = logging.getLogger(__name__)


BASE_URL: Final[str] = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"


SeriesKey = Literal['selic', 'ipca', 'cambio', 'pib', 'desemprego']


class BacenSeriesConfig(TypedDict, total=False):
    name: SeriesKey
    country: str
    limit: int
    start_date: str  # dd/mm/YYYY
    end_date: str    # dd/mm/YYYY


BACEN_SERIES: Mapping[SeriesKey, int] = {
    'selic': 432,
    'ipca': 433,
    'cambio': 3698,      # PTAX
    'pib': 4380,         # PIB mensal
    'desemprego': 24369, # IBGE via BCB
}


class BacenSGSSource(DataSource):
    """
    Fonte de dados do BACEN (SGS) via REST API oficial.
    """

    def __init__(self) -> None:
        super().__init__(name="BACEN_SGS", priority=1)
        self._timeout_seconds: float = 30.0
        self._max_retries: int = 3

    async def fetch_data(self, series_config: Dict[str, object]) -> pd.DataFrame:  # type: ignore[override]
        """Busca dados da série via API SGS.

        series_config esperada:
        - name: str (chave da série, ex: 'ipca')
        - country: str (ignorado para SGS, mantido por compatibilidade)
        - limit: int (meses históricos) OU start_date/end_date (dd/mm/YYYY)
        """
        parsed_config: BacenSeriesConfig = self._parse_config(series_config)
        series_name: SeriesKey = parsed_config['name']
        if series_name not in BACEN_SERIES:
            raise ValueError(f"Série {series_name} não suportada na API SGS")

        codigo: int = int(BACEN_SERIES[series_name])

        # Datas
        start_str, end_str = self._resolve_date_range(parsed_config)

        url = BASE_URL.format(codigo=codigo)
        params: Dict[str, str] = {
            'formato': 'json',
            'dataInicial': start_str,
            'dataFinal': end_str,
        }

        try:
            # Executar requisição em executor se for necessário bloquear
            df = await self._request_json_as_dataframe(url, params)
            if df.empty:
                raise ValueError("Nenhum dado retornado pela API do BACEN (SGS)")

            # Padronização de colunas
            # API retorna 'data' e 'valor'
            if 'data' not in df.columns or 'valor' not in df.columns:
                raise ValueError("Resposta inesperada da API SGS: colunas ausentes")

            df = df.rename(columns={'data': 'date', 'valor': 'value'})
            df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna(subset=['date']).sort_values('date').reset_index(drop=True)

            # Metadados
            df['source'] = self.name
            df['series_name'] = series_name.upper()
            df['series_code'] = str(codigo)
            df['unit'] = self._get_unit(series_name)
            df['frequency'] = self._get_frequency(series_name)
            df['method'] = 'sgs-api'

            self.mark_success()
            logger.info(f"✅ [BACEN_SGS] {series_name} - {len(df)} registros ({start_str} a {end_str})")
            return df
        except Exception as exc:  # noqa: BLE001
            self.mark_failure(str(exc))
            logger.error(f"❌ [BACEN_SGS] Erro ao buscar {series_name}: {exc}")
            raise

    def validate_data(self, data: pd.DataFrame) -> bool:
        if data.empty:
            return False
        required = {'date', 'value', 'source'}
        if not required.issubset(data.columns):
            return False
        if not data['date'].is_monotonic_increasing:
            return False
        null_ratio = float(data['value'].isnull().sum()) / float(len(data))
        if null_ratio > 0.1:
            return False
        return True

    async def _request_json_as_dataframe(self, url: str, params: Mapping[str, str]) -> pd.DataFrame:
        last_error: Optional[Exception] = None
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            for attempt in range(1, self._max_retries + 1):
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    try:
                        data = response.json()
                    except Exception as json_exc:  # noqa: BLE001
                        body_preview = (response.text or "").strip()[:200]
                        raise ValueError(f"Falha ao decodificar JSON (status={response.status_code}, body='{body_preview}')") from json_exc
                    if not isinstance(data, list):
                        raise ValueError(f"Formato inválido (status={response.status_code}). Tipo={type(data).__name__}")
                    return pd.DataFrame(cast(list[Dict[str, object]], data))
                except httpx.HTTPStatusError as http_exc:
                    last_error = http_exc
                    status = http_exc.response.status_code if http_exc.response is not None else 'unknown'
                    wait_seconds = min(2.0 * attempt, 6.0)
                    logger.warning(f"⚠️ [BACEN_SGS] Tentativa {attempt} falhou com HTTP {status}. Retentando em {wait_seconds:.1f}s…")
                    await asyncio.sleep(wait_seconds)
                except httpx.RequestError as req_exc:
                    last_error = req_exc
                    wait_seconds = min(2.0 * attempt, 6.0)
                    logger.warning(f"⚠️ [BACEN_SGS] Tentativa {attempt} erro de rede: {req_exc}. Retentando em {wait_seconds:.1f}s…")
                    await asyncio.sleep(wait_seconds)
                except Exception as exc:  # noqa: PERF203, BLE001
                    last_error = exc
                    wait_seconds = min(2.0 * attempt, 6.0)
                    msg = str(exc) or exc.__class__.__name__
                    logger.warning(f"⚠️ [BACEN_SGS] Tentativa {attempt} falhou: {msg}. Retentando em {wait_seconds:.1f}s…")
                    await asyncio.sleep(wait_seconds)
        assert last_error is not None
        raise last_error

    def _resolve_date_range(self, series_config: BacenSeriesConfig) -> Tuple[str, str]:
        # Preferir datas explícitas
        start = series_config.get('start_date')
        end = series_config.get('end_date')
        if isinstance(start, str) and isinstance(end, str):
            return start, end

        # Caso contrário, usar 'limit' em meses
        limit_val = series_config.get('limit')
        months: int
        if isinstance(limit_val, int) and limit_val > 0:
            months = limit_val
        else:
            months = 120

        end_dt = datetime.today().date()
        start_dt = (datetime.today() - timedelta(days=30 * months)).date()
        # Formato exigido pela API: dd/mm/YYYY
        return start_dt.strftime('%d/%m/%Y'), end_dt.strftime('%d/%m/%Y')

    def _get_unit(self, series_name: SeriesKey) -> str:
        units: Dict[SeriesKey, str] = {
            'ipca': '%',
            'selic': '%',
            'cambio': 'BRL/USD',
            'pib': 'R$ milhões',
            'desemprego': '%',
        }
        return units.get(series_name, 'unknown')

    def _get_frequency(self, series_name: SeriesKey) -> str:
        if series_name == 'cambio':
            return 'daily'
        if series_name == 'desemprego':
            return 'monthly'  # série agregada mensal via SGS
        return 'monthly'

    def _parse_config(self, series_config: Dict[str, object]) -> BacenSeriesConfig:
        name_raw = series_config.get('name')
        if not isinstance(name_raw, str):
            raise ValueError("Parâmetro 'name' é obrigatório e deve ser string")
        name_norm = name_raw.lower()
        if name_norm not in BACEN_SERIES:
            raise ValueError(f"Série '{name_norm}' não suportada")

        parsed: BacenSeriesConfig = {
            'name': cast(SeriesKey, name_norm)
        }

        if isinstance(series_config.get('country'), str):
            parsed['country'] = cast(str, series_config['country'])
        if isinstance(series_config.get('limit'), int):
            parsed['limit'] = cast(int, series_config['limit'])
        if isinstance(series_config.get('start_date'), str):
            parsed['start_date'] = cast(str, series_config['start_date'])
        if isinstance(series_config.get('end_date'), str):
            parsed['end_date'] = cast(str, series_config['end_date'])
        return parsed


