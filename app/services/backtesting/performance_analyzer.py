"""
Analisador de Performance - Calcula métricas avançadas de performance
Implementa análise de risco, drawdown, e comparação com benchmarks
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Métricas de performance detalhadas"""
    # Retornos
    total_return: float
    annualized_return: float
    monthly_return: float
    daily_return: float
    
    # Risco
    volatility: float
    max_drawdown: float
    max_drawdown_duration: int  # dias
    var_95: float  # Value at Risk 95%
    cvar_95: float  # Conditional Value at Risk 95%
    
    # Ratios de Performance
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float
    
    # Estatísticas de Trades
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float
    
    # Período
    start_date: str
    end_date: str
    trading_days: int

class PerformanceAnalyzer:
    """
    Analisador de performance para estratégias de trading
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        """
        Inicializa o analisador de performance
        
        Args:
            risk_free_rate: Taxa livre de risco anual
        """
        self.risk_free_rate = risk_free_rate
    
    def analyze_performance(self, 
                           portfolio_values: List[Dict],
                           trades: List[Dict],
                           benchmark_data: Optional[pd.DataFrame] = None) -> PerformanceMetrics:
        """
        Analisa performance completa da estratégia
        
        Args:
            portfolio_values: Lista de valores do portfolio ao longo do tempo
            trades: Lista de trades executados
            benchmark_data: Dados do benchmark para comparação
            
        Returns:
            PerformanceMetrics com todas as métricas calculadas
        """
        try:
            # Converter para DataFrame
            portfolio_df = pd.DataFrame(portfolio_values)
            portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
            portfolio_df = portfolio_df.set_index('date').sort_index()
            
            # Calcular retornos
            portfolio_df['returns'] = portfolio_df['portfolio_value'].pct_change().fillna(0)
            
            # Métricas de retorno
            return_metrics = self._calculate_return_metrics(portfolio_df)
            
            # Métricas de risco
            risk_metrics = self._calculate_risk_metrics(portfolio_df)
            
            # Ratios de performance
            performance_ratios = self._calculate_performance_ratios(
                portfolio_df, return_metrics, risk_metrics, benchmark_data
            )
            
            # Estatísticas de trades
            trade_metrics = self._calculate_trade_metrics(trades)
            
            # Combinar todas as métricas
            metrics = PerformanceMetrics(
                # Retornos
                total_return=return_metrics['total_return'],
                annualized_return=return_metrics['annualized_return'],
                monthly_return=return_metrics['monthly_return'],
                daily_return=return_metrics['daily_return'],
                
                # Risco
                volatility=risk_metrics['volatility'],
                max_drawdown=risk_metrics['max_drawdown'],
                max_drawdown_duration=risk_metrics['max_drawdown_duration'],
                var_95=risk_metrics['var_95'],
                cvar_95=risk_metrics['cvar_95'],
                
                # Ratios
                sharpe_ratio=performance_ratios['sharpe_ratio'],
                sortino_ratio=performance_ratios['sortino_ratio'],
                calmar_ratio=performance_ratios['calmar_ratio'],
                information_ratio=performance_ratios['information_ratio'],
                
                # Trades
                total_trades=trade_metrics['total_trades'],
                winning_trades=trade_metrics['winning_trades'],
                losing_trades=trade_metrics['losing_trades'],
                win_rate=trade_metrics['win_rate'],
                avg_win=trade_metrics['avg_win'],
                avg_loss=trade_metrics['avg_loss'],
                profit_factor=trade_metrics['profit_factor'],
                expectancy=trade_metrics['expectancy'],
                
                # Período
                start_date=portfolio_df.index[0].strftime('%Y-%m-%d'),
                end_date=portfolio_df.index[-1].strftime('%Y-%m-%d'),
                trading_days=len(portfolio_df)
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erro na análise de performance: {e}")
            raise
    
    def _calculate_return_metrics(self, portfolio_df: pd.DataFrame) -> Dict[str, float]:
        """Calcula métricas de retorno"""
        try:
            initial_value = portfolio_df['portfolio_value'].iloc[0]
            final_value = portfolio_df['portfolio_value'].iloc[-1]
            
            # Retorno total
            total_return = (final_value - initial_value) / initial_value
            
            # Retorno anualizado
            years = (portfolio_df.index[-1] - portfolio_df.index[0]).days / 365.25
            annualized_return = (1 + total_return) ** (1 / years) - 1
            
            # Retorno mensal médio
            monthly_returns = portfolio_df['returns'].resample('M').apply(lambda x: (1 + x).prod() - 1)
            monthly_return = monthly_returns.mean()
            
            # Retorno diário médio
            daily_return = portfolio_df['returns'].mean()
            
            return {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'monthly_return': monthly_return,
                'daily_return': daily_return
            }
            
        except Exception as e:
            logger.error(f"Erro no cálculo de retornos: {e}")
            return {
                'total_return': 0.0,
                'annualized_return': 0.0,
                'monthly_return': 0.0,
                'daily_return': 0.0
            }
    
    def _calculate_risk_metrics(self, portfolio_df: pd.DataFrame) -> Dict[str, float]:
        """Calcula métricas de risco"""
        try:
            returns = portfolio_df['returns']
            
            # Volatilidade anualizada
            volatility = returns.std() * np.sqrt(252)
            
            # Maximum Drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Duração máxima do drawdown
            max_drawdown_duration = self._calculate_max_drawdown_duration(drawdown)
            
            # Value at Risk (VaR) 95%
            var_95 = np.percentile(returns, 5)
            
            # Conditional Value at Risk (CVaR) 95%
            cvar_95 = returns[returns <= var_95].mean()
            
            return {
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'max_drawdown_duration': max_drawdown_duration,
                'var_95': var_95,
                'cvar_95': cvar_95
            }
            
        except Exception as e:
            logger.error(f"Erro no cálculo de risco: {e}")
            return {
                'volatility': 0.0,
                'max_drawdown': 0.0,
                'max_drawdown_duration': 0,
                'var_95': 0.0,
                'cvar_95': 0.0
            }
    
    def _calculate_max_drawdown_duration(self, drawdown: pd.Series) -> int:
        """Calcula duração máxima do drawdown em dias"""
        try:
            # Encontrar períodos de drawdown
            in_drawdown = drawdown < 0
            drawdown_periods = []
            current_period = 0
            
            for is_dd in in_drawdown:
                if is_dd:
                    current_period += 1
                else:
                    if current_period > 0:
                        drawdown_periods.append(current_period)
                        current_period = 0
            
            # Adicionar último período se terminar em drawdown
            if current_period > 0:
                drawdown_periods.append(current_period)
            
            return max(drawdown_periods) if drawdown_periods else 0
            
        except Exception as e:
            logger.error(f"Erro no cálculo da duração do drawdown: {e}")
            return 0
    
    def _calculate_performance_ratios(self, 
                                    portfolio_df: pd.DataFrame,
                                    return_metrics: Dict[str, float],
                                    risk_metrics: Dict[str, float],
                                    benchmark_data: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        """Calcula ratios de performance"""
        try:
            returns = portfolio_df['returns']
            annualized_return = return_metrics['annualized_return']
            volatility = risk_metrics['volatility']
            max_drawdown = risk_metrics['max_drawdown']
            
            # Sharpe Ratio
            excess_return = annualized_return - self.risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0
            
            # Sortino Ratio (usando apenas retornos negativos)
            negative_returns = returns[returns < 0]
            downside_volatility = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
            sortino_ratio = excess_return / downside_volatility if downside_volatility > 0 else 0
            
            # Calmar Ratio
            calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # Information Ratio (vs benchmark)
            information_ratio = 0.0
            if benchmark_data is not None:
                # Alinhar dados do benchmark
                benchmark_returns = benchmark_data['returns'].reindex(portfolio_df.index).fillna(0)
                excess_returns = returns - benchmark_returns
                tracking_error = excess_returns.std() * np.sqrt(252)
                information_ratio = excess_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0
            
            return {
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'calmar_ratio': calmar_ratio,
                'information_ratio': information_ratio
            }
            
        except Exception as e:
            logger.error(f"Erro no cálculo de ratios: {e}")
            return {
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'calmar_ratio': 0.0,
                'information_ratio': 0.0
            }
    
    def _calculate_trade_metrics(self, trades: List[Dict]) -> Dict[str, float]:
        """Calcula métricas de trades"""
        try:
            if not trades:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'profit_factor': 0.0,
                    'expectancy': 0.0
                }
            
            trades_df = pd.DataFrame(trades)
            
            # Separar trades vencedores e perdedores
            winning_trades = trades_df[trades_df['position_change'] > 0]
            losing_trades = trades_df[trades_df['position_change'] < 0]
            
            total_trades = len(trades_df)
            winning_count = len(winning_trades)
            losing_count = len(losing_trades)
            
            # Taxa de vitória
            win_rate = winning_count / total_trades if total_trades > 0 else 0
            
            # Ganho médio
            avg_win = winning_trades['position_change'].mean() if len(winning_trades) > 0 else 0
            
            # Perda média
            avg_loss = abs(losing_trades['position_change'].mean()) if len(losing_trades) > 0 else 0
            
            # Profit Factor
            total_wins = winning_trades['position_change'].sum() if len(winning_trades) > 0 else 0
            total_losses = abs(losing_trades['position_change'].sum()) if len(losing_trades) > 0 else 0
            profit_factor = total_wins / total_losses if total_losses > 0 else 0
            
            # Expectativa
            expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_count,
                'losing_trades': losing_count,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'expectancy': expectancy
            }
            
        except Exception as e:
            logger.error(f"Erro no cálculo de métricas de trades: {e}")
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'expectancy': 0.0
            }
    
    def generate_performance_report(self, metrics: PerformanceMetrics) -> str:
        """Gera relatório de performance em texto"""
        try:
            report = f"""
# RELATÓRIO DE PERFORMANCE - ESTRATÉGIA CLI

## Período de Análise
- Início: {metrics.start_date}
- Fim: {metrics.end_date}
- Dias de Trading: {metrics.trading_days}

## Retornos
- Retorno Total: {metrics.total_return:.2%}
- Retorno Anualizado: {metrics.annualized_return:.2%}
- Retorno Mensal Médio: {metrics.monthly_return:.2%}
- Retorno Diário Médio: {metrics.daily_return:.2%}

## Risco
- Volatilidade Anual: {metrics.volatility:.2%}
- Maximum Drawdown: {metrics.max_drawdown:.2%}
- Duração Máxima do Drawdown: {metrics.max_drawdown_duration} dias
- VaR 95%: {metrics.var_95:.2%}
- CVaR 95%: {metrics.cvar_95:.2%}

## Ratios de Performance
- Sharpe Ratio: {metrics.sharpe_ratio:.2f}
- Sortino Ratio: {metrics.sortino_ratio:.2f}
- Calmar Ratio: {metrics.calmar_ratio:.2f}
- Information Ratio: {metrics.information_ratio:.2f}

## Estatísticas de Trades
- Total de Trades: {metrics.total_trades}
- Trades Vencedores: {metrics.winning_trades}
- Trades Perdedores: {metrics.losing_trades}
- Taxa de Vitória: {metrics.win_rate:.2%}
- Ganho Médio: {metrics.avg_win:.2%}
- Perda Média: {metrics.avg_loss:.2%}
- Profit Factor: {metrics.profit_factor:.2f}
- Expectativa: {metrics.expectancy:.2%}

## Avaliação da Estratégia
"""
            
            # Avaliação qualitativa
            if metrics.sharpe_ratio > 1.0:
                report += "✅ Sharpe Ratio excelente (>1.0)\n"
            elif metrics.sharpe_ratio > 0.5:
                report += "⚠️ Sharpe Ratio bom (0.5-1.0)\n"
            else:
                report += "❌ Sharpe Ratio baixo (<0.5)\n"
            
            if metrics.max_drawdown > -0.20:
                report += "✅ Drawdown controlado (<20%)\n"
            elif metrics.max_drawdown > -0.30:
                report += "⚠️ Drawdown moderado (20-30%)\n"
            else:
                report += "❌ Drawdown alto (>30%)\n"
            
            if metrics.win_rate > 0.60:
                report += "✅ Taxa de vitória alta (>60%)\n"
            elif metrics.win_rate > 0.50:
                report += "⚠️ Taxa de vitória moderada (50-60%)\n"
            else:
                report += "❌ Taxa de vitória baixa (<50%)\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Erro na geração do relatório: {e}")
            return f"Erro na geração do relatório: {e}"
