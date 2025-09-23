"""
Fonte de dados da OECD - Atualizada para usar API CSV
"""

import httpx
import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from .base_source import DataSource

logger = logging.getLogger(__name__)


class OECDSource(DataSource):
    """Fonte de dados da OECD via API CSV (fonte única e confiável)"""
    
    def __init__(self):
        super().__init__("OECD_CSV", priority=1)
        self.base_url = "https://sdmx.oecd.org/public/rest/data"
        self.timeout = 30
        
        # Países disponíveis para CLI
        self.countries = ['BRA', 'USA', 'CHN', 'OECD', 'EA19', 'DEU', 'GBR']
    
    async def fetch_data(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Busca dados de CLI da OECD via CSV"""
        country = series_config.get('country', 'BRA')
        start_year = series_config.get('start_year', 2020)
        end_year = series_config.get('end_year', 2025)
        
        if country not in self.countries:
            raise ValueError(f"País {country} não suportado")
        
        # URL da API CSV (mais estável que SDMX)
        url = f"{self.base_url}/OECD.SDD.STES,DSD_STES@DF_CLI/.M.LI...AA...H"
        params = {
            'startPeriod': f"{start_year}-01",
            'endPeriod': f"{end_year}-12",
            'dimensionAtObservation': 'AllDimensions',
            'format': 'csvfilewithlabels'
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                # Ler CSV diretamente
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                
                if df.empty:
                    raise ValueError("Nenhum dado retornado")
                
                # Filtrar para o país específico e CLI normalizado
                df_filtered = df[
                    (df['REF_AREA'] == country) & 
                    (df['ADJUSTMENT'] == 'AA')  # Amplitude adjusted
                ].copy()
                
                if df_filtered.empty:
                    raise ValueError(f"Nenhum dado CLI encontrado para {country}")
                
                # Processar dados
                df_result = df_filtered[['TIME_PERIOD', 'OBS_VALUE']].copy()
                df_result = df_result.rename(columns={'TIME_PERIOD': 'date', 'OBS_VALUE': 'value'})
                df_result['date'] = pd.to_datetime(df_result['date'] + '-01')
                df_result['value'] = pd.to_numeric(df_result['value'], errors='coerce')
                
                # Adicionar metadados
                df_result['source'] = self.name
                df_result['series_name'] = f'CLI_{country}'
                df_result['series_code'] = f'CLI_{country}'
                df_result['country'] = country
                df_result['unit'] = 'index'
                df_result['frequency'] = 'monthly'
                df_result['method'] = 'OECD_CSV'
                
                # Ordenar por data
                df_result = df_result.sort_values('date').reset_index(drop=True)
                
                self.mark_success()
                logger.info(f"✅ [OECD CSV] Sucesso ao buscar CLI {country} ({len(df_result)} registros)")
                return df_result
                
        except Exception as e:
            self.mark_failure(str(e))
            logger.error(f"❌ [OECD CSV] Erro ao buscar CLI {country}: {e}")
            raise
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Valida qualidade dos dados CLI"""
        if data.empty:
            return False
        
        # Verificar se tem as colunas necessárias
        required_cols = ['date', 'value', 'source', 'country']
        if not all(col in data.columns for col in required_cols):
            return False
        
        # Verificar se não tem muitos valores nulos
        null_ratio = data['value'].isnull().sum() / len(data)
        if null_ratio > 0.1:  # Mais de 10% de nulos
            return False
        
        # Verificar se as datas estão em ordem
        if not data['date'].is_monotonic_increasing:
            return False
        
        # Verificar se os valores CLI são razoáveis (geralmente entre 80-120)
        if data['value'].min() < 70 or data['value'].max() > 130:
            return False
        
        return True
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Verifica o status de saúde da fonte OECD"""
        try:
            # Testar com Brasil (país mais confiável)
            test_config = {'country': 'BRA', 'start_year': 2024, 'end_year': 2024}
            test_df = await self.fetch_data(test_config)
            
            return {
                'status': 'healthy' if not test_df.empty else 'degraded',
                'last_check': datetime.now().isoformat(),
                'test_records': len(test_df),
                'error': None,
                'method': 'OECD_CSV'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'test_records': 0,
                'error': str(e),
                'method': 'OECD_CSV'
            }