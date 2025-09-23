"""
Fonte de dados do Trading Economics (fonte secundária para desemprego)
"""

import httpx
import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from .base_source import DataSource

logger = logging.getLogger(__name__)


class TradingEconomicsSource(DataSource):
    """Fonte de dados do Trading Economics para desemprego e consenso de mercado"""
    
    def __init__(self):
        super().__init__("TradingEconomics", priority=3)
        self.base_url = "https://api.tradingeconomics.com"
        self.timeout = 30
        
        # API Key (será configurada via environment)
        self.api_key = None
        
        # Séries disponíveis
        self.series_map = {
            'desemprego': 'BRAURHARMQDSMEI',  # Taxa de desemprego Brasil
            'ipca': 'BRACPIALLMINMEI',        # IPCA Brasil
            'selic': 'BRARECM',               # Taxa SELIC Brasil
            'pib': 'BRARGDPRPTSPPPPT'         # PIB Brasil
        }
    
    async def fetch_data(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Busca dados do Trading Economics"""
        series_name = series_config['name']
        series_code = self.series_map.get(series_name)
        
        if not series_code:
            raise ValueError(f"Série {series_name} não encontrada no Trading Economics")
        
        if not self.api_key:
            raise ValueError("API Key do Trading Economics não configurada")
        
        url = f"{self.base_url}/historical/country/brazil/indicator/{series_code}"
        params = {
            'c': self.api_key,
            'format': 'json',
            'd1': series_config.get('start_date', '2020-01-01'),
            'd2': series_config.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if not data:
                    raise ValueError("Nenhum dado retornado")
                
                # Converter para DataFrame
                df = pd.DataFrame(data)
                
                # Processar dados
                df['date'] = pd.to_datetime(df['DateTime'])
                df['value'] = pd.to_numeric(df['Value'], errors='coerce')
                
                # Adicionar metadados
                df['source'] = self.name
                df['series_name'] = series_name.upper()
                df['series_code'] = series_code
                df['unit'] = self._get_unit(series_name)
                df['frequency'] = self._get_frequency(series_name)
                df['method'] = 'TradingEconomics_API'
                
                # Adicionar consenso de mercado se disponível
                if 'Forecast' in df.columns:
                    df['consensus'] = pd.to_numeric(df['Forecast'], errors='coerce')
                
                # Selecionar colunas relevantes
                result_cols = ['date', 'value', 'source', 'series_name', 'series_code', 'unit', 'frequency', 'method']
                if 'consensus' in df.columns:
                    result_cols.append('consensus')
                
                df_result = df[result_cols].copy()
                df_result = df_result.sort_values('date').reset_index(drop=True)
                
                self.mark_success()
                logger.info(f"✅ [TradingEconomics] Sucesso ao buscar {series_name} ({len(df_result)} registros)")
                return df_result
                
        except Exception as e:
            self.mark_failure(str(e))
            logger.error(f"❌ [TradingEconomics] Erro ao buscar {series_name}: {e}")
            raise
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Valida qualidade dos dados do Trading Economics"""
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
        
        # Verificar se as datas estão em ordem
        if not data['date'].is_monotonic_increasing:
            return False
        
        return True
    
    def _get_unit(self, series_name: str) -> str:
        """Retorna unidade da série"""
        units = {
            'desemprego': '%',
            'ipca': '%',
            'selic': '%',
            'pib': 'USD'
        }
        return units.get(series_name, 'unknown')
    
    def _get_frequency(self, series_name: str) -> str:
        """Retorna frequência da série"""
        if series_name == 'desemprego':
            return 'quarterly'
        elif series_name == 'selic':
            return 'monthly'
        else:
            return 'monthly'
    
    def set_api_key(self, api_key: str):
        """Define a API key do Trading Economics"""
        self.api_key = api_key
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Verifica o status de saúde da fonte Trading Economics"""
        try:
            if not self.api_key:
                return {
                    'status': 'unhealthy',
                    'last_check': datetime.now().isoformat(),
                    'test_records': 0,
                    'error': 'API key não configurada',
                    'method': 'TradingEconomics_API'
                }
            
            # Testar com desemprego (série mais confiável)
            test_config = {'name': 'desemprego', 'start_date': '2024-01-01', 'end_date': '2024-12-31'}
            test_df = await self.fetch_data(test_config)
            
            return {
                'status': 'healthy' if not test_df.empty else 'degraded',
                'last_check': datetime.now().isoformat(),
                'test_records': len(test_df),
                'error': None,
                'method': 'TradingEconomics_API'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'test_records': 0,
                'error': str(e),
                'method': 'TradingEconomics_API'
            }
