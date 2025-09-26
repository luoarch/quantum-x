"""
Módulo de Análise de Spillovers para o Brasil
Implementa RF021-RF040 conforme DRS
"""

from .trade_channel import TradeChannelAnalyzer
from .commodity_channel import CommodityChannelAnalyzer
from .financial_channel import FinancialChannelAnalyzer
from .supply_chain_channel import SupplyChainChannelAnalyzer
from .spillover_aggregator import SpilloverAggregator

__all__ = [
    'TradeChannelAnalyzer',
    'CommodityChannelAnalyzer',
    'FinancialChannelAnalyzer', 
    'SupplyChainChannelAnalyzer',
    'SpilloverAggregator'
]

__version__ = "1.0.0"
