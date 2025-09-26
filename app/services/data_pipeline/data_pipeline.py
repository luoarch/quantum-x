"""
Pipeline de Dados Principal
Conforme DRS seção 7.2 - Coleta automática a cada 6 horas
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

from app.core.config import settings
from app.services.data_sources.fred_collector import FREDCollector
from app.services.data_sources.bcb_collector import BCBCollector
from app.services.data_pipeline.data_validator import DataValidator
from app.services.data_pipeline.data_processor import DataProcessor
from app.services.global_regime_analysis.rs_gvar_model import RSGVARModel
from app.services.brazil_spillovers.spillover_aggregator import SpilloverAggregator

logger = logging.getLogger(__name__)

class DataPipeline:
    """
    Pipeline de Dados Principal
    
    Coordena coleta, validação e processamento de dados conforme DRS
    """
    
    def __init__(self):
        """Inicializar pipeline de dados"""
        self.fred_collector = FREDCollector()
        self.bcb_collector = BCBCollector()
        self.validator = DataValidator()
        self.processor = DataProcessor()
        self.rs_gvar_model = RSGVARModel()
        self.spillover_aggregator = SpilloverAggregator()
        
        # Cache para dados processados
        self.cached_data = {}
        self.last_update = None
        
    async def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Executar pipeline completo de dados
        
        Returns:
            Dict com resultados do pipeline
        """
        logger.info("Iniciando pipeline completo de dados")
        start_time = datetime.now()
        
        try:
            # 1. Coletar dados globais
            global_data = await self._collect_global_data()
            
            # 2. Coletar dados do Brasil
            brazil_data = await self._collect_brazil_data()
            
            # 3. Validar dados coletados
            validation_results = await self._validate_data(global_data, brazil_data)
            
            # 4. Processar dados
            processed_data = await self._process_data(global_data, brazil_data)
            
            # 5. Executar análise de regimes
            regime_results = await self._analyze_regimes(processed_data['global'])
            
            # 6. Calcular spillovers
            spillover_results = await self._calculate_spillovers(
                regime_results, processed_data['brazil']
            )
            
            # 7. Gerar previsões
            forecast_results = await self._generate_forecasts(
                regime_results, spillover_results, processed_data['brazil']
            )
            
            # 8. Atualizar cache
            self._update_cache({
                'global_data': global_data,
                'brazil_data': brazil_data,
                'regime_results': regime_results,
                'spillover_results': spillover_results,
                'forecast_results': forecast_results
            })
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Pipeline executado com sucesso em {execution_time:.2f}s")
            
            return {
                'status': 'success',
                'execution_time': execution_time,
                'data_quality': validation_results,
                'regime_analysis': regime_results,
                'spillover_analysis': spillover_results,
                'forecasts': forecast_results,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Erro no pipeline de dados: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    async def _collect_global_data(self) -> pd.DataFrame:
        """Coletar dados globais (G7 + China)"""
        logger.info("Coletando dados globais")
        
        try:
            # Coletar dados do FRED
            fred_data = await self.fred_collector.collect()
            
            # TODO: Implementar coletores para OECD, World Bank, Yahoo Finance
            # Por enquanto, usar apenas dados do FRED
            
            return fred_data
            
        except Exception as e:
            logger.error(f"Erro ao coletar dados globais: {e}")
            raise
    
    async def _collect_brazil_data(self) -> pd.DataFrame:
        """Coletar dados do Brasil"""
        logger.info("Coletando dados do Brasil")
        
        try:
            # Coletar dados do BCB
            bcb_data = await self.bcb_collector.collect()
            
            # TODO: Implementar coletores para IBGE, MDIC, IPEADATA
            # Por enquanto, usar apenas dados do BCB
            
            return bcb_data
            
        except Exception as e:
            logger.error(f"Erro ao coletar dados do Brasil: {e}")
            raise
    
    async def _validate_data(
        self, 
        global_data: pd.DataFrame, 
        brazil_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Validar dados coletados"""
        logger.info("Validando dados coletados")
        
        validation_results = {}
        
        # Validar dados globais
        global_validation = self.validator.validate_dataset(global_data, 'fred')
        validation_results['global'] = {
            'is_valid': global_validation.is_valid,
            'issues': global_validation.issues,
            'quality_score': global_validation.quality_score
        }
        
        # Validar dados do Brasil
        brazil_validation = self.validator.validate_dataset(brazil_data, 'bcb')
        validation_results['brazil'] = {
            'is_valid': brazil_validation.is_valid,
            'issues': brazil_validation.issues,
            'quality_score': brazil_validation.quality_score
        }
        
        return validation_results
    
    async def _process_data(
        self, 
        global_data: pd.DataFrame, 
        brazil_data: pd.DataFrame
    ) -> Dict[str, pd.DataFrame]:
        """Processar dados para análise"""
        logger.info("Processando dados")
        
        # Processar dados globais
        processed_global = self.processor.process_global_data(global_data)
        
        # Processar dados do Brasil
        processed_brazil = self.processor.process_brazil_data(brazil_data)
        
        return {
            'global': processed_global,
            'brazil': processed_brazil
        }
    
    async def _analyze_regimes(self, global_data: pd.DataFrame) -> Dict[str, Any]:
        """Executar análise de regimes globais"""
        logger.info("Executando análise de regimes globais")
        
        try:
            # Ajustar modelo RS-GVAR
            regime_result = self.rs_gvar_model.fit(global_data)
            
            # Verificar se o modelo convergiu
            if not regime_result.convergence:
                logger.warning("Modelo RS-GVAR não convergiu")
            
            return {
                'regimes': regime_result.regimes,
                'regime_probabilities': regime_result.regime_probabilities,
                'transition_matrix': regime_result.transition_matrix,
                'regime_characteristics': regime_result.regime_characteristics,
                'validation_metrics': regime_result.validation_metrics,
                'convergence': regime_result.convergence
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de regimes: {e}")
            raise
    
    async def _calculate_spillovers(
        self, 
        regime_results: Dict[str, Any], 
        brazil_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calcular spillovers para o Brasil"""
        logger.info("Calculando spillovers para o Brasil")
        
        try:
            # Extrair choques do regime atual
            current_regime = regime_results['regimes'][-1]
            regime_probabilities = regime_results['regime_probabilities'][-1]
            
            # Simular choques baseados no regime atual
            global_shocks = self._simulate_global_shocks(current_regime, regime_probabilities)
            
            # Calcular spillovers
            spillover_result = self.spillover_aggregator.aggregate_spillovers(
                global_shocks['regime_shock'],
                global_shocks['commodity_shocks'],
                global_shocks['financial_shocks'],
                global_shocks['supply_chain_shocks']
            )
            
            return {
                'total_impact': spillover_result.total_impact,
                'channel_breakdown': spillover_result.impact_breakdown,
                'confidence_interval': spillover_result.confidence_interval,
                'channel_correlations': spillover_result.channel_correlations
            }
            
        except Exception as e:
            logger.error(f"Erro no cálculo de spillovers: {e}")
            raise
    
    async def _generate_forecasts(
        self, 
        regime_results: Dict[str, Any], 
        spillover_results: Dict[str, Any],
        brazil_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Gerar previsões regime-condicionais"""
        logger.info("Gerando previsões regime-condicionais")
        
        try:
            # TODO: Implementar modelos de previsão específicos
            # Por enquanto, retornar previsões simuladas
            
            forecasts = {
                'gdp_growth': {
                    'current_quarter': 1.8,
                    'next_quarter': 1.5,
                    'confidence_interval': [1.2, 1.8]
                },
                'inflation': {
                    'current_month': 4.2,
                    'forecast_12_months': 4.8,
                    'target_range': [3.0, 6.0]
                },
                'exchange_rate': {
                    'current': 5.25,
                    'forecast_3m': 5.45,
                    'volatility': 0.15
                }
            }
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Erro na geração de previsões: {e}")
            raise
    
    def _simulate_global_shocks(
        self, 
        current_regime: int, 
        regime_probabilities: np.ndarray
    ) -> Dict[str, Any]:
        """Simular choques globais baseados no regime atual"""
        
        # Choques baseados no regime atual
        regime_shocks = {
            0: {'demand_shock': -0.05, 'price_shock': -0.03, 'exchange_shock': 0.02},  # Recessão
            1: {'demand_shock': 0.02, 'price_shock': 0.01, 'exchange_shock': -0.01},   # Recuperação
            2: {'demand_shock': 0.05, 'price_shock': 0.03, 'exchange_shock': -0.02},   # Expansão
            3: {'demand_shock': -0.03, 'price_shock': -0.02, 'exchange_shock': 0.01},  # Contração
        }
        
        base_shock = regime_shocks.get(current_regime, regime_shocks[0])
        
        return {
            'regime_shock': base_shock,
            'commodity_shocks': {
                'iron_ore': base_shock['price_shock'] * 0.5,
                'soybeans': base_shock['price_shock'] * 0.3,
                'crude_oil': base_shock['price_shock'] * 0.2
            },
            'financial_shocks': {
                'sovereign_spread': base_shock['exchange_shock'] * 100,
                'capital_flow': base_shock['demand_shock'] * 0.1
            },
            'supply_chain_shocks': {
                'disruption': abs(base_shock['demand_shock']) * 0.1,
                'logistics_cost': base_shock['price_shock'] * 0.2
            }
        }
    
    def _update_cache(self, data: Dict[str, Any]):
        """Atualizar cache de dados"""
        self.cached_data = data
        self.last_update = datetime.now()
        logger.info("Cache de dados atualizado")
    
    def get_cached_data(self) -> Optional[Dict[str, Any]]:
        """Obter dados do cache"""
        if self.cached_data and self.last_update:
            # Verificar se o cache ainda é válido (menos de 6 horas)
            if (datetime.now() - self.last_update).total_seconds() < 6 * 3600:
                return self.cached_data
        return None
    
    async def run_incremental_update(self) -> Dict[str, Any]:
        """Executar atualização incremental dos dados"""
        logger.info("Executando atualização incremental")
        
        # Verificar se há dados em cache
        cached_data = self.get_cached_data()
        if cached_data:
            logger.info("Usando dados do cache")
            return cached_data
        
        # Executar pipeline completo
        return await self.run_full_pipeline()
