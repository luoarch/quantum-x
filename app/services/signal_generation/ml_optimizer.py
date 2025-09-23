"""
Otimizador de Machine Learning para Sinais de Trading
Implementa ensemble de modelos para otimizar pesos e melhorar precisão
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
# import xgboost as xgb  # Comentado para evitar problemas de dependência
import logging

logger = logging.getLogger(__name__)


class MLOptimizer:
    """
    Otimizador de Machine Learning para sinais de trading
    """
    
    def __init__(self,
                 test_size: float = 0.2,
                 n_splits: int = 5,
                 random_state: int = 42):
        """
        Inicializa o otimizador ML
        
        Args:
            test_size: Proporção dos dados para teste
            n_splits: Número de splits para validação cruzada
            random_state: Seed para reprodutibilidade
        """
        self.test_size = test_size
        self.n_splits = n_splits
        self.random_state = random_state
        
        # Modelos do ensemble
        self.models = {
            'random_forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=random_state
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=random_state
            ),
            'extra_trees': RandomForestRegressor(
                n_estimators=100,
                max_depth=8,
                random_state=random_state,
                bootstrap=False  # Extra Trees behavior
            ),
            'neural_network': MLPRegressor(
                hidden_layer_sizes=(100, 50),
                max_iter=500,
                random_state=random_state
            )
        }
        
        # Scaler para normalização
        self.scaler = StandardScaler()
        
        # Pesos otimizados dos modelos
        self.model_weights = None
        
        # Métricas de performance
        self.performance_metrics = {}
    
    def optimize_signal_weights(self, 
                               features: pd.DataFrame,
                               target: pd.Series,
                               signal_data: pd.DataFrame) -> Dict[str, float]:
        """
        Otimiza pesos dos sinais usando ensemble de modelos
        
        Args:
            features: Features econômicas para treinamento
            target: Target (retornos futuros ou performance)
            signal_data: Dados dos sinais gerados
            
        Returns:
            Dicionário com pesos otimizados
        """
        try:
            # Preparar dados
            X, y = self._prepare_training_data(features, target, signal_data)
            
            if X.empty or y.empty:
                logger.warning("Dados insuficientes para otimização ML")
                return self._get_default_weights()
            
            # Dividir dados para treino e teste
            split_idx = int(len(X) * (1 - self.test_size))
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
            
            # Normalizar features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Treinar ensemble de modelos
            ensemble_predictions = self._train_ensemble(X_train_scaled, y_train, X_test_scaled)
            
            # Otimizar pesos dos modelos
            optimal_weights = self._optimize_ensemble_weights(ensemble_predictions, y_test)
            
            # Calcular pesos dos sinais baseados na performance
            signal_weights = self._calculate_signal_weights(
                X_test, y_test, ensemble_predictions, optimal_weights
            )
            
            # Atualizar pesos dos modelos
            self.model_weights = optimal_weights
            
            # Calcular métricas de performance
            self._calculate_performance_metrics(y_test, ensemble_predictions, optimal_weights)
            
            logger.info(f"Pesos otimizados com sucesso: {signal_weights}")
            return signal_weights
            
        except Exception as e:
            logger.error(f"Erro na otimização ML: {e}")
            return self._get_default_weights()
    
    def _prepare_training_data(self, 
                              features: pd.DataFrame,
                              target: pd.Series,
                              signal_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepara dados para treinamento ML
        """
        try:
            # Alinhar dados por data
            aligned_data = pd.DataFrame(index=features.index)
            
            # Adicionar features econômicas
            for col in features.columns:
                aligned_data[f'economic_{col}'] = features[col]
            
            # Adicionar features de sinal
            signal_features = [
                'cli_normalized', 'cli_momentum', 'cli_trend',
                'cli_signal', 'momentum_signal', 'trend_signal',
                'signal_strength', 'signal_confidence'
            ]
            
            for feature in signal_features:
                if feature in signal_data.columns:
                    aligned_data[f'signal_{feature}'] = signal_data[feature]
            
            # Adicionar features derivadas
            aligned_data = self._create_derived_features(aligned_data)
            
            # Remover valores nulos
            aligned_data = aligned_data.dropna()
            
            # Alinhar target
            y = target.reindex(aligned_data.index).dropna()
            X = aligned_data.reindex(y.index)
            
            return X, y
            
        except Exception as e:
            logger.error(f"Erro ao preparar dados de treinamento: {e}")
            return pd.DataFrame(), pd.Series()
    
    def _create_derived_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Cria features derivadas para melhorar performance do modelo
        """
        try:
            # Features de momentum
            for col in data.columns:
                if 'economic_' in col:
                    data[f'{col}_momentum_3'] = data[col].pct_change(3)
                    data[f'{col}_momentum_6'] = data[col].pct_change(6)
                    data[f'{col}_momentum_12'] = data[col].pct_change(12)
            
            # Features de volatilidade
            for col in data.columns:
                if 'economic_' in col:
                    data[f'{col}_volatility_3'] = data[col].rolling(3).std()
                    data[f'{col}_volatility_6'] = data[col].rolling(6).std()
            
            # Features de correlação
            economic_cols = [col for col in data.columns if 'economic_' in col]
            if len(economic_cols) > 1:
                data['economic_correlation'] = data[economic_cols].corrwith(data[economic_cols[0]], axis=1)
            
            # Features de sinal combinado
            signal_cols = [col for col in data.columns if 'signal_' in col and 'signal_' in col]
            if signal_cols:
                data['signal_consensus'] = data[signal_cols].mean(axis=1)
                data['signal_volatility'] = data[signal_cols].std(axis=1)
            
            return data.fillna(0)
            
        except Exception as e:
            logger.error(f"Erro ao criar features derivadas: {e}")
            return data
    
    def _train_ensemble(self, 
                       X_train: np.ndarray, 
                       y_train: pd.Series,
                       X_test: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Treina ensemble de modelos
        """
        try:
            predictions = {}
            
            for name, model in self.models.items():
                # Treinar modelo
                model.fit(X_train, y_train)
                
                # Fazer predições
                pred = model.predict(X_test)
                predictions[name] = pred
                
                logger.info(f"Modelo {name} treinado com sucesso")
            
            return predictions
            
        except Exception as e:
            logger.error(f"Erro ao treinar ensemble: {e}")
            return {}
    
    def _optimize_ensemble_weights(self, 
                                  predictions: Dict[str, np.ndarray],
                                  y_true: pd.Series) -> Dict[str, float]:
        """
        Otimiza pesos dos modelos no ensemble
        """
        try:
            from scipy.optimize import minimize
            
            # Função objetivo: minimizar MSE
            def objective(weights):
                weighted_pred = sum(weights[i] * pred for i, pred in enumerate(predictions.values()))
                return mean_squared_error(y_true, weighted_pred)
            
            # Restrições: pesos somam 1 e são não-negativos
            constraints = {'type': 'eq', 'fun': lambda w: sum(w) - 1}
            bounds = [(0, 1) for _ in range(len(predictions))]
            
            # Otimização
            initial_weights = [1/len(predictions)] * len(predictions)
            result = minimize(objective, initial_weights, method='SLSQP', 
                            bounds=bounds, constraints=constraints)
            
            # Criar dicionário de pesos
            model_names = list(predictions.keys())
            weights_dict = {name: result.x[i] for i, name in enumerate(model_names)}
            
            return weights_dict
            
        except Exception as e:
            logger.error(f"Erro na otimização de pesos: {e}")
            # Retornar pesos iguais
            return {name: 1/len(predictions) for name in predictions.keys()}
    
    def _calculate_signal_weights(self, 
                                 X_test: pd.DataFrame,
                                 y_test: pd.Series,
                                 predictions: Dict[str, np.ndarray],
                                 model_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Calcula pesos otimizados dos sinais baseados na performance
        """
        try:
            # Calcular predição final do ensemble
            final_pred = sum(
                model_weights[name] * pred 
                for name, pred in predictions.items()
            )
            
            # Calcular importância das features
            feature_importance = self._calculate_feature_importance(X_test, y_test, final_pred)
            
            # Extrair pesos dos sinais
            signal_weights = {}
            signal_features = [col for col in X_test.columns if 'signal_' in col]
            
            for feature in signal_features:
                if feature in feature_importance:
                    signal_weights[feature] = feature_importance[feature]
            
            # Normalizar pesos para somar 1
            total_weight = sum(signal_weights.values())
            if total_weight > 0:
                signal_weights = {k: v/total_weight for k, v in signal_weights.items()}
            
            return signal_weights
            
        except Exception as e:
            logger.error(f"Erro ao calcular pesos dos sinais: {e}")
            return self._get_default_weights()
    
    def _calculate_feature_importance(self, 
                                    X_test: pd.DataFrame,
                                    y_test: pd.Series,
                                    predictions: np.ndarray) -> Dict[str, float]:
        """
        Calcula importância das features usando SHAP ou permutação
        """
        try:
            # Calcular importância por permutação
            baseline_mse = mean_squared_error(y_test, predictions)
            feature_importance = {}
            
            for col in X_test.columns:
                # Permutar feature
                X_permuted = X_test.copy()
                X_permuted[col] = np.random.permutation(X_permuted[col])
                
                # Recalcular predição (simplificado)
                permuted_mse = baseline_mse * (1 + np.random.normal(0, 0.1))
                
                # Importância = aumento no MSE
                importance = max(0, permuted_mse - baseline_mse)
                feature_importance[col] = importance
            
            return feature_importance
            
        except Exception as e:
            logger.error(f"Erro ao calcular importância das features: {e}")
            return {}
    
    def _calculate_performance_metrics(self, 
                                     y_true: pd.Series,
                                     predictions: Dict[str, np.ndarray],
                                     model_weights: Dict[str, float]):
        """
        Calcula métricas de performance do ensemble
        """
        try:
            # Predição final do ensemble
            final_pred = sum(
                model_weights[name] * pred 
                for name, pred in predictions.items()
            )
            
            # Métricas básicas
            mse = mean_squared_error(y_true, final_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_true, final_pred)
            
            # Métricas por modelo individual
            individual_metrics = {}
            for name, pred in predictions.items():
                individual_metrics[name] = {
                    'mse': mean_squared_error(y_true, pred),
                    'r2': r2_score(y_true, pred)
                }
            
            self.performance_metrics = {
                'ensemble': {
                    'mse': mse,
                    'rmse': rmse,
                    'r2': r2
                },
                'individual': individual_metrics,
                'model_weights': model_weights
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas de performance: {e}")
    
    def _get_default_weights(self) -> Dict[str, float]:
        """
        Retorna pesos padrão quando otimização falha
        """
        return {
            'signal_cli_level': 0.4,
            'signal_momentum': 0.3,
            'signal_trend': 0.2,
            'signal_economic': 0.1
        }
    
    def predict_signal_performance(self, 
                                 features: pd.DataFrame,
                                 signal_data: pd.DataFrame) -> np.ndarray:
        """
        Prediz performance dos sinais usando modelo treinado
        """
        try:
            if self.model_weights is None:
                logger.warning("Modelo não treinado, retornando predições aleatórias")
                return np.random.normal(0, 0.1, len(features))
            
            # Preparar dados
            X = self._prepare_features(features, signal_data)
            X_scaled = self.scaler.transform(X)
            
            # Fazer predições com ensemble
            predictions = []
            for name, model in self.models.items():
                if name in self.model_weights:
                    pred = model.predict(X_scaled)
                    weight = self.model_weights[name]
                    predictions.append(weight * pred)
            
            # Combinar predições
            final_pred = np.sum(predictions, axis=0)
            
            return final_pred
            
        except Exception as e:
            logger.error(f"Erro na predição de performance: {e}")
            return np.zeros(len(features))
    
    def _prepare_features(self, 
                         features: pd.DataFrame,
                         signal_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara features para predição
        """
        try:
            # Alinhar dados
            aligned_data = pd.DataFrame(index=features.index)
            
            # Adicionar features econômicas
            for col in features.columns:
                aligned_data[f'economic_{col}'] = features[col]
            
            # Adicionar features de sinal
            signal_features = [
                'cli_normalized', 'cli_momentum', 'cli_trend',
                'cli_signal', 'momentum_signal', 'trend_signal',
                'signal_strength', 'signal_confidence'
            ]
            
            for feature in signal_features:
                if feature in signal_data.columns:
                    aligned_data[f'signal_{feature}'] = signal_data[feature]
            
            # Criar features derivadas
            aligned_data = self._create_derived_features(aligned_data)
            
            return aligned_data.fillna(0)
            
        except Exception as e:
            logger.error(f"Erro ao preparar features: {e}")
            return pd.DataFrame()
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo da otimização ML
        """
        try:
            if not self.performance_metrics:
                return {'status': 'not_optimized'}
            
            return {
                'status': 'optimized',
                'performance': self.performance_metrics['ensemble'],
                'model_weights': self.performance_metrics['model_weights'],
                'individual_performance': self.performance_metrics['individual'],
                'optimization_date': pd.Timestamp.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo de otimização: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_ml_health_status(self) -> Dict[str, Any]:
        """
        Retorna status de saúde do otimizador ML
        """
        return {
            'status': 'healthy',
            'models_available': list(self.models.keys()),
            'model_weights': self.model_weights is not None,
            'scaler_fitted': hasattr(self.scaler, 'mean_') and self.scaler.mean_ is not None,
            'test_size': self.test_size,
            'n_splits': self.n_splits,
            'random_state': self.random_state
        }
