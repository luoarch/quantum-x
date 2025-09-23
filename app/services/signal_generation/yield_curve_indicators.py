"""
Indicadores de Curva de Juros
Implementa spreads de juros para capturar expectativas de política monetária
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import requests
import json

logger = logging.getLogger(__name__)

class YieldCurveIndicators:
    """
    Indicadores de curva de juros para análise macroeconômica
    """
    
    def __init__(self, 
                 bcb_api_key: Optional[str] = None,
                 cache_duration: int = 3600):  # Cache por 1 hora
        """
        Inicializa os indicadores de curva de juros
        
        Args:
            bcb_api_key: Chave da API do BCB (opcional)
            cache_duration: Duração do cache em segundos
        """
        self.bcb_api_key = bcb_api_key
        self.cache_duration = cache_duration
        self.cache = {}
        
        # Códigos das séries do BCB
        self.series_codes = {
            'selic': 432,           # Taxa SELIC
            'swap_di_1m': 1178,     # Swap DI 1 mês
            'swap_di_3m': 1179,     # Swap DI 3 meses
            'swap_di_6m': 1180,     # Swap DI 6 meses
            'swap_di_12m': 1181,    # Swap DI 12 meses
            'swap_di_24m': 1182,    # Swap DI 24 meses
            'swap_di_36m': 1183,    # Swap DI 36 meses
            'tesouro_2y': 11,       # Tesouro 2 anos
            'tesouro_5y': 12,       # Tesouro 5 anos
            'tesouro_10y': 13,      # Tesouro 10 anos
            'tesouro_30y': 14       # Tesouro 30 anos
        }
    
    def fetch_yield_data(self, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        Busca dados de curva de juros do BCB
        
        Args:
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            
        Returns:
            Dicionário com DataFrames de cada série
        """
        try:
            data = {}
            
            for series_name, code in self.series_codes.items():
                try:
                    # Buscar dados da série
                    df = self._fetch_bcb_series(code, start_date, end_date)
                    if not df.empty:
                        data[series_name] = df
                        logger.info(f"Dados de {series_name} obtidos: {len(df)} pontos")
                    else:
                        logger.warning(f"Nenhum dado obtido para {series_name}")
                        
                except Exception as e:
                    logger.error(f"Erro ao buscar {series_name}: {e}")
                    continue
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados de curva de juros: {e}")
            return {}
    
    def _fetch_bcb_series(self, code: int, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Busca série específica do BCB
        """
        try:
            # URL da API do BCB
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
            
            params = {
                'formato': 'json',
                'dataInicial': start_date,
                'dataFinal': end_date
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return pd.DataFrame()
            
            # Converter para DataFrame
            df = pd.DataFrame(data)
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
            df = df.dropna()
            df = df.set_index('data')
            df = df.rename(columns={'valor': 'value'})
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao buscar série {code}: {e}")
            return pd.DataFrame()
    
    def calculate_spreads(self, yield_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calcula spreads de curva de juros
        """
        try:
            spreads = {}
            
            # Spread 10Y-2Y (indicador de recessão)
            if 'tesouro_10y' in yield_data and 'tesouro_2y' in yield_data:
                tesouro_10y = yield_data['tesouro_10y']['value']
                tesouro_2y = yield_data['tesouro_2y']['value']
                
                # Alinhar datas
                common_dates = tesouro_10y.index.intersection(tesouro_2y.index)
                if len(common_dates) > 0:
                    spread_10y_2y = tesouro_10y.loc[common_dates] - tesouro_2y.loc[common_dates]
                    spreads['spread_10y_2y'] = spread_10y_2y
            
            # Spread 5Y-2Y
            if 'tesouro_5y' in yield_data and 'tesouro_2y' in yield_data:
                tesouro_5y = yield_data['tesouro_5y']['value']
                tesouro_2y = yield_data['tesouro_2y']['value']
                
                common_dates = tesouro_5y.index.intersection(tesouro_2y.index)
                if len(common_dates) > 0:
                    spread_5y_2y = tesouro_5y.loc[common_dates] - tesouro_2y.loc[common_dates]
                    spreads['spread_5y_2y'] = spread_5y_2y
            
            # Spread Swap DI 12M - SELIC
            if 'swap_di_12m' in yield_data and 'selic' in yield_data:
                swap_12m = yield_data['swap_di_12m']['value']
                selic = yield_data['selic']['value']
                
                common_dates = swap_12m.index.intersection(selic.index)
                if len(common_dates) > 0:
                    spread_swap_selic = swap_12m.loc[common_dates] - selic.loc[common_dates]
                    spreads['spread_swap_selic'] = spread_swap_selic
            
            # Spread Swap DI 24M - 12M
            if 'swap_di_24m' in yield_data and 'swap_di_12m' in yield_data:
                swap_24m = yield_data['swap_di_24m']['value']
                swap_12m = yield_data['swap_di_12m']['value']
                
                common_dates = swap_24m.index.intersection(swap_12m.index)
                if len(common_dates) > 0:
                    spread_swap_24m_12m = swap_24m.loc[common_dates] - swap_12m.loc[common_dates]
                    spreads['spread_swap_24m_12m'] = spread_swap_24m_12m
            
            # Criar DataFrame com todos os spreads
            if spreads:
                spreads_df = pd.DataFrame(spreads)
                spreads_df = spreads_df.dropna()
                
                # Adicionar indicadores derivados
                spreads_df = self._calculate_derived_indicators(spreads_df)
                
                return spreads_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Erro ao calcular spreads: {e}")
            return pd.DataFrame()
    
    def _calculate_derived_indicators(self, spreads_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula indicadores derivados dos spreads
        """
        try:
            # Indicador de recessão (spread 10Y-2Y < 0)
            if 'spread_10y_2y' in spreads_df.columns:
                spreads_df['recession_indicator'] = (spreads_df['spread_10y_2y'] < 0).astype(int)
                
                # Força do indicador de recessão
                spreads_df['recession_strength'] = np.abs(spreads_df['spread_10y_2y'])
            
            # Indicador de expectativas de política monetária
            if 'spread_swap_selic' in spreads_df.columns:
                spreads_df['monetary_policy_indicator'] = np.where(
                    spreads_df['spread_swap_selic'] > 0, 1, -1
                )
            
            # Indicador de curva invertida
            if 'spread_10y_2y' in spreads_df.columns:
                spreads_df['curve_inverted'] = (spreads_df['spread_10y_2y'] < -0.5).astype(int)
            
            # Média móvel dos spreads
            for col in spreads_df.columns:
                if col.startswith('spread_'):
                    spreads_df[f'{col}_ma_3m'] = spreads_df[col].rolling(window=3, min_periods=1).mean()
                    spreads_df[f'{col}_ma_6m'] = spreads_df[col].rolling(window=6, min_periods=1).mean()
            
            return spreads_df
            
        except Exception as e:
            logger.error(f"Erro ao calcular indicadores derivados: {e}")
            return spreads_df
    
    def generate_signals(self, spreads_df: pd.DataFrame) -> pd.DataFrame:
        """
        Gera sinais baseados nos spreads de curva de juros
        """
        try:
            signals = spreads_df.copy()
            
            # Sinal de compra baseado em curva normal (spread positivo)
            if 'spread_10y_2y' in signals.columns:
                signals['buy_signal'] = (signals['spread_10y_2y'] > 0.5).astype(int)
                signals['sell_signal'] = (signals['spread_10y_2y'] < -0.5).astype(int)
            
            # Sinal de alerta de recessão
            if 'recession_indicator' in signals.columns:
                signals['recession_alert'] = (signals['recession_indicator'] == 1).astype(int)
            
            # Sinal de política monetária
            if 'monetary_policy_indicator' in signals.columns:
                signals['monetary_signal'] = signals['monetary_policy_indicator']
            
            # Sinal combinado
            signals['combined_signal'] = 0
            if 'buy_signal' in signals.columns and 'sell_signal' in signals.columns:
                signals['combined_signal'] = signals['buy_signal'] - signals['sell_signal']
            
            # Força do sinal
            signals['signal_strength'] = 0
            if 'spread_10y_2y' in signals.columns:
                signals['signal_strength'] = np.abs(signals['spread_10y_2y'])
            
            return signals
            
        except Exception as e:
            logger.error(f"Erro ao gerar sinais: {e}")
            return spreads_df
    
    def get_yield_summary(self, spreads_df: pd.DataFrame) -> Dict:
        """
        Gera resumo dos indicadores de curva de juros
        """
        try:
            if spreads_df.empty:
                return {'error': 'Nenhum dado disponível'}
            
            summary = {
                'total_periods': len(spreads_df),
                'date_range': {
                    'start': spreads_df.index.min().strftime('%Y-%m-%d'),
                    'end': spreads_df.index.max().strftime('%Y-%m-%d')
                },
                'spreads': {}
            }
            
            # Estatísticas dos spreads
            for col in spreads_df.columns:
                if col.startswith('spread_'):
                    summary['spreads'][col] = {
                        'mean': float(spreads_df[col].mean()),
                        'std': float(spreads_df[col].std()),
                        'min': float(spreads_df[col].min()),
                        'max': float(spreads_df[col].max()),
                        'current': float(spreads_df[col].iloc[-1]) if len(spreads_df) > 0 else 0
                    }
            
            # Indicadores de recessão
            if 'recession_indicator' in spreads_df.columns:
                recession_periods = spreads_df['recession_indicator'].sum()
                summary['recession_indicators'] = {
                    'recession_periods': int(recession_periods),
                    'recession_frequency': float(recession_periods / len(spreads_df)),
                    'current_recession': bool(spreads_df['recession_indicator'].iloc[-1]) if len(spreads_df) > 0 else False
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")
            return {'error': str(e)}
