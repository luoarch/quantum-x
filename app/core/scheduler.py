"""
Agendador para Coleta Automática de Dados
Conforme DRS seção 7.2 - Coleta automática a cada 6 horas
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.services.data_pipeline.data_pipeline import DataPipeline
from app.core.config import settings

logger = logging.getLogger(__name__)

class DataScheduler:
    """
    Agendador de coleta automática de dados
    
    Executa pipeline de dados conforme cronograma definido no DRS
    """
    
    def __init__(self):
        """Inicializar agendador"""
        self.scheduler = AsyncIOScheduler()
        self.data_pipeline = DataPipeline()
        self.is_running = False
        
    async def start(self):
        """Iniciar agendador"""
        if self.is_running:
            logger.warning("Agendador já está em execução")
            return
        
        logger.info("Iniciando agendador de coleta de dados")
        
        # Agendar coleta automática a cada 6 horas
        self.scheduler.add_job(
            self._run_data_collection,
            trigger=IntervalTrigger(hours=6),
            id='data_collection',
            name='Coleta Automática de Dados',
            max_instances=1,
            replace_existing=True
        )
        
        # Agendar coleta de emergência (se dados estão muito antigos)
        self.scheduler.add_job(
            self._check_data_freshness,
            trigger=IntervalTrigger(hours=1),
            id='data_freshness_check',
            name='Verificação de Atualização de Dados',
            max_instances=1,
            replace_existing=True
        )
        
        # Agendar análise de regimes (diariamente às 8h)
        self.scheduler.add_job(
            self._run_regime_analysis,
            trigger=CronTrigger(hour=8, minute=0),
            id='regime_analysis',
            name='Análise Diária de Regimes',
            max_instances=1,
            replace_existing=True
        )
        
        # Agendar cálculo de spillovers (a cada 4 horas)
        self.scheduler.add_job(
            self._run_spillover_calculation,
            trigger=IntervalTrigger(hours=4),
            id='spillover_calculation',
            name='Cálculo de Spillovers',
            max_instances=1,
            replace_existing=True
        )
        
        # Iniciar agendador
        self.scheduler.start()
        self.is_running = True
        
        logger.info("Agendador iniciado com sucesso")
        
        # Executar coleta inicial
        await self._run_data_collection()
    
    async def stop(self):
        """Parar agendador"""
        if not self.is_running:
            logger.warning("Agendador não está em execução")
            return
        
        logger.info("Parando agendador")
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Agendador parado")
    
    async def _run_data_collection(self):
        """Executar coleta de dados"""
        logger.info("Iniciando coleta automática de dados")
        start_time = datetime.now()
        
        try:
            result = await self.data_pipeline.run_full_pipeline()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if result['status'] == 'success':
                logger.info(f"Coleta de dados concluída com sucesso em {execution_time:.2f}s")
                
                # Log de métricas de qualidade
                data_quality = result.get('data_quality', {})
                for source, quality in data_quality.items():
                    if isinstance(quality, dict):
                        score = quality.get('quality_score', 0)
                        logger.info(f"Qualidade dos dados {source}: {score:.2f}")
                
            else:
                logger.error(f"Erro na coleta de dados: {result.get('error', 'Erro desconhecido')}")
                
        except Exception as e:
            logger.error(f"Erro inesperado na coleta de dados: {e}")
    
    async def _check_data_freshness(self):
        """Verificar se dados estão atualizados"""
        logger.debug("Verificando atualização dos dados")
        
        try:
            cached_data = self.data_pipeline.get_cached_data()
            
            if cached_data is None:
                logger.warning("Nenhum dado em cache - executando coleta de emergência")
                await self._run_data_collection()
                return
            
            # Verificar se dados são muito antigos (mais de 8 horas)
            last_update = cached_data.get('timestamp')
            if last_update:
                age_hours = (datetime.now() - last_update).total_seconds() / 3600
                
                if age_hours > 8:
                    logger.warning(f"Dados muito antigos ({age_hours:.1f}h) - executando coleta de emergência")
                    await self._run_data_collection()
                else:
                    logger.debug(f"Dados atualizados há {age_hours:.1f} horas")
            
        except Exception as e:
            logger.error(f"Erro na verificação de atualização: {e}")
    
    async def _run_regime_analysis(self):
        """Executar análise de regimes"""
        logger.info("Iniciando análise diária de regimes")
        
        try:
            # Verificar se há dados disponíveis
            cached_data = self.data_pipeline.get_cached_data()
            if cached_data is None:
                logger.warning("Nenhum dado disponível para análise de regimes")
                return
            
            # Executar análise de regimes
            global_data = cached_data.get('global_data')
            if global_data is not None:
                regime_results = await self.data_pipeline._analyze_regimes(global_data)
                logger.info("Análise de regimes concluída")
            else:
                logger.warning("Dados globais não disponíveis para análise de regimes")
                
        except Exception as e:
            logger.error(f"Erro na análise de regimes: {e}")
    
    async def _run_spillover_calculation(self):
        """Executar cálculo de spillovers"""
        logger.info("Iniciando cálculo de spillovers")
        
        try:
            # Verificar se há dados disponíveis
            cached_data = self.data_pipeline.get_cached_data()
            if cached_data is None:
                logger.warning("Nenhum dado disponível para cálculo de spillovers")
                return
            
            # Executar cálculo de spillovers
            regime_results = cached_data.get('regime_results')
            brazil_data = cached_data.get('brazil_data')
            
            if regime_results is not None and brazil_data is not None:
                spillover_results = await self.data_pipeline._calculate_spillovers(
                    regime_results, brazil_data
                )
                logger.info("Cálculo de spillovers concluído")
            else:
                logger.warning("Dados necessários não disponíveis para cálculo de spillovers")
                
        except Exception as e:
            logger.error(f"Erro no cálculo de spillovers: {e}")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Obter status do agendador"""
        jobs = []
        
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'is_running': self.is_running,
            'jobs': jobs,
            'job_count': len(jobs)
        }
    
    async def run_manual_collection(self) -> Dict[str, Any]:
        """Executar coleta manual de dados"""
        logger.info("Executando coleta manual de dados")
        
        try:
            result = await self.data_pipeline.run_full_pipeline()
            logger.info("Coleta manual concluída")
            return result
        except Exception as e:
            logger.error(f"Erro na coleta manual: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    async def force_regime_analysis(self) -> Dict[str, Any]:
        """Forçar análise de regimes"""
        logger.info("Forçando análise de regimes")
        
        try:
            await self._run_regime_analysis()
            return {
                'status': 'success',
                'message': 'Análise de regimes executada',
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Erro na análise forçada de regimes: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now()
            }