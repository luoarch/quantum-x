"""
Sistema de Dimensionamento de Posições usando Kelly Criterion
Implementa cálculo dinâmico de tamanho de posição baseado em risco
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PositionSizing:
    """
    Sistema de dimensionamento de posições para trading
    """
    
    def __init__(self,
                 max_position_size: float = 0.25,      # Tamanho máximo da posição (25%)
                 min_position_size: float = 0.01,      # Tamanho mínimo da posição (1%)
                 risk_free_rate: float = 0.05,         # Taxa livre de risco anual
                 max_drawdown: float = 0.15,           # Drawdown máximo permitido (15%)
                 volatility_window: int = 20):         # Janela para cálculo de volatilidade
        """
        Inicializa o sistema de dimensionamento
        
        Args:
            max_position_size: Tamanho máximo da posição como % do capital
            min_position_size: Tamanho mínimo da posição como % do capital
            risk_free_rate: Taxa livre de risco anual
            max_drawdown: Drawdown máximo permitido
            volatility_window: Janela para cálculo de volatilidade
        """
        self.max_position_size = max_position_size
        self.min_position_size = min_position_size
        self.risk_free_rate = risk_free_rate
        self.max_drawdown = max_drawdown
        self.volatility_window = volatility_window
        
        # Parâmetros do Kelly Criterion
        self.kelly_multiplier = 0.25  # Fator de segurança (25% do Kelly)
        self.min_win_rate = 0.45      # Taxa de vitória mínima para aplicar Kelly
        
    def calculate_position_size(self, 
                              signals_df: pd.DataFrame,
                              returns_data: Optional[pd.Series] = None,
                              current_capital: float = 100000.0) -> pd.DataFrame:
        """
        Calcula tamanho das posições baseado nos sinais
        
        Args:
            signals_df: DataFrame com sinais de trading
            returns_data: Dados de retornos históricos (opcional)
            current_capital: Capital atual disponível
            
        Returns:
            DataFrame com tamanhos de posição calculados
        """
        try:
            if signals_df.empty:
                logger.warning("Dados de sinais vazios para cálculo de posição")
                return pd.DataFrame()
            
            # Preparar dados
            position_df = signals_df.copy()
            
            # Calcular retornos se não fornecidos
            if returns_data is None:
                returns_data = self._estimate_returns_from_cli(signals_df)
            
            # Calcular métricas de risco
            position_df['volatility'] = self._calculate_volatility(returns_data)
            position_df['sharpe_ratio'] = self._calculate_sharpe_ratio(returns_data)
            position_df['max_drawdown'] = self._calculate_max_drawdown(returns_data)
            
            # Calcular probabilidades de sucesso
            position_df['win_probability'] = self._calculate_win_probability(signals_df, returns_data)
            position_df['expected_return'] = self._calculate_expected_return(signals_df, returns_data)
            
            # Aplicar Kelly Criterion
            position_df['kelly_fraction'] = self._calculate_kelly_fraction(position_df)
            
            # Aplicar ajustes de risco
            position_df['risk_adjusted_size'] = self._apply_risk_adjustments(position_df)
            
            # Calcular tamanho final da posição
            position_df['position_size'] = self._calculate_final_position_size(
                position_df, current_capital
            )
            
            # Calcular valor monetário da posição
            position_df['position_value'] = position_df['position_size'] * current_capital
            
            # Calcular stop loss e take profit
            position_df['stop_loss'] = self._calculate_stop_loss(position_df)
            position_df['take_profit'] = self._calculate_take_profit(position_df)
            
            logger.info(f"Tamanhos de posição calculados: {len(position_df)} pontos")
            return position_df
            
        except Exception as e:
            logger.error(f"Erro ao calcular tamanho das posições: {e}")
            return pd.DataFrame()
    
    def _estimate_returns_from_cli(self, signals_df: pd.DataFrame) -> pd.Series:
        """
        Estima retornos baseados no CLI quando dados históricos não disponíveis
        """
        try:
            # Usar momentum do CLI como proxy para retornos
            cli_momentum = signals_df['cli_momentum'].fillna(0)
            
            # Aplicar transformação para simular retornos
            returns = cli_momentum * 0.01  # Escalar para retornos percentuais
            
            # Adicionar ruído para realismo
            noise = np.random.normal(0, 0.005, len(returns))
            returns = returns + noise
            
            return returns
            
        except Exception as e:
            logger.error(f"Erro ao estimar retornos: {e}")
            return pd.Series(0, index=signals_df.index)
    
    def _calculate_volatility(self, returns: pd.Series) -> pd.Series:
        """
        Calcula volatilidade dos retornos
        """
        try:
            if isinstance(returns, pd.Series):
                volatility = returns.rolling(window=self.volatility_window).std()
                return volatility.fillna(returns.std())
            else:
                # Se for array numpy, calcular manualmente
                volatility = np.full_like(returns, np.std(returns))
                return volatility
            
        except Exception as e:
            logger.error(f"Erro ao calcular volatilidade: {e}")
            return pd.Series(0.02, index=returns.index)  # 2% padrão
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> pd.Series:
        """
        Calcula Sharpe ratio dos retornos
        """
        try:
            excess_returns = returns - (self.risk_free_rate / 12)  # Mensal
            volatility = self._calculate_volatility(returns)
            
            sharpe = excess_returns / volatility
            return sharpe.fillna(0)
            
        except Exception as e:
            logger.error(f"Erro ao calcular Sharpe ratio: {e}")
            return pd.Series(0, index=returns.index)
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> pd.Series:
        """
        Calcula drawdown máximo
        """
        try:
            if isinstance(returns, pd.Series):
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                return drawdown.fillna(0)
            else:
                # Se for array numpy, calcular manualmente
                cumulative = np.cumprod(1 + returns)
                running_max = np.maximum.accumulate(cumulative)
                drawdown = (cumulative - running_max) / running_max
                return drawdown
            
        except Exception as e:
            logger.error(f"Erro ao calcular drawdown: {e}")
            return pd.Series(0, index=returns.index)
    
    def _calculate_win_probability(self, 
                                 signals_df: pd.DataFrame, 
                                 returns: pd.Series) -> pd.Series:
        """
        Calcula probabilidade de sucesso baseada nos sinais
        """
        try:
            # Usar confiança do sinal como base para probabilidade
            base_prob = signals_df['signal_confidence'].fillna(0.5)
            
            # Ajustar baseado na força do sinal
            strength_factor = signals_df['signal_strength'] / 5.0
            
            # Ajustar baseado na consistência
            consistency = self._calculate_signal_consistency(signals_df)
            
            # Calcular probabilidade final
            win_prob = base_prob * 0.5 + strength_factor * 0.3 + consistency * 0.2
            
            # Limitar entre 0.1 e 0.9
            win_prob = np.clip(win_prob, 0.1, 0.9)
            
            return win_prob
            
        except Exception as e:
            logger.error(f"Erro ao calcular probabilidade de vitória: {e}")
            return pd.Series(0.5, index=signals_df.index)
    
    def _calculate_signal_consistency(self, signals_df: pd.DataFrame) -> pd.Series:
        """
        Calcula consistência dos sinais
        """
        try:
            # Calcular consistência baseada na concordância entre sinais
            signal_cols = ['cli_signal', 'momentum_signal', 'trend_signal']
            available_cols = [col for col in signal_cols if col in signals_df.columns]
            
            if not available_cols:
                return pd.Series(0.5, index=signals_df.index)
            
            # Contar sinais positivos, negativos e neutros
            positive_count = (signals_df[available_cols] > 0).sum(axis=1)
            negative_count = (signals_df[available_cols] < 0).sum(axis=1)
            
            # Calcular consistência
            max_agreement = np.maximum(positive_count, negative_count)
            consistency = max_agreement / len(available_cols)
            
            return consistency
            
        except Exception as e:
            logger.error(f"Erro ao calcular consistência: {e}")
            return pd.Series(0.5, index=signals_df.index)
    
    def _calculate_expected_return(self, 
                                 signals_df: pd.DataFrame, 
                                 returns: pd.Series) -> pd.Series:
        """
        Calcula retorno esperado baseado nos sinais
        """
        try:
            # Usar momentum do CLI como base
            cli_momentum = signals_df['cli_momentum'].fillna(0)
            
            # Aplicar transformação para retorno esperado
            expected_return = cli_momentum * 0.02  # 2% por unidade de momentum
            
            # Ajustar baseado na confiança
            confidence = signals_df['signal_confidence'].fillna(0.5)
            expected_return = expected_return * confidence
            
            return expected_return
            
        except Exception as e:
            logger.error(f"Erro ao calcular retorno esperado: {e}")
            return pd.Series(0, index=signals_df.index)
    
    def _calculate_kelly_fraction(self, position_df: pd.DataFrame) -> pd.Series:
        """
        Calcula fração de Kelly para cada posição
        """
        try:
            # Kelly Criterion: f = (bp - q) / b
            # onde b = odds, p = probabilidade de vitória, q = probabilidade de perda
            
            win_prob = position_df['win_probability']
            expected_return = position_df['expected_return']
            volatility = position_df['volatility']
            
            # Calcular odds (b) baseado no retorno esperado e volatilidade
            odds = expected_return / volatility
            
            # Aplicar Kelly Criterion
            kelly_fraction = (odds * win_prob - (1 - win_prob)) / odds
            
            # Aplicar fator de segurança
            kelly_fraction = kelly_fraction * self.kelly_multiplier
            
            # Limitar entre 0 e max_position_size
            kelly_fraction = np.clip(kelly_fraction, 0, self.max_position_size)
            
            # Aplicar apenas se taxa de vitória for suficiente
            kelly_fraction = np.where(
                win_prob >= self.min_win_rate,
                kelly_fraction,
                0
            )
            
            return kelly_fraction.fillna(0)
            
        except Exception as e:
            logger.error(f"Erro ao calcular fração de Kelly: {e}")
            return pd.Series(0, index=position_df.index)
    
    def _apply_risk_adjustments(self, position_df: pd.DataFrame) -> pd.Series:
        """
        Aplica ajustes de risco ao tamanho da posição
        """
        try:
            base_size = position_df['kelly_fraction']
            
            # Ajuste por volatilidade (reduzir posição se alta volatilidade)
            volatility_adj = 1 - (position_df['volatility'] - 0.02) * 2
            volatility_adj = np.clip(volatility_adj, 0.5, 1.0)
            
            # Ajuste por drawdown (reduzir posição se alto drawdown)
            drawdown_adj = 1 - position_df['max_drawdown'] / self.max_drawdown
            drawdown_adj = np.clip(drawdown_adj, 0.3, 1.0)
            
            # Ajuste por Sharpe ratio (aumentar posição se bom Sharpe)
            sharpe_adj = 1 + (position_df['sharpe_ratio'] - 1) * 0.2
            sharpe_adj = np.clip(sharpe_adj, 0.8, 1.2)
            
            # Aplicar ajustes
            adjusted_size = base_size * volatility_adj * drawdown_adj * sharpe_adj
            
            return adjusted_size.fillna(0)
            
        except Exception as e:
            logger.error(f"Erro ao aplicar ajustes de risco: {e}")
            return position_df['kelly_fraction']
    
    def _calculate_final_position_size(self, 
                                     position_df: pd.DataFrame, 
                                     current_capital: float) -> pd.Series:
        """
        Calcula tamanho final da posição
        """
        try:
            base_size = position_df['risk_adjusted_size']
            
            # Aplicar limites mínimos e máximos
            final_size = np.clip(base_size, self.min_position_size, self.max_position_size)
            
            # Aplicar apenas para sinais BUY/SELL
            signal_type = position_df['signal_type']
            final_size = np.where(
                signal_type.isin(['BUY', 'SELL']),
                final_size,
                0
            )
            
            return final_size
            
        except Exception as e:
            logger.error(f"Erro ao calcular tamanho final: {e}")
            return pd.Series(0, index=position_df.index)
    
    def _calculate_stop_loss(self, position_df: pd.DataFrame) -> pd.Series:
        """
        Calcula nível de stop loss
        """
        try:
            # Stop loss baseado na volatilidade
            volatility = position_df['volatility']
            stop_loss = -volatility * 2  # 2 desvios padrão
            
            # Ajustar baseado no tipo de sinal
            signal_type = position_df['signal_type']
            stop_loss = np.where(
                signal_type == 'BUY',
                stop_loss,
                np.where(signal_type == 'SELL', -stop_loss, 0)
            )
            
            return stop_loss.fillna(-0.05)  # 5% padrão
            
        except Exception as e:
            logger.error(f"Erro ao calcular stop loss: {e}")
            return pd.Series(-0.05, index=position_df.index)
    
    def _calculate_take_profit(self, position_df: pd.DataFrame) -> pd.Series:
        """
        Calcula nível de take profit
        """
        try:
            # Take profit baseado no retorno esperado
            expected_return = position_df['expected_return']
            take_profit = expected_return * 2  # 2x o retorno esperado
            
            # Ajustar baseado no tipo de sinal
            signal_type = position_df['signal_type']
            take_profit = np.where(
                signal_type == 'BUY',
                take_profit,
                np.where(signal_type == 'SELL', -take_profit, 0)
            )
            
            # Limitar entre 1% e 20%
            take_profit = np.clip(take_profit, 0.01, 0.20)
            
            return take_profit.fillna(0.10)  # 10% padrão
            
        except Exception as e:
            logger.error(f"Erro ao calcular take profit: {e}")
            return pd.Series(0.10, index=position_df.index)
    
    def get_position_summary(self, position_df: pd.DataFrame) -> Dict[str, any]:
        """
        Retorna resumo das posições calculadas
        """
        try:
            if position_df.empty:
                return {'error': 'Nenhuma posição calculada'}
            
            # Filtrar apenas posições ativas
            active_positions = position_df[position_df['position_size'] > 0]
            
            if active_positions.empty:
                return {'message': 'Nenhuma posição ativa'}
            
            # Calcular métricas
            total_exposure = active_positions['position_value'].sum()
            avg_position_size = active_positions['position_size'].mean()
            max_position_size = active_positions['position_size'].max()
            
            # Calcular risco total
            portfolio_volatility = active_positions['volatility'].mean()
            portfolio_sharpe = active_positions['sharpe_ratio'].mean()
            
            # Calcular distribuição por tipo de sinal
            signal_distribution = active_positions['signal_type'].value_counts()
            
            return {
                'total_positions': len(active_positions),
                'total_exposure': round(total_exposure, 2),
                'exposure_percentage': round((total_exposure / 100000) * 100, 2),
                'average_position_size': round(avg_position_size, 4),
                'max_position_size': round(max_position_size, 4),
                'portfolio_volatility': round(portfolio_volatility, 4),
                'portfolio_sharpe': round(portfolio_sharpe, 4),
                'signal_distribution': signal_distribution.to_dict(),
                'avg_win_probability': round(active_positions['win_probability'].mean(), 3),
                'avg_expected_return': round(active_positions['expected_return'].mean(), 4)
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo de posições: {e}")
            return {'error': str(e)}
    
    def get_position_health_status(self) -> Dict[str, any]:
        """
        Retorna status de saúde do sistema de posicionamento
        """
        return {
            'status': 'healthy',
            'max_position_size': self.max_position_size,
            'min_position_size': self.min_position_size,
            'risk_free_rate': self.risk_free_rate,
            'max_drawdown': self.max_drawdown,
            'volatility_window': self.volatility_window,
            'kelly_multiplier': self.kelly_multiplier,
            'min_win_rate': self.min_win_rate
        }
