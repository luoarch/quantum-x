"""
Tipos específicos para taxas de juros
Foco em Fed Funds Rate, Treasury Rates e Selic
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime
from enum import Enum
import pandas as pd

class InterestRateType(Enum):
    """Tipos de taxas de juros"""
    FED_FUNDS = "fed_funds"
    FED_FUNDS_DAILY = "fed_funds_daily"
    TREASURY_1M = "treasury_1m"
    TREASURY_3M = "treasury_3m"
    TREASURY_6M = "treasury_6m"
    TREASURY_1Y = "treasury_1y"
    TREASURY_2Y = "treasury_2y"
    TREASURY_3Y = "treasury_3y"
    TREASURY_5Y = "treasury_5y"
    TREASURY_7Y = "treasury_7y"
    TREASURY_10Y = "treasury_10y"
    TREASURY_20Y = "treasury_20y"
    TREASURY_30Y = "treasury_30y"
    SELIC = "selic"

class RateMaturity(Enum):
    """Maturidades das taxas"""
    OVERNIGHT = "overnight"
    SHORT_TERM = "short_term"  # 1M, 3M, 6M
    MEDIUM_TERM = "medium_term"  # 1Y, 2Y, 3Y
    LONG_TERM = "long_term"  # 5Y, 7Y, 10Y, 20Y, 30Y

@dataclass
class InterestRatePoint:
    """Ponto de dados de taxa de juros"""
    date: datetime
    rate: float
    rate_type: InterestRateType
    maturity: Optional[RateMaturity] = None
    change: Optional[float] = None
    pct_change: Optional[float] = None

@dataclass
class YieldCurvePoint:
    """Ponto da curva de juros"""
    maturity_months: int
    rate: float
    rate_type: InterestRateType

@dataclass
class YieldCurve:
    """Curva de juros completa"""
    date: datetime
    points: List[YieldCurvePoint]
    slope_2y10y: Optional[float] = None
    slope_3m10y: Optional[float] = None

@dataclass
class InterestRateData:
    """Dados de taxas de juros organizados"""
    fed_funds: pd.Series
    treasury_rates: Dict[InterestRateType, pd.Series]
    selic: pd.Series
    yield_curves: List[YieldCurve]
    metadata: Dict[str, Union[str, int, float]]

class InterestRateAccessor:
    """Interface para acesso fácil às taxas de juros"""
    
    def __init__(self, data: InterestRateData):
        self.data = data
        self._fed_funds = data.fed_funds
        self._treasury_rates = data.treasury_rates
        self._selic = data.selic
    
    # Fed Funds Rate
    def get_fed_funds(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.Series:
        """Obter Fed Funds Rate"""
        return self._filter_series(self._fed_funds, start_date, end_date)
    
    def get_fed_funds_current(self) -> float:
        """Obter Fed Funds Rate atual"""
        return self._fed_funds.iloc[-1]
    
    def get_fed_funds_change(self, periods: int = 1) -> pd.Series:
        """Obter mudança na Fed Funds Rate"""
        return self._fed_funds.diff(periods)
    
    # Treasury Rates
    def get_treasury_rate(self, rate_type: InterestRateType, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.Series:
        """Obter taxa do Treasury específica"""
        if rate_type not in self._treasury_rates:
            raise ValueError(f"Taxa {rate_type} não disponível")
        return self._filter_series(self._treasury_rates[rate_type], start_date, end_date)
    
    def get_treasury_10y(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.Series:
        """Obter 10-Year Treasury Rate"""
        return self.get_treasury_rate(InterestRateType.TREASURY_10Y, start_date, end_date)
    
    def get_treasury_2y(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.Series:
        """Obter 2-Year Treasury Rate"""
        return self.get_treasury_rate(InterestRateType.TREASURY_2Y, start_date, end_date)
    
    def get_treasury_3m(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.Series:
        """Obter 3-Month Treasury Rate"""
        return self.get_treasury_rate(InterestRateType.TREASURY_3M, start_date, end_date)
    
    # Selic
    def get_selic(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.Series:
        """Obter Selic"""
        return self._filter_series(self._selic, start_date, end_date)
    
    def get_selic_current(self) -> float:
        """Obter Selic atual"""
        return self._selic.iloc[-1]
    
    def get_selic_change(self, periods: int = 1) -> pd.Series:
        """Obter mudança na Selic"""
        return self._selic.diff(periods)
    
    # Yield Curve
    def get_yield_curve(self, date: Optional[datetime] = None) -> YieldCurve:
        """Obter curva de juros para uma data específica"""
        if date is None:
            date = self._fed_funds.index[-1]
        
        # Encontrar curva mais próxima da data
        for curve in self.data.yield_curves:
            if abs((curve.date - date).days) <= 7:  # Dentro de 7 dias
                return curve
        
        # Se não encontrar, criar curva com dados disponíveis
        return self._create_yield_curve(date)
    
    def get_yield_curve_slope_2y10y(self, date: Optional[datetime] = None) -> float:
        """Obter slope da curva 2Y-10Y"""
        if date is None:
            date = self._fed_funds.index[-1]
        
        try:
            treasury_10y = self.get_treasury_10y(date, date)
            treasury_2y = self.get_treasury_2y(date, date)
            
            if len(treasury_10y) > 0 and len(treasury_2y) > 0:
                return treasury_10y.iloc[0] - treasury_2y.iloc[0]
        except:
            pass
        
        return 0.0
    
    def get_yield_curve_slope_3m10y(self, date: Optional[datetime] = None) -> float:
        """Obter slope da curva 3M-10Y"""
        if date is None:
            date = self._fed_funds.index[-1]
        
        try:
            treasury_10y = self.get_treasury_10y(date, date)
            treasury_3m = self.get_treasury_3m(date, date)
            
            if len(treasury_10y) > 0 and len(treasury_3m) > 0:
                return treasury_10y.iloc[0] - treasury_3m.iloc[0]
        except:
            pass
        
        return 0.0
    
    # Spreads
    def get_fed_selic_spread(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.Series:
        """Obter spread Fed-Selic"""
        fed = self.get_fed_funds(start_date, end_date)
        selic = self.get_selic(start_date, end_date)
        return fed - selic
    
    def get_treasury_spread(self, long_term: InterestRateType, short_term: InterestRateType, 
                           start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.Series:
        """Obter spread entre taxas do Treasury"""
        long_rate = self.get_treasury_rate(long_term, start_date, end_date)
        short_rate = self.get_treasury_rate(short_term, start_date, end_date)
        return long_rate - short_rate
    
    # Estatísticas
    def get_rate_statistics(self, rate_type: InterestRateType, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, float]:
        """Obter estatísticas de uma taxa"""
        if rate_type == InterestRateType.SELIC:
            series = self.get_selic(start_date, end_date)
        elif rate_type == InterestRateType.FED_FUNDS:
            series = self.get_fed_funds(start_date, end_date)
        else:
            series = self.get_treasury_rate(rate_type, start_date, end_date)
        
        return {
            'mean': series.mean(),
            'std': series.std(),
            'min': series.min(),
            'max': series.max(),
            'current': series.iloc[-1],
            'observations': len(series)
        }
    
    # Métodos auxiliares
    def _filter_series(self, series: pd.Series, start_date: Optional[datetime], end_date: Optional[datetime]) -> pd.Series:
        """Filtrar série por data"""
        if start_date is None and end_date is None:
            return series
        
        mask = pd.Series(True, index=series.index)
        
        if start_date is not None:
            mask &= series.index >= start_date
        
        if end_date is not None:
            mask &= series.index <= end_date
        
        return series[mask]
    
    def _create_yield_curve(self, date: datetime) -> YieldCurve:
        """Criar curva de juros para uma data específica"""
        points = []
        
        # Mapear tipos de taxa para maturidades em meses
        maturity_map = {
            InterestRateType.TREASURY_1M: 1,
            InterestRateType.TREASURY_3M: 3,
            InterestRateType.TREASURY_6M: 6,
            InterestRateType.TREASURY_1Y: 12,
            InterestRateType.TREASURY_2Y: 24,
            InterestRateType.TREASURY_3Y: 36,
            InterestRateType.TREASURY_5Y: 60,
            InterestRateType.TREASURY_7Y: 84,
            InterestRateType.TREASURY_10Y: 120,
            InterestRateType.TREASURY_20Y: 240,
            InterestRateType.TREASURY_30Y: 360
        }
        
        for rate_type, maturity_months in maturity_map.items():
            if rate_type in self._treasury_rates:
                try:
                    rate_series = self._treasury_rates[rate_type]
                    # Encontrar valor mais próximo da data
                    closest_idx = rate_series.index.get_indexer([date], method='nearest')[0]
                    if closest_idx >= 0:
                        rate = rate_series.iloc[closest_idx]
                        points.append(YieldCurvePoint(maturity_months, rate, rate_type))
                except:
                    continue
        
        slope_2y10y = self.get_yield_curve_slope_2y10y(date)
        slope_3m10y = self.get_yield_curve_slope_3m10y(date)
        
        return YieldCurve(date, points, slope_2y10y, slope_3m10y)

# Constantes úteis
TREASURY_MATURITIES = [
    InterestRateType.TREASURY_1M,
    InterestRateType.TREASURY_3M,
    InterestRateType.TREASURY_6M,
    InterestRateType.TREASURY_1Y,
    InterestRateType.TREASURY_2Y,
    InterestRateType.TREASURY_3Y,
    InterestRateType.TREASURY_5Y,
    InterestRateType.TREASURY_7Y,
    InterestRateType.TREASURY_10Y,
    InterestRateType.TREASURY_20Y,
    InterestRateType.TREASURY_30Y
]

SHORT_TERM_RATES = [
    InterestRateType.TREASURY_1M,
    InterestRateType.TREASURY_3M,
    InterestRateType.TREASURY_6M
]

MEDIUM_TERM_RATES = [
    InterestRateType.TREASURY_1Y,
    InterestRateType.TREASURY_2Y,
    InterestRateType.TREASURY_3Y
]

LONG_TERM_RATES = [
    InterestRateType.TREASURY_5Y,
    InterestRateType.TREASURY_7Y,
    InterestRateType.TREASURY_10Y,
    InterestRateType.TREASURY_20Y,
    InterestRateType.TREASURY_30Y
]
