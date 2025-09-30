"""
Serviço para carregar e organizar dados de taxas de juros
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Union
import os
import json

from src.types.interest_rates import (
    InterestRateData, InterestRateAccessor, InterestRateType, 
    YieldCurve, YieldCurvePoint, RateMaturity
)

class InterestRateService:
    """Serviço para gerenciar dados de taxas de juros"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._data: Optional[InterestRateData] = None
        self._accessor: Optional[InterestRateAccessor] = None
    
    def load_data(self) -> InterestRateData:
        """Carregar dados de taxas de juros"""
        if self._data is not None:
            return self._data
        
        print("📊 Carregando dados de taxas de juros...")
        
        # Carregar dados do Fed
        fed_data = self._load_fed_data()
        
        # Carregar dados da Selic
        selic_data = self._load_selic_data()
        
        # Organizar dados
        self._data = self._organize_data(fed_data, selic_data)
        
        print(f"✅ Dados carregados: {len(self._data.fed_funds)} observações")
        print(f"   Período: {self._data.fed_funds.index[0].date()} a {self._data.fed_funds.index[-1].date()}")
        
        return self._data
    
    def get_accessor(self) -> InterestRateAccessor:
        """Obter interface de acesso aos dados"""
        if self._accessor is None:
            data = self.load_data()
            self._accessor = InterestRateAccessor(data)
        
        return self._accessor
    
    def _load_fed_data(self) -> pd.DataFrame:
        """Carregar dados do Fed"""
        fed_path = os.path.join(self.data_dir, "raw", "fed_detailed_data.csv")
        
        if not os.path.exists(fed_path):
            raise FileNotFoundError(f"Dados do Fed não encontrados: {fed_path}")
        
        df = pd.read_csv(fed_path, index_col=0, parse_dates=True)
        
        # Mapear colunas para tipos de taxa
        column_mapping = {
            'fedfunds': InterestRateType.FED_FUNDS,
            'dff': InterestRateType.FED_FUNDS_DAILY,
            'dgs1mo': InterestRateType.TREASURY_1M,
            'dgs3mo': InterestRateType.TREASURY_3M,
            'dgs6mo': InterestRateType.TREASURY_6M,
            'dgs1': InterestRateType.TREASURY_1Y,
            'dgs2': InterestRateType.TREASURY_2Y,
            'dgs3': InterestRateType.TREASURY_3Y,
            'dgs5': InterestRateType.TREASURY_5Y,
            'dgs7': InterestRateType.TREASURY_7Y,
            'dgs10': InterestRateType.TREASURY_10Y,
            'dgs20': InterestRateType.TREASURY_20Y,
            'dgs30': InterestRateType.TREASURY_30Y
        }
        
        # Filtrar apenas colunas de taxas de juros
        rate_columns = {col: rate_type for col, rate_type in column_mapping.items() if col in df.columns}
        
        return df[list(rate_columns.keys())]
    
    def _load_selic_data(self) -> pd.Series:
        """Carregar dados da Selic"""
        selic_path = os.path.join(self.data_dir, "raw", "fed_selic_combined.csv")
        
        if not os.path.exists(selic_path):
            raise FileNotFoundError(f"Dados da Selic não encontrados: {selic_path}")
        
        df = pd.read_csv(selic_path, index_col=0, parse_dates=True)
        
        if 'selic' not in df.columns:
            raise ValueError("Coluna 'selic' não encontrada nos dados")
        
        return df['selic']
    
    def _organize_data(self, fed_data: pd.DataFrame, selic_data: pd.Series) -> InterestRateData:
        """Organizar dados em estrutura de taxas de juros"""
        
        # Fed Funds Rate (usar fedfunds se disponível, senão dff)
        if 'fedfunds' in fed_data.columns:
            fed_funds = fed_data['fedfunds']
        elif 'dff' in fed_data.columns:
            fed_funds = fed_data['dff']
        else:
            raise ValueError("Fed Funds Rate não encontrada nos dados")
        
        # Treasury Rates
        treasury_rates = {}
        treasury_mapping = {
            'dgs1mo': InterestRateType.TREASURY_1M,
            'dgs3mo': InterestRateType.TREASURY_3M,
            'dgs6mo': InterestRateType.TREASURY_6M,
            'dgs1': InterestRateType.TREASURY_1Y,
            'dgs2': InterestRateType.TREASURY_2Y,
            'dgs3': InterestRateType.TREASURY_3Y,
            'dgs5': InterestRateType.TREASURY_5Y,
            'dgs7': InterestRateType.TREASURY_7Y,
            'dgs10': InterestRateType.TREASURY_10Y,
            'dgs20': InterestRateType.TREASURY_20Y,
            'dgs30': InterestRateType.TREASURY_30Y
        }
        
        for col, rate_type in treasury_mapping.items():
            if col in fed_data.columns:
                treasury_rates[rate_type] = fed_data[col]
        
        # Criar curvas de juros para datas principais
        yield_curves = self._create_yield_curves(fed_data, treasury_rates)
        
        # Metadados
        metadata = {
            'created_at': datetime.now().isoformat(),
            'observations': len(fed_funds),
            'start_date': fed_funds.index[0].isoformat(),
            'end_date': fed_funds.index[-1].isoformat(),
            'treasury_rates_count': len(treasury_rates),
            'yield_curves_count': len(yield_curves)
        }
        
        return InterestRateData(
            fed_funds=fed_funds,
            treasury_rates=treasury_rates,
            selic=selic_data,
            yield_curves=yield_curves,
            metadata=metadata
        )
    
    def _create_yield_curves(self, fed_data: pd.DataFrame, treasury_rates: Dict[InterestRateType, pd.Series]) -> List[YieldCurve]:
        """Criar curvas de juros para datas principais"""
        yield_curves = []
        
        # Criar curvas para datas principais (trimestralmente)
        dates = fed_data.index[::3]  # A cada 3 meses
        
        for date in dates:
            points = []
            
            # Mapear maturidades
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
                if rate_type in treasury_rates:
                    try:
                        rate_series = treasury_rates[rate_type]
                        # Encontrar valor mais próximo da data
                        closest_idx = rate_series.index.get_indexer([date], method='nearest')[0]
                        if closest_idx >= 0:
                            rate = rate_series.iloc[closest_idx]
                            points.append(YieldCurvePoint(maturity_months, rate, rate_type))
                    except:
                        continue
            
            if points:  # Só adicionar se houver pontos
                # Calcular slopes
                slope_2y10y = self._calculate_slope_2y10y(treasury_rates, date)
                slope_3m10y = self._calculate_slope_3m10y(treasury_rates, date)
                
                yield_curves.append(YieldCurve(date, points, slope_2y10y, slope_3m10y))
        
        return yield_curves
    
    def _calculate_slope_2y10y(self, treasury_rates: Dict[InterestRateType, pd.Series], date: datetime) -> float:
        """Calcular slope 2Y-10Y"""
        try:
            if (InterestRateType.TREASURY_10Y in treasury_rates and 
                InterestRateType.TREASURY_2Y in treasury_rates):
                
                rate_10y = treasury_rates[InterestRateType.TREASURY_10Y]
                rate_2y = treasury_rates[InterestRateType.TREASURY_2Y]
                
                # Encontrar valores mais próximos da data
                idx_10y = rate_10y.index.get_indexer([date], method='nearest')[0]
                idx_2y = rate_2y.index.get_indexer([date], method='nearest')[0]
                
                if idx_10y >= 0 and idx_2y >= 0:
                    return rate_10y.iloc[idx_10y] - rate_2y.iloc[idx_2y]
        except:
            pass
        
        return 0.0
    
    def _calculate_slope_3m10y(self, treasury_rates: Dict[InterestRateType, pd.Series], date: datetime) -> float:
        """Calcular slope 3M-10Y"""
        try:
            if (InterestRateType.TREASURY_10Y in treasury_rates and 
                InterestRateType.TREASURY_3M in treasury_rates):
                
                rate_10y = treasury_rates[InterestRateType.TREASURY_10Y]
                rate_3m = treasury_rates[InterestRateType.TREASURY_3M]
                
                # Encontrar valores mais próximos da data
                idx_10y = rate_10y.index.get_indexer([date], method='nearest')[0]
                idx_3m = rate_3m.index.get_indexer([date], method='nearest')[0]
                
                if idx_10y >= 0 and idx_3m >= 0:
                    return rate_10y.iloc[idx_10y] - rate_3m.iloc[idx_3m]
        except:
            pass
        
        return 0.0
    
    def get_rate_summary(self) -> Dict[str, Dict[str, float]]:
        """Obter resumo das taxas de juros"""
        accessor = self.get_accessor()
        
        summary = {}
        
        # Fed Funds
        fed_stats = accessor.get_rate_statistics(InterestRateType.FED_FUNDS)
        summary['fed_funds'] = fed_stats
        
        # Selic
        selic_stats = accessor.get_rate_statistics(InterestRateType.SELIC)
        summary['selic'] = selic_stats
        
        # Treasury Rates principais
        for rate_type in [InterestRateType.TREASURY_3M, InterestRateType.TREASURY_2Y, InterestRateType.TREASURY_10Y]:
            try:
                stats = accessor.get_rate_statistics(rate_type)
                summary[rate_type.value] = stats
            except:
                continue
        
        return summary
    
    def get_current_rates(self) -> Dict[str, float]:
        """Obter taxas atuais"""
        accessor = self.get_accessor()
        
        rates = {
            'fed_funds': accessor.get_fed_funds_current(),
            'selic': accessor.get_selic_current()
        }
        
        # Treasury rates principais
        for rate_type in [InterestRateType.TREASURY_3M, InterestRateType.TREASURY_2Y, InterestRateType.TREASURY_10Y]:
            try:
                current_rate = accessor.get_treasury_rate(rate_type).iloc[-1]
                rates[rate_type.value] = current_rate
            except:
                continue
        
        return rates
