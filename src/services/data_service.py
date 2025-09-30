"""
Serviço de dados
"""

import logging
import pandas as pd
from typing import Dict, Any, Optional
import os

from ..core.config import get_settings
from .interest_rate_service import InterestRateService
from .selic_service import SelicService

logger = logging.getLogger(__name__)

class DataService:
    """Serviço para gerenciamento de dados"""
    
    def __init__(self):
        self.settings = get_settings()
        self.interest_rate_service = InterestRateService()
        self.selic_service = SelicService()
    
    async def get_prediction_data(self) -> pd.DataFrame:
        """Obter dados para previsão"""
        try:
            # Carregar dados combinados
            combined_data = self.selic_service._load_combined_data()
            
            # Preparar dados para previsão
            prediction_data = self._prepare_prediction_data(combined_data)
            
            return prediction_data
            
        except Exception as e:
            logger.error(f"Erro ao obter dados de previsão: {str(e)}", exc_info=True)
            raise
    
    def _prepare_prediction_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preparar dados para previsão"""
        try:
            # Garantir que temos as colunas necessárias
            required_columns = ['fed_rate', 'selic']
            for col in required_columns:
                if col not in data.columns:
                    raise ValueError(f"Coluna {col} não encontrada nos dados")
            
            # Criar variáveis derivadas
            prediction_data = data.copy()
            
            # Mudanças mensais
            prediction_data['fed_change'] = prediction_data['fed_rate'].diff()
            prediction_data['selic_change'] = prediction_data['selic'].diff()
            
            # Spillover
            prediction_data['spillover'] = prediction_data['fed_rate'] - prediction_data['selic']
            prediction_data['spillover_change'] = prediction_data['spillover'].diff()
            
            # Remover NaNs
            prediction_data = prediction_data.dropna()
            
            logger.info(f"Dados preparados: {len(prediction_data)} observações")
            
            return prediction_data
            
        except Exception as e:
            logger.error(f"Erro ao preparar dados: {str(e)}", exc_info=True)
            raise
    
    async def get_data_summary(self) -> Dict[str, Any]:
        """Obter resumo dos dados"""
        try:
            # Carregar dados
            fed_data = self.interest_rate_service.load_all_interest_rate_data()
            selic_data = self.selic_service.load_data()
            
            summary = {
                "fed_data": {
                    "observations": len(fed_data.fed_rates) if fed_data else 0,
                    "start_date": fed_data.start_date.isoformat() if fed_data else None,
                    "end_date": fed_data.end_date.isoformat() if fed_data else None,
                    "columns": len(fed_data.fed_rates[0].__dict__) if fed_data and fed_data.fed_rates else 0
                },
                "selic_data": {
                    "observations": len(selic_data.selic) if selic_data else 0,
                    "start_date": selic_data.selic.index[0].isoformat() if selic_data and not selic_data.selic.empty else None,
                    "end_date": selic_data.selic.index[-1].isoformat() if selic_data and not selic_data.selic.empty else None,
                    "has_ipca": selic_data.ipca is not None
                },
                "combined_data": {
                    "observations": 0,
                    "start_date": None,
                    "end_date": None
                }
            }
            
            # Dados combinados
            try:
                combined_data = self.selic_service._load_combined_data()
                summary["combined_data"] = {
                    "observations": len(combined_data),
                    "start_date": combined_data.index[0].isoformat() if not combined_data.empty else None,
                    "end_date": combined_data.index[-1].isoformat() if not combined_data.empty else None
                }
            except Exception as e:
                logger.warning(f"Erro ao carregar dados combinados: {e}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo dos dados: {str(e)}", exc_info=True)
            raise
    
    async def validate_data_quality(self) -> Dict[str, Any]:
        """Validar qualidade dos dados"""
        try:
            issues = []
            warnings = []
            
            # Carregar dados
            combined_data = self.selic_service._load_combined_data()
            
            # Verificar completude
            missing_data = combined_data.isnull().sum()
            for col, missing_count in missing_data.items():
                if missing_count > 0:
                    issues.append(f"Coluna {col} tem {missing_count} valores ausentes")
            
            # Verificar consistência temporal
            if len(combined_data) < 10:
                warnings.append("Poucos dados disponíveis para análise confiável")
            
            # Verificar range de valores
            if 'selic' in combined_data.columns:
                selic_min = combined_data['selic'].min()
                selic_max = combined_data['selic'].max()
                if selic_min < 0 or selic_max > 50:
                    warnings.append(f"Valores de Selic fora do range esperado: {selic_min:.2f} - {selic_max:.2f}")
            
            if 'fed_rate' in combined_data.columns:
                fed_min = combined_data['fed_rate'].min()
                fed_max = combined_data['fed_rate'].max()
                if fed_min < 0 or fed_max > 25:
                    warnings.append(f"Valores de Fed Funds fora do range esperado: {fed_min:.2f} - {fed_max:.2f}")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "data_points": len(combined_data),
                "columns": list(combined_data.columns)
            }
            
        except Exception as e:
            logger.error(f"Erro na validação de dados: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "issues": [f"Erro ao validar dados: {str(e)}"],
                "warnings": [],
                "data_points": 0,
                "columns": []
            }
    
    async def get_data_metadata(self) -> Dict[str, Any]:
        """Obter metadados dos dados"""
        try:
            combined_data = self.selic_service._load_combined_data()
            
            metadata = {
                "sources": {
                    "fed": "FRED API",
                    "selic": "BCB API + Historical"
                },
                "frequency": "monthly",
                "last_updated": combined_data.index[-1].isoformat() if not combined_data.empty else None,
                "columns": {
                    col: {
                        "type": str(combined_data[col].dtype),
                        "non_null_count": int(combined_data[col].count()),
                        "null_count": int(combined_data[col].isnull().sum())
                    }
                    for col in combined_data.columns
                },
                "statistics": {
                    "fed_rate": {
                        "mean": float(combined_data['fed_rate'].mean()) if 'fed_rate' in combined_data.columns else None,
                        "std": float(combined_data['fed_rate'].std()) if 'fed_rate' in combined_data.columns else None,
                        "min": float(combined_data['fed_rate'].min()) if 'fed_rate' in combined_data.columns else None,
                        "max": float(combined_data['fed_rate'].max()) if 'fed_rate' in combined_data.columns else None
                    },
                    "selic": {
                        "mean": float(combined_data['selic'].mean()) if 'selic' in combined_data.columns else None,
                        "std": float(combined_data['selic'].std()) if 'selic' in combined_data.columns else None,
                        "min": float(combined_data['selic'].min()) if 'selic' in combined_data.columns else None,
                        "max": float(combined_data['selic'].max()) if 'selic' in combined_data.columns else None
                    }
                }
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Erro ao obter metadados dos dados: {str(e)}", exc_info=True)
            raise
