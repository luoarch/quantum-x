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
            'pib': 4380,  # PIB mensal - corrigido para 'pib'
            'pib_mensal': 4380,  # Mantido para compatibilidade
            'desemprego': 24369  # Taxa de desemprego (IBGE via BCB)
        }
    
    async def fetch_data(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Busca dados do BCB usando python-bcb com múltiplas requisições"""
        series_name = series_config['name']
        series_code = self.series_map.get(series_name)
        
        if not series_code:
            raise ValueError(f"Série {series_name} não encontrada no BCB")
        
        try:
            # Executar em thread separada para não bloquear
            loop = asyncio.get_event_loop()
            
            # Coletar dados em chunks de 20 (limite do BCB)
            all_data = []
            limit = series_config.get('limit', 20)
            
            if limit > 20:
                # Fazer múltiplas requisições para obter mais dados
                chunks = (limit + 19) // 20  # Arredondar para cima
                logger.info(f"📊 [BCB] Coletando {chunks} chunks de 20 dados para {series_name}")
                
                for i in range(chunks):
                    try:
                        chunk_data = await loop.run_in_executor(
                            None, 
                            lambda: sgs.get(series_code, last=20)
                        )
                        if not chunk_data.empty:
                            all_data.append(chunk_data)
                            logger.info(f"✅ [BCB] Chunk {i+1}/{chunks} coletado: {len(chunk_data)} dados")
                    except Exception as e:
                        logger.warning(f"⚠️ [BCB] Erro no chunk {i+1}: {e}")
                        break
                
                if all_data:
                    df = pd.concat(all_data, ignore_index=True)
                    logger.info(f"✅ [BCB] Total coletado: {len(df)} dados")
                else:
                    raise ValueError("Nenhum chunk coletado com sucesso")
            else:
                df = await loop.run_in_executor(
                    None, 
                    lambda: sgs.get(series_code, last=limit)
                )
            
            if df.empty:
                raise ValueError("Nenhum dado retornado")
            
            # Processar dados
            df = df.reset_index()
            
            # Verificar se as colunas existem
            if len(df.columns) >= 2:
                df.columns = ['date', 'value']
            else:
                # Se não tiver colunas suficientes, criar estrutura padrão
                df = df.reset_index()
                if 'date' not in df.columns:
                    # Criar datas válidas baseadas no índice
                    df['date'] = pd.date_range(start='2020-01-01', periods=len(df), freq='M')
                if 'value' not in df.columns:
                    df['value'] = df.iloc[:, 0] if len(df.columns) > 0 else 0
            
            # Validar e corrigir datas inválidas
            if 'date' in df.columns:
                # Converter para datetime se necessário
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                # Remover linhas com datas inválidas
                df = df.dropna(subset=['date'])
                # Se ainda houver datas inválidas, criar datas padrão
                if df['date'].isna().any() or (df['date'] == 0).any():
                    logger.warning(f"⚠️ [BCB] Datas inválidas detectadas para {series_name}, criando datas padrão")
                    df['date'] = pd.date_range(start='2020-01-01', periods=len(df), freq='M')
            
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
