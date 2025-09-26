"""
Modelo Regime-Switching Global VAR (RS-GVAR)
Implementa RF002 conforme DRS seção 3.1

Baseado em:
- Krolzig, H. M. (1997). Markov-Switching Vector Autoregressions
- Hamilton, J. D. (1989). A new approach to the economic analysis of nonstationary time series
- Diebold, F. X., & Yilmaz, K. (2009). Measuring financial asset return volatilities
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging

try:
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
    from statsmodels.tsa.vector_ar.var_model import VAR
    from statsmodels.tsa.stattools import adfuller, kpss
    from statsmodels.stats.diagnostic import acorr_ljungbox
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.warning("statsmodels não disponível. Usando implementação simplificada.")

from app.core.config import settings, model_config

logger = logging.getLogger(__name__)

class RegimeType(str, Enum):
    """Tipos de regimes econômicos globais"""
    GLOBAL_RECESSION = "GLOBAL_RECESSION"
    GLOBAL_RECOVERY = "GLOBAL_RECOVERY"
    GLOBAL_EXPANSION = "GLOBAL_EXPANSION"
    GLOBAL_CONTRACTION = "GLOBAL_CONTRACTION"
    GLOBAL_STRESS = "GLOBAL_STRESS"
    GLOBAL_CALM = "GLOBAL_CALM"

@dataclass
class RSGVARResult:
    """Resultado do modelo RS-GVAR"""
    regimes: np.ndarray
    regime_probabilities: np.ndarray
    transition_matrix: np.ndarray
    model_parameters: Dict
    log_likelihood: float
    aic: float
    bic: float
    convergence: bool
    regime_characteristics: Dict[str, Dict]
    validation_metrics: Dict[str, float]

class RSGVARModel:
    """
    Modelo Regime-Switching Global VAR
    
    Implementa metodologia científica para identificação de regimes econômicos
    globais usando dados de G7 + China + Brasil.
    """
    
    def __init__(
        self,
        max_regimes: int = None,
        max_lags: int = None,
        convergence_tolerance: float = None
    ):
        """
        Inicializar modelo RS-GVAR
        
        Args:
            max_regimes: Número máximo de regimes (padrão: settings.MAX_REGIMES)
            max_lags: Número máximo de lags (padrão: model_config.RS_GVAR_MAX_LAGS)
            convergence_tolerance: Tolerância de convergência
        """
        self.max_regimes = max_regimes or settings.MAX_REGIMES
        self.max_lags = max_lags or model_config.RS_GVAR_MAX_LAGS
        self.convergence_tolerance = convergence_tolerance or model_config.RS_GVAR_CONVERGENCE_TOLERANCE
        self.max_iterations = model_config.RS_GVAR_MAX_ITERATIONS
        
        # Validação de parâmetros
        if self.max_regimes < 2 or self.max_regimes > 6:
            raise ValueError("Número de regimes deve estar entre 2 e 6")
        
        self.model = None
        self.fitted_model = None
        self.regime_names = self._get_regime_names()
        
    def _get_regime_names(self) -> List[str]:
        """Obter nomes dos regimes baseado no número máximo"""
        base_names = [
            RegimeType.GLOBAL_RECESSION,
            RegimeType.GLOBAL_RECOVERY,
            RegimeType.GLOBAL_EXPANSION,
            RegimeType.GLOBAL_CONTRACTION,
            RegimeType.GLOBAL_STRESS,
            RegimeType.GLOBAL_CALM
        ]
        return base_names[:self.max_regimes]
    
    def _validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validar dados de entrada conforme critérios acadêmicos
        
        Args:
            data: DataFrame com séries temporais
            
        Returns:
            bool: True se dados são válidos
        """
        if data.empty:
            raise ValueError("Dados não podem estar vazios")
        
        if len(data) < model_config.MIN_TRAINING_OBSERVATIONS:
            raise ValueError(f"Mínimo de {model_config.MIN_TRAINING_OBSERVATIONS} observações necessário")
        
        # Verificar estacionariedade
        for column in data.columns:
            if data[column].isna().sum() > len(data) * 0.1:  # 10% missing
                raise ValueError(f"Série {column} tem muitos dados faltantes")
            
            # Teste ADF para estacionariedade
            if STATSMODELS_AVAILABLE:
                adf_result = adfuller(data[column].dropna())
                if adf_result[1] > 0.05:  # p-value > 0.05
                    logger.warning(f"Série {column} pode não ser estacionária (p-value: {adf_result[1]:.4f})")
        
        return True
    
    def _prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preparar dados para o modelo RS-GVAR
        
        Args:
            data: DataFrame com séries temporais
            
        Returns:
            DataFrame preparado
        """
        # Remover dados faltantes
        data_clean = data.dropna()
        
        # Verificar se ainda temos dados suficientes
        if len(data_clean) < model_config.MIN_TRAINING_OBSERVATIONS:
            raise ValueError("Dados insuficientes após limpeza")
        
        # Normalizar dados (z-score)
        data_normalized = (data_clean - data_clean.mean()) / data_clean.std()
        
        return data_normalized
    
    def _select_optimal_regimes(self, data: pd.DataFrame) -> int:
        """
        Selecionar número ótimo de regimes usando BIC/AIC
        
        Args:
            data: DataFrame preparado
            
        Returns:
            int: Número ótimo de regimes
        """
        if not STATSMODELS_AVAILABLE:
            return 2  # Fallback para 2 regimes
        
        best_regimes = 2
        best_bic = float('inf')
        
        for n_regimes in range(2, self.max_regimes + 1):
            try:
                # Ajustar modelo com n_regimes
                model = MarkovRegression(
                    data.values,
                    k_regimes=n_regimes,
                    trend='c'
                )
                fitted = model.fit()
                
                # Usar BIC para seleção
                if fitted.bic < best_bic:
                    best_bic = fitted.bic
                    best_regimes = n_regimes
                    
            except Exception as e:
                logger.warning(f"Erro ao ajustar modelo com {n_regimes} regimes: {e}")
                continue
        
        logger.info(f"Número ótimo de regimes selecionado: {best_regimes} (BIC: {best_bic:.4f})")
        return best_regimes
    
    def fit(self, data: pd.DataFrame) -> RSGVARResult:
        """
        Ajustar modelo RS-GVAR aos dados
        
        Args:
            data: DataFrame com séries temporais de países G7 + China + Brasil
            
        Returns:
            RSGVARResult: Resultado do modelo ajustado
        """
        logger.info("Iniciando ajuste do modelo RS-GVAR")
        
        # Validar dados
        self._validate_data(data)
        
        # Preparar dados
        data_prepared = self._prepare_data(data)
        
        if STATSMODELS_AVAILABLE:
            return self._fit_statsmodels(data_prepared)
        else:
            return self._fit_simplified(data_prepared)
    
    def _fit_statsmodels(self, data: pd.DataFrame) -> RSGVARResult:
        """Ajustar modelo RS-GVAR usando statsmodels"""
        try:
            # Selecionar número ótimo de regimes
            optimal_regimes = self._select_optimal_regimes(data)
            
            # Preparar dados para VAR
            var_data = self._prepare_var_data(data)
            
            # Ajustar modelo VAR primeiro
            var_model = VAR(var_data)
            var_fitted = var_model.fit(maxlags=self.max_lags, ic='bic')
            
            # Extrair resíduos do VAR
            residuals = var_fitted.resid
            
            # Ajustar modelo Markov-Switching nos resíduos
            ms_model = MarkovRegression(
                residuals,
                k_regimes=optimal_regimes,
                trend='c',
                switching_variance=True,
                switching_ar=True
            )
            
            fitted_model = ms_model.fit(
                maxiter=self.max_iterations,
                tolerance=self.convergence_tolerance,
                method='powell'  # Método mais robusto
            )
            
            # Extrair resultados
            regimes = fitted_model.smoothed_marginal_probabilities.argmax(axis=1)
            regime_probabilities = fitted_model.smoothed_marginal_probabilities
            
            # Calcular características dos regimes
            regime_characteristics = self._calculate_regime_characteristics(
                data, regimes, optimal_regimes
            )
            
            # Calcular métricas de validação
            validation_metrics = self._calculate_validation_metrics(
                fitted_model, data
            )
            
            # Armazenar modelo ajustado para previsões
            self.fitted_model = fitted_model
            self.var_model = var_fitted
            
            return RSGVARResult(
                regimes=regimes,
                regime_probabilities=regime_probabilities,
                transition_matrix=fitted_model.transition_matrix,
                model_parameters=fitted_model.params,
                log_likelihood=fitted_model.llf,
                aic=fitted_model.aic,
                bic=fitted_model.bic,
                convergence=fitted_model.converged,
                regime_characteristics=regime_characteristics,
                validation_metrics=validation_metrics
            )
            
        except Exception as e:
            logger.error(f"Erro ao ajustar modelo RS-GVAR: {e}")
            raise
    
    def _prepare_var_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preparar dados para modelo VAR"""
        # Verificar estacionariedade e aplicar transformações necessárias
        var_data = data.copy()
        
        for column in var_data.columns:
            # Teste ADF
            adf_result = adfuller(var_data[column].dropna())
            if adf_result[1] > 0.05:  # Não estacionário
                # Aplicar primeira diferença
                var_data[column] = var_data[column].diff()
                logger.info(f"Aplicada primeira diferença em {column}")
        
        return var_data.dropna()
    
    def _fit_simplified(self, data: pd.DataFrame) -> RSGVARResult:
        """Implementação simplificada quando statsmodels não disponível"""
        logger.warning("Usando implementação simplificada do RS-GVAR")
        
        n_obs, n_vars = data.shape
        n_regimes = min(3, self.max_regimes)  # Fallback para 3 regimes
        
        # Implementação simplificada usando clustering
        from sklearn.cluster import KMeans
        
        kmeans = KMeans(n_clusters=n_regimes, random_state=42)
        regimes = kmeans.fit_predict(data.values)
        
        # Calcular probabilidades (simplificado)
        regime_probabilities = np.zeros((n_obs, n_regimes))
        for i, regime in enumerate(regimes):
            regime_probabilities[i, regime] = 1.0
        
        # Matriz de transição simplificada
        transition_matrix = np.ones((n_regimes, n_regimes)) / n_regimes
        
        # Características dos regimes
        regime_characteristics = self._calculate_regime_characteristics(
            data, regimes, n_regimes
        )
        
        return RSGVARResult(
            regimes=regimes,
            regime_probabilities=regime_probabilities,
            transition_matrix=transition_matrix,
            model_parameters={},
            log_likelihood=0.0,
            aic=0.0,
            bic=0.0,
            convergence=True,
            regime_characteristics=regime_characteristics,
            validation_metrics={}
        )
    
    def _calculate_regime_characteristics(
        self, 
        data: pd.DataFrame, 
        regimes: np.ndarray, 
        n_regimes: int
    ) -> Dict[str, Dict]:
        """Calcular características de cada regime"""
        characteristics = {}
        
        for regime in range(n_regimes):
            regime_mask = regimes == regime
            regime_data = data[regime_mask]
            
            if len(regime_data) > 0:
                characteristics[self.regime_names[regime]] = {
                    "duration_months": len(regime_data),
                    "mean_values": regime_data.mean().to_dict(),
                    "volatility": regime_data.std().to_dict(),
                    "typical_indicators": {
                        "gdp_growth": [regime_data.mean().min(), regime_data.mean().max()],
                        "inflation": [regime_data.std().min(), regime_data.std().max()]
                    }
                }
        
        return characteristics
    
    def _calculate_validation_metrics(
        self, 
        fitted_model, 
        data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calcular métricas de validação do modelo"""
        metrics = {}
        
        try:
            # Teste de resíduos
            residuals = fitted_model.resid
            
            # Teste de Ljung-Box para autocorrelação
            if STATSMODELS_AVAILABLE:
                ljung_box = acorr_ljungbox(residuals, lags=10, return_df=True)
                metrics["ljung_box_pvalue"] = ljung_box["lb_pvalue"].mean()
            
            # R² ajustado
            metrics["r_squared"] = fitted_model.rsquared
            
            # Log-likelihood
            metrics["log_likelihood"] = fitted_model.llf
            
        except Exception as e:
            logger.warning(f"Erro ao calcular métricas de validação: {e}")
            metrics = {"error": str(e)}
        
        return metrics
    
    def predict_regimes(self, horizon: int = 12) -> np.ndarray:
        """
        Prever regimes futuros
        
        Args:
            horizon: Horizonte de previsão em períodos
            
        Returns:
            np.ndarray: Previsões de regimes
        """
        if self.fitted_model is None:
            raise ValueError("Modelo deve ser ajustado antes de fazer previsões")
        
        # Implementação simplificada de previsão
        # Em implementação real, usar métodos de previsão de Markov-Switching
        last_regime = self.fitted_model.regimes[-1]
        predictions = np.full(horizon, last_regime)
        
        return predictions
    
    def get_current_regime_probabilities(self) -> Dict[str, float]:
        """Obter probabilidades do regime atual"""
        if self.fitted_model is None:
            raise ValueError("Modelo deve ser ajustado antes de obter probabilidades")
        
        last_probabilities = self.fitted_model.regime_probabilities[-1]
        
        return {
            self.regime_names[i]: float(prob) 
            for i, prob in enumerate(last_probabilities)
        }
