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
from app.services.data_sources.bacen_sgs_source import BacenSGSSource
from app.services.data_sources.yahoo_source import YahooSource
from app.services.data_sources.ipea_source import IPEASource
from app.services.data_sources.oecd_source import OECDSource
from app.services.data_sources.trading_economics_source import TradingEconomicsSource
from app.services.data_sources.fred_source import FREDSource
from app.services.data_sources.worldbank_source import WorldBankSource
from app.services.data_sources.ipea_cli_source import IPEACLISource
from app.services.data_sources.github_oecd_source import GitHubOECDSource

logger = logging.getLogger(__name__)

# Configurar níveis de log específicos
def log_debug(message: str, **kwargs):
    """Log para mensagens detalhadas de debug"""
    logger.debug(message, extra=kwargs)

def log_info(message: str, **kwargs):
    """Log para eventos de sucesso e fluxo normal"""
    logger.info(message, extra=kwargs)

def log_warning(message: str, **kwargs):
    """Log para warnings de rate-limit e validação cruzada"""
    logger.warning(message, extra=kwargs)

def log_error(message: str, exc_info: bool = True, **kwargs):
    """Log para erros com stack trace"""
    logger.error(message, exc_info=exc_info, extra=kwargs)


class RobustDataCollector:
    """Coletor de dados com redundância, failover automático e validação cruzada"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Controle de concorrência
        self._semaphore = asyncio.Semaphore(3)  # Máximo 3 requisições simultâneas
        
        # Métricas de health check
        self._health_metrics = {
            'last_success': {},
            'last_failure': {},
            'retry_count': {},
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0
        }
        
        # Sistema de prioridade e failover inteligente
        self.sources = {}
        
        # Inicializar fontes com tratamento de dependências opcionais
        try:
            self.sources['bcb'] = BCBSource()  # Primária via python-bcb
            logger.info("✅ BCBSource inicializado (python-bcb disponível)")
        except Exception as e:
            logger.warning(f"⚠️ BCBSource não disponível: {e}")
        
        self.sources['bacen_sgs'] = BacenSGSSource()  # Primária alternativa via API oficial SGS
        self.sources['yahoo'] = YahooSource()  # Preços de mercado (ETFs, índices, ações)
        
        try:
            self.sources['ipea'] = IPEASource()  # Secundária para IPCA, SELIC, PIB; Primária para Desemprego
        except Exception as e:
            logger.warning(f"⚠️ IPEASource não disponível: {e}")
        
        try:
            self.sources['oecd'] = OECDSource()  # Primária para CLI
        except Exception as e:
            logger.warning(f"⚠️ OECDSource não disponível: {e}")
        
        try:
            self.sources['trading_economics'] = TradingEconomicsSource()  # Secundária para Desemprego
        except Exception as e:
            logger.warning(f"⚠️ TradingEconomicsSource não disponível: {e}")
        
        self.sources['fred'] = FREDSource()  # Fallback para CLI
        
        try:
            self.sources['worldbank'] = WorldBankSource()  # Fallback para CLI
        except Exception as e:
            logger.warning(f"⚠️ WorldBankSource não disponível: {e}")
        
        try:
            self.sources['ipea_cli'] = IPEACLISource()  # Fallback para CLI Brasil
        except Exception as e:
            logger.warning(f"⚠️ IPEACLISource não disponível: {e}")
        
        try:
            self.sources['github_oecd'] = GitHubOECDSource()  # Fallback para CLI
        except Exception as e:
            logger.warning(f"⚠️ GitHubOECDSource não disponível: {e}")
        
        logger.info(f"✅ {len(self.sources)} fontes de dados inicializadas")
        
        # Configurar API key do Trading Economics se disponível
        try:
            from app.core.config import settings
            if hasattr(settings, 'TRADING_ECONOMICS_API_KEY') and settings.TRADING_ECONOMICS_API_KEY:
                self.sources['trading_economics'].set_api_key(settings.TRADING_ECONOMICS_API_KEY)
        except Exception as e:
            logger.warning(f"Erro ao configurar Trading Economics API key: {e}")
        
        self.health_status = {}
        
        # Estratégia de prioridade por série (apenas fontes disponíveis)
        self.priority_strategy = {}
        
        # IPCA: priorizar fontes disponíveis
        ipca_sources = []
        if 'bcb' in self.sources: ipca_sources.append('bcb')
        ipca_sources.append('bacen_sgs')  # Sempre disponível
        if 'ipea' in self.sources: ipca_sources.append('ipea')
        self.priority_strategy['ipca'] = ipca_sources
        
        # SELIC: priorizar fontes disponíveis
        selic_sources = []
        if 'bcb' in self.sources: selic_sources.append('bcb')
        selic_sources.append('bacen_sgs')  # Sempre disponível
        if 'ipea' in self.sources: selic_sources.append('ipea')
        self.priority_strategy['selic'] = selic_sources
        
        # Câmbio: priorizar fontes disponíveis
        cambio_sources = []
        if 'bcb' in self.sources: cambio_sources.append('bcb')
        cambio_sources.append('bacen_sgs')  # Sempre disponível
        if 'ipea' in self.sources: cambio_sources.append('ipea')
        self.priority_strategy['cambio'] = cambio_sources
        
        # PIB: priorizar fontes disponíveis
        pib_sources = []
        if 'bcb' in self.sources: pib_sources.append('bcb')
        pib_sources.append('bacen_sgs')  # Sempre disponível
        if 'ipea' in self.sources: pib_sources.append('ipea')
        self.priority_strategy['pib'] = pib_sources
        
        # Produção Industrial
        prod_sources = []
        if 'bcb' in self.sources: prod_sources.append('bcb')
        if 'ipea' in self.sources: prod_sources.append('ipea')
        self.priority_strategy['prod_industrial'] = prod_sources
        
        # Desemprego
        desemprego_sources = ['bacen_sgs']  # Sempre disponível
        if 'ipea' in self.sources: desemprego_sources.append('ipea')
        if 'trading_economics' in self.sources: desemprego_sources.append('trading_economics')
        self.priority_strategy['desemprego'] = desemprego_sources
        
        # CLI: priorizar fontes disponíveis
        cli_sources = ['fred']  # Sempre disponível
        if 'oecd' in self.sources: cli_sources.append('oecd')
        if 'worldbank' in self.sources: cli_sources.append('worldbank')
        if 'ipea_cli' in self.sources: cli_sources.append('ipea_cli')
        if 'github_oecd' in self.sources: cli_sources.append('github_oecd')
        self.priority_strategy['cli'] = cli_sources

        # Adicionar séries faltantes
        self.priority_strategy['yield_curve'] = ['fred']
        # Removido ibc_br - série não suportada pelas fontes atuais

        # Estratégia de ativos de mercado (nova categoria)
        self.market_priority = {
            'BOVA11': ['yahoo'],
            'IBOVESPA': ['yahoo'],
            'VALE': ['yahoo'],
            'PETR': ['yahoo'],
            'BRL_USD': ['yahoo']
        }
    
    async def collect_series_with_priority(
        self, 
        series_name: str, 
        country: str = 'BRA',
        months: int = 120
    ) -> Dict[str, Any]:
        """Coleta dados com sistema de prioridade e validação cruzada"""
        
        logger.info(f"🔄 [COLLECTOR] Iniciando coleta de {series_name} com sistema de prioridade")
        logger.debug(f"📋 [COLLECTOR] Estratégia: {self.priority_strategy.get(series_name, [])}")
        logger.debug(f"🌍 [COLLECTOR] País: {country}, Meses: {months}")
        
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
            for idx, row in data.iterrows():
                # Validar data antes de salvar
                if 'date' not in row or pd.isna(row['date']) or row['date'] == 0:
                    logger.warning(f"⚠️ Data inválida para {series_name} (linha {idx}): {row.get('date', 'N/A')}")
                    logger.debug(f"📊 Row completo: {row.to_dict()}")
                    continue
                
                # Converter data para datetime se necessário
                try:
                    if isinstance(row['date'], str):
                        date_val = pd.to_datetime(row['date'])
                    elif hasattr(row['date'], 'to_pydatetime'):
                        date_val = row['date'].to_pydatetime()
                    else:
                        date_val = pd.to_datetime(row['date'])
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao converter data para {series_name}: {e}")
                    continue
                
                # Verificar se já existe registro
                existing = self.db.query(EconomicSeries).filter(
                    EconomicSeries.series_name == series_name.upper(),
                    EconomicSeries.date == date_val
                ).first()
                
                if not existing:
                    series_record = EconomicSeries(
                        series_code=row.get('series_code', series_name.upper()),
                        series_name=series_name.upper(),
                        date=date_val,
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
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Retorna status de saúde do coletor com métricas detalhadas
        
        Returns:
            Dict[str, Any]: Status de saúde com métricas para monitoramento
        """
        total_requests = self._health_metrics['total_requests']
        failed_requests = self._health_metrics['failed_requests']
        
        # Calcular status baseado na taxa de sucesso
        if total_requests == 0:
            status = 'unknown'
        elif failed_requests < total_requests * 0.5:
            status = 'healthy'
        else:
            status = 'degraded'
        
        return {
            'status': status,
            'metrics': self._health_metrics.copy(),
            'sources_status': {
                source_name: {
                    'last_success': self._health_metrics['last_success'].get(source_name),
                    'last_failure': self._health_metrics['last_failure'].get(source_name),
                    'retry_count': self._health_metrics['retry_count'].get(source_name, 0)
                }
                for source_name in self.sources.keys()
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def collect_all_series(self, months: int = 120) -> Dict[str, Any]:
        """
        Coleta todas as séries econômicas com sistema de prioridade e failover
        
        Args:
            months (int): Número de meses de dados históricos a coletar
            
        Returns:
            Dict[str, Any]: Resultados da coleta com estrutura:
                - results: Dict com dados de cada série
                - summary: Dict com estatísticas da coleta
                - errors: List com erros encontrados
        """
        
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
        
        # Log dos resultados
        logger.info(f"📊 Resultados da coleta: {len(collection_results)} séries")
        for i, result in enumerate(collection_results):
            if isinstance(result, Exception):
                logger.error(f"❌ Série {i}: {result}")
            else:
                logger.info(f"✅ Série {i}: {type(result)}")
                if isinstance(result, dict):
                    logger.debug(f"📊 Dict keys: {list(result.keys())}")
                    if 'data' in result:
                        logger.debug(f"📊 Data type: {type(result['data'])}")
                        if hasattr(result['data'], 'shape'):
                            logger.debug(f"📊 Data shape: {result['data'].shape}")
        
        # Processar resultados
        for i, result in enumerate(collection_results):
            series_name = all_series[i]
            
            if isinstance(result, Exception):
                results[series_name] = pd.DataFrame()
                logger.error(f"❌ Erro na coleta de {series_name}: {result}")
            else:
                # Extrair DataFrame do resultado
                if isinstance(result, dict) and 'data' in result:
                    results[series_name] = result['data']
                    logger.info(f"✅ {series_name}: {len(result['data'])} registros")
                else:
                    results[series_name] = pd.DataFrame()
                    logger.warning(f"⚠️ {series_name}: Formato inesperado")
        
        # Estatísticas finais
        successful = sum(1 for r in results.values() if not r.empty)
        total_records = sum(len(r) for r in results.values())
        
        logger.info(f"✅ Coleta completa: {successful}/{len(all_series)} séries, {total_records} registros")
        
        # Retornar apenas os DataFrames, não o dict completo
        return results
    
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