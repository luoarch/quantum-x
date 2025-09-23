"""
Gerador de Sinais de Trading baseado em CLI
Implementa lógica de sinais BUY/SELL/HOLD com thresholds dinâmicos
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Tipos de sinais de trading"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalStrength(Enum):
    """Força dos sinais"""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4
    EXTREME = 5


class SignalGenerator:
    """
    Gerador de sinais de trading baseado em CLI e séries econômicas
    """
    
    def __init__(self,
                 cli_buy_threshold: float = 102.0,      # Threshold para sinal BUY (aumentado)
                 cli_sell_threshold: float = 98.0,      # Threshold para sinal SELL (reduzido)
                 momentum_threshold: float = 0.3,       # Threshold de momentum (reduzido)
                 trend_threshold: float = 0.2,          # Threshold de tendência (reduzido)
                 min_signal_strength: int = 1,          # Força mínima para gerar sinal (reduzido)
                 use_regime_switching: bool = True,     # Ativar modelos de regime
                 regime_confirmation_months: int = 1):  # Meses para confirmar regime (reduzido)
        """
        Inicializa o gerador de sinais
        
        Args:
            cli_buy_threshold: Threshold CLI para sinal de compra
            cli_sell_threshold: Threshold CLI para sinal de venda
            momentum_threshold: Threshold de momentum para confirmação
            trend_threshold: Threshold de tendência para confirmação
            min_signal_strength: Força mínima do sinal (1-5)
        """
        self.cli_buy_threshold = cli_buy_threshold
        self.cli_sell_threshold = cli_sell_threshold
        self.momentum_threshold = momentum_threshold
        self.trend_threshold = trend_threshold
        self.min_signal_strength = min_signal_strength
        self.use_regime_switching = use_regime_switching
        self.regime_confirmation_months = regime_confirmation_months
        
        # Pesos para diferentes indicadores
        self.weights = {
            'cli_level': 0.4,
            'cli_momentum': 0.3,
            'cli_trend': 0.2,
            'economic_confirm': 0.1
        }
    
    def generate_signals(self, 
                        cli_data: pd.DataFrame,
                        economic_data: Optional[Dict[str, pd.DataFrame]] = None) -> pd.DataFrame:
        """
        Gera sinais de trading baseados no CLI
        
        Args:
            cli_data: DataFrame com dados do CLI calculado
            economic_data: Dados econômicos adicionais para confirmação
            
        Returns:
            DataFrame com sinais de trading
        """
        try:
            if cli_data.empty:
                logger.warning("Dados CLI vazios para geração de sinais")
                return pd.DataFrame()
            
            # Preparar dados
            signals_df = cli_data.copy()
            
            # Calcular indicadores de sinal
            signals_df['cli_signal'] = self._calculate_cli_signal(signals_df)
            signals_df['momentum_signal'] = self._calculate_momentum_signal(signals_df)
            signals_df['trend_signal'] = self._calculate_trend_signal(signals_df)
            signals_df['economic_signal'] = self._calculate_economic_signal(signals_df, economic_data)
            
            # Calcular sinal combinado
            signals_df['combined_signal'] = self._calculate_combined_signal(signals_df)
            signals_df['signal_strength'] = self._calculate_signal_strength(signals_df)
            
            # Aplicar filtros de qualidade
            signals_df['final_signal'] = self._apply_quality_filters(signals_df)
            
            # Aplicar confirmação de regime se ativado
            if self.use_regime_switching:
                signals_df = self._apply_regime_confirmation(signals_df)
            signals_df['signal_type'] = signals_df['final_signal'].apply(self._get_signal_type)
            
            # Calcular métricas adicionais
            signals_df['signal_confidence'] = self._calculate_confidence(signals_df)
            signals_df['risk_level'] = self._calculate_risk_level(signals_df)
            
            logger.info(f"Sinais gerados com sucesso: {len(signals_df)} pontos")
            return signals_df
            
        except Exception as e:
            logger.error(f"Erro ao gerar sinais: {e}")
            return pd.DataFrame()
    
    def _calculate_cli_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula sinal baseado no nível do CLI
        """
        try:
            cli = df['cli_normalized']
            
            # Sinal baseado em thresholds
            signal = np.where(
                cli > self.cli_buy_threshold, 1,  # BUY
                np.where(
                    cli < self.cli_sell_threshold, -1,  # SELL
                    0  # HOLD
                )
            )
            
            return pd.Series(signal, index=df.index)
            
        except Exception as e:
            logger.error(f"Erro ao calcular sinal CLI: {e}")
            return pd.Series(0, index=df.index)
    
    def _calculate_momentum_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula sinal baseado no momentum do CLI
        """
        try:
            momentum = df['cli_momentum']
            
            # Sinal baseado em momentum
            signal = np.where(
                momentum > self.momentum_threshold, 1,  # Momentum positivo
                np.where(
                    momentum < -self.momentum_threshold, -1,  # Momentum negativo
                    0  # Neutro
                )
            )
            
            return pd.Series(signal, index=df.index)
            
        except Exception as e:
            logger.error(f"Erro ao calcular sinal momentum: {e}")
            return pd.Series(0, index=df.index)
    
    def _calculate_trend_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula sinal baseado na tendência do CLI
        """
        try:
            trend = df['cli_trend']
            cli = df['cli_normalized']
            
            # Calcular tendência relativa
            trend_relative = (trend - cli) / cli
            
            # Sinal baseado em tendência
            signal = np.where(
                trend_relative > self.trend_threshold, 1,  # Tendência ascendente
                np.where(
                    trend_relative < -self.trend_threshold, -1,  # Tendência descendente
                    0  # Neutro
                )
            )
            
            return pd.Series(signal, index=df.index)
            
        except Exception as e:
            logger.error(f"Erro ao calcular sinal tendência: {e}")
            return pd.Series(0, index=df.index)
    
    def _calculate_economic_signal(self, 
                                 df: pd.DataFrame, 
                                 economic_data: Optional[Dict[str, pd.DataFrame]]) -> pd.Series:
        """
        Calcula sinal baseado em confirmação econômica
        """
        try:
            if economic_data is None:
                return pd.Series(0, index=df.index)
            
            # Calcular sinal econômico baseado em múltiplas séries
            economic_signals = []
            
            for series_name, series_data in economic_data.items():
                if series_data.empty:
                    continue
                
                # Alinhar por data
                aligned_data = series_data.set_index('date').reindex(df.index, method='ffill')
                
                if aligned_data.empty:
                    continue
                
                # Calcular sinal para esta série
                series_signal = self._calculate_series_signal(aligned_data['value'], series_name)
                economic_signals.append(series_signal)
            
            if not economic_signals:
                return pd.Series(0, index=df.index)
            
            # Média ponderada dos sinais econômicos
            combined_signal = np.mean(economic_signals, axis=0)
            
            return pd.Series(combined_signal, index=df.index)
            
        except Exception as e:
            logger.error(f"Erro ao calcular sinal econômico: {e}")
            return pd.Series(0, index=df.index)
    
    def _calculate_series_signal(self, series: pd.Series, series_name: str) -> np.ndarray:
        """
        Calcula sinal para uma série econômica específica
        """
        try:
            # Calcular momentum da série
            momentum = series.pct_change(3).fillna(0)
            
            # Aplicar lógica específica por tipo de série
            if series_name in ['ipca', 'desemprego']:
                # Para inflação e desemprego, valores menores são melhores
                signal = np.where(momentum < -0.01, 1,  # Melhoria
                                np.where(momentum > 0.01, -1, 0))  # Piora
            else:
                # Para outras séries, valores maiores são melhores
                signal = np.where(momentum > 0.01, 1,  # Melhoria
                                np.where(momentum < -0.01, -1, 0))  # Piora
            
            return signal
            
        except Exception as e:
            logger.error(f"Erro ao calcular sinal da série {series_name}: {e}")
            return np.zeros(len(series))
    
    def _calculate_combined_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula sinal combinado ponderado
        """
        try:
            # Aplicar pesos aos sinais individuais
            weighted_signal = (
                df['cli_signal'] * self.weights['cli_level'] +
                df['momentum_signal'] * self.weights['cli_momentum'] +
                df['trend_signal'] * self.weights['cli_trend'] +
                df['economic_signal'] * self.weights['economic_confirm']
            )
            
            # Normalizar para [-1, 1]
            max_weight = sum(self.weights.values())
            normalized_signal = weighted_signal / max_weight
            
            return normalized_signal
            
        except Exception as e:
            logger.error(f"Erro ao calcular sinal combinado: {e}")
            return pd.Series(0, index=df.index)
    
    def _calculate_signal_strength(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula força do sinal (1-5)
        """
        try:
            # Calcular força baseada na magnitude e consistência
            magnitude = abs(df['combined_signal'])
            consistency = self._calculate_consistency(df)
            
            # Combinar magnitude e consistência
            strength = (magnitude * 0.7 + consistency * 0.3) * 5
            
            # Arredondar para inteiro e limitar a [1, 5]
            strength = np.clip(np.round(strength), 1, 5)
            
            return strength.astype(int)
            
        except Exception as e:
            logger.error(f"Erro ao calcular força do sinal: {e}")
            return pd.Series(1, index=df.index)
    
    def _calculate_consistency(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula consistência dos sinais (0-1)
        """
        try:
            # Calcular consistência baseada na concordância entre sinais
            signals = df[['cli_signal', 'momentum_signal', 'trend_signal', 'economic_signal']]
            
            # Contar sinais positivos, negativos e neutros
            positive_count = (signals > 0).sum(axis=1)
            negative_count = (signals < 0).sum(axis=1)
            neutral_count = (signals == 0).sum(axis=1)
            
            # Calcular consistência
            max_agreement = np.maximum(positive_count, negative_count)
            consistency = max_agreement / len(signals.columns)
            
            return consistency
            
        except Exception as e:
            logger.error(f"Erro ao calcular consistência: {e}")
            return pd.Series(0.5, index=df.index)
    
    def _apply_quality_filters(self, df: pd.DataFrame) -> pd.Series:
        """
        Aplica filtros de qualidade aos sinais
        """
        try:
            # Filtrar sinais com força insuficiente
            quality_filter = df['signal_strength'] >= self.min_signal_strength
            
            # Aplicar filtro de confiança mínima (lidar com NaN)
            confidence_filter = df['signal_confidence'].fillna(0) >= 0.6
            
            # Combinar filtros
            final_filter = quality_filter & confidence_filter
            
            # Aplicar sinal apenas onde filtros passam
            final_signal = df['combined_signal'].where(final_filter, 0)
            
            return final_signal
            
        except Exception as e:
            logger.error(f"Erro ao aplicar filtros de qualidade: {e}")
            return df['combined_signal']
    
    def _get_signal_type(self, signal_value: float) -> str:
        """
        Converte valor numérico do sinal para tipo
        """
        if signal_value > 0.1:
            return SignalType.BUY.value
        elif signal_value < -0.1:
            return SignalType.SELL.value
        else:
            return SignalType.HOLD.value
    
    def _calculate_confidence(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula confiança do sinal (0-1)
        """
        try:
            # Calcular confiança baseada em múltiplos fatores
            consistency = self._calculate_consistency(df)
            strength_factor = df['signal_strength'] / 5.0
            cli_stability = 1 - abs(df['cli_normalized'] - 100) / 100
            
            # Combinar fatores
            confidence = (consistency * 0.4 + strength_factor * 0.4 + cli_stability * 0.2)
            
            return np.clip(confidence, 0, 1)
            
        except Exception as e:
            logger.error(f"Erro ao calcular confiança: {e}")
            return pd.Series(0.5, index=df.index)
    
    def _calculate_risk_level(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula nível de risco do sinal (1-5)
        """
        try:
            # Calcular risco baseado na volatilidade e incerteza
            cli_volatility = df['cli_normalized'].rolling(6).std().fillna(0)
            confidence_factor = 1 - df['signal_confidence']
            
            # Combinar fatores de risco
            risk_score = (cli_volatility * 0.6 + confidence_factor * 0.4) * 5
            
            # Arredondar para inteiro e limitar a [1, 5]
            risk_level = np.clip(np.round(risk_score), 1, 5)
            
            return risk_level.astype(int)
            
        except Exception as e:
            logger.error(f"Erro ao calcular nível de risco: {e}")
            return pd.Series(3, index=df.index)
    
    def get_signal_summary(self, signals_df: pd.DataFrame) -> Dict[str, any]:
        """
        Retorna resumo dos sinais gerados
        """
        try:
            if signals_df.empty:
                return {'error': 'Nenhum sinal gerado'}
            
            # Contar sinais por tipo
            signal_counts = signals_df['signal_type'].value_counts()
            
            # Calcular métricas
            total_signals = len(signals_df)
            buy_signals = signal_counts.get('BUY', 0)
            sell_signals = signal_counts.get('SELL', 0)
            hold_signals = signal_counts.get('HOLD', 0)
            
            avg_confidence = signals_df['signal_confidence'].mean()
            avg_strength = signals_df['signal_strength'].mean()
            avg_risk = signals_df['risk_level'].mean()
            
            return {
                'total_signals': total_signals,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'hold_signals': hold_signals,
                'buy_percentage': (buy_signals / total_signals) * 100,
                'sell_percentage': (sell_signals / total_signals) * 100,
                'hold_percentage': (hold_signals / total_signals) * 100,
                'average_confidence': round(avg_confidence, 3),
                'average_strength': round(avg_strength, 2),
                'average_risk': round(avg_risk, 2),
                'last_signal': signals_df['signal_type'].iloc[-1] if not signals_df.empty else None,
                'last_confidence': round(signals_df['signal_confidence'].iloc[-1], 3) if not signals_df.empty else None
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo de sinais: {e}")
            return {'error': str(e)}
    
    def get_signal_health_status(self) -> Dict[str, any]:
        """
        Retorna status de saúde do gerador de sinais
        """
        return {
            'status': 'healthy',
            'cli_buy_threshold': self.cli_buy_threshold,
            'cli_sell_threshold': self.cli_sell_threshold,
            'momentum_threshold': self.momentum_threshold,
            'trend_threshold': self.trend_threshold,
            'min_signal_strength': self.min_signal_strength,
            'weights': self.weights,
            'use_regime_switching': self.use_regime_switching,
            'regime_confirmation_months': self.regime_confirmation_months
        }
    
    def _apply_regime_confirmation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica confirmação de regime para reduzir over-trading
        """
        try:
            # Identificar regimes baseados no CLI
            df['regime'] = self._identify_regime(df)
            
            # Aplicar confirmação de regime
            df['regime_confirmed'] = False
            df['final_signal_confirmed'] = df['final_signal'].copy()
            
            for i in range(len(df)):
                if i < self.regime_confirmation_months:
                    continue
                
                # Verificar se o regime se manteve estável
                recent_regimes = df['regime'].iloc[i-self.regime_confirmation_months:i+1]
                regime_stable = len(recent_regimes.unique()) == 1
                
                if regime_stable:
                    df.loc[df.index[i], 'regime_confirmed'] = True
                else:
                    # Se regime não estável, manter HOLD
                    df.loc[df.index[i], 'final_signal_confirmed'] = 0
            
            # Atualizar sinal final com confirmação
            df['final_signal'] = df['final_signal_confirmed']
            
            return df
            
        except Exception as e:
            logger.error(f"Erro na confirmação de regime: {e}")
            return df
    
    def _identify_regime(self, df: pd.DataFrame) -> pd.Series:
        """
        Identifica regimes econômicos baseados no CLI
        """
        try:
            regimes = []
            
            for i, row in df.iterrows():
                cli_value = row['cli_normalized']
                momentum = row['cli_momentum']
                trend = row['cli_trend']
                
                # Definir regimes baseados em múltiplos indicadores
                if cli_value > 110 and momentum > 0 and trend > 0:
                    regime = 'EXPANSION'  # Expansão forte
                elif cli_value > 105 and momentum > 0:
                    regime = 'GROWTH'     # Crescimento moderado
                elif cli_value < 90 and momentum < 0 and trend < 0:
                    regime = 'RECESSION' # Recessão
                elif cli_value < 95 and momentum < 0:
                    regime = 'SLOWDOWN'   # Desaceleração
                else:
                    regime = 'NEUTRAL'    # Neutro
                
                regimes.append(regime)
            
            return pd.Series(regimes, index=df.index)
            
        except Exception as e:
            logger.error(f"Erro na identificação de regime: {e}")
            return pd.Series(['NEUTRAL'] * len(df), index=df.index)
