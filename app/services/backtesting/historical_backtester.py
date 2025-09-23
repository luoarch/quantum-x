"""
Backtester Histórico - Implementa backtesting rigoroso com dados históricos reais
Simula trading com ativos reais baseado nos sinais CLI gerados
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass

from app.services.signal_generation import CLICalculator, SignalGenerator, MLOptimizer, PositionSizing
from app.services.robust_data_collector import RobustDataCollector
from app.core.database import get_db
from app.models.time_series import EconomicSeries, TradingSignal

logger = logging.getLogger(__name__)

@dataclass
class BacktestResult:
    """Resultado do backtesting"""
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    avg_trade_return: float
    volatility: float
    calmar_ratio: float
    sortino_ratio: float
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    signals_generated: int
    buy_signals: int
    sell_signals: int
    hold_signals: int

class HistoricalBacktester:
    """
    Backtester histórico para validar estratégia CLI com dados reais
    """
    
    def __init__(self, 
                 initial_capital: float = 100000.0,
                 transaction_cost: float = 0.001,  # 0.1% por transação
                 risk_free_rate: float = 0.05):    # 5% ao ano
        """
        Inicializa o backtester histórico
        
        Args:
            initial_capital: Capital inicial para simulação
            transaction_cost: Custo de transação (0.1% = 0.001)
            risk_free_rate: Taxa livre de risco anual
        """
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.risk_free_rate = risk_free_rate
        
        # Componentes do sistema de sinais
        self.cli_calculator = CLICalculator()
        self.signal_generator = SignalGenerator()
        self.ml_optimizer = MLOptimizer()
        self.position_sizing = PositionSizing()
        
        # Dados históricos
        self.economic_data = {}
        self.cli_data = pd.DataFrame()
        self.signals_data = pd.DataFrame()
        self.positions_data = pd.DataFrame()
        
        # Resultados do backtest
        self.backtest_results = []
        self.portfolio_values = []
        self.trades = []
    
    async def run_historical_backtest(self, 
                                    start_date: str = "2010-01-01",
                                    end_date: str = "2025-09-23",
                                    rebalance_frequency: str = "monthly") -> BacktestResult:
        """
        Executa backtesting histórico completo
        
        Args:
            start_date: Data de início do backtesting
            end_date: Data de fim do backtesting
            rebalance_frequency: Frequência de rebalanceamento (monthly, weekly, daily)
            
        Returns:
            BacktestResult com métricas de performance
        """
        try:
            logger.info(f"🚀 Iniciando backtesting histórico: {start_date} a {end_date}")
            
            # 1. Coletar dados históricos
            logger.info("📊 1. Coletando dados históricos...")
            await self._collect_historical_data(start_date, end_date)
            
            if not self.economic_data:
                raise ValueError("Falha na coleta de dados históricos")
            
            # 2. Calcular CLI histórico
            logger.info("🧮 2. Calculando CLI histórico...")
            self.cli_data = self.cli_calculator.calculate_cli(self.economic_data)
            
            if self.cli_data.empty:
                raise ValueError("Falha no cálculo do CLI histórico")
            
            # 3. Gerar sinais históricos
            logger.info("📈 3. Gerando sinais históricos...")
            self.signals_data = self.signal_generator.generate_signals(
                self.cli_data, self.economic_data
            )
            
            if self.signals_data.empty:
                raise ValueError("Falha na geração de sinais históricos")
            
            # 4. Simular trading
            logger.info("💰 4. Simulando trading...")
            await self._simulate_trading(rebalance_frequency)
            
            # 5. Calcular métricas de performance
            logger.info("📊 5. Calculando métricas de performance...")
            result = self._calculate_performance_metrics(start_date, end_date)
            
            logger.info("✅ Backtesting histórico concluído com sucesso!")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro no backtesting histórico: {e}")
            raise
    
    async def _collect_historical_data(self, start_date: str, end_date: str):
        """Coleta dados históricos do período especificado"""
        try:
            db = next(get_db())
            collector = RobustDataCollector(db)
            
            # Calcular número de meses necessários
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1
            
            # Coletar dados
            collection_result = await collector.collect_all_series(months=months)
            self.economic_data = collection_result.get('economic', {})
            
            logger.info(f"✅ Dados coletados: {len(self.economic_data)} séries")
            for series_name, df in self.economic_data.items():
                logger.info(f"   - {series_name}: {len(df)} pontos")
            
        except Exception as e:
            logger.error(f"Erro na coleta de dados históricos: {e}")
            raise
    
    async def _simulate_trading(self, rebalance_frequency: str):
        """Simula trading baseado nos sinais gerados"""
        try:
            # Preparar dados para simulação
            portfolio_value = self.initial_capital
            cash = self.initial_capital
            position = 0.0  # Posição atual (0 = sem posição, 1 = 100% investido)
            
            # Criar DataFrame de resultados
            results = []
            
            # Filtrar sinais válidos
            valid_signals = self.signals_data[
                self.signals_data['signal_type'].isin(['BUY', 'SELL'])
            ].copy()
            
            if valid_signals.empty:
                logger.warning("Nenhum sinal válido para simulação")
                return
            
            # Simular cada sinal
            for idx, signal_row in valid_signals.iterrows():
                signal_type = signal_row['signal_type']
                signal_strength = signal_row['signal_strength']
                signal_confidence = signal_row['signal_confidence']
                cli_value = signal_row['cli_normalized']
                
                # Calcular tamanho da posição baseado no sinal
                if signal_type == 'BUY':
                    target_position = min(1.0, signal_strength / 5.0)  # Máximo 100%
                elif signal_type == 'SELL':
                    target_position = max(0.0, 1.0 - (signal_strength / 5.0))  # Mínimo 0%
                else:
                    continue
                
                # Calcular mudança de posição
                position_change = target_position - position
                
                if abs(position_change) > 0.01:  # Só trade se mudança > 1%
                    # Calcular custo da transação
                    trade_value = abs(position_change) * portfolio_value
                    transaction_cost = trade_value * self.transaction_cost
                    
                    # Atualizar posição
                    position = target_position
                    cash = cash - (position_change * portfolio_value) - transaction_cost
                    portfolio_value = cash + (position * portfolio_value)
                    
                    # Registrar trade
                    trade = {
                        'date': idx,
                        'signal_type': signal_type,
                        'signal_strength': signal_strength,
                        'signal_confidence': signal_confidence,
                        'cli_value': cli_value,
                        'position_before': position - position_change,
                        'position_after': position,
                        'position_change': position_change,
                        'trade_value': trade_value,
                        'transaction_cost': transaction_cost,
                        'portfolio_value': portfolio_value,
                        'cash': cash
                    }
                    
                    results.append(trade)
                    self.trades.append(trade)
                
                # Registrar valor do portfolio
                self.portfolio_values.append({
                    'date': idx,
                    'portfolio_value': portfolio_value,
                    'cash': cash,
                    'position': position,
                    'cli_value': cli_value
                })
            
            # Criar DataFrame de resultados
            self.backtest_results = pd.DataFrame(results)
            
            logger.info(f"✅ Simulação concluída: {len(self.trades)} trades executados")
            
        except Exception as e:
            logger.error(f"Erro na simulação de trading: {e}")
            raise
    
    def _calculate_performance_metrics(self, start_date: str, end_date: str) -> BacktestResult:
        """Calcula métricas de performance do backtesting"""
        try:
            if not self.portfolio_values:
                raise ValueError("Nenhum dado de portfolio para análise")
            
            # Converter para DataFrame
            portfolio_df = pd.DataFrame(self.portfolio_values)
            portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
            portfolio_df = portfolio_df.set_index('date').sort_index()
            
            # Calcular retornos
            portfolio_df['returns'] = portfolio_df['portfolio_value'].pct_change().fillna(0)
            
            # Métricas básicas
            initial_value = portfolio_df['portfolio_value'].iloc[0]
            final_value = portfolio_df['portfolio_value'].iloc[-1]
            total_return = (final_value - initial_value) / initial_value
            
            # Retorno anualizado
            years = (portfolio_df.index[-1] - portfolio_df.index[0]).days / 365.25
            annualized_return = (1 + total_return) ** (1 / years) - 1
            
            # Volatilidade
            volatility = portfolio_df['returns'].std() * np.sqrt(252)  # Anualizada
            
            # Sharpe Ratio
            excess_return = annualized_return - self.risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0
            
            # Maximum Drawdown
            cumulative = (1 + portfolio_df['returns']).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Calmar Ratio
            calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # Sortino Ratio (usando apenas retornos negativos)
            negative_returns = portfolio_df['returns'][portfolio_df['returns'] < 0]
            downside_volatility = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
            sortino_ratio = excess_return / downside_volatility if downside_volatility > 0 else 0
            
            # Estatísticas de trades
            if self.trades:
                trades_df = pd.DataFrame(self.trades)
                profitable_trades = len(trades_df[trades_df['position_change'] > 0])
                total_trades = len(trades_df)
                win_rate = profitable_trades / total_trades if total_trades > 0 else 0
                avg_trade_return = trades_df['position_change'].mean()
            else:
                profitable_trades = 0
                total_trades = 0
                win_rate = 0
                avg_trade_return = 0
            
            # Estatísticas de sinais
            signals_summary = self.signal_generator.get_signal_summary(self.signals_data)
            
            return BacktestResult(
                total_return=total_return,
                annualized_return=annualized_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                total_trades=total_trades,
                profitable_trades=profitable_trades,
                avg_trade_return=avg_trade_return,
                volatility=volatility,
                calmar_ratio=calmar_ratio,
                sortino_ratio=sortino_ratio,
                start_date=datetime.strptime(start_date, "%Y-%m-%d"),
                end_date=datetime.strptime(end_date, "%Y-%m-%d"),
                initial_capital=initial_value,
                final_capital=final_value,
                signals_generated=signals_summary['total_signals'],
                buy_signals=signals_summary['buy_signals'],
                sell_signals=signals_summary['sell_signals'],
                hold_signals=signals_summary['hold_signals']
            )
            
        except Exception as e:
            logger.error(f"Erro no cálculo de métricas: {e}")
            raise
    
    def get_backtest_summary(self) -> Dict[str, Any]:
        """Retorna resumo do backtesting"""
        try:
            if not self.backtest_results:
                return {'error': 'Nenhum resultado de backtesting disponível'}
            
            # Calcular métricas básicas
            portfolio_df = pd.DataFrame(self.portfolio_values)
            portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
            portfolio_df = portfolio_df.set_index('date').sort_index()
            
            initial_value = portfolio_df['portfolio_value'].iloc[0]
            final_value = portfolio_df['portfolio_value'].iloc[-1]
            total_return = (final_value - initial_value) / initial_value
            
            return {
                'period': f"{portfolio_df.index[0].strftime('%Y-%m-%d')} a {portfolio_df.index[-1].strftime('%Y-%m-%d')}",
                'initial_capital': initial_value,
                'final_capital': final_value,
                'total_return': f"{total_return:.2%}",
                'total_trades': len(self.trades),
                'signals_generated': len(self.signals_data),
                'cli_data_points': len(self.cli_data)
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")
            return {'error': str(e)}
    
    def export_results(self, filename: str = None) -> str:
        """Exporta resultados do backtesting para CSV"""
        try:
            if filename is None:
                filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Combinar dados de portfolio e trades
            portfolio_df = pd.DataFrame(self.portfolio_values)
            trades_df = pd.DataFrame(self.trades)
            
            # Salvar em arquivo
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                portfolio_df.to_excel(writer, sheet_name='Portfolio', index=False)
                trades_df.to_excel(writer, sheet_name='Trades', index=False)
                self.signals_data.to_excel(writer, sheet_name='Signals', index=True)
                self.cli_data.to_excel(writer, sheet_name='CLI', index=True)
            
            logger.info(f"✅ Resultados exportados para: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Erro na exportação: {e}")
            raise
