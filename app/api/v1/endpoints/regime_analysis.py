"""
Endpoints para Análise Científica de Regimes Econômicos
Rotas dedicadas para análise robusta de regimes
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import pandas as pd

from app.services.regime_analysis import (
    ScientificRegimeAnalyzer,
    AustrianCompatibleRegimeAnalyzer,
    RegimeAnalysisResult,
    RegimeType
)
from app.core.database import get_db
from app.services.robust_data_collector import RobustDataCollector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regime-analysis", tags=["Regime Analysis"])

# Instâncias globais dos analisadores
scientific_analyzer = ScientificRegimeAnalyzer()
austrian_analyzer = AustrianCompatibleRegimeAnalyzer()


@router.get("/health")
async def health_check():
    """Health check para análise de regimes"""
    return {
        "status": "healthy",
        "service": "regime-analysis",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_regimes(
    country: str = Query(..., description="País para análise (BRA, USA, etc.)"),
    indicators: Optional[List[str]] = Query(None, description="Lista de indicadores específicos"),
    analysis_type: str = Query("scientific", description="Tipo de análise: scientific, austrian, hybrid"),
    max_regimes: int = Query(5, description="Número máximo de regimes a testar"),
    confidence_threshold: float = Query(0.6, description="Limiar de confiança para identificação"),
    db=Depends(get_db)
):
    """
    Análise científica de regimes econômicos
    
    Args:
        country: País para análise
        indicators: Lista de indicadores específicos (opcional)
        analysis_type: Tipo de análise (scientific, austrian, hybrid)
        max_regimes: Número máximo de regimes a testar
        confidence_threshold: Limiar de confiança
        
    Returns:
        Resultado completo da análise de regimes
    """
    try:
        logger.info(f"🚀 Iniciando análise de regimes para {country}")
        logger.info(f"📊 Tipo: {analysis_type}, Max regimes: {max_regimes}")
        
        # Coletar dados
        data_collector = RobustDataCollector(db)
        
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
            data = await _collect_default_indicators(data_collector, country)
        
        if not data:
            raise HTTPException(
                status_code=400,
                detail="Nenhum dado disponível para análise"
            )
        
        # Converter para DataFrame
        analysis_data = _prepare_analysis_data(data)
        
        # Executar análise baseada no tipo
        if analysis_type == "scientific":
            result = await scientific_analyzer.analyze_regimes(analysis_data, country)
        elif analysis_type == "austrian":
            result = await _run_austrian_analysis(analysis_data, country)
        elif analysis_type == "hybrid":
            result = await _run_hybrid_analysis(analysis_data, country)
        else:
            raise HTTPException(
                status_code=400,
                detail="Tipo de análise inválido. Use: scientific, austrian, hybrid"
            )
        
        # Converter resultado para dict
        result_dict = _convert_result_to_dict(result)
        
        logger.info(f"✅ Análise concluída - Regime: {result_dict.get('current_regime', 'UNKNOWN')}")
        return result_dict
        
    except Exception as e:
        logger.error(f"❌ Erro na análise de regimes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na análise de regimes: {str(e)}"
        )


@router.get("/forecast", response_model=List[Dict[str, Any]])
async def forecast_regimes(
    country: str = Query(..., description="País para previsão"),
    horizon: int = Query(6, description="Horizonte de previsão em meses"),
    analysis_type: str = Query("scientific", description="Tipo de análise"),
    db=Depends(get_db)
):
    """
    Previsão de regimes econômicos futuros
    
    Args:
        country: País para previsão
        horizon: Horizonte de previsão em meses
        analysis_type: Tipo de análise
        
    Returns:
        Lista com previsões de regime
    """
    try:
        logger.info(f"🔮 Gerando previsão de regimes para {country}")
        logger.info(f"📅 Horizonte: {horizon} meses")
        
        # Coletar dados históricos
        data_collector = RobustDataCollector(db)
        data = await _collect_default_indicators(data_collector, country)
        
        if not data:
            raise HTTPException(
                status_code=400,
                detail="Dados insuficientes para previsão"
            )
        
        # Preparar dados
        analysis_data = _prepare_analysis_data(data)
        
        # Gerar previsão
        if analysis_type == "scientific":
            forecast = await scientific_analyzer.get_regime_forecast(analysis_data, horizon)
        else:
            # Para outros tipos, usar análise científica como base
            forecast = await scientific_analyzer.get_regime_forecast(analysis_data, horizon)
        
        logger.info(f"✅ Previsão gerada: {len(forecast)} períodos")
        return forecast
        
    except Exception as e:
        logger.error(f"❌ Erro na previsão: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na previsão: {str(e)}"
        )


@router.get("/validation", response_model=Dict[str, Any])
async def validate_regime_model(
    country: str = Query(..., description="País para validação"),
    model_type: str = Query("markov_switching", description="Tipo de modelo"),
    db=Depends(get_db)
):
    """
    Validação estatística de modelo de regimes
    
    Args:
        country: País para validação
        model_type: Tipo de modelo
        
    Returns:
        Resultado da validação estatística
    """
    try:
        logger.info(f"🧪 Validando modelo de regimes para {country}")
        
        # Coletar dados
        data_collector = RobustDataCollector(db)
        data = await _collect_default_indicators(data_collector, country)
        
        if not data:
            raise HTTPException(
                status_code=400,
                detail="Dados insuficientes para validação"
            )
        
        # Preparar dados
        analysis_data = _prepare_analysis_data(data)
        
        # Ajustar modelo
        model_results = await scientific_analyzer.model.fit(analysis_data)
        
        if 'error' in model_results:
            raise HTTPException(
                status_code=400,
                detail=f"Erro no ajuste do modelo: {model_results['error']}"
            )
        
        # Validar modelo
        validation_result = await scientific_analyzer.validator.validate(
            model_results['model'], analysis_data
        )
        
        # Converter para dict
        validation_dict = {
            'is_valid': validation_result.is_valid,
            'aic': validation_result.aic,
            'bic': validation_result.bic,
            'log_likelihood': validation_result.log_likelihood,
            'convergence': validation_result.convergence,
            'linearity_test': validation_result.linearity_test,
            'regime_number_test': validation_result.regime_number_test,
            'out_of_sample_metrics': validation_result.out_of_sample_metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Validação concluída - Válido: {validation_result.is_valid}")
        return validation_dict
        
    except Exception as e:
        logger.error(f"❌ Erro na validação: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na validação: {str(e)}"
        )


@router.get("/characteristics", response_model=Dict[str, Any])
async def get_regime_characteristics(
    country: str = Query(..., description="País para análise"),
    db=Depends(get_db)
):
    """
    Obtém características detalhadas dos regimes identificados
    
    Args:
        country: País para análise
        
    Returns:
        Características dos regimes
    """
    try:
        logger.info(f"🔍 Analisando características dos regimes para {country}")
        
        # Coletar dados
        data_collector = RobustDataCollector(db)
        data = await _collect_default_indicators(data_collector, country)
        
        if not data:
            raise HTTPException(
                status_code=400,
                detail="Dados insuficientes para análise"
            )
        
        # Preparar dados
        analysis_data = _prepare_analysis_data(data)
        
        # Ajustar modelo
        model_results = await scientific_analyzer.model.fit(analysis_data)
        
        if 'error' in model_results:
            raise HTTPException(
                status_code=400,
                detail=f"Erro no ajuste do modelo: {model_results['error']}"
            )
        
        # Caracterizar regimes
        characteristics = await scientific_analyzer.characterizer.characterize_regimes(
            model_results['model'], analysis_data
        )
        
        # Converter para dict
        characteristics_dict = {}
        for regime_type, char in characteristics.items():
            characteristics_dict[regime_type.value] = {
                'name': char.name,
                'duration_months': char.duration_months,
                'frequency': char.frequency,
                'mean_values': char.mean_values,
                'std_values': char.std_values,
                'confidence': char.confidence,
                'typical_periods': char.typical_periods
            }
        
        logger.info(f"✅ Características obtidas: {len(characteristics)} regimes")
        return {
            'regime_characteristics': characteristics_dict,
            'total_regimes': len(characteristics),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter características: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter características: {str(e)}"
        )


@router.get("/austrian-analysis", response_model=Dict[str, Any])
async def austrian_regime_analysis(
    country: str = Query(..., description="País para análise"),
    db=Depends(get_db)
):
    """
    Análise de regimes compatível com escola austríaca
    
    Args:
        country: País para análise
        
    Returns:
        Análise baseada em teoria austríaca
    """
    try:
        logger.info(f"🏛️ Executando análise austríaca para {country}")
        
        # Coletar dados
        data_collector = RobustDataCollector(db)
        data = await _collect_default_indicators(data_collector, country)
        
        if not data:
            raise HTTPException(
                status_code=400,
                detail="Dados insuficientes para análise austríaca"
            )
        
        # Preparar dados
        analysis_data = _prepare_analysis_data(data)
        
        # Executar análises austríacas
        credit_analysis = await austrian_analyzer.detect_credit_expansion(analysis_data)
        production_analysis = await austrian_analyzer.detect_production_distortions(analysis_data)
        malinvestment_analysis = await austrian_analyzer.detect_malinvestment_signals(analysis_data)
        monetary_analysis = await austrian_analyzer.analyze_monetary_policy_cycle(analysis_data)
        
        result = {
            'credit_expansion': credit_analysis,
            'production_distortions': production_analysis,
            'malinvestment_signals': malinvestment_analysis,
            'monetary_policy_cycle': monetary_analysis,
            'analysis_type': 'austrian',
            'country': country,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Análise austríaca concluída para {country}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro na análise austríaca: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na análise austríaca: {str(e)}"
        )


async def _collect_default_indicators(data_collector: RobustDataCollector, country: str) -> Dict[str, pd.DataFrame]:
    """Coleta indicadores padrão para análise"""
    try:
        indicators = {}
        
        # Indicadores básicos
        basic_indicators = ['ipca', 'selic', 'pib', 'desemprego']
        
        for indicator in basic_indicators:
            try:
                result = await data_collector.collect_series_with_priority(
                    series_name=indicator,
                    country=country,
                    months=60
                )
                if isinstance(result, dict) and 'data' in result:
                    indicators[indicator] = result['data']
            except Exception as e:
                logger.warning(f"⚠️ Erro ao coletar {indicator}: {e}")
        
        return indicators
        
    except Exception as e:
        logger.error(f"❌ Erro ao coletar indicadores padrão: {e}")
        return {}


def _prepare_analysis_data(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Prepara dados para análise"""
    try:
        if not data:
            return pd.DataFrame()
        
        # Mesclar dados por data
        merged_data = None
        
        for name, df in data.items():
            if df.empty or 'value' not in df.columns:
                continue
            
            # Preparar dados
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
        logger.error(f"❌ Erro ao preparar dados: {e}")
        return pd.DataFrame()


def _convert_result_to_dict(result: RegimeAnalysisResult) -> Dict[str, Any]:
    """Converte resultado para dicionário"""
    try:
        return {
            'current_regime': result.current_regime.value,
            'regime_probabilities': {k.value: v for k, v in result.regime_probabilities.items()},
            'regime_characteristics': {
                k.value: {
                    'name': v.name,
                    'duration_months': v.duration_months,
                    'frequency': v.frequency,
                    'mean_values': v.mean_values,
                    'std_values': v.std_values,
                    'confidence': v.confidence,
                    'typical_periods': v.typical_periods
                } for k, v in result.regime_characteristics.items()
            },
            'transition_matrix': {
                k.value: {kk.value: vv for kk, vv in v.items()}
                for k, v in result.transition_matrix.items()
            },
            'model_validation': {
                'is_valid': result.model_validation.is_valid,
                'aic': result.model_validation.aic,
                'bic': result.model_validation.bic,
                'log_likelihood': result.model_validation.log_likelihood,
                'convergence': result.model_validation.convergence,
                'linearity_test': result.model_validation.linearity_test,
                'regime_number_test': result.model_validation.regime_number_test,
                'out_of_sample_metrics': result.model_validation.out_of_sample_metrics
            },
            'confidence': result.confidence,
            'timestamp': result.timestamp,
            'data_quality': result.data_quality
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao converter resultado: {e}")
        return {'error': str(e)}


async def _run_austrian_analysis(data: pd.DataFrame, country: str) -> Dict[str, Any]:
    """Executa análise austríaca"""
    try:
        # Executar análises austríacas
        credit_analysis = await austrian_analyzer.detect_credit_expansion(data)
        production_analysis = await austrian_analyzer.detect_production_distortions(data)
        malinvestment_analysis = await austrian_analyzer.detect_malinvestment_signals(data)
        monetary_analysis = await austrian_analyzer.analyze_monetary_policy_cycle(data)
        
        return {
            'analysis_type': 'austrian',
            'country': country,
            'credit_expansion': credit_analysis,
            'production_distortions': production_analysis,
            'malinvestment_signals': malinvestment_analysis,
            'monetary_policy_cycle': monetary_analysis,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na análise austríaca: {e}")
        return {'error': str(e)}


async def _run_hybrid_analysis(data: pd.DataFrame, country: str) -> Dict[str, Any]:
    """Executa análise híbrida (científica + austríaca)"""
    try:
        # Análise científica
        scientific_result = await scientific_analyzer.analyze_regimes(data, country)
        
        # Análise austríaca
        austrian_result = await _run_austrian_analysis(data, country)
        
        return {
            'analysis_type': 'hybrid',
            'country': country,
            'scientific_analysis': _convert_result_to_dict(scientific_result),
            'austrian_analysis': austrian_result,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na análise híbrida: {e}")
        return {'error': str(e)}
