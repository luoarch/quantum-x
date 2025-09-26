"""
Endpoints para Análise Macroeconômica Avançada
Sistema completo de análise macro com dados históricos
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.macro_analysis.pipeline import MacroAnalysisPipeline, PipelineConfig
from app.services.macro_analysis.historical_data_manager import HistoricalDataManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/analysis/complete")
async def get_complete_macro_analysis(
    country: str = Query("BRA", description="País para análise"),
    force_refresh: bool = Query(False, description="Forçar atualização dos dados"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Executa análise macroeconômica completa
    
    Args:
        country: País para análise (BRA, USA, GLOBAL)
        force_refresh: Forçar atualização dos dados
        db: Sessão do banco de dados
        
    Returns:
        Dict com resultado completo da análise
    """
    try:
        logger.info(f"🚀 Iniciando análise macro completa para {country}")
        
        # Configurar pipeline
        config = PipelineConfig(
            country=country,
            force_data_refresh=force_refresh
        )
        
        # Executar análise
        pipeline = MacroAnalysisPipeline(db, config)
        result = await pipeline.run_complete_analysis(country, force_refresh)
        
        # Converter resultado para dict
        analysis_dict = {
            'country': country,
            'regimes': result.regimes,
            'market_cycles': result.market_cycles,
            'transitions': result.transitions,
            'signals': result.signals,
            'confidence': result.confidence,
            'data_quality': result.data_quality,
            'timestamp': result.timestamp.isoformat(),
            'pipeline_metadata': getattr(result, 'pipeline_metadata', {})
        }
        
        logger.info(f"✅ Análise macro concluída para {country} - Confiança: {result.confidence:.2%}")
        return analysis_dict
        
    except Exception as e:
        logger.error(f"❌ Erro na análise macro: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na análise macro: {str(e)}")


@router.get("/analysis/historical")
async def get_historical_analysis(
    country: str = Query("BRA", description="País para análise"),
    start_date: str = Query(None, description="Data de início (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Data de fim (YYYY-MM-DD)"),
    months: int = Query(12, description="Número de meses para análise"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Executa análise histórica para período específico
    
    Args:
        country: País para análise
        start_date: Data de início
        end_date: Data de fim
        months: Número de meses (se start_date não especificado)
        db: Sessão do banco de dados
        
    Returns:
        Dict com análise histórica
    """
    try:
        logger.info(f"📚 Iniciando análise histórica para {country}")
        
        # Processar datas
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now() - timedelta(days=months * 30)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = datetime.now()
        
        # Executar análise histórica
        pipeline = MacroAnalysisPipeline(db)
        result = await pipeline.run_historical_analysis(country, start_dt, end_dt)
        
        logger.info(f"✅ Análise histórica concluída para {country}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro na análise histórica: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na análise histórica: {str(e)}")


@router.get("/analysis/comparative")
async def get_comparative_analysis(
    countries: str = Query("BRA,USA", description="Países para comparação (separados por vírgula)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Executa análise comparativa entre países
    
    Args:
        countries: Lista de países separados por vírgula
        db: Sessão do banco de dados
        
    Returns:
        Dict com análise comparativa
    """
    try:
        country_list = [c.strip().upper() for c in countries.split(',')]
        logger.info(f"🌍 Iniciando análise comparativa para {country_list}")
        
        # Executar análise comparativa
        pipeline = MacroAnalysisPipeline(db)
        result = await pipeline.run_comparative_analysis(country_list)
        
        logger.info(f"✅ Análise comparativa concluída para {len(country_list)} países")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro na análise comparativa: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na análise comparativa: {str(e)}")


@router.get("/analysis/sentiment")
async def get_sentiment_analysis(
    force_refresh: bool = Query(False, description="Forçar atualização dos dados"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Executa análise de sentimento de mercado
    
    Args:
        force_refresh: Forçar atualização dos dados
        db: Sessão do banco de dados
        
    Returns:
        Dict com análise de sentimento
    """
    try:
        logger.info("😊 Iniciando análise de sentimento")
        
        # Executar análise de sentimento
        pipeline = MacroAnalysisPipeline(db)
        result = await pipeline.run_sentiment_analysis(force_refresh)
        
        logger.info("✅ Análise de sentimento concluída")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro na análise de sentimento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na análise de sentimento: {str(e)}")


@router.get("/analysis/risk-assessment")
async def get_risk_assessment(
    country: str = Query("BRA", description="País para avaliação"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Executa avaliação de risco macroeconômico
    
    Args:
        country: País para avaliação
        db: Sessão do banco de dados
        
    Returns:
        Dict com avaliação de risco
    """
    try:
        logger.info(f"⚠️ Iniciando avaliação de risco para {country}")
        
        # Executar avaliação de risco
        pipeline = MacroAnalysisPipeline(db)
        result = await pipeline.run_risk_assessment(country)
        
        logger.info(f"✅ Avaliação de risco concluída para {country}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro na avaliação de risco: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na avaliação de risco: {str(e)}")


@router.post("/data/sync")
async def sync_historical_data(
    background_tasks: BackgroundTasks,
    series_list: Optional[List[str]] = Query(None, description="Lista de séries para sincronizar"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Sincroniza dados históricos
    
    Args:
        background_tasks: Tarefas em background
        series_list: Lista de séries para sincronizar
        db: Sessão do banco de dados
        
    Returns:
        Dict com resultado da sincronização
    """
    try:
        logger.info("🔄 Iniciando sincronização de dados históricos")
        
        # Executar sincronização
        historical_manager = HistoricalDataManager(db)
        result = await historical_manager.sync_all_series(series_list)
        
        logger.info(f"✅ Sincronização concluída: {result['successful']} sucessos, {result['failed']} falhas")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro na sincronização: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na sincronização: {str(e)}")


@router.get("/data/summary")
async def get_data_summary(
    series_name: Optional[str] = Query(None, description="Nome da série específica"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtém resumo dos dados históricos
    
    Args:
        series_name: Nome da série específica (opcional)
        db: Sessão do banco de dados
        
    Returns:
        Dict com resumo dos dados
    """
    try:
        logger.info("📊 Gerando resumo dos dados históricos")
        
        historical_manager = HistoricalDataManager(db)
        
        if series_name:
            # Resumo de série específica
            result = await historical_manager.get_data_summary(series_name)
        else:
            # Resumo geral do banco
            result = await historical_manager.get_database_stats()
        
        logger.info("✅ Resumo dos dados gerado")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar resumo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resumo: {str(e)}")


@router.get("/data/historical/{series_name}")
async def get_historical_series_data(
    series_name: str,
    start_date: Optional[str] = Query(None, description="Data de início (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data de fim (YYYY-MM-DD)"),
    months: Optional[int] = Query(None, description="Número de meses"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtém dados históricos de uma série específica
    
    Args:
        series_name: Nome da série
        start_date: Data de início
        end_date: Data de fim
        months: Número de meses
        db: Sessão do banco de dados
        
    Returns:
        Dict com dados da série
    """
    try:
        logger.info(f"📈 Buscando dados históricos para {series_name}")
        
        # Processar datas
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        # Buscar dados
        historical_manager = HistoricalDataManager(db)
        data = await historical_manager.get_historical_data(
            series_name=series_name,
            start_date=start_dt,
            end_date=end_dt,
            months=months
        )
        
        if data.empty:
            return {
                'series_name': series_name,
                'data': [],
                'message': 'Nenhum dado encontrado',
                'count': 0
            }
        
        # Converter para formato JSON
        data_dict = data.to_dict('records')
        
        logger.info(f"✅ {len(data_dict)} registros encontrados para {series_name}")
        return {
            'series_name': series_name,
            'data': data_dict,
            'count': len(data_dict),
            'date_range': {
                'start': data['date'].min().isoformat(),
                'end': data['date'].max().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar dados históricos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados históricos: {str(e)}")


@router.delete("/data/cleanup")
async def cleanup_old_data(
    days_to_keep: int = Query(365, description="Dias de dados para manter"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Remove dados antigos do banco (manutenção)
    
    Args:
        days_to_keep: Número de dias de dados para manter
        db: Sessão do banco de dados
        
    Returns:
        Dict com resultado da limpeza
    """
    try:
        logger.info(f"🧹 Iniciando limpeza de dados antigos (manter {days_to_keep} dias)")
        
        # Executar limpeza
        historical_manager = HistoricalDataManager(db)
        result = await historical_manager.cleanup_old_data(days_to_keep)
        
        logger.info(f"✅ Limpeza concluída: {result['records_removed']} registros removidos")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro na limpeza: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na limpeza: {str(e)}")


@router.get("/health")
async def get_macro_analysis_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check para análise macro
    
    Args:
        db: Sessão do banco de dados
        
    Returns:
        Dict com status de saúde
    """
    try:
        # Verificar componentes
        historical_manager = HistoricalDataManager(db)
        pipeline = MacroAnalysisPipeline(db)
        
        # Testar conectividade
        db_stats = await historical_manager.get_database_stats()
        
        return {
            'status': 'healthy',
            'database': 'connected',
            'total_records': db_stats.get('total_records', 0),
            'total_series': db_stats.get('total_series', 0),
            'pipeline': 'ready',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no health check: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
