"""
Data Repository - Single Responsibility Principle
Repositório para acesso a dados FED-Selic
"""

import pandas as pd
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
from fredapi import Fred
import requests
import logging

from src.core.interfaces import IDataRepository
from src.core.exceptions import DataRepositoryError, ExternalServiceError
from src.core.models import DataQuality

logger = logging.getLogger(__name__)

class FedDataRepository(IDataRepository):
    """
    Repositório para dados do Fed
    
    Responsabilidades:
    - Obter dados do Fed Funds Rate
    - Obter calendário de reuniões do FOMC
    - Processar dados históricos
    """
    
    def __init__(self, fred_api_key: str):
        self.fred = Fred(api_key=fred_api_key)
        self.fed_funds_rate_series = "FEDFUNDS"
        self.fomc_meetings_series = "FOMC"
    
    async def get_fed_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Obter dados do Fed Funds Rate"""
        try:
            # Obter dados do FRED
            fed_funds = self.fred.get_series(
                self.fed_funds_rate_series,
                start=start_date,
                end=end_date
            )
            
            if fed_funds.empty:
                raise DataRepositoryError("Nenhum dado do Fed encontrado")
            
            # Processar dados
            df = pd.DataFrame({
                'date': fed_funds.index,
                'fed_funds_rate': fed_funds.values,
                'fed_move_bps': self._calculate_moves(fed_funds.values)
            })
            
            # Validar qualidade
            quality = await self._assess_data_quality(df, "fed")
            if quality.overall_score < 0.7:
                logger.warning(f"Qualidade dos dados do Fed baixa: {quality.overall_score}")
            
            return df
            
        except Exception as e:
            raise DataRepositoryError(f"Erro ao obter dados do Fed: {str(e)}")
    
    async def get_selic_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Implementação vazia - delegada para SelicDataRepository"""
        raise NotImplementedError("Use SelicDataRepository para dados da Selic")
    
    async def get_copom_calendar(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Implementação vazia - delegada para SelicDataRepository"""
        raise NotImplementedError("Use SelicDataRepository para calendário do Copom")
    
    def _calculate_moves(self, rates: List[float]) -> List[float]:
        """Calcular movimentos em pontos-base"""
        moves = [0.0]  # Primeiro valor é 0
        for i in range(1, len(rates)):
            move_bps = (rates[i] - rates[i-1]) * 100  # Converter para bps
            moves.append(move_bps)
        return moves
    
    async def _assess_data_quality(self, data: pd.DataFrame, source: str) -> DataQuality:
        """Avaliar qualidade dos dados"""
        n_total = len(data)
        n_complete = data.dropna().shape[0]
        completeness = n_complete / n_total if n_total > 0 else 0
        
        # Verificar consistência (valores dentro de faixa esperada)
        if source == "fed":
            valid_range = (0, 20)  # Fed Funds Rate entre 0% e 20%
            valid_values = data['fed_funds_rate'].between(*valid_range).sum()
        else:
            valid_values = n_complete
        
        consistency = valid_values / n_total if n_total > 0 else 0
        
        # Verificar timeliness (dados recentes)
        latest_date = data['date'].max()
        days_old = (datetime.now() - latest_date).days
        timeliness = max(0, 1 - days_old / 30)  # Penalizar dados > 30 dias
        
        # Verificar accuracy (sem outliers extremos)
        if source == "fed":
            q1 = data['fed_funds_rate'].quantile(0.25)
            q3 = data['fed_funds_rate'].quantile(0.75)
            iqr = q3 - q1
            outliers = ((data['fed_funds_rate'] < q1 - 3*iqr) | 
                       (data['fed_funds_rate'] > q3 + 3*iqr)).sum()
            accuracy = 1 - outliers / n_total if n_total > 0 else 0
        else:
            accuracy = 1.0
        
        overall_score = (completeness + consistency + timeliness + accuracy) / 4
        
        issues = []
        if completeness < 0.9:
            issues.append("Dados incompletos")
        if consistency < 0.9:
            issues.append("Valores inconsistentes")
        if timeliness < 0.8:
            issues.append("Dados desatualizados")
        if accuracy < 0.9:
            issues.append("Possíveis outliers")
        
        return DataQuality(
            source=source,
            completeness=completeness,
            consistency=consistency,
            timeliness=timeliness,
            accuracy=accuracy,
            overall_score=overall_score,
            issues=issues
        )

class SelicDataRepository(IDataRepository):
    """
    Repositório para dados da Selic e Copom
    
    Responsabilidades:
    - Obter dados da Selic
    - Obter calendário do Copom
    - Processar dados históricos
    """
    
    def __init__(self, bcb_api_url: str = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados"):
        self.bcb_api_url = bcb_api_url
        self.selic_series_code = "11"  # Código da Selic no BCB
    
    async def get_fed_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Implementação vazia - delegada para FedDataRepository"""
        raise NotImplementedError("Use FedDataRepository para dados do Fed")
    
    async def get_selic_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Obter dados da Selic"""
        try:
            # Formatar datas para API do BCB
            start_str = start_date.strftime("%d/%m/%Y")
            end_str = end_date.strftime("%d/%m/%Y")
            
            # Fazer requisição para API do BCB
            params = {
                'formato': 'json',
                'dataInicial': start_str,
                'dataFinal': end_str
            }
            
            response = requests.get(self.bcb_api_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                raise DataRepositoryError("Nenhum dado da Selic encontrado")
            
            # Processar dados
            df = pd.DataFrame(data)
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
            df['selic_rate'] = pd.to_numeric(df['valor'])
            df['selic_move_bps'] = self._calculate_moves(df['selic_rate'].values)
            
            # Renomear colunas para consistência
            df = df.rename(columns={'data': 'date'})
            
            # Validar qualidade
            quality = await self._assess_data_quality(df, "selic")
            if quality.overall_score < 0.7:
                logger.warning(f"Qualidade dos dados da Selic baixa: {quality.overall_score}")
            
            return df[['date', 'selic_rate', 'selic_move_bps']]
            
        except requests.RequestException as e:
            raise ExternalServiceError(f"Erro na API do BCB: {str(e)}", service="bcb")
        except Exception as e:
            raise DataRepositoryError(f"Erro ao obter dados da Selic: {str(e)}")
    
    async def get_copom_calendar(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Obter calendário do Copom"""
        try:
            # Calendário do Copom é fixo (8 reuniões por ano)
            # Implementação simplificada - em produção, usar API oficial
            copom_dates = self._generate_copom_dates(start_date, end_date)
            
            df = pd.DataFrame({
                'date': copom_dates,
                'meeting_number': range(1, len(copom_dates) + 1),
                'is_meeting': True
            })
            
            return df
            
        except Exception as e:
            raise DataRepositoryError(f"Erro ao obter calendário do Copom: {str(e)}")
    
    def _calculate_moves(self, rates: List[float]) -> List[float]:
        """Calcular movimentos em pontos-base"""
        moves = [0.0]  # Primeiro valor é 0
        for i in range(1, len(rates)):
            move_bps = (rates[i] - rates[i-1]) * 100  # Converter para bps
            moves.append(move_bps)
        return moves
    
    def _generate_copom_dates(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Gerar datas das reuniões do Copom"""
        # Datas aproximadas das reuniões do Copom (terceira quarta-feira do mês)
        copom_dates = []
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            # Terceira quarta-feira do mês
            first_day = current_date.replace(day=1)
            first_wednesday = first_day + timedelta(days=(2 - first_day.weekday()) % 7)
            third_wednesday = first_wednesday + timedelta(weeks=2)
            
            if start_date <= third_wednesday <= end_date:
                copom_dates.append(third_wednesday)
            
            # Próximo mês
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return copom_dates
    
    async def _assess_data_quality(self, data: pd.DataFrame, source: str) -> DataQuality:
        """Avaliar qualidade dos dados"""
        n_total = len(data)
        n_complete = data.dropna().shape[0]
        completeness = n_complete / n_total if n_total > 0 else 0
        
        # Verificar consistência (valores dentro de faixa esperada)
        if source == "selic":
            valid_range = (0, 50)  # Selic entre 0% e 50%
            valid_values = data['selic_rate'].between(*valid_range).sum()
        else:
            valid_values = n_complete
        
        consistency = valid_values / n_total if n_total > 0 else 0
        
        # Verificar timeliness
        latest_date = data['date'].max()
        days_old = (datetime.now() - latest_date).days
        timeliness = max(0, 1 - days_old / 7)  # Penalizar dados > 7 dias
        
        # Verificar accuracy
        if source == "selic":
            q1 = data['selic_rate'].quantile(0.25)
            q3 = data['selic_rate'].quantile(0.75)
            iqr = q3 - q1
            outliers = ((data['selic_rate'] < q1 - 3*iqr) | 
                       (data['selic_rate'] > q3 + 3*iqr)).sum()
            accuracy = 1 - outliers / n_total if n_total > 0 else 0
        else:
            accuracy = 1.0
        
        overall_score = (completeness + consistency + timeliness + accuracy) / 4
        
        issues = []
        if completeness < 0.9:
            issues.append("Dados incompletos")
        if consistency < 0.9:
            issues.append("Valores inconsistentes")
        if timeliness < 0.8:
            issues.append("Dados desatualizados")
        if accuracy < 0.9:
            issues.append("Possíveis outliers")
        
        return DataQuality(
            source=source,
            completeness=completeness,
            consistency=consistency,
            timeliness=timeliness,
            accuracy=accuracy,
            overall_score=overall_score,
            issues=issues
        )

class CompositeDataRepository(IDataRepository):
    """
    Repositório composto que combina Fed e Selic
    
    Composite Pattern - combina múltiplos repositórios
    """
    
    def __init__(self, fed_repo: FedDataRepository, selic_repo: SelicDataRepository):
        self.fed_repo = fed_repo
        self.selic_repo = selic_repo
    
    async def get_fed_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Delegar para FedDataRepository"""
        return await self.fed_repo.get_fed_data(start_date, end_date)
    
    async def get_selic_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Delegar para SelicDataRepository"""
        return await self.selic_repo.get_selic_data(start_date, end_date)
    
    async def get_copom_calendar(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Delegar para SelicDataRepository"""
        return await self.selic_repo.get_copom_calendar(start_date, end_date)
    
    async def get_aligned_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Obter dados alinhados Fed-Selic"""
        try:
            # Obter dados de ambos os repositórios
            fed_data = await self.get_fed_data(start_date, end_date)
            selic_data = await self.get_selic_data(start_date, end_date)
            copom_calendar = await self.get_copom_calendar(start_date, end_date)
            
            # Alinhar por data
            aligned_data = pd.merge(
                fed_data, selic_data, on='date', how='inner'
            )
            
            # Adicionar informações do Copom
            aligned_data = pd.merge(
                aligned_data, copom_calendar, on='date', how='left'
            )
            aligned_data['is_meeting'] = aligned_data['is_meeting'].fillna(False)
            
            return aligned_data
            
        except Exception as e:
            raise DataRepositoryError(f"Erro ao alinhar dados: {str(e)}")
