"""
Fonte de dados do GitHub OECD - CLI Data
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


class GitHubOECDSource(DataSource):
    """Fonte de dados do GitHub OECD para CLI"""
    
    def __init__(self):
        super().__init__("GitHub_OECD", priority=5)
        self.base_url = "https://raw.githubusercontent.com/OECD-Data/CLI-data/main/cli-data.csv"
        self.timeout = settings.REQUEST_TIMEOUT
        self.min_interval = 5.0  # GitHub é mais lento
        self._lock = asyncio.Lock()
        self._last_request_time = 0
        
        # Países suportados
        self.countries = ['BRA', 'USA', 'CHN', 'DEU', 'GBR', 'OECD']
    
    async def _rate_limit(self):
        """Implementa rate limiting para GitHub"""
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                logger.info(f"⏳ GitHub rate limiting: aguardando {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
            
            self._last_request_time = time.time()
    
    async def fetch_data(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Busca dados de CLI via GitHub OECD"""
        try:
            country = series_config.get('country', 'BRA')
            start_year = series_config.get('start_year', 2020)
            end_year = series_config.get('end_year', 2025)
            
            if country not in self.countries:
                raise ValueError(f"País {country} não suportado pelo GitHub OECD")
            
            # Aplicar rate limiting
            await self._rate_limit()
            
            # URL para download do CSV
            url = f"{self.base_url}/cli-data.csv"
            
            logger.info(f"🌐 [GitHub OECD] Baixando CLI data para {country}")
            logger.info(f"📅 Período: {start_year} a {end_year}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Ler CSV diretamente
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                
                if df.empty:
                    raise ValueError("Nenhum dado retornado")
                
                # Filtrar para o país específico
                df_filtered = df[df['LOCATION'] == country].copy()
                
                if df_filtered.empty:
                    raise ValueError(f"Nenhum dado CLI encontrado para {country}")
                
                # Processar dados
                df_result = df_filtered[['TIME', 'Value']].copy()
                df_result = df_result.rename(columns={'TIME': 'date', 'Value': 'value'})
                df_result['date'] = pd.to_datetime(df_result['date'] + '-01')
                df_result['value'] = pd.to_numeric(df_result['value'], errors='coerce')
                
                # Filtrar por período
                df_result = df_result[(df_result['date'].dt.year >= start_year) & (df_result['date'].dt.year <= end_year)]
                
                if df_result.empty:
                    raise ValueError(f"Nenhum dado no período {start_year}-{end_year} para {country}")
                
                # Adicionar metadados
                df_result['source'] = self.name
                df_result['series_name'] = 'CLI_OECD_GitHub'
                df_result['series_code'] = 'CLI_GitHub'
                df_result['unit'] = 'Index'
                df_result['frequency'] = 'Monthly'
                df_result['country'] = country
                
                # Ordenar por data
                df_result = df_result.sort_values('date').reset_index(drop=True)
                
                self.mark_success()
                logger.info(f"✅ [GitHub OECD] Sucesso ao buscar CLI {country} ({len(df_result)} registros)")
                return df_result
                
        except Exception as e:
            self.mark_failure(str(e))
            logger.error(f"❌ [GitHub OECD] Erro ao buscar CLI {series_config.get('country', 'BRA')}: {e}")
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
        """Verifica o status de saúde da fonte GitHub OECD"""
        try:
            # Testar com dados recentes
            test_config = {'country': 'BRA', 'start_year': 2024, 'end_year': 2024}
            test_df = await self.fetch_data(test_config)
            
            return {
                'status': 'healthy' if not test_df.empty else 'degraded',
                'last_check': datetime.now().isoformat(),
                'test_records': len(test_df),
                'error': None,
                'method': 'GitHub_OECD_CSV'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'test_records': 0,
                'error': str(e),
                'method': 'GitHub_OECD_CSV'
            }
