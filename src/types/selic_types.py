"""
Tipos específicos para dados da Selic
Inclui Selic, CDI, e outras taxas brasileiras
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime
from enum import Enum
import pandas as pd

class SelicRateType(Enum):
    """Tipos de taxas da Selic"""
    SELIC = "selic"
    SELIC_META = "selic_meta"
    SELIC_EFETIVA = "selic_efetiva"
    CDI = "cdi"
    CDI_OVER = "cdi_over"
    IPCA = "ipca"
    IPCA_ACUMULADO = "ipca_acumulado"

class CopomMeeting(Enum):
    """Reuniões do Copom"""
    JANEIRO = "janeiro"
    MARCO = "marco"
    MAIO = "maio"
    JUNHO = "junho"
    AGOSTO = "agosto"
    SETEMBRO = "setembro"
    NOVEMBRO = "novembro"
    DEZEMBRO = "dezembro"

@dataclass
class SelicDataPoint:
    """Ponto de dados da Selic"""
    date: datetime
    selic: float
    rate_type: SelicRateType
    copom_meeting: Optional[CopomMeeting] = None
    change: Optional[float] = None
    pct_change: Optional[float] = None
    is_meeting_day: bool = False

@dataclass
class CopomDecision:
    """Decisão do Copom"""
    date: datetime
    selic_before: float
    selic_after: float
    change_bps: int
    decision: str  # "aumento", "reducao", "manutencao"
    meeting: CopomMeeting
    rationale: Optional[str] = None

@dataclass
class SelicCycle:
    """Ciclo da Selic"""
    start_date: datetime
    end_date: datetime
    start_rate: float
    end_rate: float
    max_rate: float
    min_rate: float
    total_change_bps: int
    cycle_type: str  # "alta", "baixa", "estavel"
    duration_months: int

@dataclass
class SelicData:
    """Dados da Selic organizados"""
    selic: pd.Series
    selic_meta: Optional[pd.Series] = None
    cdi: Optional[pd.Series] = None
    ipca: Optional[pd.Series] = None
    copom_decisions: List[CopomDecision] = None
    cycles: List[SelicCycle] = None
    metadata: Dict[str, Union[str, int, float]] = None

class SelicAccessor:
    """Interface para acesso fácil aos dados da Selic"""
    
    def __init__(self, data: SelicData):
        self.data = data
        self._selic = data.selic
        self._selic_meta = data.selic_meta
        self._cdi = data.cdi
        self._ipca = data.ipca
    
    # Selic básica
    def get_selic(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.Series:
        """Obter Selic"""
        return self._filter_series(self._selic, start_date, end_date)
    
    def get_selic_current(self) -> float:
        """Obter Selic atual"""
        return self._selic.iloc[-1]
    
    def get_selic_change(self, periods: int = 1) -> pd.Series:
        """Obter mudança na Selic"""
        return self._selic.diff(periods)
    
    def get_selic_pct_change(self, periods: int = 1) -> pd.Series:
        """Obter mudança percentual na Selic"""
        return self._selic.pct_change(periods) * 100
    
    # Selic Meta
    def get_selic_meta(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Optional[pd.Series]:
        """Obter Selic Meta"""
        if self._selic_meta is None:
            return None
        return self._filter_series(self._selic_meta, start_date, end_date)
    
    def get_selic_meta_current(self) -> Optional[float]:
        """Obter Selic Meta atual"""
        if self._selic_meta is None:
            return None
        return self._selic_meta.iloc[-1]
    
    # CDI
    def get_cdi(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Optional[pd.Series]:
        """Obter CDI"""
        if self._cdi is None:
            return None
        return self._filter_series(self._cdi, start_date, end_date)
    
    def get_cdi_current(self) -> Optional[float]:
        """Obter CDI atual"""
        if self._cdi is None:
            return None
        return self._cdi.iloc[-1]
    
    def get_selic_cdi_spread(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Optional[pd.Series]:
        """Obter spread Selic-CDI"""
        if self._cdi is None:
            return None
        selic = self.get_selic(start_date, end_date)
        cdi = self.get_cdi(start_date, end_date)
        return selic - cdi
    
    # IPCA
    def get_ipca(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Optional[pd.Series]:
        """Obter IPCA"""
        if self._ipca is None:
            return None
        return self._filter_series(self._ipca, start_date, end_date)
    
    def get_ipca_current(self) -> Optional[float]:
        """Obter IPCA atual"""
        if self._ipca is None:
            return None
        return self._ipca.iloc[-1]
    
    def get_ipca_yoy(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Optional[pd.Series]:
        """Obter IPCA acumulado em 12 meses"""
        if self._ipca is None:
            return None
        ipca = self.get_ipca(start_date, end_date)
        return ipca.pct_change(12) * 100
    
    def get_ipca_mom(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Optional[pd.Series]:
        """Obter IPCA mensal"""
        if self._ipca is None:
            return None
        ipca = self.get_ipca(start_date, end_date)
        return ipca.pct_change() * 100
    
    # Ciclos da Selic
    def get_selic_cycles(self) -> List[SelicCycle]:
        """Obter ciclos da Selic"""
        if self.data.cycles is None:
            return []
        return self.data.cycles
    
    def get_current_cycle(self) -> Optional[SelicCycle]:
        """Obter ciclo atual da Selic"""
        cycles = self.get_selic_cycles()
        if not cycles:
            return None
        
        current_date = datetime.now()
        for cycle in cycles:
            if cycle.start_date <= current_date <= cycle.end_date:
                return cycle
        
        return cycles[-1] if cycles else None
    
    def get_cycle_by_type(self, cycle_type: str) -> List[SelicCycle]:
        """Obter ciclos por tipo"""
        cycles = self.get_selic_cycles()
        return [cycle for cycle in cycles if cycle.cycle_type == cycle_type]
    
    # Decisões do Copom
    def get_copom_decisions(self) -> List[CopomDecision]:
        """Obter decisões do Copom"""
        if self.data.copom_decisions is None:
            return []
        return self.data.copom_decisions
    
    def get_recent_decisions(self, months: int = 12) -> List[CopomDecision]:
        """Obter decisões recentes do Copom"""
        decisions = self.get_copom_decisions()
        cutoff_date = datetime.now() - pd.DateOffset(months=months)
        return [d for d in decisions if d.date >= cutoff_date]
    
    def get_decisions_by_type(self, decision_type: str) -> List[CopomDecision]:
        """Obter decisões por tipo"""
        decisions = self.get_copom_decisions()
        return [d for d in decisions if d.decision == decision_type]
    
    # Análise de tendências
    def get_selic_trend(self, periods: int = 12) -> str:
        """Obter tendência da Selic"""
        recent_selic = self._selic.tail(periods)
        if len(recent_selic) < 2:
            return "indefinida"
        
        first_rate = recent_selic.iloc[0]
        last_rate = recent_selic.iloc[-1]
        change = last_rate - first_rate
        
        if change > 0.5:
            return "alta"
        elif change < -0.5:
            return "baixa"
        else:
            return "estavel"
    
    def get_selic_volatility(self, periods: int = 12) -> float:
        """Obter volatilidade da Selic"""
        recent_selic = self._selic.tail(periods)
        return recent_selic.std()
    
    def get_selic_range(self, periods: int = 12) -> Tuple[float, float]:
        """Obter range da Selic"""
        recent_selic = self._selic.tail(periods)
        return recent_selic.min(), recent_selic.max()
    
    # Estatísticas
    def get_selic_statistics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, float]:
        """Obter estatísticas da Selic"""
        selic = self.get_selic(start_date, end_date)
        
        return {
            'mean': selic.mean(),
            'std': selic.std(),
            'min': selic.min(),
            'max': selic.max(),
            'current': selic.iloc[-1],
            'observations': len(selic),
            'trend': self.get_selic_trend(),
            'volatility': self.get_selic_volatility()
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

# Constantes úteis
SELIC_DISCRETIZATION = 25  # Múltiplos de 25 bps
COPOM_MEETINGS_PER_YEAR = 8
SELIC_TARGET_RANGE = (2.0, 20.0)  # Range típico da Selic

# Períodos históricos importantes da Selic
SELIC_HISTORICAL_PERIODS = {
    "crise_2008": (datetime(2008, 1, 1), datetime(2009, 12, 31)),
    "crise_2015": (datetime(2015, 1, 1), datetime(2016, 12, 31)),
    "covid_2020": (datetime(2020, 1, 1), datetime(2021, 12, 31)),
    "inflacao_2021": (datetime(2021, 1, 1), datetime(2022, 12, 31)),
    "recente": (datetime(2020, 1, 1), datetime.now())
}

# Tipos de decisão do Copom
COPOM_DECISION_TYPES = {
    "aumento": "Aumento da taxa",
    "reducao": "Redução da taxa", 
    "manutencao": "Manutenção da taxa"
}

# Tipos de ciclo da Selic
SELIC_CYCLE_TYPES = {
    "alta": "Ciclo de alta",
    "baixa": "Ciclo de baixa",
    "estavel": "Ciclo estável"
}
