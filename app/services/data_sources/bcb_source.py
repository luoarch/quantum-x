"""
Fonte de dados do Banco Central do Brasil - Atualizada com python-bcb
"""

import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta
import logging
import asyncio

from .base_source import DataSource

logger = logging.getLogger(__name__)

try:
    from bcb import sgs
    BCB_AVAILABLE = True
except ImportError:
    BCB_AVAILABLE = False
    logger.warning("Biblioteca python-bcb não disponível. Instale com: pip install python-bcb")


class BCBSource(DataSource):
    """Fonte de dados do BCB via python-bcb (fonte primária)"""
    
    def __init__(self):
        super().__init__("BCB_python-bcb", priority=1)
        self.timeout = 30
        
        if not BCB_AVAILABLE:
            raise ImportError("Biblioteca python-bcb é obrigatória para BCBSource")
        
        # Mapeamento de séries (códigos validados)
        self.series_map = {
            'ipca': 433,
            'selic': 432,
            'cambio': 1,  # Câmbio comercial - compra
            'prod_industrial': 21859,
            'pib_mensal': 4380,
            'desemprego': 24369  # Taxa de desemprego (IBGE via BCB)
        }
    
    async def fetch_data(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Busca dados do BCB usando python-bcb"""
        series_name = series_config['name']
        series_code = self.series_map.get(series_name)
        
        if not series_code:
            raise ValueError(f"Série {series_name} não encontrada no BCB")
        
        try:
            # Executar em thread separada para não bloquear
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: sgs.get(series_code, last=min(series_config.get('limit', 20), 20))
            )
            
            if df.empty:
                raise ValueError("Nenhum dado retornado")
            
            # Processar dados
            df = df.reset_index()
            df.columns = ['date', 'value']
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            # Adicionar metadados
            df['source'] = self.name
            df['series_name'] = series_name.upper()
            df['series_code'] = str(series_code)
            df['unit'] = self._get_unit(series_name)
            df['frequency'] = self._get_frequency(series_name)
            df['method'] = 'python-bcb'
            
            # Ordenar por data
            df = df.sort_values('date').reset_index(drop=True)
            
            self.mark_success()
            logger.info(f"✅ [BCB python-bcb] Sucesso ao buscar {series_name} ({len(df)} registros)")
            return df
                
        except Exception as e:
            self.mark_failure(str(e))
            logger.error(f"❌ [BCB python-bcb] Erro ao buscar {series_name}: {e}")
            raise
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Valida qualidade dos dados do BCB"""
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
        
        # Verificar se os valores são razoáveis
        if data['value'].min() < -100 or data['value'].max() > 10000:
            return False
        
        return True
    
    def _get_unit(self, series_name: str) -> str:
        """Retorna unidade da série"""
        units = {
            'ipca': '%',
            'selic': '%',
            'cambio': 'BRL/USD',
            'prod_industrial': 'index',
            'pib_mensal': 'R$ milhões',
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
