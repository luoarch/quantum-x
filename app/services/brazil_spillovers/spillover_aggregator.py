"""
Agregador de Spillovers Brasil
Implementa RF025 conforme DRS seção 3.2

Baseado em:
- Diebold, F. X., & Yilmaz, K. (2009). Measuring financial asset return volatilities
- Pesaran, H. H., & Shin, Y. (1998). Generalized impulse response analysis
- Chudik, A., & Pesaran, M. H. (2016). Theory and practice of GVAR modeling
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

from app.services.brazil_spillovers.trade_channel import TradeChannelAnalyzer, TradeChannelResult
from app.services.brazil_spillovers.commodity_channel import CommodityChannelAnalyzer, CommodityChannelResult
from app.services.brazil_spillovers.financial_channel import FinancialChannelAnalyzer, FinancialChannelResult
from app.services.brazil_spillovers.supply_chain_channel import SupplyChainChannelAnalyzer, SupplyChainChannelResult

logger = logging.getLogger(__name__)

@dataclass
class SpilloverAggregationResult:
    """Resultado da agregação de spillovers"""
    total_impact: float
    impact_breakdown: Dict[str, float]
    confidence_interval: Tuple[float, float]
    channel_correlations: Dict[str, Dict[str, float]]
    variance_decomposition: Dict[str, float]
    direct_effects: Dict[str, float]
    indirect_effects: Dict[str, float]

class SpilloverAggregator:
    """
    Agregador de Spillovers para o Brasil
    
    Consolida efeitos de todos os canais em impacto agregado
    conforme especificação RF025 do DRS.
    """
    
    def __init__(self):
        """Inicializar agregador de spillovers"""
        self.trade_analyzer = TradeChannelAnalyzer()
        self.commodity_analyzer = CommodityChannelAnalyzer()
        self.financial_analyzer = FinancialChannelAnalyzer()
        self.supply_chain_analyzer = SupplyChainChannelAnalyzer()
        
        # Pesos dinâmicos por canal (baseados na literatura)
        self.channel_weights = {
            "trade": 0.35,      # Canal comercial
            "commodity": 0.30,  # Canal de commodities
            "financial": 0.25,  # Canal financeiro
            "supply_chain": 0.10 # Canal de cadeias globais
        }
        
        # Matriz de correlação entre canais (estimada)
        self.channel_correlations = self._initialize_correlations()
    
    def _initialize_correlations(self) -> Dict[str, Dict[str, float]]:
        """Inicializar matriz de correlação entre canais"""
        return {
            "trade": {
                "commodity": 0.6,      # Comércio e commodities correlacionados
                "financial": 0.4,      # Comércio e finanças moderadamente correlacionados
                "supply_chain": 0.8    # Comércio e cadeias globais altamente correlacionados
            },
            "commodity": {
                "trade": 0.6,
                "financial": 0.3,      # Commodities e finanças pouco correlacionados
                "supply_chain": 0.5
            },
            "financial": {
                "trade": 0.4,
                "commodity": 0.3,
                "supply_chain": 0.2    # Finanças e cadeias globais pouco correlacionados
            },
            "supply_chain": {
                "trade": 0.8,
                "commodity": 0.5,
                "financial": 0.2
            }
        }
    
    def aggregate_spillovers(
        self,
        global_regime_shock: Dict[str, float],
        commodity_price_shocks: Dict[str, float],
        financial_shocks: Dict[str, float],
        supply_chain_shocks: Dict[str, float]
    ) -> SpilloverAggregationResult:
        """
        Agregar spillovers de todos os canais
        
        Args:
            global_regime_shock: Choque de regime global
            commodity_price_shocks: Choques de preços de commodities
            financial_shocks: Choques financeiros
            supply_chain_shocks: Choques de cadeias globais
            
        Returns:
            SpilloverAggregationResult: Resultado agregado
        """
        logger.info("Agregando spillovers de todos os canais")
        
        # 1. Calcular spillovers por canal
        trade_result = self._calculate_trade_spillovers(global_regime_shock)
        commodity_result = self._calculate_commodity_spillovers(commodity_price_shocks)
        financial_result = self._calculate_financial_spillovers(financial_shocks)
        supply_chain_result = self._calculate_supply_chain_spillovers(supply_chain_shocks)
        
        # 2. Calcular efeitos diretos
        direct_effects = self._calculate_direct_effects(
            trade_result, commodity_result, financial_result, supply_chain_result
        )
        
        # 3. Calcular efeitos indiretos (spillovers entre canais)
        indirect_effects = self._calculate_indirect_effects(
            trade_result, commodity_result, financial_result, supply_chain_result
        )
        
        # 4. Agregar impactos
        total_impact = self._aggregate_impacts(direct_effects, indirect_effects)
        
        # 5. Calcular decomposição da variância
        variance_decomposition = self._calculate_variance_decomposition(
            trade_result, commodity_result, financial_result, supply_chain_result
        )
        
        # 6. Calcular intervalo de confiança
        confidence_interval = self._calculate_aggregate_confidence_interval(
            trade_result, commodity_result, financial_result, supply_chain_result
        )
        
        return SpilloverAggregationResult(
            total_impact=total_impact,
            impact_breakdown=direct_effects,
            confidence_interval=confidence_interval,
            channel_correlations=self.channel_correlations,
            variance_decomposition=variance_decomposition,
            direct_effects=direct_effects,
            indirect_effects=indirect_effects
        )
    
    def _calculate_trade_spillovers(self, global_regime_shock: Dict[str, float]) -> TradeChannelResult:
        """Calcular spillovers via canal comercial"""
        # Extrair choques de demanda e preços do regime global
        demand_shock = global_regime_shock.get("demand_shock", 0.0)
        price_shock = global_regime_shock.get("price_shock", 0.0)
        exchange_shock = global_regime_shock.get("exchange_shock", 0.0)
        
        # Distribuir choque global por países
        global_demand_shock = {
            country: demand_shock * weight 
            for country, weight in self.trade_analyzer.get_trade_weights().items()
        }
        
        global_price_shock = {
            country: price_shock * weight 
            for country, weight in self.trade_analyzer.get_trade_weights().items()
        }
        
        return self.trade_analyzer.calculate_spillovers(
            global_demand_shock, global_price_shock, exchange_shock
        )
    
    def _calculate_commodity_spillovers(self, commodity_price_shocks: Dict[str, float]) -> CommodityChannelResult:
        """Calcular spillovers via canal de commodities"""
        global_demand_shock = commodity_price_shocks.get("global_demand", 0.0)
        exchange_shock = commodity_price_shocks.get("exchange_shock", 0.0)
        
        return self.commodity_analyzer.calculate_spillovers(
            commodity_price_shocks, global_demand_shock, exchange_shock
        )
    
    def _calculate_financial_spillovers(self, financial_shocks: Dict[str, float]) -> FinancialChannelResult:
        """Calcular spillovers via canal financeiro"""
        # Implementação simplificada - será expandida
        return FinancialChannelResult(
            impact_magnitude=financial_shocks.get("sovereign_spread", 0.0) * 0.1,
            key_drivers=["sovereign_spread_increase"],
            affected_sectors=["banking", "real_estate"],
            confidence_interval=(0.0, 0.0)
        )
    
    def _calculate_supply_chain_spillovers(self, supply_chain_shocks: Dict[str, float]) -> SupplyChainChannelResult:
        """Calcular spillovers via canal de cadeias globais"""
        # Implementação simplificada - será expandida
        return SupplyChainChannelResult(
            impact_magnitude=supply_chain_shocks.get("disruption", 0.0) * 0.05,
            key_drivers=["global_supply_disruption"],
            affected_sectors=["automotive", "electronics"],
            confidence_interval=(0.0, 0.0)
        )
    
    def _calculate_direct_effects(
        self,
        trade_result: TradeChannelResult,
        commodity_result: CommodityChannelResult,
        financial_result: FinancialChannelResult,
        supply_chain_result: SupplyChainChannelResult
    ) -> Dict[str, float]:
        """Calcular efeitos diretos de cada canal"""
        return {
            "trade": trade_result.impact_magnitude,
            "commodity": commodity_result.impact_magnitude,
            "financial": financial_result.impact_magnitude,
            "supply_chain": supply_chain_result.impact_magnitude
        }
    
    def _calculate_indirect_effects(
        self,
        trade_result: TradeChannelResult,
        commodity_result: CommodityChannelResult,
        financial_result: FinancialChannelResult,
        supply_chain_result: SupplyChainChannelResult
    ) -> Dict[str, float]:
        """Calcular efeitos indiretos (spillovers entre canais)"""
        indirect_effects = {}
        
        # Efeitos indiretos via correlações entre canais
        channels = ["trade", "commodity", "financial", "supply_chain"]
        results = [trade_result, commodity_result, financial_result, supply_chain_result]
        
        for i, channel in enumerate(channels):
            indirect_effect = 0.0
            for j, other_channel in enumerate(channels):
                if i != j:
                    correlation = self.channel_correlations[channel][other_channel]
                    indirect_effect += results[j].impact_magnitude * correlation * 0.3  # 30% do efeito direto
            indirect_effects[channel] = indirect_effect
        
        return indirect_effects
    
    def _aggregate_impacts(
        self,
        direct_effects: Dict[str, float],
        indirect_effects: Dict[str, float]
    ) -> float:
        """Agregar impactos diretos e indiretos"""
        total_impact = 0.0
        
        for channel in direct_effects:
            # Impacto total = efeito direto + efeito indireto
            direct = direct_effects[channel]
            indirect = indirect_effects[channel]
            weight = self.channel_weights[channel]
            
            channel_impact = (direct + indirect) * weight
            total_impact += channel_impact
        
        return total_impact
    
    def _calculate_variance_decomposition(
        self,
        trade_result: TradeChannelResult,
        commodity_result: CommodityChannelResult,
        financial_result: FinancialChannelResult,
        supply_chain_result: SupplyChainChannelResult
    ) -> Dict[str, float]:
        """Calcular decomposição da variância por canal"""
        # Calcular variância de cada canal
        trade_var = trade_result.impact_magnitude ** 2
        commodity_var = commodity_result.impact_magnitude ** 2
        financial_var = financial_result.impact_magnitude ** 2
        supply_chain_var = supply_chain_result.impact_magnitude ** 2
        
        total_var = trade_var + commodity_var + financial_var + supply_chain_var
        
        if total_var == 0:
            return {"trade": 0.25, "commodity": 0.25, "financial": 0.25, "supply_chain": 0.25}
        
        return {
            "trade": trade_var / total_var,
            "commodity": commodity_var / total_var,
            "financial": financial_var / total_var,
            "supply_chain": supply_chain_var / total_var
        }
    
    def _calculate_aggregate_confidence_interval(
        self,
        trade_result: TradeChannelResult,
        commodity_result: CommodityChannelResult,
        financial_result: FinancialChannelResult,
        supply_chain_result: SupplyChainChannelResult
    ) -> Tuple[float, float]:
        """Calcular intervalo de confiança agregado"""
        # Usar o maior intervalo de confiança como aproximação
        intervals = [
            trade_result.confidence_interval,
            commodity_result.confidence_interval,
            financial_result.confidence_interval,
            supply_chain_result.confidence_interval
        ]
        
        # Encontrar o intervalo mais amplo
        max_width = 0
        best_interval = (0.0, 0.0)
        
        for interval in intervals:
            width = interval[1] - interval[0]
            if width > max_width:
                max_width = width
                best_interval = interval
        
        return best_interval
    
    def update_channel_weights(self, new_weights: Dict[str, float]):
        """Atualizar pesos dos canais"""
        # Validar pesos
        total_weight = sum(new_weights.values())
        if not np.isclose(total_weight, 1.0, atol=0.01):
            raise ValueError("Pesos dos canais devem somar 1.0")
        
        self.channel_weights = new_weights
        logger.info("Pesos dos canais atualizados")
    
    def get_channel_weights(self) -> Dict[str, float]:
        """Obter pesos atuais dos canais"""
        return self.channel_weights.copy()
    
    def get_channel_correlations(self) -> Dict[str, Dict[str, float]]:
        """Obter correlações entre canais"""
        return self.channel_correlations.copy()
