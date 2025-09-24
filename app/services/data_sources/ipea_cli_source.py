"""
Fonte de dados do IPEA - CLI Brasil
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


class IPEACLISource(DataSource):
    """Fonte de dados do IPEA para CLI Brasil"""
    
    def __init__(self):
        super().__init__("IPEA_CLI", priority=4)
        self.base_url = "http://www.ipeadata.gov.br/api/odata4"
        self.timeout = settings.REQUEST_TIMEOUT
        self.min_interval = 3.0
        self._lock = asyncio.Lock()
        self._last_request_time = 0
        
        # Séries CLI disponíveis no IPEA
        self.cli_series = {
            'CLI12': 'CLI Brasil - IPEA',
            'CLI_BR': 'CLI Brasil - FGV',
        }
    
    async def _rate_limit(self):
        """Implementa rate limiting para IPEA"""
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                logger.info(f"⏳ IPEA rate limiting: aguardando {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
            
            self._last_request_time = time.time()
    
    async def fetch_data(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Busca dados de CLI via IPEA"""
        try:
            country = series_config.get('country', 'BRA')
            start_year = series_config.get('start_year', 2020)
            end_year = series_config.get('end_year', 2025)
            
            # Só funciona para Brasil
            if country != 'BRA':
                raise ValueError(f"IPEA CLI só disponível para Brasil, recebido: {country}")
            
            # Aplicar rate limiting
            await self._rate_limit()
            
            # Tentar diferentes séries CLI
            for series_code, series_name in self.cli_series.items():
                try:
                    url = f"{self.base_url}/Metadados('{series_code}')/Valores"
                    params = {
                        '$top': 1000,
                        '$orderby': 'VALDATA desc'
                    }
                    
                    logger.info(f"🌐 [IPEA CLI] Buscando {series_name} ({series_code})")
                    
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.get(url, params=params)
                        response.raise_for_status()
                        
                        data = response.json()
                        
                        if 'value' not in data or not data['value']:
                            logger.warning(f"⚠️ [IPEA CLI] Nenhum dado para {series_code}")
                            continue
                        
                        # Processar dados
                        df = pd.DataFrame(data['value'])
                        df = df[df['VALVALOR'].notna()]  # Remover valores nulos
                        df['value'] = pd.to_numeric(df['VALVALOR'], errors='coerce')
                        df['date'] = pd.to_datetime(df['VALDATA'])
                        
                        # Filtrar por período
                        df = df[(df['date'].dt.year >= start_year) & (df['date'].dt.year <= end_year)]
                        
                        if df.empty:
                            logger.warning(f"⚠️ [IPEA CLI] Nenhum dado no período para {series_code}")
                            continue
                        
                        # Renomear colunas
                        df = df[['date', 'value']].copy()
                        
                        # Adicionar metadados
                        df['source'] = self.name
                        df['series_name'] = series_name
                        df['series_code'] = series_code
                        df['unit'] = 'Index'
                        df['frequency'] = 'Monthly'
                        df['country'] = country
                        
                        # Ordenar por data
                        df = df.sort_values('date').reset_index(drop=True)
                        
                        self.mark_success()
                        logger.info(f"✅ [IPEA CLI] Sucesso ao buscar {series_name} ({len(df)} registros)")
                        return df
                        
                except Exception as e:
                    logger.warning(f"⚠️ [IPEA CLI] Falha na série {series_code}: {e}")
                    continue
            
            # Se chegou aqui, nenhuma série funcionou
            raise ValueError("Nenhuma série CLI disponível no IPEA")
                
        except Exception as e:
            self.mark_failure(str(e))
            logger.error(f"❌ [IPEA CLI] Erro ao buscar CLI {series_config.get('country', 'BRA')}: {e}")
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
        """Verifica o status de saúde da fonte IPEA CLI"""
        try:
            # Testar com dados recentes
            test_config = {'country': 'BRA', 'start_year': 2024, 'end_year': 2024}
            test_df = await self.fetch_data(test_config)
            
            return {
                'status': 'healthy' if not test_df.empty else 'degraded',
                'last_check': datetime.now().isoformat(),
                'test_records': len(test_df),
                'error': None,
                'method': 'IPEA_CLI_API'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'test_records': 0,
                'error': str(e),
                'method': 'IPEA_CLI_API'
            }
