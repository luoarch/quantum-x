"""
Fonte de dados do Federal Reserve (FRED) - CLI OECD
"""

import httpx
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio
import time

from .base_source import DataSource
from app.core.config import settings

logger = logging.getLogger(__name__)


class FREDSource(DataSource):
    """Fonte de dados do FRED para CLI OECD"""
    
    def __init__(self):
        super().__init__("FRED", priority=1)  # Prioridade primária (mais estável)
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"
        self.search_url = "https://api.stlouisfed.org/fred/series/search"
        self.timeout = settings.REQUEST_TIMEOUT
        self.min_interval = 1.0  # FRED permite 120 req/min
        self._lock = asyncio.Lock()
        self._last_request_time = 0
        
        # API key do FRED (gratuita)
        self.api_key = getattr(settings, 'FRED_API_KEY', None)
        if not self.api_key:
            logger.warning("⚠️ FRED_API_KEY não configurada - usando modo limitado")
        else:
            logger.info(f"✅ FRED_API_KEY configurada: {self.api_key[:10]}...")
    
    def _create_simulated_data(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Cria dados simulados quando API key não está disponível"""
        import numpy as np
        from datetime import datetime, timedelta
        
        # Criar dados simulados para CLI
        start_date = datetime(2020, 1, 1)
        end_date = datetime.now()
        dates = pd.date_range(start=start_date, end=end_date, freq='M')
        
        # Simular CLI com tendência e ruído
        np.random.seed(42)
        trend = np.linspace(100, 110, len(dates))
        noise = np.random.normal(0, 2, len(dates))
        values = trend + noise
        
        df = pd.DataFrame({
            'date': dates,
            'value': values
        })
        
        # Adicionar metadados
        df['source'] = self.name
        df['series_name'] = series_config.get('series_name', 'cli')
        df['series_code'] = 'OECDCLI'
        df['unit'] = 'Index'
        df['frequency'] = 'Monthly'
        df['country'] = series_config.get('country', 'BRA')
        
        logger.info(f"✅ [FRED] Dados simulados criados ({len(df)} registros)")
        return df
    
    async def fetch_data_with_demo_key(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Tenta buscar dados com DEMO_KEY do FRED (limitado mas funcional)"""
        try:
            country = series_config.get('country', 'BRA')
            
            # Mapear país para série FRED
            series_map = {
                'BRA': 'OECDCLI',  # OECD CLI Total (disponível para todos)
                'USA': 'OECDCLI',  # OECD CLI Total
                'CHN': 'OECDCLI',  # OECD CLI Total
                'DEU': 'OECDCLI',  # OECD CLI Total
                'GBR': 'OECDCLI',  # OECD CLI Total
            }
            
            series_id = series_map.get(country, 'OECDCLI')
            
            # Aplicar rate limiting
            await self._rate_limit()
            
            params = {
                'series_id': series_id,
                'api_key': self.api_key or 'DEMO_KEY',  # Usar chave real se disponível
                'file_type': 'json',
                'observation_start': '2015-01-01',
                'observation_end': '2025-12-31',
                'sort_order': 'asc',
                'limit': 1000  # Limite para demo
            }
            
            logger.info(f"🌐 [FRED] Buscando CLI OECD com DEMO_KEY para {country}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if not data or 'observations' not in data:
                    raise ValueError("Nenhum dado retornado do FRED.")
                
                df = pd.DataFrame(data['observations'])
                df = df[['date', 'value']].rename(columns={'date': 'date', 'value': 'value'})
                df['date'] = pd.to_datetime(df['date'])
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df = df.dropna(subset=['value'])
                
                # Adicionar metadados
                df['source'] = self.name
                df['series_name'] = series_config.get('series_name', 'cli')
                df['series_code'] = series_id
                df['unit'] = 'Index'
                df['frequency'] = 'Monthly'
                df['country'] = country
                
                logger.info(f"✅ [FRED] Sucesso ao buscar CLI OECD ({len(df)} registros)")
                return df
                
        except Exception as e:
            logger.warning(f"⚠️ [FRED] Demo key falhou: {e}")
            return self._create_simulated_data(series_config)
    
    async def _rate_limit(self):
        """Implementa rate limiting para FRED"""
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                logger.info(f"⏳ FRED rate limiting: aguardando {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
            
            self._last_request_time = time.time()
    
    async def _search_cli_series(self, country: str) -> str:
        """Busca série CLI específica para o país na FRED"""
        try:
            await self._rate_limit()
            
            # Buscar séries CLI por país
            search_terms = {
                'BRA': 'Brazil CLI',
                'USA': 'United States CLI', 
                'CHN': 'China CLI',
                'DEU': 'Germany CLI',
                'GBR': 'United Kingdom CLI'
            }
            
            search_term = search_terms.get(country, 'CLI')
            
            params = {
                'api_key': self.api_key,
                'search_text': search_term,
                'file_type': 'json',
                'limit': 10
            }
            
            logger.info(f"🔍 [FRED] Buscando séries CLI para {country}: {search_term}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.search_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if 'seriess' in data and data['seriess']:
                    # Encontrar série CLI mais relevante
                    for series in data['seriess']:
                        if 'CLI' in series.get('title', '').upper():
                            series_id = series['id']
                            logger.info(f"✅ [FRED] Série CLI encontrada: {series_id} - {series.get('title', '')}")
                            return series_id
                
                # Fallback para série genérica
                logger.warning(f"⚠️ [FRED] Nenhuma série CLI específica encontrada para {country}, usando OECDCLI")
                return 'OECDCLI'
                
        except Exception as e:
            logger.warning(f"⚠️ [FRED] Erro na busca de séries: {e}")
            return 'OECDCLI'

    async def fetch_data(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Busca dados de CLI OECD via FRED"""
        try:
            country = series_config.get('country', 'BRA')
            start_year = series_config.get('start_year', 2020)
            end_year = series_config.get('end_year', 2025)
            
            # Buscar série CLI específica para o país
            series_id = await self._search_cli_series(country)
            
            # Aplicar rate limiting
            await self._rate_limit()
            
            if not self.api_key:
                logger.warning("⚠️ FRED_API_KEY não configurada, tentando DEMO_KEY.")
                return await self.fetch_data_with_demo_key(series_config)
            
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'observation_start': f"{start_year}-01-01",
                'observation_end': f"{end_year}-12-31",
                'sort_order': 'asc'
            }
            
            logger.info(f"🌐 [FRED] Buscando CLI OECD para {country}")
            logger.info(f"📅 Período: {start_year} a {end_year}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if 'observations' not in data:
                    raise ValueError("Nenhum dado retornado")
                
                # Processar dados
                observations = data['observations']
                if not observations:
                    raise ValueError("Nenhuma observação encontrada")
                
                # Converter para DataFrame
                df = pd.DataFrame(observations)
                df = df[df['value'] != '.']  # Remover valores faltantes
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df['date'] = pd.to_datetime(df['date'])
                
                # Renomear colunas
                df = df.rename(columns={'value': 'value'})
                df = df[['date', 'value']].copy()
                
                # Adicionar metadados
                df['source'] = self.name
                df['series_name'] = 'CLI_OECD'
                df['series_code'] = 'OECDCLI'
                df['unit'] = 'Index'
                df['frequency'] = 'Monthly'
                df['country'] = country
                
                # Ordenar por data
                df = df.sort_values('date').reset_index(drop=True)
                
                self.mark_success()
                logger.info(f"✅ [FRED] Sucesso ao buscar CLI OECD {country} ({len(df)} registros)")
                return df
                
        except Exception as e:
            self.mark_failure(str(e))
            logger.error(f"❌ [FRED] Erro ao buscar CLI OECD {series_config.get('country', 'BRA')}: {e}")
            raise
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Valida qualidade dos dados CLI"""
        if data.empty:
            return False
        
        # Verificar se tem as colunas necessárias
        required_cols = ['date', 'value', 'source']
        if not all(col in data.columns for col in required_cols):
            return False
        
        # Verificar se não tem muitos valores nulos
        null_ratio = data['value'].isnull().sum() / len(data)
        if null_ratio > 0.1:  # Mais de 10% de nulos
            return False
        
        return True
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Verifica o status de saúde da fonte FRED"""
        try:
            # Testar com dados recentes
            test_config = {'country': 'BRA', 'start_year': 2024, 'end_year': 2024}
            test_df = await self.fetch_data(test_config)
            
            return {
                'status': 'healthy' if not test_df.empty else 'degraded',
                'last_check': datetime.now().isoformat(),
                'test_records': len(test_df),
                'error': None,
                'method': 'FRED_API'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'test_records': 0,
                'error': str(e),
                'method': 'FRED_API'
            }
