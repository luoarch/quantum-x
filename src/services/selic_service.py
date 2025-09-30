"""
Serviço para gerenciar dados da Selic
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
import os
import json

from src.types.selic_types import (
    SelicData, SelicAccessor, SelicRateType, CopomMeeting, 
    CopomDecision, SelicCycle, SELIC_HISTORICAL_PERIODS
)

class SelicService:
    """Serviço para gerenciar dados da Selic"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._data: Optional[SelicData] = None
        self._accessor: Optional[SelicAccessor] = None
    
    def load_data(self) -> SelicData:
        """Carregar dados da Selic"""
        if self._data is not None:
            return self._data
        
        print("🇧🇷 Carregando dados da Selic...")
        
        # Carregar dados combinados
        combined_data = self._load_combined_data()
        
        # Organizar dados
        self._data = self._organize_selic_data(combined_data)
        
        print(f"✅ Dados da Selic carregados: {len(self._data.selic)} observações")
        print(f"   Período: {self._data.selic.index[0].date()} a {self._data.selic.index[-1].date()}")
        
        return self._data
    
    def get_accessor(self) -> SelicAccessor:
        """Obter interface de acesso aos dados"""
        if self._accessor is None:
            data = self.load_data()
            self._accessor = SelicAccessor(data)
        
        return self._accessor
    
    def _load_combined_data(self) -> pd.DataFrame:
        """Carregar dados combinados Fed-Selic"""
        combined_path = os.path.join(self.data_dir, "raw", "fed_selic_combined.csv")
        
        if not os.path.exists(combined_path):
            raise FileNotFoundError(f"Dados combinados não encontrados: {combined_path}")
        
        df = pd.read_csv(combined_path, index_col=0, parse_dates=True)
        
        if 'selic' not in df.columns:
            raise ValueError("Coluna 'selic' não encontrada nos dados")
        
        return df
    
    def _organize_selic_data(self, combined_data: pd.DataFrame) -> SelicData:
        """Organizar dados da Selic"""
        
        # Selic principal
        selic = combined_data['selic']
        
        # Tentar carregar dados adicionais se disponíveis
        selic_meta = None
        cdi = None
        ipca = None
        
        # Verificar se há dados do IPCA
        if 'ipca' in combined_data.columns:
            ipca = combined_data['ipca']
        
        # Criar decisões do Copom (simuladas baseadas em mudanças significativas)
        copom_decisions = self._create_copom_decisions(selic)
        
        # Criar ciclos da Selic
        cycles = self._create_selic_cycles(selic)
        
        # Metadados
        metadata = {
            'created_at': datetime.now().isoformat(),
            'observations': len(selic),
            'start_date': selic.index[0].isoformat(),
            'end_date': selic.index[-1].isoformat(),
            'data_source': 'BCB + Historical',
            'has_ipca': ipca is not None,
            'copom_decisions_count': len(copom_decisions),
            'cycles_count': len(cycles)
        }
        
        return SelicData(
            selic=selic,
            selic_meta=selic_meta,
            cdi=cdi,
            ipca=ipca,
            copom_decisions=copom_decisions,
            cycles=cycles,
            metadata=metadata
        )
    
    def _create_copom_decisions(self, selic: pd.Series) -> List[CopomDecision]:
        """Criar decisões do Copom baseadas em mudanças significativas"""
        decisions = []
        
        # Calcular mudanças mensais
        monthly_changes = selic.diff()
        
        # Identificar mudanças significativas (> 25 bps)
        significant_changes = monthly_changes[abs(monthly_changes) >= 0.25]
        
        for date, change in significant_changes.items():
            if pd.isna(change):
                continue
            
            # Determinar tipo de decisão
            if change > 0:
                decision = "aumento"
            elif change < 0:
                decision = "reducao"
            else:
                decision = "manutencao"
            
            # Determinar reunião do Copom (aproximação)
            month = date.month
            meeting_map = {
                1: CopomMeeting.JANEIRO,
                3: CopomMeeting.MARCO,
                5: CopomMeeting.MAIO,
                6: CopomMeeting.JUNHO,
                8: CopomMeeting.AGOSTO,
                9: CopomMeeting.SETEMBRO,
                11: CopomMeeting.NOVEMBRO,
                12: CopomMeeting.DEZEMBRO
            }
            
            meeting = meeting_map.get(month, CopomMeeting.JANEIRO)
            
            # Taxa antes e depois
            selic_before = selic.loc[date] - change
            selic_after = selic.loc[date]
            
            decisions.append(CopomDecision(
                date=date,
                selic_before=selic_before,
                selic_after=selic_after,
                change_bps=int(change * 100),
                decision=decision,
                meeting=meeting,
                rationale=f"Mudança de {change:.2f}%"
            ))
        
        return sorted(decisions, key=lambda x: x.date)
    
    def _create_selic_cycles(self, selic: pd.Series) -> List[SelicCycle]:
        """Criar ciclos da Selic baseados em tendências"""
        cycles = []
        
        # Calcular mudanças mensais
        monthly_changes = selic.diff()
        
        # Identificar pontos de virada (mudança de direção)
        turning_points = []
        for i in range(1, len(monthly_changes) - 1):
            prev_change = monthly_changes.iloc[i-1]
            curr_change = monthly_changes.iloc[i]
            next_change = monthly_changes.iloc[i+1]
            
            # Mudança de direção significativa
            if (prev_change > 0 and curr_change < 0) or (prev_change < 0 and curr_change > 0):
                if abs(curr_change) >= 0.25:  # Mudança significativa
                    turning_points.append(selic.index[i])
        
        # Criar ciclos entre pontos de virada
        if not turning_points:
            # Se não há pontos de virada, criar um ciclo único
            cycles.append(SelicCycle(
                start_date=selic.index[0],
                end_date=selic.index[-1],
                start_rate=selic.iloc[0],
                end_rate=selic.iloc[-1],
                max_rate=selic.max(),
                min_rate=selic.min(),
                total_change_bps=int((selic.iloc[-1] - selic.iloc[0]) * 100),
                cycle_type=self._determine_cycle_type(selic.iloc[0], selic.iloc[-1]),
                duration_months=len(selic)
            ))
        else:
            # Criar ciclos entre pontos de virada
            cycle_starts = [selic.index[0]] + turning_points
            cycle_ends = turning_points + [selic.index[-1]]
            
            for start_date, end_date in zip(cycle_starts, cycle_ends):
                cycle_selic = selic[start_date:end_date]
                
                if len(cycle_selic) < 3:  # Pular ciclos muito curtos
                    continue
                
                cycles.append(SelicCycle(
                    start_date=start_date,
                    end_date=end_date,
                    start_rate=cycle_selic.iloc[0],
                    end_rate=cycle_selic.iloc[-1],
                    max_rate=cycle_selic.max(),
                    min_rate=cycle_selic.min(),
                    total_change_bps=int((cycle_selic.iloc[-1] - cycle_selic.iloc[0]) * 100),
                    cycle_type=self._determine_cycle_type(cycle_selic.iloc[0], cycle_selic.iloc[-1]),
                    duration_months=len(cycle_selic)
                ))
        
        return cycles
    
    def _determine_cycle_type(self, start_rate: float, end_rate: float) -> str:
        """Determinar tipo de ciclo"""
        change = end_rate - start_rate
        
        if change > 1.0:  # Aumento significativo
            return "alta"
        elif change < -1.0:  # Redução significativa
            return "baixa"
        else:
            return "estavel"
    
    def get_selic_summary(self) -> Dict[str, Union[float, str, int]]:
        """Obter resumo da Selic"""
        accessor = self.get_accessor()
        
        stats = accessor.get_selic_statistics()
        
        # Adicionar informações de ciclo
        current_cycle = accessor.get_current_cycle()
        if current_cycle:
            stats['current_cycle_type'] = current_cycle.cycle_type
            stats['current_cycle_duration'] = current_cycle.duration_months
        
        # Adicionar tendência
        stats['trend'] = accessor.get_selic_trend()
        
        # Adicionar informações do IPCA se disponível
        if accessor.get_ipca_current() is not None:
            stats['ipca_current'] = accessor.get_ipca_current()
            stats['ipca_yoy'] = accessor.get_ipca_yoy().iloc[-1]
        
        return stats
    
    def get_copom_summary(self) -> Dict[str, Union[int, List[Dict]]]:
        """Obter resumo das decisões do Copom"""
        accessor = self.get_accessor()
        
        decisions = accessor.get_copom_decisions()
        recent_decisions = accessor.get_recent_decisions(12)
        
        # Contar por tipo
        decision_counts = {}
        for decision in decisions:
            decision_counts[decision.decision] = decision_counts.get(decision.decision, 0) + 1
        
        # Últimas decisões
        last_decisions = []
        for decision in recent_decisions[-5:]:  # Últimas 5
            last_decisions.append({
                'date': decision.date.isoformat(),
                'decision': decision.decision,
                'change_bps': decision.change_bps,
                'selic_after': decision.selic_after
            })
        
        return {
            'total_decisions': len(decisions),
            'recent_decisions_count': len(recent_decisions),
            'decision_counts': decision_counts,
            'last_decisions': last_decisions
        }
    
    def get_cycle_summary(self) -> Dict[str, Union[int, List[Dict]]]:
        """Obter resumo dos ciclos da Selic"""
        accessor = self.get_accessor()
        
        cycles = accessor.get_selic_cycles()
        current_cycle = accessor.get_current_cycle()
        
        # Contar por tipo
        cycle_counts = {}
        for cycle in cycles:
            cycle_counts[cycle.cycle_type] = cycle_counts.get(cycle.cycle_type, 0) + 1
        
        # Ciclos recentes
        recent_cycles = []
        for cycle in cycles[-3:]:  # Últimos 3
            recent_cycles.append({
                'start_date': cycle.start_date.isoformat(),
                'end_date': cycle.end_date.isoformat(),
                'cycle_type': cycle.cycle_type,
                'total_change_bps': cycle.total_change_bps,
                'duration_months': cycle.duration_months
            })
        
        result = {
            'total_cycles': len(cycles),
            'cycle_counts': cycle_counts,
            'recent_cycles': recent_cycles
        }
        
        if current_cycle:
            result['current_cycle'] = {
                'start_date': current_cycle.start_date.isoformat(),
                'cycle_type': current_cycle.cycle_type,
                'duration_months': current_cycle.duration_months,
                'total_change_bps': current_cycle.total_change_bps
            }
        
        return result
