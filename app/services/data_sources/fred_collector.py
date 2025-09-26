"""
Coletor de dados do FRED (Federal Reserve Economic Data)
Conforme DRS seção 7.1.1
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import httpx

from app.core.config import settings, data_source_config
from app.services.data_sources.base_source import BaseDataCollector

logger = logging.getLogger(__name__)

class FREDCollector(BaseDataCollector):
    """Coletor de dados do FRED"""
    
    def __init__(self):
        super().__init__()
        self.api_key = settings.FRED_API_KEY
        self.base_url = "https://api.stlouisfed.org/fred"
        self.series_mapping = data_source_config.FRED_SERIES
        
    async def collect(self) -> pd.DataFrame:
        """Coletar dados do FRED"""
        if not self.api_key:
            raise ValueError("FRED_API_KEY não configurada")
        
        logger.info("Coletando dados do FRED")
        
        all_data = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for series_name, series_id in self.series_mapping.items():
                try:
                    data = await self._fetch_series(client, series_id, series_name)
                    if data is not None:
                        all_data.append(data)
                except Exception as e:
                    logger.error(f"Erro ao coletar série {series_name}: {e}")
                    continue
        
        if not all_data:
            raise ValueError("Nenhum dado coletado do FRED")
        
        # Combinar todos os dados
        combined_data = pd.concat(all_data, axis=1, sort=True)
        combined_data = combined_data.dropna()
        
        logger.info(f"Coletados {len(combined_data)} observações do FRED")
        return combined_data
    
    async def _fetch_series(
        self, 
        client: httpx.AsyncClient, 
        series_id: str, 
        series_name: str
    ) -> Optional[pd.Series]:
        """Buscar série específica do FRED"""
        
        # Calcular datas (últimos 20 anos)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=20*365)
        
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': start_date.strftime('%Y-%m-%d'),
            'observation_end': end_date.strftime('%Y-%m-%d'),
            'frequency': 'm',  # Mensal
            'units': 'lin'     # Nível
        }
        
        try:
            response = await client.get(f"{self.base_url}/series/observations", params=params)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get('observations', [])
            
            if not observations:
                logger.warning(f"Nenhuma observação encontrada para {series_name}")
                return None
            
            # Converter para DataFrame
            df_data = []
            for obs in observations:
                if obs['value'] != '.' and obs['value'] is not None:
                    df_data.append({
                        'date': pd.to_datetime(obs['date']),
                        'value': float(obs['value'])
                    })
            
            if not df_data:
                return None
            
            df = pd.DataFrame(df_data)
            df.set_index('date', inplace=True)
            
            # Renomear coluna para o nome da série
            df.columns = [series_name]
            
            return df[series_name]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao buscar {series_name}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Erro ao processar {series_name}: {e}")
            return None
    
    async def get_series_info(self, series_id: str) -> Dict[str, Any]:
        """Obter informações sobre uma série"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json'
            }
            
            try:
                response = await client.get(f"{self.base_url}/series", params=params)
                response.raise_for_status()
                
                data = response.json()
                series_info = data.get('seriess', [{}])[0]
                
                return {
                    'id': series_info.get('id'),
                    'title': series_info.get('title'),
                    'units': series_info.get('units'),
                    'frequency': series_info.get('frequency'),
                    'seasonal_adjustment': series_info.get('seasonal_adjustment'),
                    'last_updated': series_info.get('last_updated')
                }
                
            except Exception as e:
                logger.error(f"Erro ao obter informações da série {series_id}: {e}")
                return {}
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validar dados coletados"""
        if data.empty:
            return False
        
        # Verificar se há dados suficientes (mínimo 100 observações)
        if len(data) < 100:
            logger.warning(f"Dados insuficientes: {len(data)} observações")
            return False
        
        # Verificar se há muitos dados faltantes
        missing_pct = data.isnull().sum().sum() / (len(data) * len(data.columns))
        if missing_pct > 0.1:  # 10%
            logger.warning(f"Muitos dados faltantes: {missing_pct:.2%}")
            return False
        
        return True
