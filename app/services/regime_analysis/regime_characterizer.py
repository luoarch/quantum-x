"""
Caracterizador de Regimes Econômicos
Identifica e caracteriza regimes baseado em dados, não em definições a priori
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .interfaces import IRegimeCharacterizer, RegimeCharacteristics, RegimeType

logger = logging.getLogger(__name__)


class ScientificRegimeCharacterizer(IRegimeCharacterizer):
    """
    Caracterizador científico de regimes econômicos
    Identifica características emergentes dos dados
    """
    
    def __init__(self, confidence_threshold: float = 0.6):
        """
        Inicializa o caracterizador
        
        Args:
            confidence_threshold: Limiar de confiança para identificação de regimes
        """
        self.confidence_threshold = confidence_threshold
        self.scaler = StandardScaler()
        
        # Mapeamento de características para tipos de regime
        self.regime_patterns = {
            'recession': {
                'gdp_growth': (-np.inf, 0.0),
                'unemployment': (8.0, np.inf),
                'inflation': (6.0, np.inf),
                'cli': (-np.inf, 95.0)
            },
            'recovery': {
                'gdp_growth': (0.0, 3.0),
                'unemployment': (6.0, 8.0),
                'inflation': (4.0, 6.0),
                'cli': (95.0, 100.0)
            },
            'expansion': {
                'gdp_growth': (3.0, np.inf),
                'unemployment': (0.0, 6.0),
                'inflation': (0.0, 4.0),
                'cli': (100.0, np.inf)
            },
            'contraction': {
                'gdp_growth': (0.0, 2.0),
                'unemployment': (6.0, 8.0),
                'inflation': (2.0, 4.0),
                'cli': (95.0, 100.0)
            }
        }
    
    async def characterize_regimes(self, model: Any, data: pd.DataFrame) -> Dict[RegimeType, RegimeCharacteristics]:
        """
        Caracteriza regimes baseado nos dados e modelo
        
        Args:
            model: Modelo ajustado
            data: Dados econômicos
            
        Returns:
            Dicionário com características de cada regime
        """
        try:
            logger.info("🔍 Caracterizando regimes baseado nos dados")
            
            # Obter sequência de regimes
            regime_sequence = await self._get_regime_sequence(model, data)
            
            if regime_sequence is None:
                logger.warning("⚠️ Não foi possível obter sequência de regimes")
                return {}
            
            # Caracterizar cada regime
            regime_characteristics = {}
            
            for regime_id in range(model.k_regimes if hasattr(model, 'k_regimes') else 2):
                characteristics = await self._characterize_single_regime(
                    regime_id, regime_sequence, data, model
                )
                
                if characteristics:
                    regime_characteristics[RegimeType(characteristics['name'])] = characteristics
            
            logger.info(f"✅ {len(regime_characteristics)} regimes caracterizados")
            return regime_characteristics
            
        except Exception as e:
            logger.error(f"❌ Erro ao caracterizar regimes: {e}")
            return {}
    
    async def identify_regime_name(self, characteristics: Dict[str, float]) -> RegimeType:
        """
        Identifica nome do regime baseado nas características
        
        Args:
            characteristics: Dicionário com características do regime
            
        Returns:
            Tipo do regime identificado
        """
        try:
            # Calcular scores para cada padrão de regime
            scores = {}
            
            for regime_name, patterns in self.regime_patterns.items():
                score = 0.0
                total_indicators = 0
                
                for indicator, (min_val, max_val) in patterns.items():
                    if indicator in characteristics:
                        value = characteristics[indicator]
                        
                        # Verificar se valor está dentro do range
                        if min_val <= value <= max_val:
                            score += 1.0
                        else:
                            # Penalizar distância do range
                            if value < min_val:
                                penalty = (min_val - value) / abs(min_val) if min_val != 0 else 0
                            else:
                                penalty = (value - max_val) / max_val if max_val != np.inf else 0
                            
                            score += max(0, 1.0 - penalty)
                        
                        total_indicators += 1
                
                if total_indicators > 0:
                    scores[regime_name] = score / total_indicators
                else:
                    scores[regime_name] = 0.0
            
            # Selecionar regime com maior score
            best_regime = max(scores.keys(), key=lambda k: scores[k])
            
            # Verificar se confiança é suficiente
            if scores[best_regime] < self.confidence_threshold:
                logger.warning(f"⚠️ Confiança baixa para regime {best_regime}: {scores[best_regime]:.2f}")
                return RegimeType.UNKNOWN
            
            logger.info(f"🎯 Regime identificado: {best_regime} (confiança: {scores[best_regime]:.2f})")
            return RegimeType(best_regime)
            
        except Exception as e:
            logger.error(f"❌ Erro ao identificar regime: {e}")
            return RegimeType.UNKNOWN
    
    async def _get_regime_sequence(self, model: Any, data: pd.DataFrame) -> Optional[np.ndarray]:
        """Obtém sequência de regimes do modelo"""
        try:
            if hasattr(model, 'smoothed_marginal_probabilities'):
                regime_probs = model.smoothed_marginal_probabilities
                return np.argmax(regime_probs, axis=1)
            elif hasattr(model, 'regime_probabilities'):
                regime_probs = model.regime_probabilities
                return np.argmax(regime_probs, axis=1)
            else:
                logger.warning("⚠️ Modelo não possui probabilidades de regime")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter sequência de regimes: {e}")
            return None
    
    async def _characterize_single_regime(self, regime_id: int, regime_sequence: np.ndarray, 
                                        data: pd.DataFrame, model: Any) -> Optional[RegimeCharacteristics]:
        """Caracteriza um regime específico"""
        try:
            # Identificar períodos neste regime
            regime_mask = regime_sequence == regime_id
            regime_data = data[regime_mask]
            
            if len(regime_data) == 0:
                logger.warning(f"⚠️ Regime {regime_id} não possui dados")
                return None
            
            # Calcular estatísticas descritivas
            mean_values = {}
            std_values = {}
            
            for column in regime_data.columns:
                if column != 'date' and pd.api.types.is_numeric_dtype(regime_data[column]):
                    mean_values[column] = float(regime_data[column].mean())
                    std_values[column] = float(regime_data[column].std())
            
            # Calcular duração e frequência
            duration_months = int(np.sum(regime_mask))
            frequency = float(np.mean(regime_mask))
            
            # Calcular confiança baseada na estabilidade do regime
            confidence = await self._calculate_regime_confidence(regime_id, regime_sequence, model)
            
            # Identificar nome do regime
            regime_name = await self.identify_regime_name(mean_values)
            
            # Obter períodos típicos
            typical_periods = regime_data.index.astype(str).tolist()[:5]
            
            return RegimeCharacteristics(
                name=regime_name.value,
                duration_months=duration_months,
                frequency=frequency,
                mean_values=mean_values,
                std_values=std_values,
                confidence=confidence,
                typical_periods=typical_periods
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao caracterizar regime {regime_id}: {e}")
            return None
    
    async def _calculate_regime_confidence(self, regime_id: int, regime_sequence: np.ndarray, 
                                         model: Any) -> float:
        """Calcula confiança na identificação do regime"""
        try:
            # Confiança baseada na estabilidade do regime
            regime_mask = regime_sequence == regime_id
            regime_periods = np.where(regime_mask)[0]
            
            if len(regime_periods) == 0:
                return 0.0
            
            # Calcular estabilidade (períodos consecutivos)
            stability = self._calculate_regime_stability(regime_periods)
            
            # Confiança baseada nas probabilidades do modelo
            model_confidence = 0.0
            if hasattr(model, 'smoothed_marginal_probabilities'):
                regime_probs = model.smoothed_marginal_probabilities[regime_mask, regime_id]
                model_confidence = float(np.mean(regime_probs))
            
            # Combinar estabilidade e confiança do modelo
            combined_confidence = (stability + model_confidence) / 2
            
            return min(max(combined_confidence, 0.0), 1.0)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular confiança do regime {regime_id}: {e}")
            return 0.0
    
    def _calculate_regime_stability(self, regime_periods: np.ndarray) -> float:
        """Calcula estabilidade do regime baseado em períodos consecutivos"""
        try:
            if len(regime_periods) <= 1:
                return 0.0
            
            # Calcular duração média dos períodos consecutivos
            consecutive_periods = []
            current_length = 1
            
            for i in range(1, len(regime_periods)):
                if regime_periods[i] == regime_periods[i-1] + 1:
                    current_length += 1
                else:
                    consecutive_periods.append(current_length)
                    current_length = 1
            
            consecutive_periods.append(current_length)
            
            # Estabilidade baseada na duração média dos períodos consecutivos
            avg_consecutive = np.mean(consecutive_periods)
            max_consecutive = np.max(consecutive_periods)
            
            # Normalizar para 0-1
            stability = min(avg_consecutive / 10.0, 1.0)  # Assumir que 10+ períodos consecutivos = estabilidade máxima
            
            return stability
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular estabilidade: {e}")
            return 0.0
    
    async def _analyze_regime_transitions(self, regime_sequence: np.ndarray) -> Dict[str, Any]:
        """Analisa transições entre regimes"""
        try:
            if len(regime_sequence) < 2:
                return {'error': 'Sequência muito curta'}
            
            # Calcular matriz de transição
            n_regimes = len(np.unique(regime_sequence))
            transition_matrix = np.zeros((n_regimes, n_regimes))
            
            for i in range(len(regime_sequence) - 1):
                from_regime = regime_sequence[i]
                to_regime = regime_sequence[i + 1]
                transition_matrix[from_regime, to_regime] += 1
            
            # Normalizar para probabilidades
            row_sums = transition_matrix.sum(axis=1)
            for i in range(n_regimes):
                if row_sums[i] > 0:
                    transition_matrix[i, :] /= row_sums[i]
            
            # Calcular métricas de transição
            persistence = np.diag(transition_matrix)
            avg_persistence = np.mean(persistence)
            
            return {
                'transition_matrix': transition_matrix.tolist(),
                'persistence': persistence.tolist(),
                'avg_persistence': float(avg_persistence),
                'n_transitions': int(np.sum(transition_matrix) - np.sum(persistence))
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar transições: {e}")
            return {'error': str(e)}
    
    async def _detect_regime_anomalies(self, regime_sequence: np.ndarray, 
                                     data: pd.DataFrame) -> Dict[str, Any]:
        """Detecta anomalias na identificação de regimes"""
        try:
            anomalies = []
            
            # Detectar mudanças muito frequentes
            changes = np.sum(regime_sequence[1:] != regime_sequence[:-1])
            change_rate = changes / len(regime_sequence)
            
            if change_rate > 0.5:  # Mais de 50% de mudanças
                anomalies.append({
                    'type': 'high_frequency_changes',
                    'value': change_rate,
                    'description': f'Taxa de mudança muito alta: {change_rate:.2%}'
                })
            
            # Detectar regimes muito curtos
            regime_durations = []
            current_regime = regime_sequence[0]
            current_duration = 1
            
            for i in range(1, len(regime_sequence)):
                if regime_sequence[i] == current_regime:
                    current_duration += 1
                else:
                    regime_durations.append(current_duration)
                    current_regime = regime_sequence[i]
                    current_duration = 1
            
            regime_durations.append(current_duration)
            
            short_regimes = [d for d in regime_durations if d < 3]
            if len(short_regimes) > len(regime_durations) * 0.3:
                anomalies.append({
                    'type': 'short_regimes',
                    'value': len(short_regimes),
                    'description': f'Muitos regimes curtos: {len(short_regimes)}/{len(regime_durations)}'
                })
            
            return {
                'anomalies': anomalies,
                'change_rate': change_rate,
                'avg_regime_duration': np.mean(regime_durations),
                'min_regime_duration': np.min(regime_durations),
                'max_regime_duration': np.max(regime_durations)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao detectar anomalias: {e}")
            return {'error': str(e)}
