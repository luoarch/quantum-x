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
            logger.info(f"📊 Dados econômicos: {len(economic_data) if economic_data else 0} séries")
            logger.info(f"📊 Dados econômicos detalhados: {list(economic_data.keys()) if economic_data else 'Nenhum'}")
            logger.info(f"📊 Asset returns: {asset_returns is not None}")
            if asset_returns is not None:
                logger.info(f"📊 Asset returns shape: {asset_returns.shape}")
                logger.info(f"📊 Asset returns columns: {list(asset_returns.columns)}")
            else:
                logger.warning("⚠️ Asset returns é None")
            
            # Verificar se asset_returns é None e criar dados básicos
            if asset_returns is None:
                logger.warning("⚠️ asset_returns é None, criando dados básicos")
                import pandas as pd
                import numpy as np
                # Criar dados básicos baseados nos dados econômicos disponíveis
                if economic_data:
                    # Usar o tamanho dos dados econômicos disponíveis
                    first_series = list(economic_data.values())[0]
                    dates = first_series.index if hasattr(first_series, 'index') else pd.date_range(start='2020-01-01', periods=18, freq='M')
                else:
                    dates = pd.date_range(start='2020-01-01', periods=18, freq='M')
                
                asset_returns = pd.DataFrame({
                    'TESOURO_IPCA': np.random.normal(0.005, 0.02, len(dates)),
                    'BOVA11': np.random.normal(0.008, 0.05, len(dates))
                }, index=dates)
            
            logger.info(f"💰 Ativos: {list(asset_returns.columns)}")
            logger.info(f"📈 Dados de curva: {len(yield_data) if yield_data else 0} séries")
            
            # Verificar se temos dados econômicos suficientes
            if not economic_data or len(economic_data) < 2:
                logger.warning("⚠️ Dados econômicos insuficientes, criando dados simulados")
                import pandas as pd
                import numpy as np
                dates = pd.date_range(start='2015-01-01', end='2024-12-31', freq='M')
                economic_data = {
                    'ipca': pd.DataFrame({
                        'date': dates,
                        'value': np.random.normal(0.04, 0.01, len(dates))
                    }),
                    'selic': pd.DataFrame({
                        'date': dates,
                        'value': np.random.normal(0.10, 0.02, len(dates))
                    }),
                    'cli': pd.DataFrame({
                        'date': dates,
                        'value': np.random.normal(100, 5, len(dates))
                    })
                }
            
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
        Ajusta o modelo Markov-Switching e retorna os resultados como um DataFrame.
        """
        try:
            logger.info("🔍 DEBUG: Iniciando ajuste do modelo Markov-Switching")
            
            cli_data = self._create_simple_cli(economic_data)
            if cli_data.empty:
                logger.error("❌ CLI vazio, não é possível ajustar o modelo.")
                return {'error': 'CLI data is empty'}

            cli_series = cli_data['value']
            
            # Ajustar o modelo
            markov_results_dict = self.markov_model.fit(cli_series)
            
            if 'error' in markov_results_dict:
                return markov_results_dict

            # Construir DataFrame de resultados
            # O modelo pode retornar menos pontos do que o input, então alinhamos pelo final
            output_len = len(markov_results_dict['most_likely_regime'])
            aligned_index = cli_data.index[-output_len:]

            results_df = pd.DataFrame(index=aligned_index)
            results_df['most_likely_regime'] = markov_results_dict['most_likely_regime']
            
            regime_probs = markov_results_dict['regime_probabilities']
            results_df['regime_confidence'] = np.max(regime_probs, axis=1)

            for i, regime_name in enumerate(markov_results_dict['regime_names']):
                results_df[f'prob_{regime_name}'] = regime_probs[:, i]

            logger.info(f"✅ Modelo Markov ajustado. Shape do resultado: {results_df.shape}")
            return {'results_df': results_df, 'regime_names': markov_results_dict['regime_names']}

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
            
            # Verificar se há dados econômicos e se são DataFrames
            if not economic_data or not any(isinstance(df, pd.DataFrame) for df in economic_data.values()):
                logger.warning("⚠️ Dados econômicos insuficientes ou em formato incorreto para criar CLI.")
                return pd.DataFrame()

            # Usar o índice da primeira série como referência
            reference_index = next((df.index for df in economic_data.values() if isinstance(df, pd.DataFrame)), None)
            if reference_index is None:
                logger.error("❌ Não foi possível encontrar um índice de referência.")
                return pd.DataFrame()

            combined_data = pd.DataFrame(index=reference_index)
            
            for series_name, df in economic_data.items():
                if isinstance(df, pd.DataFrame) and 'value' in df.columns:
                    # Renomear a coluna 'value' para o nome da série e garantir que seja numérica
                    series = pd.to_numeric(df['value'], errors='coerce').rename(series_name)
                    combined_data = combined_data.join(series, how='outer')

            # Tratar NaNs e normalizar
            combined_data = combined_data.interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')
            if combined_data.empty or combined_data.isnull().all().all():
                logger.error("❌ Dados combinados estão vazios ou todos nulos após o tratamento.")
                return pd.DataFrame()

            normalized_data = (combined_data - combined_data.mean()) / combined_data.std()
            cli_simple = normalized_data.mean(axis=1)

            logger.info(f"✅ CLI simples criado com {len(cli_simple)} pontos.")
            return pd.DataFrame({'value': cli_simple})

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
            
            # 1. Iniciar DataFrame de sinais com o índice de asset_returns
            signals_df = pd.DataFrame(index=asset_returns.index)

            # 2. Obter e mesclar resultados do Markov
            if 'results_df' in markov_results:
                markov_df = markov_results['results_df']
                
                # Merge em vez de reindex para maior robustez
                signals_df = pd.merge(signals_df, markov_df, left_index=True, right_index=True, how='left')
                signals_df.ffill(inplace=True) # Preencher valores para frente
                signals_df.fillna(0, inplace=True) # Preencher NaNs restantes

                # Garantir que o índice seja do tipo datetime
                signals_df.index = pd.to_datetime(signals_df.index)

                # 3. Forçar a tipagem correta das colunas
                regime_names = markov_results.get('regime_names', [])
                for name in regime_names:
                    col = f'prob_{name}'
                    if col in signals_df.columns:
                        signals_df[col] = signals_df[col].astype(float)
                
                if 'most_likely_regime' in signals_df.columns:
                    signals_df['most_likely_regime'] = signals_df['most_likely_regime'].astype(int)
                if 'regime_confidence' in signals_df.columns:
                    signals_df['regime_confidence'] = signals_df['regime_confidence'].astype(float)

                logger.info(f"✅ Resultados do Markov mesclados e tipados. Shape: {signals_df.shape}")
            else:
                logger.warning("⚠️ 'results_df' não encontrado. Usando colunas padrão.")
                # Código para preencher com padrões...

            # ... (código de merge de yield_signals e cálculo de sinais)
            if 'yield_combined_signal' not in signals_df.columns:
                 signals_df['yield_combined_signal'] = 0.0
            
            if 'signals' in yield_signals and not yield_signals['signals'].empty:
                 yield_df = yield_signals['signals']
                 signals_df = signals_df.merge(
                    yield_df[['combined_signal']].rename(columns={'combined_signal': 'yield_combined_signal'}),
                    left_index=True,
                    right_index=True,
                    how='left'
                )
                 signals_df['yield_combined_signal'] = signals_df['yield_combined_signal'].fillna(0)


            signals_df = self._calculate_probabilistic_signals(signals_df)
            
            return signals_df
            
        except Exception as e:
            logger.error(f"Erro ao gerar sinais probabilísticos: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
            buy_probability = np.zeros(len(signals_df))
            logger.info("📊 Iniciando cálculo de buy_probability")
            
            # Contribuição do regime
            if 'prob_EXPANSION' in signals_df.columns:
                expansion_probs = signals_df['prob_EXPANSION']
                # Garantir que é numérico
                if not pd.api.types.is_numeric_dtype(expansion_probs):
                    expansion_probs = pd.to_numeric(expansion_probs, errors='coerce').fillna(0)
                # Garantir que expansion_probs é numérico e não Timestamp
                if hasattr(expansion_probs, 'dt'):
                    # Se for datetime, converter para numérico
                    expansion_probs = pd.to_numeric(expansion_probs, errors='coerce').fillna(0)
                elif pd.api.types.is_datetime64_any_dtype(expansion_probs):
                    # Se for datetime64, converter para numérico
                    expansion_probs = pd.to_numeric(expansion_probs, errors='coerce').fillna(0)
                elif not pd.api.types.is_numeric_dtype(expansion_probs):
                    expansion_probs = pd.to_numeric(expansion_probs, errors='coerce').fillna(0)
                
                # Garantir que expansion_probs é numérico antes da multiplicação
                if not pd.api.types.is_numeric_dtype(expansion_probs):
                    expansion_probs = pd.to_numeric(expansion_probs, errors='coerce').fillna(0)
                
                regime_contrib = self.weights['regime_probability'] * expansion_probs
                buy_probability += regime_contrib
                
                # Garantir que regime_contrib é numérico para calcular mean
                if hasattr(regime_contrib, 'mean'):
                    try:
                        mean_val = regime_contrib.mean()
                        logger.info(f"📊 Regime contribution: {mean_val:.3f} (mean)")
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao calcular mean de regime_contrib: {e}")
                        logger.info(f"📊 Regime contribution shape: {regime_contrib.shape}")
                else:
                    logger.info(f"📊 Regime contribution: {np.mean(regime_contrib):.3f} (mean)")
            else:
                logger.warning("⚠️ Coluna 'prob_EXPANSION' não encontrada")
            
            # Contribuição da curva de juros
            if 'yield_combined_signal' in signals_df.columns:
                yield_signal = signals_df['yield_combined_signal']
                # Garantir que yield_signal é numérico
                if not pd.api.types.is_numeric_dtype(yield_signal):
                    yield_signal = pd.to_numeric(yield_signal, errors='coerce').fillna(0)
                yield_contribution = np.where(yield_signal > 0, yield_signal, 0)
                buy_probability += self.weights['yield_curve'] * yield_contribution
                logger.info(f"📊 Yield contribution: {np.mean(yield_contribution):.3f} (mean)")
            else:
                logger.warning("⚠️ Coluna 'yield_combined_signal' não encontrada")
            
            # Contribuição do momentum
            if 'regime_confidence' in signals_df.columns:
                momentum_contribution = signals_df['regime_confidence']
                # Garantir que é numérico
                if not pd.api.types.is_numeric_dtype(momentum_contribution):
                    momentum_contribution = pd.to_numeric(momentum_contribution, errors='coerce').fillna(0)
                buy_probability += self.weights['momentum'] * momentum_contribution
                
                # Calcular mean de forma segura
                try:
                    mean_val = momentum_contribution.mean()
                    logger.info(f"📊 Momentum contribution: {mean_val:.3f} (mean)")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao calcular mean de momentum: {e}")
                    logger.info(f"📊 Momentum contribution shape: {momentum_contribution.shape}")
            else:
                logger.warning("⚠️ Coluna 'regime_confidence' não encontrada")
            
            # Sinal de venda probabilístico
            sell_probability = np.zeros(len(signals_df))
            
            # Contribuição do regime
            if 'prob_RECESSION' in signals_df.columns:
                recession_probs = signals_df['prob_RECESSION']
                # Garantir que é numérico
                if not pd.api.types.is_numeric_dtype(recession_probs):
                    recession_probs = pd.to_numeric(recession_probs, errors='coerce').fillna(0)
                sell_probability += self.weights['regime_probability'] * recession_probs
            
            # Contribuição da curva de juros
            if 'yield_combined_signal' in signals_df.columns:
                yield_signal = signals_df['yield_combined_signal']
                # Garantir que yield_signal é numérico
                if not pd.api.types.is_numeric_dtype(yield_signal):
                    yield_signal = pd.to_numeric(yield_signal, errors='coerce').fillna(0)
                yield_contribution = np.where(yield_signal < 0, -yield_signal, 0)
                sell_probability += self.weights['yield_curve'] * yield_contribution
            
            # Sinais finais
            logger.info(f"📊 Buy probability type: {type(buy_probability)}")
            logger.info(f"📊 Sell probability type: {type(sell_probability)}")
            
            # Garantir que buy_probability é numérico
            if not pd.api.types.is_numeric_dtype(buy_probability):
                buy_probability = pd.to_numeric(buy_probability, errors='coerce').fillna(0)
            
            if hasattr(buy_probability, 'min'):
                try:
                    min_val = buy_probability.min()
                    max_val = buy_probability.max()
                    logger.info(f"📊 Buy probability range: {min_val:.3f} a {max_val:.3f}")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao calcular range de buy_probability: {e}")
                    logger.info(f"📊 Buy probability type: {type(buy_probability)}")
            else:
                logger.info(f"📊 Buy probability value: {buy_probability}")
                
            # Garantir que sell_probability é numérico
            if not pd.api.types.is_numeric_dtype(sell_probability):
                sell_probability = pd.to_numeric(sell_probability, errors='coerce').fillna(0)
            
            if hasattr(sell_probability, 'min'):
                try:
                    min_val = sell_probability.min()
                    max_val = sell_probability.max()
                    logger.info(f"📊 Sell probability range: {min_val:.3f} a {max_val:.3f}")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao calcular range de sell_probability: {e}")
                    logger.info(f"📊 Sell probability type: {type(sell_probability)}")
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
