"""
Análise do Canal Comercial - Spillovers Brasil
Implementa RF021 conforme DRS seção 3.2

Baseado em:
- Frankel, J. A., & Romer, D. (1999). Does trade cause growth?
- Imbs, J. (2004). Trade, finance, specialization, and synchronization
- Kose, M. A., et al. (2003). How does globalization affect the synchronization of business cycles?
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

from app.core.config import settings, model_config

logger = logging.getLogger(__name__)

@dataclass
class TradeChannelResult:
    """Resultado da análise do canal comercial"""
    impact_magnitude: float
    key_drivers: List[str]
    affected_sectors: List[str]
    trade_weights: Dict[str, float]
    elasticities: Dict[str, float]
    confidence_interval: Tuple[float, float]

class TradeChannelAnalyzer:
    """
    Analisador do Canal Comercial para Spillovers Brasil
    
    Quantifica spillovers via comércio internacional Brasil-Mundo
    conforme especificação RF021 do DRS.
    """
    
    def __init__(self):
        """Inicializar analisador do canal comercial"""
        self.trade_weights = self._initialize_trade_weights()
        self.sector_weights = self._initialize_sector_weights()
        
    def _initialize_trade_weights(self) -> Dict[str, float]:
        """
        Inicializar pesos comerciais por país/região
        
        Baseado na pauta comercial brasileira (dados aproximados)
        """
        return {
            "USA": 0.18,      # Estados Unidos
            "CHN": 0.32,      # China
            "DEU": 0.08,      # Alemanha
            "ARG": 0.07,      # Argentina
            "NLD": 0.05,      # Holanda
            "JPN": 0.04,      # Japão
            "GBR": 0.04,      # Reino Unido
            "ITA": 0.03,      # Itália
            "FRA": 0.03,      # França
            "CAN": 0.02,      # Canadá
            "OTHER": 0.14     # Outros países
        }
    
    def _initialize_sector_weights(self) -> Dict[str, float]:
        """
        Inicializar pesos por setor da economia brasileira
        
        Baseado na estrutura produtiva brasileira
        """
        return {
            "agriculture": 0.15,      # Agropecuária
            "mining": 0.12,           # Mineração
            "manufacturing": 0.25,    # Indústria de transformação
            "services": 0.40,         # Serviços
            "construction": 0.08      # Construção civil
        }
    
    def calculate_spillovers(
        self, 
        global_demand_shock: Dict[str, float],
        global_price_shock: Dict[str, float],
        exchange_rate_shock: float
    ) -> TradeChannelResult:
        """
        Calcular spillovers via canal comercial
        
        Args:
            global_demand_shock: Choque de demanda global por país
            global_price_shock: Choque de preços globais por país
            exchange_rate_shock: Choque na taxa de câmbio
            
        Returns:
            TradeChannelResult: Resultado da análise
        """
        logger.info("Calculando spillovers via canal comercial")
        
        # 1. Calcular impacto via demanda global
        demand_impact = self._calculate_demand_impact(global_demand_shock)
        
        # 2. Calcular impacto via preços globais
        price_impact = self._calculate_price_impact(global_price_shock)
        
        # 3. Calcular impacto via taxa de câmbio
        exchange_impact = self._calculate_exchange_impact(exchange_rate_shock)
        
        # 4. Agregar impactos
        total_impact = demand_impact + price_impact + exchange_impact
        
        # 5. Identificar drivers principais
        key_drivers = self._identify_key_drivers(
            global_demand_shock, global_price_shock, exchange_rate_shock
        )
        
        # 6. Identificar setores afetados
        affected_sectors = self._identify_affected_sectors(
            demand_impact, price_impact, exchange_impact
        )
        
        # 7. Calcular elasticidades
        elasticities = self._calculate_elasticities(
            global_demand_shock, global_price_shock, exchange_rate_shock
        )
        
        # 8. Calcular intervalo de confiança
        confidence_interval = self._calculate_confidence_interval(total_impact)
        
        return TradeChannelResult(
            impact_magnitude=total_impact,
            key_drivers=key_drivers,
            affected_sectors=affected_sectors,
            trade_weights=self.trade_weights,
            elasticities=elasticities,
            confidence_interval=confidence_interval
        )
    
    def _calculate_demand_impact(self, global_demand_shock: Dict[str, float]) -> float:
        """Calcular impacto via demanda global"""
        impact = 0.0
        
        for country, shock in global_demand_shock.items():
            if country in self.trade_weights:
                # Elasticidade demanda-exportação (baseada em literatura)
                elasticity = 1.5  # Valor típico da literatura
                country_impact = self.trade_weights[country] * shock * elasticity
                impact += country_impact
                
        return impact
    
    def _calculate_price_impact(self, global_price_shock: Dict[str, float]) -> float:
        """Calcular impacto via preços globais"""
        impact = 0.0
        
        for country, shock in global_price_shock.items():
            if country in self.trade_weights:
                # Elasticidade preço-exportação
                elasticity = -0.8  # Valor típico da literatura
                country_impact = self.trade_weights[country] * shock * elasticity
                impact += country_impact
                
        return impact
    
    def _calculate_exchange_impact(self, exchange_rate_shock: float) -> float:
        """Calcular impacto via taxa de câmbio"""
        # Elasticidade câmbio-exportação
        elasticity = 0.6  # Valor típico da literatura
        
        return exchange_rate_shock * elasticity
    
    def _identify_key_drivers(
        self, 
        global_demand_shock: Dict[str, float],
        global_price_shock: Dict[str, float],
        exchange_rate_shock: float
    ) -> List[str]:
        """Identificar drivers principais do spillover"""
        drivers = []
        
        # Identificar países com maior choque de demanda
        max_demand_country = max(global_demand_shock.items(), key=lambda x: abs(x[1]))
        if abs(max_demand_country[1]) > 0.05:  # Threshold de 5%
            drivers.append(f"{max_demand_country[0]}_demand_slowdown")
        
        # Identificar países com maior choque de preços
        max_price_country = max(global_price_shock.items(), key=lambda x: abs(x[1]))
        if abs(max_price_country[1]) > 0.05:  # Threshold de 5%
            drivers.append(f"{max_price_country[0]}_price_increase")
        
        # Verificar choque cambial
        if abs(exchange_rate_shock) > 0.1:  # Threshold de 10%
            drivers.append("exchange_rate_volatility")
        
        return drivers
    
    def _identify_affected_sectors(
        self,
        demand_impact: float,
        price_impact: float,
        exchange_impact: float
    ) -> List[str]:
        """Identificar setores mais afetados"""
        sectors = []
        
        # Setores mais sensíveis à demanda global
        if abs(demand_impact) > 0.1:
            sectors.extend(["manufacturing", "agriculture"])
        
        # Setores mais sensíveis a preços
        if abs(price_impact) > 0.1:
            sectors.extend(["mining", "manufacturing"])
        
        # Setores mais sensíveis ao câmbio
        if abs(exchange_impact) > 0.1:
            sectors.extend(["manufacturing", "services"])
        
        return list(set(sectors))  # Remover duplicatas
    
    def _calculate_elasticities(
        self,
        global_demand_shock: Dict[str, float],
        global_price_shock: Dict[str, float],
        exchange_rate_shock: float
    ) -> Dict[str, float]:
        """Calcular elasticidades do canal comercial"""
        elasticities = {}
        
        # Elasticidade demanda-exportação
        if any(abs(shock) > 0.01 for shock in global_demand_shock.values()):
            elasticities["demand_export"] = 1.5
        
        # Elasticidade preço-exportação
        if any(abs(shock) > 0.01 for shock in global_price_shock.values()):
            elasticities["price_export"] = -0.8
        
        # Elasticidade câmbio-exportação
        if abs(exchange_rate_shock) > 0.01:
            elasticities["exchange_export"] = 0.6
        
        return elasticities
    
    def _calculate_confidence_interval(self, impact: float) -> Tuple[float, float]:
        """Calcular intervalo de confiança para o impacto"""
        # Erro padrão baseado na literatura (aproximado)
        std_error = abs(impact) * 0.2  # 20% do valor absoluto
        
        lower_bound = impact - 1.96 * std_error
        upper_bound = impact + 1.96 * std_error
        
        return (lower_bound, upper_bound)
    
    def get_trade_weights(self) -> Dict[str, float]:
        """Obter pesos comerciais atuais"""
        return self.trade_weights.copy()
    
    def update_trade_weights(self, new_weights: Dict[str, float]):
        """Atualizar pesos comerciais"""
        # Validar pesos
        total_weight = sum(new_weights.values())
        if not np.isclose(total_weight, 1.0, atol=0.01):
            raise ValueError("Pesos comerciais devem somar 1.0")
        
        self.trade_weights = new_weights
        logger.info("Pesos comerciais atualizados")
    
    def get_sector_exposure(self, sector: str) -> float:
        """Obter exposição de um setor ao comércio internacional"""
        if sector not in self.sector_weights:
            raise ValueError(f"Setor {sector} não encontrado")
        
        # Exposição baseada no peso do setor e intensidade comercial
        sector_weight = self.sector_weights[sector]
        trade_intensity = 0.3  # Intensidade comercial média (30%)
        
        return sector_weight * trade_intensity
