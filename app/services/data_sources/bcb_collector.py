"""
Coletor de dados do BCB (Banco Central do Brasil)
Conforme DRS seção 7.1.2
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

class BCBCollector(BaseDataCollector):
    """Coletor de dados do BCB"""
    
    def __init__(self):
        super().__init__()
        self.api_key = settings.BCB_API_KEY
        self.base_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
        self.series_mapping = data_source_config.BCB_SERIES
        
    async def collect(self) -> pd.DataFrame:
        """Coletar dados do BCB"""
        logger.info("Coletando dados do BCB")
        
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
            raise ValueError("Nenhum dado coletado do BCB")
        
        # Combinar todos os dados
        combined_data = pd.concat(all_data, axis=1, sort=True)
        combined_data = combined_data.dropna()
        
        logger.info(f"Coletados {len(combined_data)} observações do BCB")
        return combined_data
    
    async def _fetch_series(
        self, 
        client: httpx.AsyncClient, 
        series_id: int, 
        series_name: str
    ) -> Optional[pd.Series]:
        """Buscar série específica do BCB"""
        
        # Calcular datas (últimos 20 anos)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=20*365)
        
        params = {
            'codigoSerie': series_id,
            'dataInicial': start_date.strftime('%d/%m/%Y'),
            'dataFinal': end_date.strftime('%d/%m/%Y'),
            'formato': 'json'
        }
        
        try:
            response = await client.get(f"{self.base_url}/{series_id}/dados", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                logger.warning(f"Nenhuma observação encontrada para {series_name}")
                return None
            
            # Converter para DataFrame
            df_data = []
            for obs in data:
                if obs['valor'] is not None:
                    df_data.append({
                        'date': pd.to_datetime(obs['data'], format='%d/%m/%Y'),
                        'value': float(obs['valor'])
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
