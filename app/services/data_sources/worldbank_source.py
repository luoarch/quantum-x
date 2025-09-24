"""
Fonte de dados do World Bank - Composite Leading Indicators
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


class WorldBankSource(DataSource):
    """Fonte de dados do World Bank para CLI"""
    
    def __init__(self):
        super().__init__("WorldBank", priority=3)
        self.base_url = "http://api.worldbank.org/v2/country"
        self.timeout = settings.REQUEST_TIMEOUT
        self.min_interval = 3.0  # World Bank é mais lento
        self._lock = asyncio.Lock()
        self._last_request_time = 0
        
        # Mapear países para códigos World Bank
        self.country_map = {
            'BRA': 'BR',  # Brasil
            'USA': 'US',  # Estados Unidos
            'CHN': 'CN',  # China
            'DEU': 'DE',  # Alemanha
            'GBR': 'GB',  # Reino Unido
        }
    
    async def _rate_limit(self):
        """Implementa rate limiting para World Bank"""
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                logger.info(f"⏳ World Bank rate limiting: aguardando {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
            
            self._last_request_time = time.time()
    
    async def fetch_data(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Busca dados de CLI via World Bank"""
        try:
            country = series_config.get('country', 'BRA')
            start_year = series_config.get('start_year', 2020)
            end_year = series_config.get('end_year', 2025)
            
            # Mapear país
            country_code = self.country_map.get(country, 'BR')
            
            # Aplicar rate limiting
            await self._rate_limit()
            
            # URL para Composite Leading Indicators
            url = f"{self.base_url}/{country_code}/indicator/CMO.CLI"
            params = {
                'date': f"{start_year}:{end_year}",
                'format': 'json',
                'per_page': 1000
            }
            
            logger.info(f"🌐 [World Bank] Buscando CLI para {country} ({country_code})")
            logger.info(f"📅 Período: {start_year} a {end_year}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if not data or len(data) < 2:
                    raise ValueError("Nenhum dado retornado")
                
                # World Bank retorna array com metadados e dados
                observations = data[1] if len(data) > 1 else []
                
                if not observations:
                    raise ValueError("Nenhuma observação encontrada")
                
                # Processar dados
                df = pd.DataFrame(observations)
                df = df[df['value'].notna()]  # Remover valores nulos
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df['date'] = pd.to_datetime(df['date'])
                
                # Renomear colunas
                df = df.rename(columns={'value': 'value'})
                df = df[['date', 'value']].copy()
                
                # Adicionar metadados
                df['source'] = self.name
                df['series_name'] = 'CLI_WorldBank'
                df['series_code'] = 'CMO.CLI'
                df['unit'] = 'Index'
                df['frequency'] = 'Monthly'
                df['country'] = country
                
                # Ordenar por data
                df = df.sort_values('date').reset_index(drop=True)
                
                self.mark_success()
                logger.info(f"✅ [World Bank] Sucesso ao buscar CLI {country} ({len(df)} registros)")
                return df
                
        except Exception as e:
            self.mark_failure(str(e))
            logger.error(f"❌ [World Bank] Erro ao buscar CLI {series_config.get('country', 'BRA')}: {e}")
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
        """Verifica o status de saúde da fonte World Bank"""
        try:
            # Testar com dados recentes
            test_config = {'country': 'BRA', 'start_year': 2024, 'end_year': 2024}
            test_df = await self.fetch_data(test_config)
            
            return {
                'status': 'healthy' if not test_df.empty else 'degraded',
                'last_check': datetime.now().isoformat(),
                'test_records': len(test_df),
                'error': None,
                'method': 'WorldBank_API'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'test_records': 0,
                'error': str(e),
                'method': 'WorldBank_API'
            }
