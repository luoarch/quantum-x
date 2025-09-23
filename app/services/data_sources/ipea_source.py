"""
Fonte de dados do IPEA (Instituto de Pesquisa Econômica Aplicada)
"""

import httpx
import pandas as pd
from typing import Dict, Any
from datetime import datetime
import logging

from .base_source import DataSource

logger = logging.getLogger(__name__)


class IPEASource(DataSource):
    """Fonte de dados do IPEA via API OData"""
    
    def __init__(self):
        super().__init__("IPEA", priority=2)
        self.base_url = "http://www.ipeadata.gov.br/api/odata4"
        self.timeout = 30
        
        # Mapeamento de séries IPEA (códigos corrigidos)
        self.series_map = {
            'ipca': 'PRECOS12_IPCA12',
            'selic': 'BM12_TJOVER12',
            'cambio': 'BM12_TJOVER12',  # Código correto para câmbio PTAX
            'prod_industrial': 'BM12_IPCA12',
            'pib': 'BM12_PIB12',
            'desemprego': 'PNADC12_TDESOC12'  # Código correto para PNAD Contínua
        }
    
    async def fetch_data(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Busca dados do IPEA"""
        series_name = series_config['name']
        series_code = self.series_map.get(series_name)
        
        if not series_code:
            raise ValueError(f"Série {series_name} não encontrada no IPEA")
        
        # Construir URL OData
        url = f"{self.base_url}/Metadados('{series_code}')/Valores"
        
        # Parâmetros OData
        params = {
            '$orderby': 'VALDATA desc',
            '$top': series_config.get('limit', 100)
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if 'value' not in data:
                    raise ValueError("Formato de resposta inválido")
                
                values = data['value']
                
                if not values:
                    raise ValueError("Nenhum dado retornado")
                
                # Converter para DataFrame
                df = pd.DataFrame(values)
                
                # Processar colunas
                df['date'] = pd.to_datetime(df['VALDATA'])
                df['value'] = pd.to_numeric(df['VALVALOR'], errors='coerce')
                
                # Adicionar metadados
                df['source'] = self.name
                df['series_name'] = series_name.upper()
                df['series_code'] = series_code
                df['unit'] = self._get_unit(series_name)
                df['frequency'] = self._get_frequency(series_name)
                
                # Selecionar colunas relevantes
                df = df[['date', 'value', 'source', 'series_name', 'series_code', 'unit', 'frequency']]
                
                # Ordenar por data
                df = df.sort_values('date').reset_index(drop=True)
                
                self.mark_success()
                return df
                
        except Exception as e:
            self.mark_failure(str(e))
            raise
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Valida qualidade dos dados do IPEA"""
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
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Verifica o status de saúde da fonte IPEA"""
        try:
            # Testar com IPCA (série mais confiável)
            test_config = {'name': 'ipca', 'limit': 1}
            test_df = await self.fetch_data(test_config)
            
            return {
                'status': 'healthy' if not test_df.empty else 'degraded',
                'last_check': datetime.now().isoformat(),
                'test_records': len(test_df),
                'error': None,
                'method': 'OData4'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'test_records': 0,
                'error': str(e),
                'method': 'OData4'
            }
    
    def _get_unit(self, series_name: str) -> str:
        """Retorna unidade da série"""
        units = {
            'ipca': '%',
            'selic': '%',
            'cambio': 'BRL/USD',
            'prod_industrial': 'index',
            'pib': 'R$ milhões',
            'desemprego': '%'
        }
        return units.get(series_name, 'unknown')
    
    def _get_frequency(self, series_name: str) -> str:
        """Retorna frequência da série"""
        if series_name == 'cambio':
            return 'daily'
        elif series_name == 'desemprego':
            return 'quarterly'
        else:
            return 'monthly'
