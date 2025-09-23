"""
Simulador de Ativos - Simula trading com ativos reais
Implementa simulação de Tesouro IPCA+ 2045, BOVA11, e outros ativos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import requests

logger = logging.getLogger(__name__)

class AssetSimulator:
    """
    Simulador de ativos para backtesting
    """
    
    def __init__(self):
        """Inicializa o simulador de ativos"""
        self.asset_data = {}
        self.benchmark_data = {}
    
    async def load_asset_data(self, 
                             asset_symbols: List[str],
                             start_date: str,
                             end_date: str) -> Dict[str, pd.DataFrame]:
        """
        Carrega dados históricos de ativos
        
        Args:
            asset_symbols: Lista de símbolos dos ativos (ex: ['BOVA11', 'TESOURO_IPCA_2045'])
            start_date: Data de início
            end_date: Data de fim
            
        Returns:
            Dicionário com dados históricos dos ativos
        """
        try:
            logger.info(f"📊 Carregando dados de ativos: {asset_symbols}")
            
            for symbol in asset_symbols:
                if symbol == 'BOVA11':
                    data = await self._load_bova11_data(start_date, end_date)
                elif symbol == 'TESOURO_IPCA_2045':
                    data = await self._load_tesouro_ipca_data(start_date, end_date)
                elif symbol == 'IBOVESPA':
                    data = await self._load_ibovespa_data(start_date, end_date)
                else:
                    logger.warning(f"Ativo {symbol} não suportado, usando dados simulados")
                    data = self._generate_simulated_asset_data(symbol, start_date, end_date)
                
                if not data.empty:
                    self.asset_data[symbol] = data
                    logger.info(f"✅ {symbol}: {len(data)} pontos carregados")
                else:
                    logger.warning(f"❌ Falha ao carregar {symbol}")
            
            return self.asset_data
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados de ativos: {e}")
            return {}
    
    async def _load_bova11_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Carrega dados históricos do BOVA11 (ETF do Ibovespa)"""
        try:
            # Simular dados do BOVA11 baseado no Ibovespa
            # Em produção, usar API real (Alpha Vantage, Yahoo Finance, etc.)
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Simular preços baseados em tendência e volatilidade realista
            np.random.seed(42)  # Para reprodutibilidade
            
            # Preço inicial
            initial_price = 100.0
            
            # Retornos diários simulados (baseados em dados históricos do BOVA11)
            daily_returns = np.random.normal(0.0008, 0.015, len(dates))  # 0.08% médio, 1.5% vol
            
            # Aplicar tendência de longo prazo
            trend = np.linspace(0, 0.3, len(dates))  # 30% de crescimento no período
            
            # Calcular preços
            prices = initial_price * np.exp(np.cumsum(daily_returns + trend / len(dates)))
            
            # Criar DataFrame
            df = pd.DataFrame({
                'date': dates,
                'open': prices,
                'high': prices * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
                'low': prices * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
                'close': prices,
                'volume': np.random.randint(1000000, 5000000, len(dates))
            })
            
            # Ajustar high/low para serem consistentes
            df['high'] = np.maximum(df['high'], df['close'])
            df['low'] = np.minimum(df['low'], df['close'])
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados do BOVA11: {e}")
            return pd.DataFrame()
    
    async def _load_tesouro_ipca_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Carrega dados históricos do Tesouro IPCA+ 2045"""
        try:
            # Simular dados do Tesouro IPCA+ 2045
            # Em produção, usar API do Tesouro Direto
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Preço inicial (valor típico do Tesouro IPCA+ 2045)
            initial_price = 1000.0
            
            # Simular retornos baseados em:
            # 1. Taxa Selic (componente fixo)
            # 2. IPCA (inflação)
            # 3. Prêmio de risco
            
            # Componente Selic (simulado)
            selic_component = np.random.normal(0.0002, 0.0005, len(dates))  # 0.02% médio
            
            # Componente IPCA (simulado)
            ipca_component = np.random.normal(0.0003, 0.0008, len(dates))  # 0.03% médio
            
            # Prêmio de risco (volatilidade baixa para tesouro)
            risk_premium = np.random.normal(0.0001, 0.0002, len(dates))  # 0.01% médio
            
            # Retorno total
            daily_returns = selic_component + ipca_component + risk_premium
            
            # Calcular preços
            prices = initial_price * np.exp(np.cumsum(daily_returns))
            
            # Criar DataFrame
            df = pd.DataFrame({
                'date': dates,
                'price': prices,
                'yield': daily_returns * 252,  # Yield anualizado
                'duration': 20.0,  # Duração aproximada
                'maturity': '2045-05-15'  # Vencimento
            })
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados do Tesouro IPCA+: {e}")
            return pd.DataFrame()
    
    async def _load_ibovespa_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Carrega dados históricos do Ibovespa"""
        try:
            # Simular dados do Ibovespa
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Índice inicial
            initial_index = 100000.0
            
            # Retornos diários simulados
            daily_returns = np.random.normal(0.0005, 0.018, len(dates))  # 0.05% médio, 1.8% vol
            
            # Calcular índice
            index_values = initial_index * np.exp(np.cumsum(daily_returns))
            
            # Criar DataFrame
            df = pd.DataFrame({
                'date': dates,
                'index': index_values,
                'returns': daily_returns
            })
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados do Ibovespa: {e}")
            return pd.DataFrame()
    
    def _generate_simulated_asset_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Gera dados simulados para ativos não suportados"""
        try:
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Parâmetros baseados no tipo de ativo
            if 'STOCK' in symbol.upper():
                initial_price = 50.0
                daily_return = 0.0008
                volatility = 0.02
            elif 'BOND' in symbol.upper():
                initial_price = 100.0
                daily_return = 0.0003
                volatility = 0.005
            else:
                initial_price = 100.0
                daily_return = 0.0005
                volatility = 0.01
            
            # Gerar preços
            returns = np.random.normal(daily_return, volatility, len(dates))
            prices = initial_price * np.exp(np.cumsum(returns))
            
            df = pd.DataFrame({
                'date': dates,
                'price': prices,
                'returns': returns
            })
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao gerar dados simulados para {symbol}: {e}")
            return pd.DataFrame()
    
    def simulate_trading_with_assets(self, 
                                   signals_data: pd.DataFrame,
                                   asset_symbol: str,
                                   initial_capital: float = 100000.0) -> Dict[str, Any]:
        """
        Simula trading com ativo específico baseado nos sinais
        
        Args:
            signals_data: DataFrame com sinais de trading
            asset_symbol: Símbolo do ativo para trading
            initial_capital: Capital inicial
            
        Returns:
            Dicionário com resultados da simulação
        """
        try:
            if asset_symbol not in self.asset_data:
                raise ValueError(f"Dados do ativo {asset_symbol} não disponíveis")
            
            asset_df = self.asset_data[asset_symbol]
            
            # Alinhar sinais com dados do ativo
            aligned_signals = signals_data.copy()
            aligned_signals['date'] = pd.to_datetime(aligned_signals.index)
            
            # Merge com dados do ativo
            if 'price' in asset_df.columns:
                price_col = 'price'
            elif 'close' in asset_df.columns:
                price_col = 'close'
            elif 'index' in asset_df.columns:
                price_col = 'index'
            else:
                raise ValueError(f"Coluna de preço não encontrada para {asset_symbol}")
            
            # Fazer merge por data
            merged_data = pd.merge(
                aligned_signals,
                asset_df[['date', price_col]].rename(columns={price_col: 'asset_price'}),
                on='date',
                how='left'
            )
            
            # Preencher valores faltantes
            merged_data['asset_price'] = merged_data['asset_price'].fillna(method='ffill')
            
            # Simular trading
            portfolio_value = initial_capital
            cash = initial_capital
            shares = 0.0
            trades = []
            
            for idx, row in merged_data.iterrows():
                if pd.isna(row['asset_price']):
                    continue
                
                signal_type = row['signal_type']
                asset_price = row['asset_price']
                
                if signal_type == 'BUY' and cash > 0:
                    # Comprar ativo
                    shares_to_buy = cash / asset_price
                    shares += shares_to_buy
                    cash = 0
                    
                    trades.append({
                        'date': row['date'],
                        'action': 'BUY',
                        'price': asset_price,
                        'shares': shares_to_buy,
                        'value': shares_to_buy * asset_price,
                        'portfolio_value': shares * asset_price
                    })
                
                elif signal_type == 'SELL' and shares > 0:
                    # Vender ativo
                    cash = shares * asset_price
                    shares = 0
                    
                    trades.append({
                        'date': row['date'],
                        'action': 'SELL',
                        'price': asset_price,
                        'shares': shares,
                        'value': cash,
                        'portfolio_value': cash
                    })
                
                # Atualizar valor do portfolio
                portfolio_value = cash + (shares * asset_price)
            
            # Calcular métricas
            final_value = portfolio_value
            total_return = (final_value - initial_capital) / initial_capital
            
            # Calcular retornos diários
            if trades:
                trades_df = pd.DataFrame(trades)
                trades_df['date'] = pd.to_datetime(trades_df['date'])
                trades_df = trades_df.set_index('date').sort_index()
                
                # Calcular retornos
                trades_df['returns'] = trades_df['portfolio_value'].pct_change().fillna(0)
                volatility = trades_df['returns'].std() * np.sqrt(252)
            else:
                volatility = 0.0
            
            return {
                'asset_symbol': asset_symbol,
                'initial_capital': initial_capital,
                'final_value': final_value,
                'total_return': total_return,
                'volatility': volatility,
                'total_trades': len(trades),
                'trades': trades,
                'final_shares': shares,
                'final_cash': cash
            }
            
        except Exception as e:
            logger.error(f"Erro na simulação de trading: {e}")
            return {}
    
    def get_asset_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos ativos carregados"""
        try:
            summary = {}
            
            for symbol, data in self.asset_data.items():
                if data.empty:
                    continue
                
                # Calcular métricas básicas
                if 'price' in data.columns:
                    price_col = 'price'
                elif 'close' in data.columns:
                    price_col = 'close'
                elif 'index' in data.columns:
                    price_col = 'index'
                else:
                    continue
                
                initial_price = data[price_col].iloc[0]
                final_price = data[price_col].iloc[-1]
                total_return = (final_price - initial_price) / initial_price
                
                # Calcular volatilidade
                if 'returns' in data.columns:
                    volatility = data['returns'].std() * np.sqrt(252)
                else:
                    returns = data[price_col].pct_change().fillna(0)
                    volatility = returns.std() * np.sqrt(252)
                
                summary[symbol] = {
                    'data_points': len(data),
                    'start_date': data['date'].iloc[0].strftime('%Y-%m-%d'),
                    'end_date': data['date'].iloc[-1].strftime('%Y-%m-%d'),
                    'initial_price': initial_price,
                    'final_price': final_price,
                    'total_return': total_return,
                    'volatility': volatility
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro no resumo de ativos: {e}")
            return {}
