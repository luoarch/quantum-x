"""
Stationarity Service - Single Responsibility Principle
Serviço responsável por testes de estacionariedade
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from src.core.interfaces import IStationarityService
from src.core.exceptions import StationarityTestError
from src.core.models import StationarityTestResult, StructuralBreakResult

class StationarityService(IStationarityService):
    """
    Serviço de testes de estacionariedade
    
    Responsabilidades:
    - Testar estacionariedade de séries
    - Detectar quebras estruturais
    - Aplicar transformações necessárias
    """
    
    def __init__(self, 
                 significance_level: float = 0.05,
                 max_lags: int = 4):
        self.significance_level = significance_level
        self.max_lags = max_lags
    
    async def test_stationarity(self, series: pd.Series) -> Dict[str, Any]:
        """Testar estacionariedade da série"""
        try:
            # Verificar se a série tem dados suficientes
            if len(series) < 10:
                raise StationarityTestError(
                    "Série muito curta para teste de estacionariedade",
                    series_name=series.name or "unknown"
                )
            
            # Remover valores NaN
            clean_series = series.dropna()
            if len(clean_series) < 10:
                raise StationarityTestError(
                    "Série insuficiente após limpeza",
                    series_name=series.name or "unknown"
                )
            
            # Executar testes
            adf_result = self._adf_test(clean_series)
            kpss_result = self._kpss_test(clean_series)
            dfgls_result = self._dfgls_test(clean_series)
            pp_result = self._pp_test(clean_series)
            
            # Determinar estacionariedade
            is_stationary = self._determine_stationarity(
                adf_result, kpss_result, dfgls_result, pp_result
            )
            
            # Gerar recomendações
            recommendations = self._generate_recommendations(
                is_stationary, adf_result, kpss_result, dfgls_result, pp_result
            )
            
            return {
                "series_name": series.name or "unknown",
                "is_stationary": is_stationary,
                "adf_pvalue": adf_result["pvalue"],
                "kpss_pvalue": kpss_result["pvalue"],
                "dfgls_pvalue": dfgls_result.get("pvalue"),
                "pp_pvalue": pp_result.get("pvalue"),
                "confidence_level": self.significance_level,
                "methodology": "Elliott et al. (1996)",
                "recommendations": recommendations,
                "tested_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise StationarityTestError(f"Erro no teste de estacionariedade: {str(e)}")
    
    async def detect_structural_breaks(self, series: pd.Series) -> Dict[str, Any]:
        """Detectar quebras estruturais"""
        try:
            # Verificar se a série tem dados suficientes
            if len(series) < 20:
                return {
                    "series_name": series.name or "unknown",
                    "has_breaks": False,
                    "break_dates": [],
                    "break_probabilities": [],
                    "methodology": "Zivot-Andrews",
                    "confidence_level": self.significance_level,
                    "message": "Série muito curta para detecção de quebras"
                }
            
            # Remover valores NaN
            clean_series = series.dropna()
            
            # Teste Zivot-Andrews (quebra única)
            za_result = self._zivot_andrews_test(clean_series)
            
            # Determinar se há quebras
            has_breaks = za_result["pvalue"] < self.significance_level
            break_dates = [za_result["break_date"]] if has_breaks else []
            break_probabilities = [1 - za_result["pvalue"]] if has_breaks else []
            
            return {
                "series_name": series.name or "unknown",
                "has_breaks": has_breaks,
                "break_dates": break_dates,
                "break_probabilities": break_probabilities,
                "methodology": "Zivot-Andrews",
                "confidence_level": self.significance_level,
                "tested_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise StationarityTestError(f"Erro na detecção de quebras: {str(e)}")
    
    def _adf_test(self, series: pd.Series) -> Dict[str, Any]:
        """Teste ADF (Augmented Dickey-Fuller)"""
        try:
            from statsmodels.tsa.stattools import adfuller
            
            result = adfuller(series, maxlag=self.max_lags, autolag='AIC')
            
            return {
                "statistic": result[0],
                "pvalue": result[1],
                "critical_values": result[4],
                "test_type": "ADF"
            }
        except ImportError:
            return {"pvalue": 0.5, "test_type": "ADF", "error": "statsmodels não disponível"}
        except Exception:
            return {"pvalue": 0.5, "test_type": "ADF", "error": "Erro no teste ADF"}
    
    def _kpss_test(self, series: pd.Series) -> Dict[str, Any]:
        """Teste KPSS (Kwiatkowski-Phillips-Schmidt-Shin)"""
        try:
            from statsmodels.tsa.stattools import kpss
            
            result = kpss(series, regression='c', nlags=self.max_lags)
            
            return {
                "statistic": result[0],
                "pvalue": result[1],
                "critical_values": result[3],
                "test_type": "KPSS"
            }
        except ImportError:
            return {"pvalue": 0.5, "test_type": "KPSS", "error": "statsmodels não disponível"}
        except Exception:
            return {"pvalue": 0.5, "test_type": "KPSS", "error": "Erro no teste KPSS"}
    
    def _dfgls_test(self, series: pd.Series) -> Dict[str, Any]:
        """Teste DF-GLS (Elliott-Rothenberg-Stock)"""
        try:
            from arch.unitroot import DFGLS
            
            result = DFGLS(series, lags=self.max_lags, trend='c')
            
            return {
                "statistic": result.stat,
                "pvalue": result.pvalue,
                "critical_values": result.critical_values,
                "test_type": "DF-GLS"
            }
        except ImportError:
            return {"pvalue": 0.5, "test_type": "DF-GLS", "error": "arch não disponível"}
        except Exception:
            return {"pvalue": 0.5, "test_type": "DF-GLS", "error": "Erro no teste DF-GLS"}
    
    def _pp_test(self, series: pd.Series) -> Dict[str, Any]:
        """Teste Phillips-Perron"""
        try:
            from statsmodels.tsa.stattools import PhillipsPerron
            
            result = PhillipsPerron(series, lags=self.max_lags, trend='c')
            
            return {
                "statistic": result.stat,
                "pvalue": result.pvalue,
                "critical_values": result.critical_values,
                "test_type": "Phillips-Perron"
            }
        except ImportError:
            return {"pvalue": 0.5, "test_type": "Phillips-Perron", "error": "statsmodels não disponível"}
        except Exception:
            return {"pvalue": 0.5, "test_type": "Phillips-Perron", "error": "Erro no teste PP"}
    
    def _zivot_andrews_test(self, series: pd.Series) -> Dict[str, Any]:
        """Teste Zivot-Andrews para quebras estruturais"""
        try:
            from arch.unitroot import ZivotAndrews
            
            result = ZivotAndrews(series, lags=self.max_lags, trend='c')
            
            return {
                "statistic": result.stat,
                "pvalue": result.pvalue,
                "break_date": result.break_date,
                "test_type": "Zivot-Andrews"
            }
        except ImportError:
            return {"pvalue": 0.5, "break_date": None, "test_type": "Zivot-Andrews", "error": "arch não disponível"}
        except Exception:
            return {"pvalue": 0.5, "break_date": None, "test_type": "Zivot-Andrews", "error": "Erro no teste ZA"}
    
    def _determine_stationarity(self, adf_result, kpss_result, dfgls_result, pp_result) -> bool:
        """Determinar estacionariedade baseado nos testes"""
        # Lógica baseada em Elliott et al. (1996)
        adf_rejects = adf_result["pvalue"] < self.significance_level
        kpss_rejects = kpss_result["pvalue"] < self.significance_level
        
        # Se ADF rejeita H0 (não há raiz unitária) E KPSS não rejeita H0 (é estacionária)
        if adf_rejects and not kpss_rejects:
            return True
        
        # Se ADF não rejeita H0 (há raiz unitária) E KPSS rejeita H0 (não é estacionária)
        if not adf_rejects and kpss_rejects:
            return False
        
        # Casos ambíguos - usar DF-GLS se disponível
        if "pvalue" in dfgls_result and dfgls_result["pvalue"] is not None:
            return dfgls_result["pvalue"] < self.significance_level
        
        # Fallback para ADF
        return adf_rejects
    
    def _generate_recommendations(self, is_stationary, adf_result, kpss_result, dfgls_result, pp_result) -> list:
        """Gerar recomendações baseadas nos resultados"""
        recommendations = []
        
        if is_stationary:
            recommendations.append("Série é estacionária - pode ser usada diretamente")
        else:
            recommendations.append("Série não é estacionária - considere diferenciação")
            
            if adf_result["pvalue"] > 0.1:
                recommendations.append("ADF sugere forte evidência de raiz unitária")
            
            if kpss_result["pvalue"] < 0.01:
                recommendations.append("KPSS sugere forte evidência de não-estacionariedade")
        
        # Recomendações específicas por teste
        if "error" in adf_result:
            recommendations.append("ADF não disponível - instale statsmodels")
        
        if "error" in dfgls_result:
            recommendations.append("DF-GLS não disponível - instale arch")
        
        return recommendations
