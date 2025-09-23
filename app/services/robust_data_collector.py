"""
Coletor de dados robusto com sistema de prioridade e validação cruzada
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.time_series import EconomicSeries, DataCollectionLog
from app.services.data_sources.base_source import DataSource
from app.services.data_sources.bcb_source import BCBSource
from app.services.data_sources.ipea_source import IPEASource
from app.services.data_sources.oecd_source import OECDSource
from app.services.data_sources.trading_economics_source import TradingEconomicsSource

logger = logging.getLogger(__name__)


class RobustDataCollector:
    """Coletor de dados com redundância, failover automático e validação cruzada"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Sistema de prioridade e failover inteligente
        self.sources = {
            'bcb': BCBSource(),  # Primária para IPCA, SELIC, PIB, Câmbio
            'ipea': IPEASource(),  # Secundária para IPCA, SELIC, PIB; Primária para Desemprego
            'oecd': OECDSource(),  # Primária para CLI
            'trading_economics': TradingEconomicsSource()  # Secundária para Desemprego
        }
        
        # Configurar API key do Trading Economics se disponível
        if hasattr(settings, 'TRADING_ECONOMICS_API_KEY'):
            self.sources['trading_economics'].set_api_key(settings.TRADING_ECONOMICS_API_KEY)
        
        self.health_status = {}
        
        # Estratégia de prioridade por série
        self.priority_strategy = {
            'ipca': ['bcb', 'ipea'],
            'selic': ['bcb', 'ipea'],
            'cambio': ['bcb', 'ipea'],
            'pib': ['bcb', 'ipea'],
            'prod_industrial': ['bcb', 'ipea'],
            'desemprego': ['ipea', 'trading_economics'],
            'cli': ['oecd']
        }
    
    async def collect_series_with_priority(
        self, 
        series_name: str, 
        country: str = 'BRA',
        months: int = 60
    ) -> Dict[str, Any]:
        """Coleta dados com sistema de prioridade e validação cruzada"""
        
        logger.info(f"🔄 Iniciando coleta de {series_name} com sistema de prioridade")
        
        # Verificar se a série tem estratégia definida
        if series_name not in self.priority_strategy:
            raise ValueError(f"Série {series_name} não tem estratégia de prioridade definida")
        
        priority_sources = self.priority_strategy[series_name]
        results = {}
        primary_data = None
        secondary_data = None
        
        # Tentar fontes em ordem de prioridade
        for i, source_name in enumerate(priority_sources):
            try:
                source = self.sources[source_name]
                
                # Configurar parâmetros da série
                series_config = {
                    'name': series_name,
                    'country': country,
                    'limit': months
                }
                
                # Buscar dados
                data = await source.fetch_data(series_config)
                
                if not data.empty:
                    results[source_name] = {
                        'data': data,
                        'status': 'success',
                        'records': len(data),
                        'method': data.get('method', 'unknown').iloc[0] if 'method' in data.columns else 'unknown'
                    }
                    
                    if i == 0:  # Primeira fonte (primária)
                        primary_data = data
                        logger.info(f"✅ [Primária] {source_name}: {len(data)} registros")
                    else:  # Fontes secundárias
                        secondary_data = data
                        logger.info(f"✅ [Secundária] {source_name}: {len(data)} registros")
                        
                        # Validação cruzada se temos dados de duas fontes
                        if primary_data is not None and secondary_data is not None:
                            validation_result = self._cross_validate_data(
                                primary_data, secondary_data, series_name
                            )
                            results['cross_validation'] = validation_result
                            
                            if validation_result['discrepancy_detected']:
                                logger.warning(f"⚠️ Discrepância detectada em {series_name}: {validation_result['discrepancy_percent']:.2f}%")
                            else:
                                logger.info(f"✅ Validação cruzada OK para {series_name}")
                    
                    # Se é a fonte primária e tem dados, podemos parar aqui
                    if i == 0 and not data.empty:
                        break
                        
            except Exception as e:
                logger.error(f"❌ [Falha] {source_name} para {series_name}: {e}")
                results[source_name] = {
                    'data': pd.DataFrame(),
                    'status': 'error',
                    'error': str(e),
                    'records': 0
                }
        
        # Determinar resultado final
        if primary_data is not None and not primary_data.empty:
            final_data = primary_data
            final_status = 'success'
            final_source = priority_sources[0]
        elif secondary_data is not None and not secondary_data.empty:
            final_data = secondary_data
            final_status = 'partial'
            final_source = priority_sources[1] if len(priority_sources) > 1 else priority_sources[0]
        else:
            final_data = pd.DataFrame()
            final_status = 'failed'
            final_source = None
        
        # Salvar no banco de dados
        if not final_data.empty:
            await self._save_to_database(final_data, series_name, final_source)
        
        # Log da coleta
        await self._log_collection(series_name, final_status, len(final_data), results)
        
        return {
            'series_name': series_name,
            'status': final_status,
            'data': final_data,
            'source': final_source,
            'records': len(final_data),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def _cross_validate_data(
        self, 
        primary_data: pd.DataFrame, 
        secondary_data: pd.DataFrame, 
        series_name: str
    ) -> Dict[str, Any]:
        """Validação cruzada entre fontes primária e secundária"""
        
        try:
            # Mesclar dados por data para comparação
            merged = pd.merge(
                primary_data[['date', 'value']], 
                secondary_data[['date', 'value']], 
                on='date', 
                suffixes=('_primary', '_secondary')
            )
            
            if merged.empty:
                return {
                    'discrepancy_detected': False,
                    'discrepancy_percent': 0.0,
                    'comparison_points': 0,
                    'status': 'no_overlap'
                }
            
            # Calcular diferença percentual
            merged['diff_percent'] = abs(
                (merged['value_primary'] - merged['value_secondary']) / 
                merged['value_primary'] * 100
            )
            
            # Verificar se há discrepância significativa (>1%)
            max_discrepancy = merged['diff_percent'].max()
            avg_discrepancy = merged['diff_percent'].mean()
            
            discrepancy_detected = max_discrepancy > 1.0
            
            return {
                'discrepancy_detected': discrepancy_detected,
                'discrepancy_percent': max_discrepancy,
                'avg_discrepancy_percent': avg_discrepancy,
                'comparison_points': len(merged),
                'status': 'warning' if discrepancy_detected else 'ok'
            }
            
        except Exception as e:
            logger.error(f"Erro na validação cruzada: {e}")
            return {
                'discrepancy_detected': False,
                'discrepancy_percent': 0.0,
                'comparison_points': 0,
                'status': 'error',
                'error': str(e)
            }
    
    async def _save_to_database(self, data: pd.DataFrame, series_name: str, source: str):
        """Salva dados no banco de dados"""
        try:
            for _, row in data.iterrows():
                # Verificar se já existe registro
                existing = self.db.query(EconomicSeries).filter(
                    EconomicSeries.series_name == series_name.upper(),
                    EconomicSeries.date == row['date']
                ).first()
                
                if not existing:
                    series_record = EconomicSeries(
                        series_code=row.get('series_code', series_name.upper()),
                        series_name=series_name.upper(),
                        date=row['date'],
                        value=row['value'],
                        source=source,
                        country=row.get('country', 'BRA'),
                        unit=row.get('unit', 'unknown'),
                        frequency=row.get('frequency', 'monthly'),
                        method=row.get('method', 'unknown')
                    )
                    self.db.add(series_record)
            
            self.db.commit()
            logger.info(f"💾 Dados de {series_name} salvos no banco")
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados de {series_name}: {e}")
            self.db.rollback()
    
    async def _log_collection(
        self, 
        series_name: str, 
        status: str, 
        records: int, 
        results: Dict[str, Any]
    ):
        """Registra log da coleta"""
        try:
            # Limpar DataFrames dos resultados para serialização JSON
            clean_results = {}
            for key, value in results.items():
                if isinstance(value, dict) and 'data' in value:
                    # Converter DataFrame para dict serializável
                    df = value['data']
                    if hasattr(df, 'to_dict'):
                        # Converter timestamps para string antes de serializar
                        df_sample = df.head(3).copy()
                        if 'date' in df_sample.columns:
                            df_sample['date'] = df_sample['date'].astype(str)
                        
                        clean_results[key] = {
                            **value,
                            'data': {
                                'records': len(df),
                                'columns': list(df.columns) if not df.empty else [],
                                'sample': df_sample.to_dict('records') if not df.empty else []
                            }
                        }
                    else:
                        clean_results[key] = value
                else:
                    clean_results[key] = value
            
            # Determinar source baseado nos resultados
            source = "unknown"
            if clean_results:
                # Pegar o primeiro source que teve sucesso
                for key, value in clean_results.items():
                    if isinstance(value, dict) and value.get('status') == 'success':
                        source = key.upper()
                        break
            
            log_record = DataCollectionLog(
                source=source,
                series_name=series_name.upper(),
                series_code=clean_results.get('series_code') if clean_results else None,
                collected_at=datetime.now(),
                status=status,
                records_collected=records,
                details=clean_results
            )
            self.db.add(log_record)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Erro ao registrar log: {e}")
    
    async def collect_all_series(self, months: int = 60) -> Dict[str, Any]:
        """Coleta todas as séries com sistema de prioridade"""
        
        logger.info("🚀 Iniciando coleta completa com sistema de prioridade")
        
        all_series = list(self.priority_strategy.keys())
        results = {}
        
        # Coletar todas as séries em paralelo
        tasks = []
        for series_name in all_series:
            task = self.collect_series_with_priority(series_name, months=months)
            tasks.append(task)
        
        # Executar em paralelo
        collection_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        for i, result in enumerate(collection_results):
            series_name = all_series[i]
            
            if isinstance(result, Exception):
                results[series_name] = {
                    'status': 'error',
                    'error': str(result),
                    'records': 0
                }
            else:
                results[series_name] = result
        
        # Estatísticas finais
        successful = sum(1 for r in results.values() if r['status'] in ['success', 'partial'])
        total_records = sum(r.get('records', 0) for r in results.values())
        
        logger.info(f"✅ Coleta completa: {successful}/{len(all_series)} séries, {total_records} registros")
        
        return {
            'summary': {
                'total_series': len(all_series),
                'successful_series': successful,
                'total_records': total_records,
                'timestamp': datetime.now().isoformat()
            },
            'results': results
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Verifica status de saúde de todas as fontes"""
        
        health_results = {}
        
        for source_name, source in self.sources.items():
            try:
                health = await source.get_health_status()
                health_results[source_name] = health
            except Exception as e:
                health_results[source_name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }
        
        return health_results