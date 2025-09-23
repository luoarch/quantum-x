"""
Gerador de Sinais Probabilísticos Avançado
Integra Markov-Switching, HRP e indicadores de curva de juros
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

# Importar módulos customizados
from .markov_switching_model import MarkovSwitchingModel
from .hierarchical_risk_parity import HierarchicalRiskParity
from .yield_curve_indicators import YieldCurveIndicators

logger = logging.getLogger(__name__)

class ProbabilisticSignalGenerator:
    """
    Gerador de sinais probabilísticos integrado
    Combina múltiplos modelos para sinais robustos
    """
    
    def __init__(self, 
                 confidence_threshold: float = 0.8,  # Confiança mínima para executar trade
                 regime_confirmation_months: int = 2,  # Meses para confirmar regime
                 spread_threshold: float = 0.5):  # Threshold para spreads
        """
        Inicializa o gerador de sinais probabilísticos
        
        Args:
            confidence_threshold: Confiança mínima para executar trade
            regime_confirmation_months: Meses para confirmar regime
            spread_threshold: Threshold para spreads
        """
        self.confidence_threshold = confidence_threshold
        self.regime_confirmation_months = regime_confirmation_months
        self.spread_threshold = spread_threshold
        
        # Inicializar modelos
        self.markov_model = MarkovSwitchingModel(n_regimes=4)
        self.hrp_allocator = HierarchicalRiskParity()
        self.yield_indicators = YieldCurveIndicators()
        
        # Pesos para diferentes indicadores
        self.weights = {
            'regime_probability': 0.4,
            'yield_curve': 0.3,
            'momentum': 0.2,
            'volatility': 0.1
        }
    
    def generate_signals(self, 
                        economic_data: Dict[str, pd.DataFrame],
                        asset_returns: pd.DataFrame,
                        yield_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict:
        """
        Gera sinais probabilísticos integrados
        
        Args:
            economic_data: Dados econômicos
            asset_returns: Retornos dos ativos
            yield_data: Dados de curva de juros (opcional)
            
        Returns:
            Dicionário com sinais e métricas
        """
        try:
            logger.info("🚀 INICIANDO GERAÇÃO DE SINAIS PROBABILÍSTICOS")
            logger.info(f"📊 Dados econômicos: {len(economic_data)} séries")
            logger.info(f"💰 Ativos: {list(asset_returns.columns)}")
            logger.info(f"📈 Dados de curva: {len(yield_data) if yield_data else 0} séries")
            
            # 1. Ajustar modelo Markov-Switching
            logger.info("🧠 ETAPA 1: Ajustando modelo Markov-Switching...")
            markov_results = self._fit_markov_model(economic_data)
            logger.info(f"✅ Modelo Markov ajustado: {type(markov_results)}")
            
            # 2. Calcular indicadores de curva de juros
            logger.info("📊 ETAPA 2: Calculando indicadores de curva de juros...")
            yield_signals = self._calculate_yield_signals(yield_data)
            logger.info(f"✅ Indicadores de curva calculados: {len(yield_signals.get('signals', []))} pontos")
            
            # 3. Gerar sinais probabilísticos
            logger.info("🎯 ETAPA 3: Gerando sinais probabilísticos...")
            probabilistic_signals = self._generate_probabilistic_signals(
                markov_results, yield_signals, asset_returns
            )
            logger.info(f"✅ Sinais probabilísticos gerados: {len(probabilistic_signals)} pontos")
            
            # 4. Aplicar confirmação de regime
            logger.info("🔒 ETAPA 4: Aplicando confirmação de regime...")
            confirmed_signals = self._apply_regime_confirmation(probabilistic_signals)
            logger.info(f"✅ Confirmação de regime aplicada: {len(confirmed_signals)} pontos")
            
            # 5. Calcular alocação HRP
            logger.info("💰 ETAPA 5: Calculando alocação HRP...")
            hrp_allocation = self._calculate_hrp_allocation(
                asset_returns, probabilistic_signals
            )
            logger.info(f"✅ Alocação HRP calculada: {type(hrp_allocation)}")
            
            # 6. Gerar resumo
            logger.info("📋 ETAPA 6: Gerando resumo...")
            summary = self._generate_signal_summary(
                confirmed_signals, hrp_allocation, markov_results
            )
            logger.info(f"✅ Resumo gerado: {len(summary)} métricas")
            
            logger.info("🎉 GERAÇÃO DE SINAIS CONCLUÍDA COM SUCESSO!")
            
            return {
                'signals': confirmed_signals,
                'hrp_allocation': hrp_allocation,
                'markov_results': markov_results,
                'yield_signals': yield_signals,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO na geração de sinais: {e}")
            import traceback
            logger.error(f"📋 Traceback completo: {traceback.format_exc()}")
            return {'error': str(e)}
    
    def _fit_markov_model(self, economic_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Ajusta modelo Markov-Switching
        """
        try:
            logger.info("🔍 DEBUG: Iniciando ajuste do modelo Markov-Switching")
            logger.info(f"📊 Séries econômicas disponíveis: {list(economic_data.keys())}")
            
            # Preparar dados para o modelo
            if 'cli_normalized' in economic_data:
                cli_data = economic_data['cli_normalized']
                logger.info(f"✅ CLI encontrado: {len(cli_data)} pontos")
                logger.info(f"📊 CLI columns: {list(cli_data.columns)}")
                logger.info(f"📊 CLI shape: {cli_data.shape}")
                if 'value' in cli_data.columns:
                    logger.info(f"📈 CLI range: {cli_data['value'].min():.2f} a {cli_data['value'].max():.2f}")
                else:
                    logger.warning("⚠️ CLI não tem coluna 'value'")
            else:
                logger.warning("⚠️ CLI não encontrado, criando CLI simples")
                # Criar CLI simples se não disponível
                cli_data = self._create_simple_cli(economic_data)
                logger.info(f"🔧 CLI simples criado: {len(cli_data)} pontos")
            
            if cli_data.empty:
                logger.error("❌ CLI vazio após criação")
                return {'error': 'CLI vazio'}
            
            logger.info("🧠 Ajustando modelo Markov-Switching...")
            
            # Preparar dados para o modelo
            if 'value' in cli_data.columns:
                cli_series = cli_data['value']
            else:
                logger.error("❌ CLI não tem coluna 'value'")
                return {'error': 'CLI sem coluna value'}
            
            # Ajustar modelo
            logger.info(f"🧠 Ajustando modelo com {len(cli_series)} pontos de dados")
            logger.info(f"📊 CLI series type: {type(cli_series)}")
            logger.info(f"📊 CLI series shape: {cli_series.shape if hasattr(cli_series, 'shape') else 'N/A'}")
            logger.info(f"📊 CLI series index type: {type(cli_series.index)}")
            
            markov_results = self.markov_model.fit(cli_series)
            logger.info(f"✅ Modelo Markov ajustado com sucesso")
            logger.info(f"📊 Resultado type: {type(markov_results)}")
            logger.info(f"📊 Resultado keys: {list(markov_results.keys()) if isinstance(markov_results, dict) else 'N/A'}")
            
            if 'error' in markov_results:
                logger.error(f"❌ Erro no modelo Markov: {markov_results['error']}")
                return markov_results
            
            logger.info(f"📊 Regimes identificados: {len(markov_results.get('regime_names', []))}")
            logger.info(f"🎯 Confiança média: {np.mean(markov_results.get('regime_probabilities', [[0]])):.3f}")
            
            return markov_results
            
        except Exception as e:
            logger.error(f"❌ ERRO ao ajustar modelo Markov: {e}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return {'error': str(e)}
    
    def _create_simple_cli(self, economic_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Cria CLI simples se não disponível
        """
        try:
            logger.info("🔧 DEBUG: Criando CLI simples")
            logger.info(f"📊 Séries disponíveis: {list(economic_data.keys())}")
            
            # Combinar séries econômicas
            combined_data = pd.DataFrame()
            
            for series_name, df in economic_data.items():
                logger.debug(f"📊 Processando série: {series_name}")
                if 'value' in df.columns:
                    combined_data[series_name] = df['value']
                    logger.debug(f"✅ Série {series_name} adicionada: {len(df)} pontos")
                else:
                    logger.warning(f"⚠️ Série {series_name} não tem coluna 'value'")
            
            logger.info(f"📊 Dados combinados: {combined_data.shape}")
            
            # Normalizar e calcular média
            if not combined_data.empty:
                logger.info("📊 Normalizando dados...")
                normalized_data = combined_data.apply(lambda x: (x - x.mean()) / x.std())
                cli_simple = normalized_data.mean(axis=1)
                
                logger.info(f"✅ CLI simples criado: {len(cli_simple)} pontos")
                logger.info(f"📈 CLI range: {cli_simple.min():.2f} a {cli_simple.max():.2f}")
                
                return pd.DataFrame({
                    'value': cli_simple
                })
            else:
                logger.error("❌ Nenhum dado disponível para criar CLI")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ ERRO ao criar CLI simples: {e}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return pd.DataFrame()
    
    def _calculate_yield_signals(self, yield_data: Optional[Dict[str, pd.DataFrame]]) -> Dict:
        """
        Calcula sinais de curva de juros
        """
        try:
            if yield_data is None or not yield_data:
                return {'signals': pd.DataFrame(), 'summary': {}}
            
            # Calcular spreads
            spreads_df = self.yield_indicators.calculate_spreads(yield_data)
            
            if spreads_df.empty:
                return {'signals': pd.DataFrame(), 'summary': {}}
            
            # Gerar sinais
            signals_df = self.yield_indicators.generate_signals(spreads_df)
            
            # Gerar resumo
            summary = self.yield_indicators.get_yield_summary(spreads_df)
            
            return {
                'signals': signals_df,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular sinais de curva de juros: {e}")
            return {'signals': pd.DataFrame(), 'summary': {}}
    
    def _generate_probabilistic_signals(self, 
                                       markov_results: Dict, 
                                       yield_signals: Dict,
                                       asset_returns: pd.DataFrame) -> pd.DataFrame:
        """
        Gera sinais probabilísticos integrados
        """
        try:
            logger.info("🎯 DEBUG: Iniciando geração de sinais probabilísticos")
            logger.info(f"📊 Asset returns: {len(asset_returns)} pontos")
            logger.info(f"🧠 Markov results keys: {list(markov_results.keys())}")
            logger.info(f"📈 Yield signals keys: {list(yield_signals.keys())}")
            
            # Preparar dados base
            dates = asset_returns.index
            signals_df = pd.DataFrame(index=dates)
            logger.info(f"📅 Datas preparadas: {len(dates)} pontos")
            
            # Sinais do modelo Markov-Switching
            if 'regime_probabilities' in markov_results:
                regime_probs = markov_results['regime_probabilities']
                most_likely_regime = markov_results['most_likely_regime']
                logger.info(f"📊 Regime probabilities shape: {regime_probs.shape}")
                logger.info(f"🏆 Most likely regime shape: {most_likely_regime.shape}")
                logger.info(f"📊 Signals_df index length: {len(signals_df)}")
                
                # Verificar alinhamento de tamanhos
                if len(regime_probs) != len(signals_df):
                    logger.warning(f"⚠️ Tamanho incompatível: regime_probs={len(regime_probs)}, signals_df={len(signals_df)}")
                    # Ajustar tamanho
                    min_len = min(len(regime_probs), len(signals_df))
                    regime_probs = regime_probs[:min_len]
                    most_likely_regime = most_likely_regime[:min_len]
                    signals_df = signals_df.iloc[:min_len]
                    logger.info(f"📊 Ajustado para tamanho: {min_len}")
                
                # Adicionar probabilidades de regime
                for i, regime_name in enumerate(markov_results['regime_names']):
                    signals_df[f'prob_{regime_name}'] = regime_probs[:, i]
                    logger.debug(f"📊 Adicionada probabilidade para regime: {regime_name}")
                
                signals_df['most_likely_regime'] = most_likely_regime
                signals_df['regime_confidence'] = np.max(regime_probs, axis=1)
                logger.info(f"✅ Sinais Markov adicionados: {len(signals_df.columns)} colunas")
            else:
                logger.warning("⚠️ 'regime_probabilities' não encontrado em markov_results")
                logger.info(f"📊 Markov results keys: {list(markov_results.keys())}")
                # Criar colunas padrão
                signals_df['prob_EXPANSION'] = 0.25
                signals_df['prob_RECESSION'] = 0.25
                signals_df['prob_RECOVERY'] = 0.25
                signals_df['prob_CONTRACTION'] = 0.25
                signals_df['most_likely_regime'] = 0
                signals_df['regime_confidence'] = 0.25
            
            # Sinais de curva de juros
            if not yield_signals['signals'].empty:
                yield_df = yield_signals['signals']
                
                # Alinhar datas
                common_dates = dates.intersection(yield_df.index)
                if len(common_dates) > 0:
                    for col in yield_df.columns:
                        if col in ['buy_signal', 'sell_signal', 'combined_signal', 'signal_strength']:
                            signals_df.loc[common_dates, f'yield_{col}'] = yield_df.loc[common_dates, col]
            
            # Calcular sinais probabilísticos
            logger.info("🎯 Calculando sinais probabilísticos...")
            logger.info(f"📊 Signals_df antes: {signals_df.shape}")
            logger.info(f"📊 Columns antes: {list(signals_df.columns)}")
            
            signals_df = self._calculate_probabilistic_signals(signals_df)
            
            logger.info(f"📊 Signals_df depois: {signals_df.shape}")
            logger.info(f"📊 Columns depois: {list(signals_df.columns)}")
            
            return signals_df
            
        except Exception as e:
            logger.error(f"Erro ao gerar sinais probabilísticos: {e}")
            return pd.DataFrame()
    
    def _calculate_probabilistic_signals(self, signals_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula sinais probabilísticos baseados em múltiplos indicadores
        """
        try:
            logger.info("🎯 DEBUG: Calculando sinais probabilísticos")
            logger.info(f"📊 Input shape: {signals_df.shape}")
            logger.info(f"📊 Available columns: {list(signals_df.columns)}")
            logger.info(f"📊 Weights: {self.weights}")
            
            # Sinal de compra probabilístico
            buy_probability = 0.0
            logger.info("📊 Iniciando cálculo de buy_probability")
            
            # Contribuição do regime
            if 'prob_EXPANSION' in signals_df.columns:
                expansion_probs = signals_df['prob_EXPANSION']
                regime_contrib = self.weights['regime_probability'] * expansion_probs
                buy_probability += regime_contrib
                logger.info(f"📊 Regime contribution: {regime_contrib.mean():.3f} (mean)")
            else:
                logger.warning("⚠️ Coluna 'prob_EXPANSION' não encontrada")
            
            # Contribuição da curva de juros
            if 'yield_combined_signal' in signals_df.columns:
                yield_signal = signals_df['yield_combined_signal']
                yield_contribution = np.where(yield_signal > 0, yield_signal, 0)
                buy_probability += self.weights['yield_curve'] * yield_contribution
                logger.info(f"📊 Yield contribution: {np.mean(yield_contribution):.3f} (mean)")
            else:
                logger.warning("⚠️ Coluna 'yield_combined_signal' não encontrada")
            
            # Contribuição do momentum
            if 'regime_confidence' in signals_df.columns:
                momentum_contribution = signals_df['regime_confidence']
                buy_probability += self.weights['momentum'] * momentum_contribution
                logger.info(f"📊 Momentum contribution: {momentum_contribution.mean():.3f} (mean)")
            else:
                logger.warning("⚠️ Coluna 'regime_confidence' não encontrada")
            
            # Sinal de venda probabilístico
            sell_probability = 0.0
            
            # Contribuição do regime
            if 'prob_RECESSION' in signals_df.columns:
                sell_probability += self.weights['regime_probability'] * signals_df['prob_RECESSION']
            
            # Contribuição da curva de juros
            if 'yield_combined_signal' in signals_df.columns:
                yield_signal = signals_df['yield_combined_signal']
                yield_contribution = np.where(yield_signal < 0, -yield_signal, 0)
                sell_probability += self.weights['yield_curve'] * yield_contribution
            
            # Sinais finais
            logger.info(f"📊 Buy probability type: {type(buy_probability)}")
            logger.info(f"📊 Sell probability type: {type(sell_probability)}")
            
            if hasattr(buy_probability, 'min'):
                logger.info(f"📊 Buy probability range: {buy_probability.min():.3f} a {buy_probability.max():.3f}")
            else:
                logger.info(f"📊 Buy probability value: {buy_probability}")
                
            if hasattr(sell_probability, 'min'):
                logger.info(f"📊 Sell probability range: {sell_probability.min():.3f} a {sell_probability.max():.3f}")
            else:
                logger.info(f"📊 Sell probability value: {sell_probability}")
                
            logger.info(f"📊 Confidence threshold: {self.confidence_threshold}")
            
            signals_df['buy_probability'] = buy_probability
            signals_df['sell_probability'] = sell_probability
            signals_df['net_signal'] = buy_probability - sell_probability
            
            # Sinais binários
            buy_condition = buy_probability > self.confidence_threshold
            sell_condition = sell_probability > self.confidence_threshold
            hold_condition = (buy_probability <= self.confidence_threshold) & (sell_probability <= self.confidence_threshold)
            
            logger.info(f"📊 Buy condition type: {type(buy_condition)}")
            logger.info(f"📊 Buy condition shape: {buy_condition.shape if hasattr(buy_condition, 'shape') else 'N/A'}")
            
            signals_df['buy_signal'] = buy_condition.astype(int)
            signals_df['sell_signal'] = sell_condition.astype(int)
            signals_df['hold_signal'] = hold_condition.astype(int)
            
            # Sinal final
            signals_df['final_signal'] = 0
            signals_df.loc[signals_df['buy_signal'] == 1, 'final_signal'] = 1
            signals_df.loc[signals_df['sell_signal'] == 1, 'final_signal'] = -1
            
            logger.info(f"✅ Sinais calculados: {signals_df.shape}")
            logger.info(f"📊 Buy signals: {signals_df['buy_signal'].sum()}")
            logger.info(f"📊 Sell signals: {signals_df['sell_signal'].sum()}")
            logger.info(f"📊 Hold signals: {signals_df['hold_signal'].sum()}")
            
            return signals_df
            
        except Exception as e:
            logger.error(f"Erro ao calcular sinais probabilísticos: {e}")
            return signals_df
    
    def _apply_regime_confirmation(self, signals_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica confirmação de regime para reduzir over-trading
        """
        try:
            logger.info("🔒 DEBUG: Aplicando confirmação de regime")
            logger.info(f"📊 Signals shape: {signals_df.shape}")
            logger.info(f"📊 Columns: {list(signals_df.columns)}")
            
            confirmed_signals = signals_df.copy()
            
            # Verificar se a coluna existe
            if 'most_likely_regime' not in confirmed_signals.columns:
                logger.warning("⚠️ Coluna 'most_likely_regime' não encontrada, pulando confirmação")
                return confirmed_signals
            
            logger.info(f"🔒 Aplicando confirmação de regime com {self.regime_confirmation_months} meses")
            
            # Aplicar confirmação de regime
            for i in range(len(confirmed_signals)):
                if i < self.regime_confirmation_months:
                    continue
                
                # Verificar estabilidade do regime
                recent_regimes = confirmed_signals['most_likely_regime'].iloc[i-self.regime_confirmation_months:i+1]
                regime_stable = len(recent_regimes.unique()) == 1
                
                if not regime_stable:
                    # Se regime não estável, manter HOLD
                    confirmed_signals.loc[confirmed_signals.index[i], 'final_signal'] = 0
                    logger.debug(f"🔒 Regime instável no ponto {i}, sinal alterado para HOLD")
            
            logger.info("✅ Confirmação de regime aplicada com sucesso")
            return confirmed_signals
            
        except Exception as e:
            logger.error(f"❌ ERRO na confirmação de regime: {e}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return signals_df
    
    def _calculate_hrp_allocation(self, 
                                 asset_returns: pd.DataFrame, 
                                 signals_df: pd.DataFrame) -> Dict:
        """
        Calcula alocação HRP baseada nos sinais
        """
        try:
            # Preparar dados para HRP
            returns_clean = asset_returns.dropna()
            
            if returns_clean.empty:
                return {'error': 'Dados de retorno insuficientes'}
            
            # Calcular alocação HRP
            hrp_results = self.hrp_allocator.allocate_portfolio(returns_clean)
            
            return hrp_results
            
        except Exception as e:
            logger.error(f"Erro na alocação HRP: {e}")
            return {'error': str(e)}
    
    def _generate_signal_summary(self, 
                                signals_df: pd.DataFrame, 
                                hrp_allocation: Dict,
                                markov_results: Dict) -> Dict:
        """
        Gera resumo dos sinais
        """
        try:
            logger.info("📋 DEBUG: Gerando resumo dos sinais")
            logger.info(f"📊 Signals shape: {signals_df.shape}")
            logger.info(f"📊 Signals columns: {list(signals_df.columns)}")
            logger.info(f"💰 HRP allocation keys: {list(hrp_allocation.keys())}")
            logger.info(f"🧠 Markov results keys: {list(markov_results.keys())}")
            
            if signals_df.empty:
                logger.error("❌ DataFrame de sinais vazio")
                return {'error': 'Nenhum sinal gerado'}
            
            # Estatísticas básicas
            total_signals = len(signals_df)
            logger.info(f"📊 Total signals: {total_signals}")
            
            # Verificar se as colunas existem antes de acessá-las
            buy_signals = signals_df['buy_signal'].sum() if 'buy_signal' in signals_df.columns else 0
            sell_signals = signals_df['sell_signal'].sum() if 'sell_signal' in signals_df.columns else 0
            hold_signals = signals_df['hold_signal'].sum() if 'hold_signal' in signals_df.columns else 0
            
            logger.info(f"📊 Buy signals: {buy_signals}")
            logger.info(f"📊 Sell signals: {sell_signals}")
            logger.info(f"📊 Hold signals: {hold_signals}")
            
            # Confiança média
            avg_confidence = signals_df['regime_confidence'].mean() if 'regime_confidence' in signals_df.columns else 0
            
            # Probabilidades médias
            avg_buy_prob = signals_df['buy_probability'].mean()
            avg_sell_prob = signals_df['sell_probability'].mean()
            
            # Resumo dos regimes
            regime_summary = {}
            if 'regime_names' in markov_results:
                for regime_name in markov_results['regime_names']:
                    prob_col = f'prob_{regime_name}'
                    if prob_col in signals_df.columns:
                        regime_summary[regime_name] = {
                            'avg_probability': float(signals_df[prob_col].mean()),
                            'max_probability': float(signals_df[prob_col].max()),
                            'frequency': float((signals_df[prob_col] > 0.5).sum() / total_signals)
                        }
            
            summary = {
                'total_signals': total_signals,
                'buy_signals': int(buy_signals),
                'sell_signals': int(sell_signals),
                'hold_signals': int(hold_signals),
                'buy_percentage': float(buy_signals / total_signals * 100),
                'sell_percentage': float(sell_signals / total_signals * 100),
                'hold_percentage': float(hold_signals / total_signals * 100),
                'avg_confidence': float(avg_confidence),
                'avg_buy_probability': float(avg_buy_prob),
                'avg_sell_probability': float(avg_sell_prob),
                'regime_summary': regime_summary,
                'hrp_allocation': hrp_allocation.get('allocation', {}),
                'hrp_metrics': hrp_allocation.get('metrics', {})
            }
            
            logger.info(f"✅ Resumo gerado com sucesso: {len(summary)} métricas")
            logger.info(f"📊 Total signals: {summary['total_signals']}")
            logger.info(f"📊 Buy percentage: {summary['buy_percentage']:.1f}%")
            logger.info(f"📊 Sell percentage: {summary['sell_percentage']:.1f}%")
            logger.info(f"🎯 Avg confidence: {summary['avg_confidence']:.3f}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ ERRO ao gerar resumo: {e}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return {'error': str(e)}
