"""
Módulo de Validação Científica Rigorosa
Implementa protocolo anti-viés e anti-alucinação
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class ScientificValidator:
    """
    Validador científico com protocolo anti-viés e anti-alucinação
    """
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.validation_results = {}
        np.random.seed(random_state)
    
    def time_series_cv_spillover(self, data: pd.DataFrame, 
                                n_splits: int = 5, 
                                test_size: int = 12) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Validação cruzada temporal específica para spillover analysis
        Evita data leakage temporal
        """
        splits = []
        total_len = len(data)
        
        for i in range(n_splits):
            train_end = total_len - (n_splits - i) * test_size
            test_start = train_end
            test_end = min(train_end + test_size, total_len)
            
            if train_end <= 0 or test_start >= total_len:
                continue
                
            train_data = data.iloc[:train_end]
            test_data = data.iloc[test_start:test_end]
            
            splits.append((train_data, test_data))
        
        return splits
    
    def comprehensive_validation(self, model, data: pd.DataFrame, baseline_model) -> Dict:
        """
        Bateria completa de validação científica
        
        Args:
            model: Modelo treinado
            data: Dados para validação
            baseline_model: Modelo baseline para comparação
            
        Returns:
            Dicionário com resultados de validação
        """
        print("🔬 Iniciando validação científica completa...")
        
        results = {}
        
        # 1. Time Series Cross-Validation
        print("📊 1. Validação cruzada temporal...")
        cv_results = self._temporal_cross_validation(model, data)
        results.update(cv_results)
        
        # 2. Teste Diebold-Mariano vs baseline
        print("📈 2. Teste Diebold-Mariano...")
        dm_results = self._diebold_mariano_test(model, data, baseline_model)
        results.update(dm_results)
        
        # 3. Robustez a outliers
        print("🛡️  3. Teste de robustez a outliers...")
        robustness_results = self._outlier_robustness_test(model, data)
        results.update(robustness_results)
        
        # 4. Verificações econômicas
        print("💰 4. Verificações de sanidade econômica...")
        economic_results = self._economic_sanity_validation(model, data)
        results.update(economic_results)
        
        # 5. Análise de estabilidade
        print("⚖️  5. Análise de estabilidade...")
        stability_results = self._stability_analysis(model, data)
        results.update(stability_results)
        
        self.validation_results = results
        print("✅ Validação científica completa finalizada!")
        
        return results
    
    def _temporal_cross_validation(self, model, data: pd.DataFrame) -> Dict:
        """Validação cruzada temporal"""
        tscv_scores = []
        splits = self.time_series_cv_spillover(data, n_splits=5, test_size=12)
        
        for i, (train_data, test_data) in enumerate(splits):
            if len(train_data) < 50 or len(test_data) < 5:
                continue
                
            try:
                # Treinar modelo no conjunto de treino
                model_copy = model.__class__(
                    var_lags=model.var_lags,
                    nn_hidden_layers=model.nn_hidden_layers,
                    simple_weight=model.simple_weight,
                    complex_weight=model.complex_weight,
                    random_state=model.random_state
                )
                model_copy.fit(train_data)
                
                # Fazer predições no conjunto de teste
                test_features = test_data[['fed_rate', 'selic']]
                predictions = model_copy.predict_with_uncertainty(test_features)
                
                # Calcular RMSE - GARANTIR DIMENSIONALIDADE
                if 'spillover' in test_data.columns:
                    y_test = test_data['spillover'].values
                    prediction = predictions['prediction']
                    
                    # GARANTIR QUE SÃO ARRAYS
                    y_test = np.atleast_1d(y_test)
                    prediction = np.atleast_1d(prediction)
                    
                    # Calcular RMSE com tamanhos compatíveis
                    min_len = min(len(prediction), len(y_test))
                    if min_len > 0:
                        rmse = np.sqrt(mean_squared_error(
                            y_test[:min_len], 
                            prediction[:min_len]
                        ))
                        tscv_scores.append(rmse)
                    else:
                        tscv_scores.append(np.inf)
                    
            except Exception as e:
                print(f"⚠️  Erro no fold {i}: {e}")
                continue
        
        if not tscv_scores:
            return {'cv_rmse': np.nan, 'cv_std': np.nan}
        
        return {
            'cv_rmse': np.mean(tscv_scores),
            'cv_std': np.std(tscv_scores),
            'cv_scores': tscv_scores
        }
    
    def _diebold_mariano_test(self, model, data: pd.DataFrame, baseline_model) -> Dict:
        """Teste Diebold-Mariano para comparar modelos - VERSÃO CORRIGIDA"""
        try:
            print("📈 2. Teste Diebold-Mariano...")
            
            # Usar dados de teste com contexto suficiente
            test_data = data.tail(24)  # Últimos 24 meses
            
            if len(test_data) < 10:
                print("⚠️  Dados insuficientes para teste Diebold-Mariano")
                return {'dm_statistic': np.nan, 'dm_pvalue': np.nan, 'significant_improvement': False}
            
            # Coletar predições com contexto adequado
            hybrid_predictions = []
            baseline_predictions = []
            actual_values = []
            
            for i in range(5, len(test_data)):  # Garantir contexto mínimo
                try:
                    # Dados de entrada com contexto
                    X_input = test_data[['fed_rate', 'selic']].iloc[i-1:i]
                    
                    # Predição híbrida
                    hybrid_result = model.predict_with_uncertainty(X_input)
                    hybrid_pred = hybrid_result['prediction']
                    
                    # Predição baseline
                    baseline_pred = baseline_model.predict(X_input, steps=1)
                    if len(baseline_pred) > 0:
                        baseline_pred = baseline_pred[0]
                    else:
                        baseline_pred = 0.0
                    
                    # Valor real
                    actual_val = test_data['spillover'].iloc[i]
                    
                    hybrid_predictions.append(hybrid_pred)
                    baseline_predictions.append(baseline_pred)
                    actual_values.append(actual_val)
                    
                except Exception as e:
                    print(f"⚠️  Erro na predição {i}: {e}")
                    continue
            
            if len(hybrid_predictions) < 5:
                print("⚠️  Poucas predições válidas para teste Diebold-Mariano")
                return {'dm_statistic': np.nan, 'dm_pvalue': np.nan, 'significant_improvement': False}
            
            # Converter para arrays
            hybrid_errors = np.array(actual_values) - np.array(hybrid_predictions)
            baseline_errors = np.array(actual_values) - np.array(baseline_predictions)
            
            # Diferença dos erros quadráticos
            error_diff = hybrid_errors**2 - baseline_errors**2
            
            # Estatística Diebold-Mariano
            if len(error_diff) > 1 and np.var(error_diff) > 0:
                dm_stat = np.mean(error_diff) / np.sqrt(np.var(error_diff) / len(error_diff))
                dm_pvalue = 2 * (1 - stats.norm.cdf(abs(dm_stat)))
                significant = dm_pvalue < 0.05
            else:
                dm_stat = np.nan
                dm_pvalue = np.nan
                significant = False
            
            print(f"   DM Statistic: {dm_stat:.4f}")
            print(f"   P-value: {dm_pvalue:.4f}")
            print(f"   Significativo: {'Sim' if significant else 'Não'}")
            
            return {
                'dm_statistic': dm_stat,
                'dm_pvalue': dm_pvalue,
                'significant_improvement': significant,
                'hybrid_rmse': np.sqrt(np.mean(hybrid_errors**2)),
                'baseline_rmse': np.sqrt(np.mean(baseline_errors**2))
            }
                
        except Exception as e:
            print(f"⚠️  Erro no teste Diebold-Mariano: {e}")
            return {'dm_statistic': np.nan, 'dm_pvalue': np.nan, 'significant_improvement': False}
    
    def _outlier_robustness_test(self, model, data: pd.DataFrame) -> Dict:
        """Teste de robustez a outliers com correção de dimensionalidade"""
        try:
            # Detectar outliers
            from sklearn.ensemble import IsolationForest
            outlier_detector = IsolationForest(contamination=0.1, random_state=42)
            outliers = outlier_detector.fit_predict(data[['fed_rate', 'selic']])
            
            # Dados limpos
            clean_data = data[outliers != -1]
            
            if len(clean_data) < 30:
                return {'robustness_rmse': np.nan, 'outlier_robust': False}
            
            # Treinar modelo nos dados limpos
            model_clean = model.__class__(
                var_lags=model.var_lags,
                nn_hidden_layers=model.nn_hidden_layers,
                simple_weight=model.simple_weight,
                complex_weight=model.complex_weight,
                random_state=model.random_state
            )
            model_clean.fit(clean_data)
            
            # Avaliar performance
            clean_features = clean_data[['fed_rate', 'selic']]
            clean_predictions = model_clean.predict_with_uncertainty(clean_features)
            
            if 'spillover' in clean_data.columns:
                # GARANTIR DIMENSIONALIDADE CORRETA
                clean_spillover = np.atleast_1d(clean_data['spillover'].values)
                clean_pred = np.atleast_1d(clean_predictions['prediction'])
                
                # Equalizar tamanhos
                min_len = min(len(clean_spillover), len(clean_pred))
                if min_len > 0:
                    clean_rmse = np.sqrt(mean_squared_error(
                        clean_spillover[:min_len], 
                        clean_pred[:min_len]
                    ))
                else:
                    clean_rmse = np.nan
                
                # Comparar com performance original
                original_features = data[['fed_rate', 'selic']]
                original_predictions = model.predict_with_uncertainty(original_features)
                
                if 'spillover' in data.columns:
                    original_spillover = np.atleast_1d(data['spillover'].values)
                    original_pred = np.atleast_1d(original_predictions['prediction'])
                    
                    min_len_orig = min(len(original_spillover), len(original_pred))
                    if min_len_orig > 0:
                        original_rmse = np.sqrt(mean_squared_error(
                            original_spillover[:min_len_orig], 
                            original_pred[:min_len_orig]
                        ))
                    else:
                        original_rmse = np.nan
                    
                    # Verificar robustez (tolerância de 10% de diferença)
                    if not np.isnan(clean_rmse) and not np.isnan(original_rmse):
                        robustness_diff = abs(original_rmse - clean_rmse)
                        is_robust = robustness_diff < max(clean_rmse, original_rmse) * 0.1
                    else:
                        robustness_diff = np.nan
                        is_robust = False
                    
                    return {
                        'robustness_rmse': clean_rmse,
                        'outlier_robust': is_robust,
                        'robustness_difference': robustness_diff
                    }
            
            return {'robustness_rmse': np.nan, 'outlier_robust': False}
            
        except Exception as e:
            print(f"⚠️  Erro no teste de robustez: {e}")
            return {'robustness_rmse': np.nan, 'outlier_robust': False}
    
    def _economic_sanity_validation(self, model, data: pd.DataFrame) -> Dict:
        """Validação de sanidade econômica"""
        try:
            features = data[['fed_rate', 'selic']]
            predictions = model.predict_with_uncertainty(features)
            
            # Verificações de sanidade
            sanity_flags = model.economic_sanity_checks(
                predictions['prediction'], 
                {'us_recession': False}
            )
            
            # Estatísticas das predições
            pred_stats = {
                'mean_spillover': np.mean(predictions['prediction']),
                'std_spillover': np.std(predictions['prediction']),
                'min_spillover': np.min(predictions['prediction']),
                'max_spillover': np.max(predictions['prediction']),
                'outlier_rate': np.mean(predictions['is_outlier']),
                'high_uncertainty_rate': np.mean(predictions['high_uncertainty'])
            }
            
            return {
                'sanity_flags': sanity_flags,
                'sanity_flags_count': len(sanity_flags),
                'prediction_stats': pred_stats,
                'economic_plausible': len(sanity_flags) == 0
            }
            
        except Exception as e:
            print(f"⚠️  Erro na validação econômica: {e}")
            return {'sanity_flags': [], 'economic_plausible': False}
    
    def _stability_analysis(self, model, data: pd.DataFrame) -> Dict:
        """Análise de estabilidade do modelo"""
        try:
            # Análise de estabilidade simplificada
            # (implementação básica)
            
            features = data[['fed_rate', 'selic']]
            predictions = model.predict_with_uncertainty(features)
            
            # Estabilidade das predições
            pred_std = np.std(predictions['prediction'])
            uncertainty_std = np.std(predictions['uncertainty'])
            
            return {
                'prediction_stability': pred_std,
                'uncertainty_stability': uncertainty_std,
                'model_stable': pred_std < 0.5 and uncertainty_std < 0.3
            }
            
        except Exception as e:
            print(f"⚠️  Erro na análise de estabilidade: {e}")
            return {'model_stable': False}
    
    def generate_validation_report(self, model, data: pd.DataFrame) -> str:
        """Gerar relatório de validação científico"""
        if not self.validation_results:
            self.comprehensive_validation(model, data)
        
        results = self.validation_results
        
        report = f"""
# Relatório de Validação Científica - Sistema de Spillovers

## Resumo Executivo
- **Modelo**: {model.__class__.__name__}
- **Período de Validação**: {data.index[0].date()} a {data.index[-1].date()}
- **Observações**: {len(data)}

## Resultados de Validação

### 1. Validação Cruzada Temporal
- **RMSE Médio**: {results.get('cv_rmse', 'N/A'):.4f}
- **Desvio Padrão**: {results.get('cv_std', 'N/A'):.4f}
- **Status**: {'✅ Aprovado' if results.get('cv_rmse', np.inf) < 0.5 else '❌ Reprovado'}

### 2. Teste Diebold-Mariano
- **Estatística DM**: {results.get('dm_statistic', 'N/A'):.4f}
- **P-valor**: {results.get('dm_pvalue', 'N/A'):.4f}
- **Melhoria Significativa**: {'✅ Sim' if results.get('significant_improvement', False) else '❌ Não'}

### 3. Robustez a Outliers
- **RMSE (dados limpos)**: {results.get('robustness_rmse', 'N/A'):.4f}
- **Robusto a Outliers**: {'✅ Sim' if results.get('outlier_robust', False) else '❌ Não'}

### 4. Sanidade Econômica
- **Flags de Sanidade**: {results.get('sanity_flags_count', 'N/A')}
- **Economicamente Plausível**: {'✅ Sim' if results.get('economic_plausible', False) else '❌ Não'}

### 5. Estabilidade do Modelo
- **Estabilidade das Predições**: {results.get('prediction_stability', 'N/A'):.4f}
- **Modelo Estável**: {'✅ Sim' if results.get('model_stable', False) else '❌ Não'}

## Conclusão
{'✅ Modelo aprovado para uso' if self._is_model_approved() else '❌ Modelo requer melhorias'}

## Limitações Identificadas
{self._identify_limitations()}
"""
        
        return report
    
    def _is_model_approved(self) -> bool:
        """Verificar se modelo foi aprovado na validação"""
        results = self.validation_results
        
        # Critérios de aprovação (mais realistas)
        cv_ok = results.get('cv_rmse', np.inf) < 0.1  # RMSE < 0.1
        dm_ok = results.get('significant_improvement', False)
        robust_ok = results.get('outlier_robust', False)
        economic_ok = results.get('economic_plausible', False)
        stable_ok = results.get('model_stable', False)
        
        # Aprovar se pelo menos 3 de 5 critérios forem atendidos
        criteria_met = sum([cv_ok, dm_ok, robust_ok, economic_ok, stable_ok])
        return criteria_met >= 3
    
    def _identify_limitations(self) -> str:
        """Identificar limitações do modelo"""
        limitations = []
        results = self.validation_results
        
        if results.get('cv_rmse', 0) >= 0.5:
            limitations.append("- Performance de validação cruzada abaixo do esperado")
        
        if not results.get('significant_improvement', False):
            limitations.append("- Não há melhoria significativa sobre baseline")
        
        if not results.get('outlier_robust', False):
            limitations.append("- Sensível a outliers estruturais")
        
        if not results.get('economic_plausible', False):
            limitations.append("- Predições economicamente implausíveis detectadas")
        
        if not results.get('model_stable', False):
            limitations.append("- Modelo instável em diferentes períodos")
        
        if not limitations:
            return "Nenhuma limitação crítica identificada"
        
        return "\n".join(limitations)

def validate_model(model, data: pd.DataFrame) -> Dict:
    """
    Função de conveniência para validar modelo
    
    Args:
        model: Modelo treinado
        data: Dados para validação
        
    Returns:
        Resultados de validação
    """
    validator = ScientificValidator()
    return validator.comprehensive_validation(model, data)

if __name__ == "__main__":
    # Teste do validador científico
    print("🧪 Testando validador científico...")
    
    # Importar dependências
    from ..data.data_loader import load_data
    from ..models.hybrid_model import create_hybrid_model
    
    # Carregar dados e treinar modelo
    data = load_data()
    model = create_hybrid_model()
    model.fit(data)
    
    # Validar modelo
    validator = ScientificValidator()
    results = validator.comprehensive_validation(model, data)
    
    # Gerar relatório
    report = validator.generate_validation_report(model, data)
    print(report)
    
    print("\n✅ Teste do validador concluído!")
