"""
Testes de propriedades de size e poder para validação científica
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import logging
from datetime import datetime

try:
    from statsmodels.tsa.stattools import adfuller, kpss
    from arch.unitroot import DFGLS
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

logger = logging.getLogger(__name__)

class SizePowerTester:
    """Testador de propriedades de size e poder"""
    
    def __init__(self, config):
        self.config = config
        self.sample_sizes = config.sample_sizes
        self.alternatives = config.get("tests.size_power.alternatives", [0.95, 0.90, 0.80, 0.70, 0.50])
        self.n_simulations = config.n_simulations
        self.significance_levels = config.significance_levels
        self.tolerances = config.get_tolerances()
    
    def test_size_properties(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Testar propriedades de size dos testes de raiz unitária"""
        logger.info("🔬 Testando propriedades de size...")
        
        if not STATSMODELS_AVAILABLE:
            return {"error": "statsmodels não disponível", "status": "skipped"}
        
        if seed is not None:
            np.random.seed(seed)
        
        results = {
            "test_type": "size_properties",
            "timestamp": datetime.utcnow().isoformat(),
            "seed": seed,
            "n_simulations": self.n_simulations,
            "sample_sizes": self.sample_sizes,
            "significance_levels": self.significance_levels,
            "size_results": [],
            "summary": {}
        }
        
        # Testar cada tamanho de amostra
        for T in self.sample_sizes:
            logger.info(f"  Testando T = {T}")
            
            size_result = self._test_size_for_sample_size(T, seed)
            results["size_results"].append(size_result)
        
        # Calcular resumo
        results["summary"] = self._calculate_size_summary(results["size_results"])
        
        logger.info(f"✅ Teste de size concluído: {results['summary']['passed']}/{results['summary']['total']} aprovados")
        
        return results
    
    def test_power_properties(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Testar propriedades de poder dos testes de raiz unitária"""
        logger.info("🔬 Testando propriedades de poder...")
        
        if not STATSMODELS_AVAILABLE:
            return {"error": "statsmodels não disponível", "status": "skipped"}
        
        if seed is not None:
            np.random.seed(seed)
        
        results = {
            "test_type": "power_properties",
            "timestamp": datetime.utcnow().isoformat(),
            "seed": seed,
            "n_simulations": self.n_simulations,
            "alternatives": self.alternatives,
            "sample_sizes": self.sample_sizes,
            "power_results": [],
            "summary": {}
        }
        
        # Testar cada alternativa
        for phi in self.alternatives:
            logger.info(f"  Testando φ = {phi}")
            
            power_result = self._test_power_for_alternative(phi, seed)
            results["power_results"].append(power_result)
        
        # Calcular resumo
        results["summary"] = self._calculate_power_summary(results["power_results"])
        
        logger.info(f"✅ Teste de poder concluído: {results['summary']['passed']}/{results['summary']['total']} aprovados")
        
        return results
    
    def _test_size_for_sample_size(self, T: int, seed: Optional[int] = None) -> Dict[str, Any]:
        """Testar size para um tamanho de amostra específico"""
        if seed is not None:
            np.random.seed(seed + T)  # Seed diferente para cada T
        
        # Gerar séries I(1) (raiz unitária)
        series_list = []
        for _ in range(self.n_simulations):
            # AR(1) com φ = 1 (raiz unitária)
            series = self._generate_unit_root_series(T)
            series_list.append(series)
        
        # Aplicar testes
        adf_rejections = []
        kpss_rejections = []
        dfgls_rejections = []
        
        for series in series_list:
            # ADF
            try:
                adf_stat, adf_pvalue, _, _, adf_critical, _ = adfuller(series, regression='c')
                adf_rejections.append(adf_pvalue < 0.05)
            except:
                adf_rejections.append(False)
            
            # KPSS
            try:
                kpss_stat, kpss_pvalue, _, kpss_critical = kpss(series, regression='c')
                kpss_rejections.append(kpss_pvalue < 0.05)
            except:
                kpss_rejections.append(False)
            
            # DF-GLS
            try:
                dfgls_result = DFGLS(series, lags=4, trend='c')
                dfgls_rejections.append(dfgls_result.pvalue < 0.05)
            except:
                dfgls_rejections.append(False)
        
        # Calcular taxas de rejeição (size)
        adf_size = np.mean(adf_rejections)
        kpss_size = np.mean(kpss_rejections)
        dfgls_size = np.mean(dfgls_rejections)
        
        # Verificar se está dentro da tolerância
        tolerance = self.tolerances.get("size_test", 0.05)
        adf_passed = abs(adf_size - 0.05) <= tolerance
        kpss_passed = abs(kpss_size - 0.05) <= tolerance
        dfgls_passed = abs(dfgls_size - 0.05) <= tolerance
        
        overall_passed = adf_passed and kpss_passed and dfgls_passed
        
        return {
            "T": T,
            "adf_size": adf_size,
            "kpss_size": kpss_size,
            "dfgls_size": dfgls_size,
            "adf_passed": adf_passed,
            "kpss_passed": kpss_passed,
            "dfgls_passed": dfgls_passed,
            "passed": overall_passed,
            "tolerance": tolerance
        }
    
    def _test_power_for_alternative(self, phi: float, seed: Optional[int] = None) -> Dict[str, Any]:
        """Testar poder para uma alternativa específica"""
        if seed is not None:
            np.random.seed(seed + int(phi * 100))  # Seed diferente para cada φ
        
        # Testar em diferentes tamanhos de amostra
        power_by_T = {}
        
        for T in self.sample_sizes:
            # Gerar séries estacionárias (φ < 1)
            series_list = []
            for _ in range(self.n_simulations):
                series = self._generate_stationary_series(T, phi)
                series_list.append(series)
            
            # Aplicar testes
            adf_rejections = []
            kpss_rejections = []
            dfgls_rejections = []
            
            for series in series_list:
                # ADF
                try:
                    adf_stat, adf_pvalue, _, _, adf_critical, _ = adfuller(series, regression='c')
                    adf_rejections.append(adf_pvalue < 0.05)
                except:
                    adf_rejections.append(False)
                
                # KPSS
                try:
                    kpss_stat, kpss_pvalue, _, kpss_critical = kpss(series, regression='c')
                    kpss_rejections.append(kpss_pvalue < 0.05)
                except:
                    kpss_rejections.append(False)
                
                # DF-GLS
                try:
                    dfgls_result = DFGLS(series, lags=4, trend='c')
                    dfgls_rejections.append(dfgls_result.pvalue < 0.05)
                except:
                    dfgls_rejections.append(False)
            
            # Calcular poder
            adf_power = np.mean(adf_rejections)
            kpss_power = np.mean(kpss_rejections)
            dfgls_power = np.mean(dfgls_rejections)
            
            power_by_T[T] = {
                "adf_power": adf_power,
                "kpss_power": kpss_power,
                "dfgls_power": dfgls_power
            }
        
        # Calcular poder médio
        adf_power_avg = np.mean([p["adf_power"] for p in power_by_T.values()])
        kpss_power_avg = np.mean([p["kpss_power"] for p in power_by_T.values()])
        dfgls_power_avg = np.mean([p["dfgls_power"] for p in power_by_T.values()])
        
        # Determinar melhor teste
        powers = {"ADF": adf_power_avg, "KPSS": kpss_power_avg, "DF-GLS": dfgls_power_avg}
        best_test = max(powers, key=powers.get)
        
        # Verificar se DF-GLS é superior (conforme literatura)
        dfgls_superior = dfgls_power_avg > adf_power_avg
        
        return {
            "alternative": phi,
            "adf_power": adf_power_avg,
            "kpss_power": kpss_power_avg,
            "dfgls_power": dfgls_power_avg,
            "best_test": best_test,
            "dfgls_superior": dfgls_superior,
            "passed": dfgls_superior,
            "power_by_T": power_by_T
        }
    
    def _generate_unit_root_series(self, T: int) -> np.ndarray:
        """Gerar série com raiz unitária (I(1))"""
        # AR(1) com φ = 1
        series = np.zeros(T)
        series[0] = np.random.normal(0, 1)
        
        for t in range(1, T):
            series[t] = series[t-1] + np.random.normal(0, 1)
        
        return series
    
    def _generate_stationary_series(self, T: int, phi: float) -> np.ndarray:
        """Gerar série estacionária AR(1)"""
        series = np.zeros(T)
        series[0] = np.random.normal(0, 1)
        
        for t in range(1, T):
            series[t] = phi * series[t-1] + np.random.normal(0, 1)
        
        return series
    
    def _calculate_size_summary(self, size_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcular resumo dos resultados de size"""
        total_tests = len(size_results)
        passed_tests = sum(1 for r in size_results if r["passed"])
        
        # Calcular estatísticas por teste
        adf_sizes = [r["adf_size"] for r in size_results]
        kpss_sizes = [r["kpss_size"] for r in size_results]
        dfgls_sizes = [r["dfgls_size"] for r in size_results]
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "adf_size_mean": np.mean(adf_sizes),
            "kpss_size_mean": np.mean(kpss_sizes),
            "dfgls_size_mean": np.mean(dfgls_sizes),
            "overall_status": "passed" if passed_tests == total_tests else "partial" if passed_tests > 0 else "failed"
        }
    
    def _calculate_power_summary(self, power_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcular resumo dos resultados de poder"""
        total_tests = len(power_results)
        passed_tests = sum(1 for r in power_results if r["passed"])
        
        # Calcular estatísticas por teste
        adf_powers = [r["adf_power"] for r in power_results]
        kpss_powers = [r["kpss_power"] for r in power_results]
        dfgls_powers = [r["dfgls_power"] for r in power_results]
        
        # Verificar se DF-GLS é consistentemente superior
        dfgls_superior_count = sum(1 for r in power_results if r["dfgls_superior"])
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "adf_power_mean": np.mean(adf_powers),
            "kpss_power_mean": np.mean(kpss_powers),
            "dfgls_power_mean": np.mean(dfgls_powers),
            "dfgls_superior_count": dfgls_superior_count,
            "dfgls_superior_rate": dfgls_superior_count / total_tests if total_tests > 0 else 0,
            "overall_status": "passed" if passed_tests == total_tests else "partial" if passed_tests > 0 else "failed"
        }
