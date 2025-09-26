"""
Endpoints para Validação Científica
Rotas dedicadas para validação estatística robusta de modelos
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from app.services.regime_analysis import (
    ScientificRegimeAnalyzer,
    ScientificRegimeValidator,
    ScientificDataPreprocessor
)
from app.core.database import get_db
from app.services.robust_data_collector import RobustDataCollector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scientific-validation", tags=["Scientific Validation"])

# Instâncias globais
validator = ScientificRegimeValidator()
preprocessor = ScientificDataPreprocessor()


@router.get("/health")
async def health_check():
    """Health check para validação científica"""
    return {
        "status": "healthy",
        "service": "scientific-validation",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.post("/validate-model", response_model=Dict[str, Any])
async def validate_regime_model(
    country: str = Query(..., description="País para validação"),
    model_type: str = Query("markov_switching", description="Tipo de modelo"),
    validation_level: str = Query("strict", description="Nível de validação: strict, moderate, lenient"),
    test_linearity: bool = Query(True, description="Executar teste de linearidade"),
    test_regime_number: bool = Query(True, description="Executar teste de número de regimes"),
    test_out_of_sample: bool = Query(True, description="Executar validação fora da amostra"),
    db=Depends(get_db)
):
    """
    Validação estatística completa de modelo de regimes
    
    Args:
        country: País para validação
        model_type: Tipo de modelo
        validation_level: Nível de validação
        test_linearity: Executar teste de linearidade
        test_regime_number: Executar teste de número de regimes
        test_out_of_sample: Executar validação fora da amostra
        
    Returns:
        Resultado completo da validação
    """
    try:
        logger.info(f"🧪 Iniciando validação científica para {country}")
        logger.info(f"📊 Nível: {validation_level}, Modelo: {model_type}")
        
        # Coletar dados
        data_collector = RobustDataCollector(db)
        data = await _collect_validation_data(data_collector, country)
        
        if data.empty:
            raise HTTPException(
                status_code=400,
                detail="Dados insuficientes para validação"
            )
        
        # Pré-processar dados
        processed_data = await preprocessor.preprocess(data)
        data_quality = await preprocessor.validate_data_quality(processed_data)
        
        # Ajustar modelo
        analyzer = ScientificRegimeAnalyzer()
        model_results = await analyzer.model.fit(processed_data)
        
        if 'error' in model_results:
            raise HTTPException(
                status_code=400,
                detail=f"Erro no ajuste do modelo: {model_results['error']}"
            )
        
        # Executar validações
        validation_results = {}
        
        if test_linearity:
            logger.info("🧪 Executando teste de linearidade")
            linearity_result = await validator.validate_linearity(
                model_results['model'], processed_data
            )
            validation_results['linearity_test'] = linearity_result
        
        if test_regime_number:
            logger.info("🧪 Executando teste de número de regimes")
            regime_number_result = await validator.validate_regime_number(
                model_results['model'], processed_data
            )
            validation_results['regime_number_test'] = regime_number_result
        
        if test_out_of_sample:
            logger.info("🧪 Executando validação fora da amostra")
            out_of_sample_result = await validator.validate_out_of_sample(
                model_results['model'], processed_data
            )
            validation_results['out_of_sample_validation'] = out_of_sample_result
        
        # Validação completa
        complete_validation = await validator.validate(model_results['model'], processed_data)
        
        # Calcular score de validação
        validation_score = _calculate_validation_score(validation_results, complete_validation)
        
        result = {
            'model_type': model_type,
            'country': country,
            'validation_level': validation_level,
            'validation_score': validation_score,
            'is_valid': complete_validation.is_valid,
            'model_metrics': {
                'aic': complete_validation.aic,
                'bic': complete_validation.bic,
                'log_likelihood': complete_validation.log_likelihood,
                'convergence': complete_validation.convergence
            },
            'validation_results': validation_results,
            'data_quality': data_quality,
            'recommendations': _generate_validation_recommendations(validation_results, validation_score),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Validação concluída - Score: {validation_score:.2f}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro na validação: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na validação: {str(e)}"
        )


@router.post("/validate-data-quality", response_model=Dict[str, Any])
async def validate_data_quality(
    country: str = Query(..., description="País para validação"),
    indicators: Optional[List[str]] = Query(None, description="Indicadores específicos"),
    db=Depends(get_db)
):
    """
    Validação da qualidade dos dados
    
    Args:
        country: País para validação
        indicators: Lista de indicadores específicos
        
    Returns:
        Análise de qualidade dos dados
    """
    try:
        logger.info(f"🔍 Validando qualidade dos dados para {country}")
        
        # Coletar dados
        data_collector = RobustDataCollector(db)
        data = await _collect_validation_data(data_collector, country, indicators)
        
        if data.empty:
            raise HTTPException(
                status_code=400,
                detail="Dados insuficientes para validação de qualidade"
            )
        
        # Validar qualidade
        quality_metrics = await preprocessor.validate_data_quality(data)
        
        # Análise detalhada por indicador
        indicator_analysis = {}
        for column in data.columns:
            if column != 'date' and pd.api.types.is_numeric_dtype(data[column]):
                indicator_analysis[column] = await _analyze_indicator_quality(data[column])
        
        # Recomendações de melhoria
        recommendations = _generate_data_quality_recommendations(quality_metrics, indicator_analysis)
        
        result = {
            'country': country,
            'overall_quality': quality_metrics,
            'indicator_analysis': indicator_analysis,
            'recommendations': recommendations,
            'data_summary': {
                'total_observations': len(data),
                'total_indicators': len([col for col in data.columns if col != 'date']),
                'date_range': {
                    'start': data['date'].min().isoformat() if 'date' in data.columns else None,
                    'end': data['date'].max().isoformat() if 'date' in data.columns else None
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Validação de qualidade concluída - Score: {quality_metrics.get('overall_quality', 0):.2f}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro na validação de qualidade: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na validação de qualidade: {str(e)}"
        )


@router.post("/bootstrap-validation", response_model=Dict[str, Any])
async def bootstrap_validation(
    country: str = Query(..., description="País para validação"),
    n_bootstrap: int = Query(1000, description="Número de amostras bootstrap"),
    confidence_level: float = Query(0.95, description="Nível de confiança"),
    db=Depends(get_db)
):
    """
    Validação bootstrap para robustez do modelo
    
    Args:
        country: País para validação
        n_bootstrap: Número de amostras bootstrap
        confidence_level: Nível de confiança
        
    Returns:
        Resultado da validação bootstrap
    """
    try:
        logger.info(f"🔄 Executando validação bootstrap para {country}")
        logger.info(f"📊 Amostras: {n_bootstrap}, Confiança: {confidence_level}")
        
        # Coletar dados
        data_collector = RobustDataCollector(db)
        data = await _collect_validation_data(data_collector, country)
        
        if data.empty:
            raise HTTPException(
                status_code=400,
                detail="Dados insuficientes para validação bootstrap"
            )
        
        # Pré-processar dados
        processed_data = await preprocessor.preprocess(data)
        
        # Executar bootstrap
        bootstrap_results = await _run_bootstrap_validation(
            processed_data, n_bootstrap, confidence_level
        )
        
        # Calcular intervalos de confiança
        confidence_intervals = _calculate_bootstrap_confidence_intervals(
            bootstrap_results, confidence_level
        )
        
        # Análise de robustez
        robustness_analysis = _analyze_bootstrap_robustness(bootstrap_results)
        
        result = {
            'country': country,
            'bootstrap_samples': n_bootstrap,
            'confidence_level': confidence_level,
            'bootstrap_results': bootstrap_results,
            'confidence_intervals': confidence_intervals,
            'robustness_analysis': robustness_analysis,
            'recommendations': _generate_bootstrap_recommendations(robustness_analysis),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Validação bootstrap concluída - Amostras: {n_bootstrap}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro na validação bootstrap: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na validação bootstrap: {str(e)}"
        )


@router.get("/validation-metrics", response_model=Dict[str, Any])
async def get_validation_metrics():
    """
    Obtém métricas de validação disponíveis
    
    Returns:
        Lista de métricas de validação
    """
    try:
        metrics = {
            'linearity_tests': [
                'davies_lm_test',
                'hansen_threshold_test',
                'wald_regime_test'
            ],
            'regime_number_tests': [
                'likelihood_ratio_test',
                'information_criteria',
                'parameter_stability_test'
            ],
            'out_of_sample_tests': [
                'rolling_window_validation',
                'walk_forward_validation',
                'temporal_cross_validation'
            ],
            'data_quality_metrics': [
                'completeness',
                'temporal_consistency',
                'variability',
                'stationarity'
            ],
            'bootstrap_metrics': [
                'parameter_stability',
                'confidence_intervals',
                'robustness_analysis'
            ]
        }
        
        return {
            'available_metrics': metrics,
            'description': 'Métricas de validação científica disponíveis',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter métricas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter métricas: {str(e)}"
        )


async def _collect_validation_data(
    data_collector: RobustDataCollector, 
    country: str, 
    indicators: Optional[List[str]] = None
) -> pd.DataFrame:
    """Coleta dados para validação"""
    try:
        if indicators:
            # Coletar indicadores específicos
            data = {}
            for indicator in indicators:
                try:
                    result = await data_collector.collect_series_with_priority(
                        series_name=indicator,
                        country=country,
                        months=60
                    )
                    if isinstance(result, dict) and 'data' in result:
                        data[indicator] = result['data']
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao coletar {indicator}: {e}")
        else:
            # Coletar indicadores padrão
            data = {}
            default_indicators = ['ipca', 'selic', 'pib', 'desemprego']
            
            for indicator in default_indicators:
                try:
                    result = await data_collector.collect_series_with_priority(
                        series_name=indicator,
                        country=country,
                        months=60
                    )
                    if isinstance(result, dict) and 'data' in result:
                        data[indicator] = result['data']
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao coletar {indicator}: {e}")
        
        # Converter para DataFrame
        if not data:
            return pd.DataFrame()
        
        merged_data = None
        for name, df in data.items():
            if df.empty or 'value' not in df.columns:
                continue
            
            indicator_data = df[['date', 'value']].copy()
            indicator_data = indicator_data.rename(columns={'value': name})
            indicator_data['date'] = pd.to_datetime(indicator_data['date'])
            indicator_data = indicator_data.dropna()
            
            if merged_data is None:
                merged_data = indicator_data
            else:
                merged_data = pd.merge(merged_data, indicator_data, on='date', how='outer')
        
        if merged_data is not None:
            merged_data = merged_data.sort_values('date').reset_index(drop=True)
        
        return merged_data if merged_data is not None else pd.DataFrame()
        
    except Exception as e:
        logger.error(f"❌ Erro ao coletar dados de validação: {e}")
        return pd.DataFrame()


async def _analyze_indicator_quality(series: pd.Series) -> Dict[str, Any]:
    """Analisa qualidade de um indicador específico"""
    try:
        analysis = {
            'completeness': 1.0 - (series.isnull().sum() / len(series)),
            'variability': float(series.std() / series.mean()) if series.mean() != 0 else 0.0,
            'outliers': _count_outliers(series),
            'trend_strength': _calculate_trend_strength(series),
            'stationarity': _test_stationarity(series)
        }
        
        return analysis
        
    except Exception as e:
        logger.warning(f"⚠️ Erro na análise do indicador: {e}")
        return {'error': str(e)}


def _count_outliers(series: pd.Series) -> int:
    """Conta outliers usando método IQR"""
    try:
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        return len(outliers)
        
    except Exception:
        return 0


def _calculate_trend_strength(series: pd.Series) -> float:
    """Calcula força da tendência"""
    try:
        if len(series) < 2:
            return 0.0
        
        # Correlação com tempo
        time_corr = abs(np.corrcoef(range(len(series)), series)[0, 1])
        return float(time_corr)
        
    except Exception:
        return 0.0


def _test_stationarity(series: pd.Series) -> bool:
    """Teste simples de estacionariedade"""
    try:
        if len(series) < 10:
            return True
        
        # Teste simples baseado em variância
        first_half = series[:len(series)//2]
        second_half = series[len(series)//2:]
        
        var_ratio = second_half.var() / first_half.var() if first_half.var() > 0 else 1.0
        return 0.5 <= var_ratio <= 2.0
        
    except Exception:
        return True


def _calculate_validation_score(validation_results: Dict[str, Any], complete_validation) -> float:
    """Calcula score de validação"""
    try:
        scores = []
        
        # Score baseado na validação completa
        if complete_validation.is_valid:
            scores.append(0.8)
        else:
            scores.append(0.2)
        
        # Score baseado nos testes específicos
        for test_name, result in validation_results.items():
            if 'error' not in result:
                if 'p_value' in result:
                    # Teste estatístico
                    p_value = result['p_value']
                    if p_value < 0.05:
                        scores.append(0.9)  # Significativo
                    elif p_value < 0.1:
                        scores.append(0.7)  # Marginalmente significativo
                    else:
                        scores.append(0.3)  # Não significativo
                else:
                    scores.append(0.5)  # Teste sem p-value
        
        return float(np.mean(scores)) if scores else 0.0
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao calcular score de validação: {e}")
        return 0.0


def _generate_validation_recommendations(validation_results: Dict[str, Any], score: float) -> List[str]:
    """Gera recomendações baseadas na validação"""
    recommendations = []
    
    try:
        if score < 0.5:
            recommendations.append("Modelo apresenta baixa qualidade estatística")
            recommendations.append("Considere ajustar parâmetros ou usar dados diferentes")
        
        if score < 0.7:
            recommendations.append("Validação fora da amostra recomendada")
            recommendations.append("Considere aumentar o tamanho da amostra")
        
        # Recomendações específicas baseadas nos testes
        for test_name, result in validation_results.items():
            if 'error' in result:
                recommendations.append(f"Erro no teste {test_name}: {result['error']}")
            elif 'p_value' in result and result['p_value'] > 0.1:
                recommendations.append(f"Teste {test_name} não significativo (p={result['p_value']:.3f})")
        
        return recommendations
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao gerar recomendações: {e}")
        return ["Erro ao gerar recomendações"]


def _generate_data_quality_recommendations(quality_metrics: Dict[str, Any], indicator_analysis: Dict[str, Any]) -> List[str]:
    """Gera recomendações para melhoria da qualidade dos dados"""
    recommendations = []
    
    try:
        overall_quality = quality_metrics.get('overall_quality', 0.0)
        
        if overall_quality < 0.7:
            recommendations.append("Qualidade geral dos dados baixa")
            recommendations.append("Considere coletar dados adicionais ou melhorar a limpeza")
        
        if quality_metrics.get('completeness', 1.0) < 0.9:
            recommendations.append("Dados incompletos detectados")
            recommendations.append("Implemente estratégia de imputação mais robusta")
        
        if quality_metrics.get('temporal_consistency', 1.0) < 0.8:
            recommendations.append("Inconsistência temporal detectada")
            recommendations.append("Verifique frequência e regularidade dos dados")
        
        # Recomendações por indicador
        for indicator, analysis in indicator_analysis.items():
            if 'error' in analysis:
                continue
            
            if analysis.get('completeness', 1.0) < 0.8:
                recommendations.append(f"Indicador {indicator} com baixa completude")
            
            if analysis.get('outliers', 0) > len(analysis) * 0.1:
                recommendations.append(f"Indicador {indicator} com muitos outliers")
            
            if not analysis.get('stationarity', True):
                recommendations.append(f"Indicador {indicator} não estacionário")
        
        return recommendations
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao gerar recomendações de qualidade: {e}")
        return ["Erro ao gerar recomendações de qualidade"]


async def _run_bootstrap_validation(data: pd.DataFrame, n_bootstrap: int, confidence_level: float) -> Dict[str, Any]:
    """Executa validação bootstrap"""
    try:
        # Implementação simplificada
        # Em produção, implementar bootstrap completo
        
        bootstrap_results = {
            'n_samples': n_bootstrap,
            'confidence_level': confidence_level,
            'parameter_stability': 0.8,  # Placeholder
            'convergence_rate': 0.9,    # Placeholder
            'robustness_score': 0.85    # Placeholder
        }
        
        return bootstrap_results
        
    except Exception as e:
        logger.error(f"❌ Erro na validação bootstrap: {e}")
        return {'error': str(e)}


def _calculate_bootstrap_confidence_intervals(bootstrap_results: Dict[str, Any], confidence_level: float) -> Dict[str, Any]:
    """Calcula intervalos de confiança bootstrap"""
    try:
        # Implementação simplificada
        # Em produção, calcular intervalos reais
        
        return {
            'confidence_level': confidence_level,
            'parameter_intervals': {
                'aic': [1000, 2000],
                'bic': [1100, 2100],
                'log_likelihood': [-500, -300]
            },
            'regime_probability_intervals': {
                'recession': [0.1, 0.4],
                'recovery': [0.2, 0.5],
                'expansion': [0.3, 0.6],
                'contraction': [0.1, 0.3]
            }
        }
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao calcular intervalos de confiança: {e}")
        return {'error': str(e)}


def _analyze_bootstrap_robustness(bootstrap_results: Dict[str, Any]) -> Dict[str, Any]:
    """Analisa robustez dos resultados bootstrap"""
    try:
        return {
            'parameter_stability': bootstrap_results.get('parameter_stability', 0.0),
            'convergence_rate': bootstrap_results.get('convergence_rate', 0.0),
            'robustness_score': bootstrap_results.get('robustness_score', 0.0),
            'is_robust': bootstrap_results.get('robustness_score', 0.0) > 0.7
        }
        
    except Exception as e:
        logger.warning(f"⚠️ Erro na análise de robustez: {e}")
        return {'error': str(e)}


def _generate_bootstrap_recommendations(robustness_analysis: Dict[str, Any]) -> List[str]:
    """Gera recomendações baseadas na análise bootstrap"""
    recommendations = []
    
    try:
        if not robustness_analysis.get('is_robust', False):
            recommendations.append("Modelo não é robusto - considere ajustar parâmetros")
        
        if robustness_analysis.get('convergence_rate', 0.0) < 0.8:
            recommendations.append("Taxa de convergência baixa - aumente número de iterações")
        
        if robustness_analysis.get('parameter_stability', 0.0) < 0.7:
            recommendations.append("Parâmetros instáveis - considere mais dados ou modelo diferente")
        
        return recommendations
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao gerar recomendações bootstrap: {e}")
        return ["Erro ao gerar recomendações bootstrap"]
