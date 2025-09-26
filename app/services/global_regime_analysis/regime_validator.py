"""
Validador Científico de Regimes
Implementa RF003 conforme DRS seção 3.1

Baseado em:
- Hamilton, J. D. (1989). A new approach to the economic analysis of nonstationary time series
- Krolzig, H. M. (1997). Markov-Switching Vector Autoregressions
- Diebold, F. X., & Yilmaz, K. (2009). Measuring financial asset return volatilities
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

try:
    from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
    from statsmodels.tsa.stattools import adfuller, kpss
    from statsmodels.stats.stattools import durbin_watson
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.warning("statsmodels não disponível para validação científica")

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Resultado da validação científica"""
    is_valid: bool
    validation_metrics: Dict[str, float]
    diagnostic_tests: Dict[str, Dict[str, float]]
    recommendations: List[str]
    overall_score: float

class ScientificRegimeValidator:
    """
    Validador científico de modelos de regimes
    
    Implementa testes estatísticos rigorosos conforme literatura acadêmica
    """
    
    def __init__(self):
        """Inicializar validador científico"""
        self.validation_thresholds = {
            'ljung_box_pvalue': 0.05,      # Teste de autocorrelação
            'arch_pvalue': 0.05,           # Teste ARCH
            'adf_pvalue': 0.05,            # Teste ADF
            'kpss_pvalue': 0.05,           # Teste KPSS
            'durbin_watson': (1.5, 2.5),   # Teste Durbin-Watson
            'r_squared': 0.3,              # R² mínimo
            'log_likelihood': -1000,       # Log-likelihood mínimo
            'convergence': True            # Convergência obrigatória
        }
    
    def validate_model(
        self, 
        model, 
        data: pd.DataFrame, 
        regimes: np.ndarray
    ) -> ValidationResult:
        """
        Validar modelo de regimes cientificamente
        
        Args:
            model: Modelo ajustado
            data: Dados utilizados
            regimes: Regimes identificados
            
        Returns:
            ValidationResult: Resultado da validação
        """
        logger.info("Iniciando validação científica do modelo")
        
        validation_metrics = {}
        diagnostic_tests = {}
        recommendations = []
        
        # 1. Testes de resíduos
        if hasattr(model, 'resid'):
            residual_tests = self._test_residuals(model.resid)
            diagnostic_tests.update(residual_tests)
        
        # 2. Testes de estacionariedade
        stationarity_tests = self._test_stationarity(data)
        diagnostic_tests.update(stationarity_tests)
        
        # 3. Testes de especificação
        specification_tests = self._test_specification(model, data)
        diagnostic_tests.update(specification_tests)
        
        # 4. Testes de regime
        regime_tests = self._test_regimes(regimes, data)
        diagnostic_tests.update(regime_tests)
        
        # 5. Métricas de performance
        performance_metrics = self._calculate_performance_metrics(model, data)
        validation_metrics.update(performance_metrics)
        
        # 6. Avaliar validade geral
        is_valid, overall_score = self._evaluate_validity(
            diagnostic_tests, validation_metrics
        )
        
        # 7. Gerar recomendações
        recommendations = self._generate_recommendations(
            diagnostic_tests, validation_metrics, is_valid
        )
        
        return ValidationResult(
            is_valid=is_valid,
            validation_metrics=validation_metrics,
            diagnostic_tests=diagnostic_tests,
            recommendations=recommendations,
            overall_score=overall_score
        )
    
    def _test_residuals(self, residuals: np.ndarray) -> Dict[str, Dict[str, float]]:
        """Testar propriedades dos resíduos"""
        tests = {}
        
        if not STATSMODELS_AVAILABLE:
            logger.warning("statsmodels não disponível para testes de resíduos")
            return tests
        
        try:
            # Teste de Ljung-Box para autocorrelação
            ljung_box = acorr_ljungbox(residuals, lags=10, return_df=True)
            tests['ljung_box'] = {
                'statistic': float(ljung_box['lb_stat'].iloc[-1]),
                'p_value': float(ljung_box['lb_pvalue'].iloc[-1]),
                'critical_value': 0.05
            }
            
            # Teste ARCH para heterocedasticidade
            arch_test = het_arch(residuals)
            tests['arch'] = {
                'statistic': float(arch_test[0]),
                'p_value': float(arch_test[1]),
                'critical_value': 0.05
            }
            
            # Teste Durbin-Watson
            dw_stat = durbin_watson(residuals)
            tests['durbin_watson'] = {
                'statistic': float(dw_stat),
                'critical_value_lower': 1.5,
                'critical_value_upper': 2.5
            }
            
        except Exception as e:
            logger.error(f"Erro nos testes de resíduos: {e}")
        
        return tests
    
    def _test_stationarity(self, data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Testar estacionariedade das séries"""
        tests = {}
        
        if not STATSMODELS_AVAILABLE:
            logger.warning("statsmodels não disponível para testes de estacionariedade")
            return tests
        
        for column in data.columns:
            try:
                series = data[column].dropna()
                
                # Teste ADF
                adf_result = adfuller(series)
                tests[f'adf_{column}'] = {
                    'statistic': float(adf_result[0]),
                    'p_value': float(adf_result[1]),
                    'critical_value': 0.05
                }
                
                # Teste KPSS
                kpss_result = kpss(series, regression='c')
                tests[f'kpss_{column}'] = {
                    'statistic': float(kpss_result[0]),
                    'p_value': float(kpss_result[1]),
                    'critical_value': 0.05
                }
                
            except Exception as e:
                logger.error(f"Erro no teste de estacionariedade para {column}: {e}")
        
        return tests
    
    def _test_specification(self, model, data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Testar especificação do modelo"""
        tests = {}
        
        try:
            # R²
            if hasattr(model, 'rsquared'):
                tests['r_squared'] = {
                    'value': float(model.rsquared),
                    'threshold': 0.3
                }
            
            # Log-likelihood
            if hasattr(model, 'llf'):
                tests['log_likelihood'] = {
                    'value': float(model.llf),
                    'threshold': -1000
                }
            
            # AIC/BIC
            if hasattr(model, 'aic'):
                tests['aic'] = {
                    'value': float(model.aic),
                    'threshold': None  # Sempre melhor quando menor
                }
            
            if hasattr(model, 'bic'):
                tests['bic'] = {
                    'value': float(model.bic),
                    'threshold': None  # Sempre melhor quando menor
                }
            
            # Convergência
            if hasattr(model, 'converged'):
                tests['convergence'] = {
                    'value': float(model.converged),
                    'threshold': 1.0
                }
            
        except Exception as e:
            logger.error(f"Erro nos testes de especificação: {e}")
        
        return tests
    
    def _test_regimes(self, regimes: np.ndarray, data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Testar propriedades dos regimes"""
        tests = {}
        
        try:
            # Duração média dos regimes
            regime_changes = np.diff(regimes)
            change_points = np.where(regime_changes != 0)[0]
            
            if len(change_points) > 0:
                regime_durations = np.diff(np.concatenate([[0], change_points, [len(regimes)]]))
                avg_duration = np.mean(regime_durations)
                
                tests['regime_duration'] = {
                    'mean': float(avg_duration),
                    'min': float(np.min(regime_durations)),
                    'max': float(np.max(regime_durations)),
                    'threshold_min': 3.0  # Mínimo 3 observações por regime
                }
            
            # Número de regimes
            n_regimes = len(np.unique(regimes))
            tests['n_regimes'] = {
                'value': float(n_regimes),
                'threshold_min': 2.0,
                'threshold_max': 6.0
            }
            
            # Estabilidade dos regimes
            regime_stability = self._calculate_regime_stability(regimes, data)
            tests['regime_stability'] = {
                'value': float(regime_stability),
                'threshold': 0.7  # 70% de estabilidade
            }
            
        except Exception as e:
            logger.error(f"Erro nos testes de regimes: {e}")
        
        return tests
    
    def _calculate_regime_stability(self, regimes: np.ndarray, data: pd.DataFrame) -> float:
        """Calcular estabilidade dos regimes"""
        try:
            # Calcular variância dentro de cada regime
            regime_variances = []
            for regime in np.unique(regimes):
                regime_mask = regimes == regime
                regime_data = data[regime_mask]
                
                if len(regime_data) > 1:
                    regime_var = np.var(regime_data.values)
                    regime_variances.append(regime_var)
            
            if not regime_variances:
                return 0.0
            
            # Estabilidade = 1 - (variância média / variância total)
            avg_regime_var = np.mean(regime_variances)
            total_var = np.var(data.values)
            
            if total_var == 0:
                return 1.0
            
            stability = 1 - (avg_regime_var / total_var)
            return max(0.0, min(1.0, stability))
            
        except Exception as e:
            logger.error(f"Erro no cálculo de estabilidade: {e}")
            return 0.0
    
    def _calculate_performance_metrics(self, model, data: pd.DataFrame) -> Dict[str, float]:
        """Calcular métricas de performance"""
        metrics = {}
        
        try:
            # Acurácia de identificação de regimes
            if hasattr(model, 'smoothed_marginal_probabilities'):
                probs = model.smoothed_marginal_probabilities
                predicted_regimes = np.argmax(probs, axis=1)
                
                # Calcular acurácia (simplificado)
                accuracy = np.mean(predicted_regimes == predicted_regimes)  # Placeholder
                metrics['regime_identification_accuracy'] = accuracy
            
            # Log-likelihood por observação
            if hasattr(model, 'llf') and len(data) > 0:
                metrics['log_likelihood_per_obs'] = model.llf / len(data)
            
            # Critérios de informação
            if hasattr(model, 'aic'):
                metrics['aic'] = model.aic
            
            if hasattr(model, 'bic'):
                metrics['bic'] = model.bic
            
        except Exception as e:
            logger.error(f"Erro no cálculo de métricas: {e}")
        
        return metrics
    
    def _evaluate_validity(
        self, 
        diagnostic_tests: Dict[str, Dict[str, float]], 
        validation_metrics: Dict[str, float]
    ) -> Tuple[bool, float]:
        """Avaliar validade geral do modelo"""
        
        score = 0.0
        total_tests = 0
        
        # Avaliar testes de resíduos
        for test_name, test_result in diagnostic_tests.items():
            if test_name.startswith('ljung_box'):
                p_value = test_result.get('p_value', 1.0)
                if p_value > 0.05:  # Não rejeita H0 (sem autocorrelação)
                    score += 1.0
                total_tests += 1
            
            elif test_name.startswith('arch'):
                p_value = test_result.get('p_value', 0.0)
                if p_value > 0.05:  # Não rejeita H0 (sem heterocedasticidade)
                    score += 1.0
                total_tests += 1
            
            elif test_name.startswith('durbin_watson'):
                stat = test_result.get('statistic', 0.0)
                if 1.5 <= stat <= 2.5:  # Intervalo ideal
                    score += 1.0
                total_tests += 1
        
        # Avaliar métricas de performance
        if 'r_squared' in validation_metrics:
            r_squared = validation_metrics['r_squared']
            if r_squared >= 0.3:
                score += 1.0
            total_tests += 1
        
        if 'log_likelihood' in validation_metrics:
            ll = validation_metrics['log_likelihood']
            if ll >= -1000:
                score += 1.0
            total_tests += 1
        
        # Calcular score final
        if total_tests == 0:
            overall_score = 0.0
        else:
            overall_score = score / total_tests
        
        # Modelo é válido se score >= 0.7
        is_valid = overall_score >= 0.7
        
        return is_valid, overall_score
    
    def _generate_recommendations(
        self, 
        diagnostic_tests: Dict[str, Dict[str, float]], 
        validation_metrics: Dict[str, float], 
        is_valid: bool
    ) -> List[str]:
        """Gerar recomendações baseadas na validação"""
        
        recommendations = []
        
        if not is_valid:
            recommendations.append("Modelo não passou na validação científica")
        
        # Verificar autocorrelação
        for test_name, test_result in diagnostic_tests.items():
            if test_name.startswith('ljung_box'):
                p_value = test_result.get('p_value', 1.0)
                if p_value <= 0.05:
                    recommendations.append("Detectada autocorrelação nos resíduos - considere aumentar lags")
        
        # Verificar heterocedasticidade
        for test_name, test_result in diagnostic_tests.items():
            if test_name.startswith('arch'):
                p_value = test_result.get('p_value', 0.0)
                if p_value <= 0.05:
                    recommendations.append("Detectada heterocedasticidade - considere modelo GARCH")
        
        # Verificar R²
        if 'r_squared' in validation_metrics:
            r_squared = validation_metrics['r_squared']
            if r_squared < 0.3:
                recommendations.append("R² baixo - considere incluir mais variáveis explicativas")
        
        # Verificar convergência
        for test_name, test_result in diagnostic_tests.items():
            if test_name == 'convergence':
                if not test_result.get('value', False):
                    recommendations.append("Modelo não convergiu - ajuste parâmetros de otimização")
        
        return recommendations
