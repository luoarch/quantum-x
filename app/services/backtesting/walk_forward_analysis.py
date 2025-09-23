"""
Walk-Forward Analysis para backtesting científico
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class BacktestResult:
    """Resultado de um período de backtest"""
    start_date: datetime
    end_date: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    signals: List[Dict[str, Any]]
    returns: pd.Series


class WalkForwardAnalysis:
    """Análise Walk-Forward para backtesting científico"""
    
    def __init__(
        self,
        train_period_years: int = 5,
        test_period_months: int = 12,
        min_trades: int = 10
    ):
        self.train_period_years = train_period_years
        self.test_period_months = test_period_months
        self.min_trades = min_trades
        self.results: List[BacktestResult] = []
    
    def run_analysis(
        self,
        data: pd.DataFrame,
        signal_generator,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Executa análise walk-forward
        
        Args:
            data: DataFrame com dados históricos
            signal_generator: Função que gera sinais
            start_date: Data de início (opcional)
            end_date: Data de fim (opcional)
        """
        logger.info("🚀 Iniciando Walk-Forward Analysis")
        
        # Definir período de análise
        if start_date is None:
            start_date = data['date'].min()
        if end_date is None:
            end_date = data['date'].max()
        
        # Filtrar dados
        analysis_data = data[
            (data['date'] >= start_date) & 
            (data['date'] <= end_date)
        ].copy()
        
        if analysis_data.empty:
            raise ValueError("Nenhum dado disponível para análise")
        
        # Calcular datas de janela
        windows = self._calculate_windows(analysis_data)
        
        logger.info(f"📊 Analisando {len(windows)} janelas de teste")
        
        # Executar análise para cada janela
        for i, (train_start, train_end, test_start, test_end) in enumerate(windows):
            logger.info(f"🔄 Janela {i+1}/{len(windows)}: {test_start.date()} - {test_end.date()}")
            
            try:
                result = self._run_window_analysis(
                    analysis_data,
                    signal_generator,
                    train_start, train_end,
                    test_start, test_end
                )
                
                if result.total_trades >= self.min_trades:
                    self.results.append(result)
                    logger.info(f"✅ Janela {i+1}: {result.total_trades} trades, WR={result.win_rate:.1%}")
                else:
                    logger.warning(f"⚠️ Janela {i+1}: Apenas {result.total_trades} trades (mínimo: {self.min_trades})")
                    
            except Exception as e:
                logger.error(f"❌ Erro na janela {i+1}: {str(e)}")
                continue
        
        # Calcular métricas consolidadas
        consolidated_metrics = self._calculate_consolidated_metrics()
        
        logger.info(f"✅ Walk-Forward concluído: {len(self.results)} janelas válidas")
        
        return {
            "total_windows": len(windows),
            "valid_windows": len(self.results),
            "consolidated_metrics": consolidated_metrics,
            "window_results": [self._result_to_dict(r) for r in self.results]
        }
    
    def _calculate_windows(self, data: pd.DataFrame) -> List[Tuple[datetime, datetime, datetime, datetime]]:
        """Calcula janelas de treino e teste"""
        windows = []
        
        current_date = data['date'].min()
        end_date = data['date'].max()
        
        while current_date < end_date:
            # Período de treino
            train_start = current_date
            train_end = current_date + timedelta(days=365 * self.train_period_years)
            
            # Período de teste
            test_start = train_end
            test_end = test_start + timedelta(days=30 * self.test_period_months)
            
            # Verificar se há dados suficientes
            train_data = data[
                (data['date'] >= train_start) & 
                (data['date'] <= train_end)
            ]
            test_data = data[
                (data['date'] >= test_start) & 
                (data['date'] <= test_end)
            ]
            
            if len(train_data) > 0 and len(test_data) > 0:
                windows.append((train_start, train_end, test_start, test_end))
            
            # Avançar para próxima janela (sobreposição de 50%)
            current_date = test_start + timedelta(days=15 * self.test_period_months)
            
            # Parar se não há mais dados
            if test_end > end_date:
                break
        
        return windows
    
    def _run_window_analysis(
        self,
        data: pd.DataFrame,
        signal_generator,
        train_start: datetime,
        train_end: datetime,
        test_start: datetime,
        test_end: datetime
    ) -> BacktestResult:
        """Executa análise para uma janela específica"""
        
        # Dados de treino
        train_data = data[
            (data['date'] >= train_start) & 
            (data['date'] <= train_end)
        ].copy()
        
        # Dados de teste
        test_data = data[
            (data['date'] >= test_start) & 
            (data['date'] <= test_end)
        ].copy()
        
        if train_data.empty or test_data.empty:
            raise ValueError("Dados insuficientes para janela")
        
        # Treinar modelo (se necessário)
        if hasattr(signal_generator, 'fit'):
            signal_generator.fit(train_data)
        
        # Gerar sinais para período de teste
        signals = []
        returns = []
        
        for _, row in test_data.iterrows():
            try:
                signal = signal_generator.generate_signal(row)
                signals.append({
                    'date': row['date'],
                    'signal': signal,
                    'price': row.get('value', 0),
                    'features': row.to_dict()
                })
                
                # Calcular retorno (simplificado)
                if len(returns) > 0:
                    ret = (row.get('value', 0) - test_data.iloc[len(returns)-1].get('value', 0)) / test_data.iloc[len(returns)-1].get('value', 0)
                    returns.append(ret)
                else:
                    returns.append(0.0)
                    
            except Exception as e:
                logger.warning(f"Erro ao gerar sinal: {e}")
                continue
        
        if not signals:
            raise ValueError("Nenhum sinal gerado")
        
        # Calcular métricas
        returns_series = pd.Series(returns, index=test_data['date'][:len(returns)])
        
        # Contar trades
        signal_changes = []
        for i in range(1, len(signals)):
            if signals[i]['signal'] != signals[i-1]['signal']:
                signal_changes.append(signals[i])
        
        total_trades = len(signal_changes)
        winning_trades = sum(1 for trade in signal_changes if self._is_winning_trade(trade, signals))
        losing_trades = total_trades - winning_trades
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_return = returns_series.sum()
        sharpe_ratio = self._calculate_sharpe_ratio(returns_series)
        max_drawdown = self._calculate_max_drawdown(returns_series)
        profit_factor = self._calculate_profit_factor(returns_series)
        
        return BacktestResult(
            start_date=test_start,
            end_date=test_end,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            profit_factor=profit_factor,
            signals=signals,
            returns=returns_series
        )
    
    def _is_winning_trade(self, trade: Dict, all_signals: List[Dict]) -> bool:
        """Determina se um trade foi lucrativo"""
        # Implementação simplificada - pode ser refinada
        return trade.get('signal') == SignalType.BUY.value
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calcula Sharpe Ratio"""
        if returns.std() == 0:
            return 0.0
        return returns.mean() / returns.std() * np.sqrt(252)  # Anualizado
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calcula Maximum Drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return abs(drawdown.min())
    
    def _calculate_profit_factor(self, returns: pd.Series) -> float:
        """Calcula Profit Factor"""
        positive_returns = returns[returns > 0].sum()
        negative_returns = abs(returns[returns < 0].sum())
        
        if negative_returns == 0:
            return float('inf') if positive_returns > 0 else 0.0
        
        return positive_returns / negative_returns
    
    def _calculate_consolidated_metrics(self) -> Dict[str, Any]:
        """Calcula métricas consolidadas de todas as janelas"""
        if not self.results:
            return {}
        
        # Métricas médias
        avg_win_rate = np.mean([r.win_rate for r in self.results])
        avg_sharpe = np.mean([r.sharpe_ratio for r in self.results])
        avg_drawdown = np.mean([r.max_drawdown for r in self.results])
        avg_profit_factor = np.mean([r.profit_factor for r in self.results])
        
        # Métricas de consistência
        win_rate_std = np.std([r.win_rate for r in self.results])
        sharpe_std = np.std([r.sharpe_ratio for r in self.results])
        
        # Contagem de janelas que passaram nos critérios
        robust_windows = sum(1 for r in self.results if self._is_robust_window(r))
        
        return {
            "avg_win_rate": avg_win_rate,
            "avg_sharpe_ratio": avg_sharpe,
            "avg_max_drawdown": avg_drawdown,
            "avg_profit_factor": avg_profit_factor,
            "win_rate_std": win_rate_std,
            "sharpe_std": sharpe_std,
            "robust_windows": robust_windows,
            "total_windows": len(self.results),
            "consistency_score": robust_windows / len(self.results) if self.results else 0
        }
    
    def _is_robust_window(self, result: BacktestResult) -> bool:
        """Verifica se uma janela atende aos critérios de robustez"""
        return (
            result.sharpe_ratio > 1.0 and
            result.max_drawdown < 0.20 and
            result.profit_factor > 1.5 and
            result.win_rate > 0.55 and
            result.total_trades > 100
        )
    
    def _result_to_dict(self, result: BacktestResult) -> Dict[str, Any]:
        """Converte resultado para dicionário"""
        return {
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat(),
            "total_trades": result.total_trades,
            "winning_trades": result.winning_trades,
            "losing_trades": result.losing_trades,
            "win_rate": result.win_rate,
            "total_return": result.total_return,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": result.max_drawdown,
            "profit_factor": result.profit_factor,
            "is_robust": self._is_robust_window(result)
        }
