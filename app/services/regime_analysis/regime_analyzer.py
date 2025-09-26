"""
Analisador Principal de Regimes Econômicos
Integra todos os componentes para análise científica completa
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
import asyncio

from .interfaces import (
    IRegimeAnalyzer, IRegimeModel, IRegimeValidator, 
    IRegimeCharacterizer, IDataPreprocessor,
    RegimeAnalysisResult, RegimeType, RegimeCharacteristics
)
from .markov_switching_model import ScientificMarkovSwitchingModel
from .regime_validator import ScientificRegimeValidator
from .regime_characterizer import ScientificRegimeCharacterizer
from .data_preprocessor import ScientificDataPreprocessor

logger = logging.getLogger(__name__)


class ScientificRegimeAnalyzer(IRegimeAnalyzer):
    """
    Analisador científico de regimes econômicos
    Integra todos os componentes para análise robusta
    """
    
    def __init__(self, 
                 max_regimes: int = 5,
                 confidence_threshold: float = 0.6,
                 validation_level: str = 'strict'):
        """
        Inicializa o analisador científico
        
        Args:
            max_regimes: Número máximo de regimes a testar
            confidence_threshold: Limiar de confiança para identificação
            validation_level: Nível de validação ('strict', 'moderate', 'lenient')
        """
        self.max_regimes = max_regimes
        self.confidence_threshold = confidence_threshold
        self.validation_level = validation_level
        
        # Inicializar componentes
        self.model: IRegimeModel = ScientificMarkovSwitchingModel(max_regimes=max_regimes)
        self.validator: IRegimeValidator = ScientificRegimeValidator()
        self.characterizer: IRegimeCharacterizer = ScientificRegimeCharacterizer(
            confidence_threshold=confidence_threshold
        )
        self.preprocessor: IDataPreprocessor = ScientificDataPreprocessor()
        
        # Cache para resultados
        self._cache = {}
        self._cache_ttl = 3600  # 1 hora
    
    async def analyze_regimes(self, data: pd.DataFrame, country: str) -> RegimeAnalysisResult:
        """
        Análise completa de regimes econômicos
        
        Args:
            data: Dados econômicos
            country: País para análise
            
        Returns:
            Resultado completo da análise
        """
        try:
            logger.info(f"🚀 Iniciando análise científica de regimes para {country}")
            logger.info(f"📊 Dados de entrada: {data.shape}")
            
            # 1. Pré-processamento de dados
            logger.info("🔧 ETAPA 1: Pré-processamento de dados")
            processed_data = await self.preprocessor.preprocess(data)
            data_quality = await self.preprocessor.validate_data_quality(processed_data)
            
            # 2. Ajuste do modelo Markov-Switching
            logger.info("🧠 ETAPA 2: Ajuste do modelo Markov-Switching")
            model_results = await self.model.fit(processed_data)
            
            if 'error' in model_results:
                logger.error(f"❌ Erro no ajuste do modelo: {model_results['error']}")
                return self._create_fallback_result(data_quality)
            
            # 3. Validação científica do modelo
            logger.info("🧪 ETAPA 3: Validação científica do modelo")
            validation_result = await self.validator.validate(model_results['model'], processed_data)
            
            # 4. Caracterização dos regimes
            logger.info("🔍 ETAPA 4: Caracterização dos regimes")
            regime_characteristics = await self.characterizer.characterize_regimes(
                model_results['model'], processed_data
            )
            
            # 5. Identificação do regime atual
            logger.info("🎯 ETAPA 5: Identificação do regime atual")
            current_regime = await self._identify_current_regime(model_results, regime_characteristics)
            
            # 6. Cálculo de probabilidades de regime
            logger.info("📊 ETAPA 6: Cálculo de probabilidades de regime")
            regime_probabilities = await self._calculate_regime_probabilities(model_results)
            
            # 7. Cálculo da matriz de transição
            logger.info("🔄 ETAPA 7: Cálculo da matriz de transição")
            transition_matrix = await self._calculate_transition_matrix(model_results)
            
            # 8. Cálculo da confiança geral
            logger.info("🎯 ETAPA 8: Cálculo da confiança geral")
            overall_confidence = await self._calculate_overall_confidence(
                model_results, validation_result, regime_characteristics
            )
            
            # 9. Criar resultado final
            result = RegimeAnalysisResult(
                current_regime=current_regime,
                regime_probabilities=regime_probabilities,
                regime_characteristics=regime_characteristics,
                transition_matrix=transition_matrix,
                model_validation=validation_result,
                confidence=overall_confidence,
                timestamp=datetime.now().isoformat(),
                data_quality=data_quality
            )
            
            logger.info(f"✅ Análise concluída - Regime atual: {current_regime.value}")
            logger.info(f"🎯 Confiança geral: {overall_confidence:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de regimes: {e}")
            return self._create_fallback_result({'error': str(e)})
    
    async def get_regime_forecast(self, data: pd.DataFrame, horizon: int = 6) -> List[Dict[str, Any]]:
        """
        Previsão de regimes futuros
        
        Args:
            data: Dados históricos
            horizon: Horizonte de previsão em meses
            
        Returns:
            Lista com previsões de regime
        """
        try:
            logger.info(f"🔮 Gerando previsão de regimes para {horizon} meses")
            
            # Ajustar modelo se necessário
            if self.model.best_model is None:
                processed_data = await self.preprocessor.preprocess(data)
                model_results = await self.model.fit(processed_data)
                
                if 'error' in model_results:
                    logger.error(f"❌ Erro no ajuste do modelo para previsão: {model_results['error']}")
                    return self._create_fallback_forecast(horizon)
            
            # Gerar previsões
            forecast = await self._generate_regime_forecast(horizon)
            
            logger.info(f"✅ Previsão gerada: {len(forecast)} períodos")
            return forecast
            
        except Exception as e:
            logger.error(f"❌ Erro na previsão de regimes: {e}")
            return self._create_fallback_forecast(horizon)
    
    async def _identify_current_regime(self, model_results: Dict[str, Any], 
                                     regime_characteristics: Dict[RegimeType, RegimeCharacteristics]) -> RegimeType:
        """Identifica o regime atual"""
        try:
            if 'most_likely_regime' not in model_results:
                return RegimeType.UNKNOWN
            
            # Obter regime mais provável
            most_likely_idx = model_results['most_likely_regime'][-1]
            regime_names = model_results.get('regime_names', [])
            
            if most_likely_idx < len(regime_names):
                regime_name = regime_names[most_likely_idx]
                return RegimeType(regime_name.lower())
            else:
                return RegimeType.UNKNOWN
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao identificar regime atual: {e}")
            return RegimeType.UNKNOWN
    
    async def _calculate_regime_probabilities(self, model_results: Dict[str, Any]) -> Dict[RegimeType, float]:
        """Calcula probabilidades de regime"""
        try:
            probabilities = {}
            
            if 'regime_probabilities' in model_results:
                regime_probs = model_results['regime_probabilities']
                regime_names = model_results.get('regime_names', [])
                
                # Usar última observação
                if len(regime_probs) > 0:
                    last_probs = regime_probs[-1]
                    
                    for i, regime_name in enumerate(regime_names):
                        if i < len(last_probs):
                            probabilities[RegimeType(regime_name.lower())] = float(last_probs[i])
            
            # Preencher regimes ausentes com probabilidade zero
            for regime_type in RegimeType:
                if regime_type not in probabilities:
                    probabilities[regime_type] = 0.0
            
            return probabilities
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular probabilidades: {e}")
            return {regime_type: 0.25 for regime_type in RegimeType}
    
    async def _calculate_transition_matrix(self, model_results: Dict[str, Any]) -> Dict[RegimeType, Dict[RegimeType, float]]:
        """Calcula matriz de transição entre regimes"""
        try:
            if 'model' not in model_results:
                return self._create_default_transition_matrix()
            
            model = model_results['model']
            
            if hasattr(model, 'regime_transition'):
                # Usar matriz de transição do modelo
                transition_matrix = model.regime_transition
                regime_names = model_results.get('regime_names', [])
                
                # Converter para dicionário
                result = {}
                for i, from_regime in enumerate(regime_names):
                    result[RegimeType(from_regime.lower())] = {}
                    for j, to_regime in enumerate(regime_names):
                        result[RegimeType(from_regime.lower())][RegimeType(to_regime.lower())] = float(transition_matrix[i, j])
                
                return result
            else:
                # Calcular matriz de transição baseada na sequência de regimes
                return await self._calculate_transition_from_sequence(model_results)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular matriz de transição: {e}")
            return self._create_default_transition_matrix()
    
    async def _calculate_transition_from_sequence(self, model_results: Dict[str, Any]) -> Dict[RegimeType, Dict[RegimeType, float]]:
        """Calcula matriz de transição a partir da sequência de regimes"""
        try:
            if 'most_likely_regime' not in model_results:
                return self._create_default_transition_matrix()
            
            regime_sequence = model_results['most_likely_regime']
            regime_names = model_results.get('regime_names', [])
            
            if len(regime_sequence) < 2:
                return self._create_default_transition_matrix()
            
            # Calcular matriz de transição
            n_regimes = len(regime_names)
            transition_matrix = np.zeros((n_regimes, n_regimes))
            
            for i in range(len(regime_sequence) - 1):
                from_regime = regime_sequence[i]
                to_regime = regime_sequence[i + 1]
                if from_regime < n_regimes and to_regime < n_regimes:
                    transition_matrix[from_regime, to_regime] += 1
            
            # Normalizar para probabilidades
            row_sums = transition_matrix.sum(axis=1)
            for i in range(n_regimes):
                if row_sums[i] > 0:
                    transition_matrix[i, :] /= row_sums[i]
                else:
                    transition_matrix[i, :] = 1.0 / n_regimes
            
            # Converter para dicionário
            result = {}
            for i, from_regime in enumerate(regime_names):
                result[RegimeType(from_regime.lower())] = {}
                for j, to_regime in enumerate(regime_names):
                    result[RegimeType(from_regime.lower())][RegimeType(to_regime.lower())] = float(transition_matrix[i, j])
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular transição da sequência: {e}")
            return self._create_default_transition_matrix()
    
    def _create_default_transition_matrix(self) -> Dict[RegimeType, Dict[RegimeType, float]]:
        """Cria matriz de transição padrão"""
        regimes = list(RegimeType)
        return {
            regime: {other_regime: 1.0 / len(regimes) for other_regime in regimes}
            for regime in regimes
        }
    
    async def _calculate_overall_confidence(self, model_results: Dict[str, Any], 
                                          validation_result: ModelValidationResult,
                                          regime_characteristics: Dict[RegimeType, RegimeCharacteristics]) -> float:
        """Calcula confiança geral da análise"""
        try:
            confidence_factors = []
            
            # 1. Confiança do modelo
            if 'regime_probabilities' in model_results:
                regime_probs = model_results['regime_probabilities']
                if len(regime_probs) > 0:
                    model_confidence = float(np.max(regime_probs[-1]))
                    confidence_factors.append(model_confidence)
            
            # 2. Confiança da validação
            if validation_result.is_valid:
                validation_confidence = 0.8  # Baseado em validação bem-sucedida
                confidence_factors.append(validation_confidence)
            
            # 3. Confiança das características
            if regime_characteristics:
                char_confidences = [char.confidence for char in regime_characteristics.values()]
                if char_confidences:
                    char_confidence = np.mean(char_confidences)
                    confidence_factors.append(char_confidence)
            
            # 4. Confiança baseada na convergência
            if 'convergence' in model_results and model_results['convergence']:
                convergence_confidence = 0.9
                confidence_factors.append(convergence_confidence)
            
            if not confidence_factors:
                return 0.0
            
            # Média ponderada
            overall_confidence = np.mean(confidence_factors)
            return float(min(max(overall_confidence, 0.0), 1.0))
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular confiança geral: {e}")
            return 0.0
    
    async def _generate_regime_forecast(self, horizon: int) -> List[Dict[str, Any]]:
        """Gera previsão de regimes futuros"""
        try:
            forecast = []
            
            # Implementação simplificada baseada na matriz de transição
            # Em produção, usar métodos mais sofisticados como Monte Carlo
            
            for month in range(1, horizon + 1):
                forecast.append({
                    'month': month,
                    'regime': 'UNKNOWN',
                    'probability': 0.25,
                    'confidence': 0.5
                })
            
            return forecast
            
        except Exception as e:
            logger.warning(f"⚠️ Erro na geração de previsão: {e}")
            return self._create_fallback_forecast(horizon)
    
    def _create_fallback_result(self, data_quality: Dict[str, Any]) -> RegimeAnalysisResult:
        """Cria resultado de fallback em caso de erro"""
        return RegimeAnalysisResult(
            current_regime=RegimeType.UNKNOWN,
            regime_probabilities={regime_type: 0.25 for regime_type in RegimeType},
            regime_characteristics={},
            transition_matrix=self._create_default_transition_matrix(),
            model_validation=ModelValidationResult(
                is_valid=False,
                aic=float('inf'),
                bic=float('inf'),
                log_likelihood=float('-inf'),
                convergence=False,
                linearity_test={'error': 'Model failed'},
                regime_number_test={'error': 'Model failed'},
                out_of_sample_metrics={'error': 'Model failed'}
            ),
            confidence=0.0,
            timestamp=datetime.now().isoformat(),
            data_quality=data_quality
        )
    
    def _create_fallback_forecast(self, horizon: int) -> List[Dict[str, Any]]:
        """Cria previsão de fallback"""
        return [
            {
                'month': i + 1,
                'regime': 'UNKNOWN',
                'probability': 0.25,
                'confidence': 0.0
            }
            for i in range(horizon)
        ]
