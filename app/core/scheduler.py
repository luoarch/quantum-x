"""
Agendador de tarefas para coleta automática de dados
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.data_collector import DataCollector

logger = logging.getLogger(__name__)

# Instância global do scheduler
scheduler = AsyncIOScheduler()


async def collect_data_job():
    """Job para coleta automática de dados"""
    logger.info("🔄 Iniciando coleta automática de dados")
    
    db = SessionLocal()
    try:
        collector = DataCollector()
        result = await collector.collect_all_data(db)
        
        if result.get('status') == 'completed':
            logger.info(f"✅ Coleta automática concluída: {result.get('total_records')} registros")
        else:
            logger.error("❌ Erro na coleta automática")
            
    except Exception as e:
        logger.error(f"❌ Erro no job de coleta: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    """Inicia o agendador"""
    if not scheduler.running:
        # Agendar coleta de dados a cada hora
        scheduler.add_job(
            collect_data_job,
            trigger=IntervalTrigger(seconds=settings.DATA_UPDATE_INTERVAL),
            id='data_collection',
            name='Coleta Automática de Dados',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("✅ Agendador iniciado com sucesso")


def stop_scheduler():
    """Para o agendador"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("⏹️ Agendador parado")
