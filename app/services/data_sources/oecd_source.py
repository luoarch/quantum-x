import httpx
import pandas as pd
import asyncio
import time
import random
import logging
from typing import Dict, Any, Optional
from io import StringIO

from .base_source import DataSource
from app.core.config import settings

logger = logging.getLogger(__name__)

class OECDSource(DataSource):
    """Fonte de dados da OECD para CLI com chunking e backoff robusto"""

    def __init__(self):
        super().__init__("OECD_CSV", priority=1)
        self.base_url = settings.OECD_BASE_URL
        self.timeout = settings.REQUEST_TIMEOUT
        self.min_interval = settings.OECD_RATE_LIMIT
        self.last_request_time = 0
        self._lock = asyncio.Lock()
        self.countries = settings.OECD_COUNTRIES

    async def _rate_limit(self):
        """Rate limiting robusto com lock"""
        async with self._lock:
            now = time.time()
            if now - self.last_request_time < self.min_interval:
                await asyncio.sleep(self.min_interval - (now - self.last_request_time))
            self.last_request_time = time.time()

    async def fetch_data(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Busca dados de CLI da OECD com chunking e backoff"""
        series_name = series_config.get('series_name', 'cli')
        country = series_config.get('country', 'BRA')
        
        if series_name != 'cli':
            raise ValueError(f"Série {series_name} não suportada pela OECD")
        
        # Verificar cache primeiro
        cache_key = f"oecd_cli_{country}_{series_name}"
        cached_data = await self._get_from_cache(cache_key)
        if cached_data is not None:
            logger.info(f"✅ [OECD CSV] Dados recuperados do cache para {country}")
            return cached_data
        
        # Buscar dados com chunking
        try:
            data = await self._fetch_data_with_chunking(country)
            if not data.empty:
                await self._save_to_cache(cache_key, data)
            return data
        except Exception as e:
            logger.error(f"❌ [OECD CSV] Erro ao buscar CLI {country}: {e}")
            raise

    async def _fetch_data_with_chunking(self, country: str) -> pd.DataFrame:
        """Busca dados com chunking de períodos (OECD limitou a 20 downloads/hora)"""
        start_year = 2023  # Período menor para evitar rate limit
        end_year = 2025
        chunk_size = 1  # 1 ano por chunk (mais conservador)
        
        df_list = []
        
        for year_start in range(start_year, end_year + 1, chunk_size):
            year_end = min(year_start + chunk_size - 1, end_year)
            
            try:
                chunk_data = await self._request_with_backoff(country, year_start, year_end)
                if not chunk_data.empty:
                    df_list.append(chunk_data)
                    logger.info(f"✅ [OECD CSV] Chunk {year_start}-{year_end} coletado ({len(chunk_data)} registros)")
                else:
                    logger.warning(f"⚠️ [OECD CSV] Chunk {year_start}-{year_end} vazio")
            except Exception as e:
                logger.error(f"❌ [OECD CSV] Erro no chunk {year_start}-{year_end}: {e}")
                continue
        
        if df_list:
            result = pd.concat(df_list, ignore_index=True)
            result = result.drop_duplicates(subset=['date']).sort_values('date')
            logger.info(f"✅ [OECD CSV] Total coletado: {len(result)} registros")
            return result
        else:
            logger.warning("⚠️ [OECD CSV] Nenhum chunk coletado com sucesso")
            return pd.DataFrame()

    async def _request_with_backoff(self, country: str, start_year: int, end_year: int) -> pd.DataFrame:
        """Faz requisição com backoff exponencial"""
        max_retries = 5
        backoff = 1.0
        
        for attempt in range(max_retries):
            try:
                await self._rate_limit()
                
                params = {
                    'startPeriod': f"{start_year}-01",
                    'endPeriod': f"{end_year}-12",
                    'format': 'csvfilewithlabels',
                    'dimensionAtObservation': 'AllDimensions'
                }
                
                logger.info(f"🌐 [OECD CSV] Fazendo requisição para {start_year}-{end_year}")
                logger.debug(f"📋 [OECD CSV] URL: {self.base_url}")
                logger.debug(f"📋 [OECD CSV] Params: {params}")
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(self.base_url, params=params)
                    logger.debug(f"📊 [OECD CSV] Status: {response.status_code}")
                    response.raise_for_status()
                    
                    df = pd.read_csv(StringIO(response.text))
                    
                    # Filtrar para o país específico e CLI normalizado
                    df_filtered = df[
                        (df['LOCATION'] == country) & 
                        (df['SUBJECT'] == 'LOLICLAA') &
                        (df['ADJUSTMENT'] == 'AA')
                    ].copy()
                    
                    if df_filtered.empty:
                        return pd.DataFrame()
                    
                    # Processar dados
                    df_result = df_filtered[['TIME_PERIOD', 'OBS_VALUE']].copy()
                    df_result = df_result.rename(columns={'TIME_PERIOD': 'date', 'OBS_VALUE': 'value'})
                    df_result['date'] = pd.to_datetime(df_result['date'] + '-01')
                    df_result['value'] = pd.to_numeric(df_result['value'], errors='coerce')
                    
                    # Adicionar metadados
                    df_result['source'] = self.name
                    df_result['series_name'] = 'CLI'
                    df_result['series_code'] = 'CLI'
                    df_result['unit'] = 'Index'
                    df_result['frequency'] = 'Monthly'
                    df_result['country'] = country
                    
                    return df_result
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = backoff + random.random()
                        logger.warning(f"⚠️ [OECD CSV] 429 recebido, aguardando {wait_time:.1f}s (tentativa {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        backoff *= 2
                        continue
                    else:
                        logger.error(f"❌ [OECD CSV] 429 persistente após {max_retries} tentativas")
                        raise RuntimeError("429 persistente após retries")
                else:
                    logger.error(f"❌ [OECD CSV] Erro HTTP {e.response.status_code}: {e}")
                    raise
            except Exception as e:
                logger.error(f"❌ [OECD CSV] Erro na requisição: {e}")
                raise
        
        logger.error(f"❌ [OECD CSV] Falha após {max_retries} tentativas")
        raise RuntimeError("Falha após múltiplas tentativas")
    
    async def _get_from_cache(self, cache_key: str):
        """Recupera dados do cache"""
        try:
            import os
            import pickle
            
            cache_dir = "cache"
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, f"{cache_key}.pkl")
            
            if os.path.exists(cache_file):
                # Verificar se o cache não expirou (24 horas)
                if time.time() - os.path.getmtime(cache_file) < 86400:
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
                else:
                    os.remove(cache_file)
            
            return None
        except Exception as e:
            logger.warning(f"⚠️ [OECD CSV] Erro ao ler cache: {e}")
            return None
    
    async def _save_to_cache(self, cache_key: str, data: pd.DataFrame):
        """Salva dados no cache"""
        try:
            import os
            import pickle
            
            cache_dir = "cache"
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, f"{cache_key}.pkl")
            
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
                
            logger.debug(f"💾 [OECD CSV] Dados salvos no cache: {cache_key}")
        except Exception as e:
            logger.warning(f"⚠️ [OECD CSV] Erro ao salvar cache: {e}")

    def validate_data(self, data: pd.DataFrame) -> bool:
        """Valida qualidade dos dados OECD CLI"""
        if data.empty:
            return False
        required_cols = ['date', 'value', 'source', 'series_name', 'country']
        if not all(col in data.columns for col in required_cols):
            return False
        if data['value'].isnull().sum() / len(data) > 0.1:
            return False
        return True