"""
Análise do Canal de Commodities - Spillovers Brasil
Implementa RF022 conforme DRS seção 3.2

Baseado em:
- Cashin, P., et al. (2002). Booms and slumps in world commodity prices
- Deaton, A. (1999). Commodity prices and growth in Africa
- Chen, Y., et al. (2010). The global financial crisis and commodity prices
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

from app.core.config import settings, model_config

logger = logging.getLogger(__name__)

@dataclass
class CommodityChannelResult:
    """Resultado da análise do canal de commodities"""
    impact_magnitude: float
    key_commodities: Dict[str, float]
    commodity_weights: Dict[str, float]
    price_elasticities: Dict[str, float]
    fiscal_impact: float
    terms_of_trade_impact: float
    confidence_interval: Tuple[float, float]

class CommodityChannelAnalyzer:
    """
    Analisador do Canal de Commodities para Spillovers Brasil
    
    Quantifica spillovers via preços de commodities relevantes para o Brasil
    conforme especificação RF022 do DRS.
    """
    
    def __init__(self):
        """Inicializar analisador do canal de commodities"""
        self.commodity_weights = model_config.COMMODITY_WEIGHTS.copy()
        self.price_elasticities = self._initialize_price_elasticities()
        self.fiscal_elasticities = self._initialize_fiscal_elasticities()
        
    def _initialize_price_elasticities(self) -> Dict[str, float]:
        """
        Inicializar elasticidades preço-quantidade por commodity
        
        Baseado na literatura acadêmica
        """
        return {
            "iron_ore": 0.8,      # Minério de ferro
            "soybeans": 0.6,      # Soja
            "crude_oil": 0.4,     # Petróleo
            "coffee": 0.7,        # Café
            "sugar": 0.5,         # Açúcar
            "corn": 0.6,          # Milho
            "beef": 0.4,          # Carne bovina
            "poultry": 0.5        # Carne de frango
        }
    
    def _initialize_fiscal_elasticities(self) -> Dict[str, float]:
        """
        Inicializar elasticidades fiscais por commodity
        
        Baseado na estrutura tributária brasileira
        """
        return {
            "iron_ore": 0.15,     # Royalties mineração
            "soybeans": 0.08,     # ICMS e exportações
            "crude_oil": 0.20,    # Royalties petróleo
            "coffee": 0.05,       # ICMS
            "sugar": 0.06,        # ICMS
            "corn": 0.05,         # ICMS
            "beef": 0.04,         # ICMS
            "poultry": 0.04       # ICMS
        }
    
    def calculate_spillovers(
        self, 
        commodity_price_shocks: Dict[str, float],
        global_demand_shock: float = 0.0,
        exchange_rate_shock: float = 0.0
    ) -> CommodityChannelResult:
        """
        Calcular spillovers via canal de commodities
        
        Args:
            commodity_price_shocks: Choques de preços por commodity
            global_demand_shock: Choque de demanda global
            exchange_rate_shock: Choque na taxa de câmbio
            
        Returns:
            CommodityChannelResult: Resultado da análise
        """
        logger.info("Calculando spillovers via canal de commodities")
        
        # 1. Calcular impacto direto dos preços
        price_impact = self._calculate_price_impact(commodity_price_shocks)
        
        # 2. Calcular impacto via demanda global
        demand_impact = self._calculate_demand_impact(global_demand_shock)
        
        # 3. Calcular impacto via câmbio
        exchange_impact = self._calculate_exchange_impact(exchange_rate_shock)
        
        # 4. Calcular impacto fiscal
        fiscal_impact = self._calculate_fiscal_impact(commodity_price_shocks)
        
        # 5. Calcular impacto nos termos de troca
        terms_of_trade_impact = self._calculate_terms_of_trade_impact(
            commodity_price_shocks, exchange_rate_shock
        )
        
        # 6. Agregar impactos
        total_impact = price_impact + demand_impact + exchange_impact
        
        # 7. Calcular contribuição por commodity
        commodity_contributions = self._calculate_commodity_contributions(
            commodity_price_shocks
        )
        
        # 8. Calcular elasticidades
        price_elasticities = self._calculate_price_elasticities(commodity_price_shocks)
        
        # 9. Calcular intervalo de confiança
        confidence_interval = self._calculate_confidence_interval(total_impact)
        
        return CommodityChannelResult(
            impact_magnitude=total_impact,
            key_commodities=commodity_contributions,
            commodity_weights=self.commodity_weights,
            price_elasticities=price_elasticities,
            fiscal_impact=fiscal_impact,
            terms_of_trade_impact=terms_of_trade_impact,
            confidence_interval=confidence_interval
        )
    
    def _calculate_price_impact(self, commodity_price_shocks: Dict[str, float]) -> float:
        """Calcular impacto direto dos preços das commodities"""
        impact = 0.0
        
        for commodity, shock in commodity_price_shocks.items():
            if commodity in self.commodity_weights:
                weight = self.commodity_weights[commodity]
                elasticity = self.price_elasticities[commodity]
                commodity_impact = weight * shock * elasticity
                impact += commodity_impact
                
        return impact
    
    def _calculate_demand_impact(self, global_demand_shock: float) -> float:
        """Calcular impacto via demanda global por commodities"""
        # Elasticidade demanda global - preços commodities
        demand_elasticity = 0.3
        
        return global_demand_shock * demand_elasticity
    
    def _calculate_exchange_impact(self, exchange_rate_shock: float) -> float:
        """Calcular impacto via taxa de câmbio"""
        # Elasticidade câmbio - preços commodities (em USD)
        exchange_elasticity = -0.5
        
        return exchange_rate_shock * exchange_elasticity
    
    def _calculate_fiscal_impact(self, commodity_price_shocks: Dict[str, float]) -> float:
        """Calcular impacto fiscal via royalties e impostos"""
        fiscal_impact = 0.0
        
        for commodity, shock in commodity_price_shocks.items():
            if commodity in self.fiscal_elasticities:
                elasticity = self.fiscal_elasticities[commodity]
                weight = self.commodity_weights[commodity]
                commodity_fiscal = weight * shock * elasticity
                fiscal_impact += commodity_fiscal
                
        return fiscal_impact
    
    def _calculate_terms_of_trade_impact(
        self, 
        commodity_price_shocks: Dict[str, float],
        exchange_rate_shock: float
    ) -> float:
        """Calcular impacto nos termos de troca"""
        # Índice de preços das exportações (commodities)
        export_price_index = 0.0
        for commodity, shock in commodity_price_shocks.items():
            if commodity in self.commodity_weights:
                weight = self.commodity_weights[commodity]
                export_price_index += weight * shock
        
        # Índice de preços das importações (assumido constante)
        import_price_index = 0.0
        
        # Termos de troca = preços exportações / preços importações
        terms_of_trade = export_price_index - import_price_index
        
        # Ajustar pelo câmbio
        terms_of_trade_adjusted = terms_of_trade + exchange_rate_shock * 0.3
        
        return terms_of_trade_adjusted
    
    def _calculate_commodity_contributions(
        self, 
        commodity_price_shocks: Dict[str, float]
    ) -> Dict[str, float]:
        """Calcular contribuição de cada commodity para o spillover"""
        contributions = {}
        
        for commodity, shock in commodity_price_shocks.items():
            if commodity in self.commodity_weights:
                weight = self.commodity_weights[commodity]
                elasticity = self.price_elasticities[commodity]
                contribution = weight * shock * elasticity
                contributions[commodity] = contribution
                
        return contributions
    
    def _calculate_price_elasticities(
        self, 
        commodity_price_shocks: Dict[str, float]
    ) -> Dict[str, float]:
        """Calcular elasticidades observadas"""
        elasticities = {}
        
        for commodity, shock in commodity_price_shocks.items():
            if commodity in self.price_elasticities and abs(shock) > 0.01:
                elasticities[commodity] = self.price_elasticities[commodity]
                
        return elasticities
    
    def _calculate_confidence_interval(self, impact: float) -> Tuple[float, float]:
        """Calcular intervalo de confiança para o impacto"""
        # Erro padrão baseado na volatilidade das commodities
        std_error = abs(impact) * 0.25  # 25% do valor absoluto
        
        lower_bound = impact - 1.96 * std_error
        upper_bound = impact + 1.96 * std_error
        
        return (lower_bound, upper_bound)
    
    def get_commodity_weights(self) -> Dict[str, float]:
        """Obter pesos das commodities"""
        return self.commodity_weights.copy()
    
    def update_commodity_weights(self, new_weights: Dict[str, float]):
        """Atualizar pesos das commodities"""
        # Validar pesos
        total_weight = sum(new_weights.values())
        if not np.isclose(total_weight, 1.0, atol=0.01):
            raise ValueError("Pesos das commodities devem somar 1.0")
        
        self.commodity_weights = new_weights
        logger.info("Pesos das commodities atualizados")
    
    def get_commodity_exposure(self, commodity: str) -> float:
        """Obter exposição do Brasil a uma commodity específica"""
        if commodity not in self.commodity_weights:
            raise ValueError(f"Commodity {commodity} não encontrada")
        
        weight = self.commodity_weights[commodity]
        elasticity = self.price_elasticities[commodity]
        
        return weight * elasticity
    
    def get_fiscal_exposure(self, commodity: str) -> float:
        """Obter exposição fiscal a uma commodity específica"""
        if commodity not in self.commodity_weights:
            raise ValueError(f"Commodity {commodity} não encontrada")
        
        weight = self.commodity_weights[commodity]
        fiscal_elasticity = self.fiscal_elasticities[commodity]
        
        return weight * fiscal_elasticity
