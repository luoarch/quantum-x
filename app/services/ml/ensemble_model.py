"""
Ensemble de Modelos para validação robusta
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import joblib
from sklearn.ensemble import (
    RandomForestRegressor, 
    GradientBoostingRegressor,
    ExtraTreesRegressor
)
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score
import shap
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class EnsembleModel:
    """Ensemble de modelos para geração de sinais robusta"""
    
    def __init__(
        self,
        models: Optional[Dict[str, Any]] = None,
        weights: Optional[Dict[str, float]] = None,
        validation_method: str = 'time_series_cv'
    ):
        self.models = models or self._get_default_models()
        self.weights = weights or self._get_default_weights()
        self.validation_method = validation_method
        self.trained_models = {}
        self.feature_importance = {}
        self.shap_explainers = {}
        self.validation_scores = {}
        
        # Verificar se pesos somam 1
        if abs(sum(self.weights.values()) - 1.0) > 1e-6:
            raise ValueError("Pesos devem somar 1.0")
    
    def _get_default_models(self) -> Dict[str, Any]:
        """Retorna modelos padrão do ensemble"""
        return {
            'random_forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'extra_trees': ExtraTreesRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            ),
            'neural_network': MLPRegressor(
                hidden_layer_sizes=(100, 50),
                activation='relu',
                solver='adam',
                max_iter=500,
                random_state=42
            ),
            'svm': SVR(
                kernel='rbf',
                C=1.0,
                gamma='scale'
            ),
            'ridge': Ridge(
                alpha=1.0,
                random_state=42
            )
        }
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Retorna pesos padrão (baseados em performance típica)"""
        return {
            'random_forest': 0.20,
            'gradient_boosting': 0.25,
            'extra_trees': 0.15,
            'neural_network': 0.20,
            'svm': 0.10,
            'ridge': 0.10
        }
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Treina o ensemble de modelos
        
        Args:
            X: Features
            y: Target
            feature_names: Nomes das features
        """
        logger.info("🚀 Iniciando treinamento do ensemble")
        
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        
        # Validar dados
        if X.empty or y.empty:
            raise ValueError("Dados de treino vazios")
        
        if len(X) != len(y):
            raise ValueError("X e y devem ter o mesmo tamanho")
        
        # Treinar cada modelo
        training_results = {}
        
        for name, model in self.models.items():
            logger.info(f"🔄 Treinando {name}")
            
            try:
                # Treinar modelo
                model.fit(X, y)
                self.trained_models[name] = model
                
                # Validar modelo
                validation_score = self._validate_model(model, X, y)
                self.validation_scores[name] = validation_score
                
                # Calcular importância das features
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[name] = dict(zip(feature_names, model.feature_importances_))
                elif hasattr(model, 'coef_'):
                    self.feature_importance[name] = dict(zip(feature_names, abs(model.coef_)))
                
                # Treinar explicador SHAP
                try:
                    if name in ['random_forest', 'gradient_boosting', 'extra_trees']:
                        self.shap_explainers[name] = shap.TreeExplainer(model)
                    else:
                        # Para outros modelos, usar KernelExplainer (mais lento)
                        self.shap_explainers[name] = shap.KernelExplainer(
                            model.predict, X.sample(min(100, len(X)))
                        )
                except Exception as e:
                    logger.warning(f"Erro ao criar explicador SHAP para {name}: {e}")
                
                training_results[name] = {
                    'status': 'success',
                    'validation_score': validation_score,
                    'feature_count': len(feature_names)
                }
                
                logger.info(f"✅ {name}: Score={validation_score:.4f}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao treinar {name}: {str(e)}")
                training_results[name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Ajustar pesos baseado na performance
        self._adjust_weights_based_on_performance()
        
        logger.info("✅ Treinamento do ensemble concluído")
        
        return {
            'training_results': training_results,
            'final_weights': self.weights,
            'validation_scores': self.validation_scores
        }
    
    def _validate_model(self, model: Any, X: pd.DataFrame, y: pd.Series) -> float:
        """Valida modelo usando cross-validation temporal"""
        
        if self.validation_method == 'time_series_cv':
            # Time Series Cross-Validation
            tscv = TimeSeriesSplit(n_splits=5)
            scores = cross_val_score(model, X, y, cv=tscv, scoring='neg_mean_squared_error')
            return -scores.mean()  # Converter para positivo
        else:
            # Cross-validation padrão
            scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
            return -scores.mean()
    
    def _adjust_weights_based_on_performance(self):
        """Ajusta pesos baseado na performance dos modelos"""
        
        if not self.validation_scores:
            return
        
        # Calcular scores normalizados (0-1)
        scores = list(self.validation_scores.values())
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return  # Todos os scores são iguais
        
        # Normalizar scores
        normalized_scores = {}
        for name, score in self.validation_scores.items():
            normalized_scores[name] = (score - min_score) / (max_score - min_score)
        
        # Ajustar pesos (média ponderada entre peso original e performance)
        alpha = 0.7  # Peso da performance vs peso original
        
        for name in self.weights:
            if name in normalized_scores:
                performance_weight = normalized_scores[name]
                original_weight = self.weights[name]
                self.weights[name] = alpha * performance_weight + (1 - alpha) * original_weight
        
        # Renormalizar para somar 1
        total_weight = sum(self.weights.values())
        for name in self.weights:
            self.weights[name] /= total_weight
        
        logger.info(f"Pesos ajustados: {self.weights}")
    
    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Faz predição usando ensemble
        
        Returns:
            Tuple: (predição_ensemble, predições_individuais)
        """
        if not self.trained_models:
            raise ValueError("Modelos não treinados")
        
        individual_predictions = {}
        ensemble_prediction = np.zeros(len(X))
        
        for name, model in self.trained_models.items():
            try:
                pred = model.predict(X)
                individual_predictions[name] = pred
                
                # Adicionar à predição ensemble (ponderada)
                weight = self.weights.get(name, 0.0)
                ensemble_prediction += weight * pred
                
            except Exception as e:
                logger.warning(f"Erro na predição de {name}: {e}")
                continue
        
        return ensemble_prediction, individual_predictions
    
    def explain_prediction(
        self,
        X: pd.DataFrame,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Explica predição usando SHAP
        
        Args:
            X: Features para explicar
            model_name: Modelo específico (se None, usa ensemble)
        """
        explanations = {}
        
        if model_name and model_name in self.shap_explainers:
            # Explicar modelo específico
            try:
                explainer = self.shap_explainers[model_name]
                shap_values = explainer.shap_values(X)
                explanations[model_name] = {
                    'shap_values': shap_values.tolist() if hasattr(shap_values, 'tolist') else shap_values,
                    'base_value': explainer.expected_value if hasattr(explainer, 'expected_value') else 0
                }
            except Exception as e:
                logger.warning(f"Erro ao explicar {model_name}: {e}")
        
        else:
            # Explicar todos os modelos disponíveis
            for name, explainer in self.shap_explainers.items():
                try:
                    shap_values = explainer.shap_values(X)
                    explanations[name] = {
                        'shap_values': shap_values.tolist() if hasattr(shap_values, 'tolist') else shap_values,
                        'base_value': explainer.expected_value if hasattr(explainer, 'expected_value') else 0,
                        'weight': self.weights.get(name, 0.0)
                    }
                except Exception as e:
                    logger.warning(f"Erro ao explicar {name}: {e}")
        
        return explanations
    
    def get_feature_importance(self) -> Dict[str, Dict[str, float]]:
        """Retorna importância das features por modelo"""
        return self.feature_importance
    
    def get_ensemble_feature_importance(self) -> Dict[str, float]:
        """Retorna importância das features do ensemble (média ponderada)"""
        if not self.feature_importance:
            return {}
        
        # Calcular média ponderada
        all_features = set()
        for model_importance in self.feature_importance.values():
            all_features.update(model_importance.keys())
        
        ensemble_importance = {}
        for feature in all_features:
            weighted_sum = 0.0
            total_weight = 0.0
            
            for model_name, importance in self.feature_importance.items():
                if feature in importance:
                    weight = self.weights.get(model_name, 0.0)
                    weighted_sum += weight * importance[feature]
                    total_weight += weight
            
            if total_weight > 0:
                ensemble_importance[feature] = weighted_sum / total_weight
        
        return ensemble_importance
    
    def validate_logic(self, X: pd.DataFrame, feature_names: List[str]) -> Dict[str, Any]:
        """
        Valida lógica do modelo usando SHAP
        
        Args:
            X: Features para validar
            feature_names: Nomes das features
        """
        explanations = self.explain_prediction(X)
        
        validation_results = {
            'logical_consistency': True,
            'warnings': [],
            'feature_contributions': {}
        }
        
        # Analisar contribuições das features
        for model_name, explanation in explanations.items():
            if 'shap_values' not in explanation:
                continue
            
            shap_values = explanation['shap_values']
            
            # Se há múltiplas instâncias, usar a primeira
            if isinstance(shap_values, list) and len(shap_values) > 0:
                instance_values = shap_values[0] if isinstance(shap_values[0], list) else shap_values
            else:
                instance_values = shap_values
            
            # Verificar consistência lógica
            feature_contributions = {}
            for i, (feature, contribution) in enumerate(zip(feature_names, instance_values)):
                feature_contributions[feature] = contribution
                
                # Verificar se contribuições fazem sentido
                if abs(contribution) > 10:  # Contribuição muito alta
                    validation_results['warnings'].append(
                        f"{model_name}: {feature} tem contribuição muito alta ({contribution:.2f})"
                    )
            
            validation_results['feature_contributions'][model_name] = feature_contributions
        
        # Verificar se há contradições entre modelos
        if len(explanations) > 1:
            self._check_model_contradictions(explanations, validation_results)
        
        return validation_results
    
    def _check_model_contradictions(
        self,
        explanations: Dict[str, Any],
        validation_results: Dict[str, Any]
    ):
        """Verifica contradições entre modelos"""
        
        # Implementação simplificada - pode ser expandida
        model_names = list(explanations.keys())
        
        for i in range(len(model_names)):
            for j in range(i + 1, len(model_names)):
                model1, model2 = model_names[i], model_names[j]
                
                # Verificar se predições são muito diferentes
                # (implementação simplificada)
                validation_results['warnings'].append(
                    f"Comparação entre {model1} e {model2} necessária"
                )
    
    def save_models(self, filepath: str):
        """Salva modelos treinados"""
        model_data = {
            'trained_models': self.trained_models,
            'weights': self.weights,
            'validation_scores': self.validation_scores,
            'feature_importance': self.feature_importance
        }
        joblib.dump(model_data, filepath)
        logger.info(f"Modelos salvos em {filepath}")
    
    def load_models(self, filepath: str):
        """Carrega modelos treinados"""
        model_data = joblib.load(filepath)
        self.trained_models = model_data['trained_models']
        self.weights = model_data['weights']
        self.validation_scores = model_data['validation_scores']
        self.feature_importance = model_data['feature_importance']
        logger.info(f"Modelos carregados de {filepath}")
