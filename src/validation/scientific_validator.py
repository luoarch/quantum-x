"""
Validador científico para modelo FED-Selic
Implementa testes de validação científica rigorosos
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime
import warnings

# Suprimir warnings de convergência
warnings.filterwarnings('ignore', category=RuntimeWarning)

try:
    from statsmodels.tsa.stattools import adfuller, kpss
    from statsmodels.tsa.arima.model import ARIMA
    from arch.unitroot import DFGLS, ZivotAndrews
    from sklearn.metrics import brier_score_loss
    from scipy import stats
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.warning("statsmodels não disponível - alguns testes serão limitados")

from .config import ValidationConfig
from .tests.size_power import SizePowerTester
from .tests.heteroskedasticity import HeteroskedasticityTester
from .tests.structural_breaks import StructuralBreaksTester
from .tests.small_samples import SmallSamplesTester
from .tests.benchmarks_np import NelsonPlosserBenchmarks
from .tests.lag_selection import LagSelectionTester

logger = logging.getLogger(__name__)

class ScientificValidator:
    """Validador científico principal"""
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self.results = {}
        
        # Inicializar testers
        self.size_power_tester = SizePowerTester(self.config)
        self.hetero_tester = HeteroskedasticityTester(self.config)
        self.breaks_tester = StructuralBreaksTester(self.config)
        self.small_samples_tester = SmallSamplesTester(self.config)
        self.benchmarks_tester = NelsonPlosserBenchmarks(self.config)
        self.lag_tester = LagSelectionTester(self.config)
    
    def test_size_properties(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Testar propriedades de size dos testes de raiz unitária"""
        logger.info("🔬 Testando propriedades de size...")
        
        if not STATSMODELS_AVAILABLE:
            return {"error": "statsmodels não disponível", "status": "skipped"}
        
        try:
            results = self.size_power_tester.test_size_properties(seed=seed)
            self.results["size_properties"] = results
            return results
        except Exception as e:
            logger.error(f"Erro no teste de size: {e}")
            return {"error": str(e), "status": "failed"}
    
    def test_power_properties(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Testar propriedades de poder dos testes de raiz unitária"""
        logger.info("🔬 Testando propriedades de poder...")
        
        if not STATSMODELS_AVAILABLE:
            return {"error": "statsmodels não disponível", "status": "skipped"}
        
        try:
            results = self.size_power_tester.test_power_properties(seed=seed)
            self.results["power_properties"] = results
            return results
        except Exception as e:
            logger.error(f"Erro no teste de poder: {e}")
            return {"error": str(e), "status": "failed"}
    
    def test_heteroskedasticity(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Testar robustez à heterocedasticidade"""
        logger.info("🔬 Testando robustez à heterocedasticidade...")
        
        if not STATSMODELS_AVAILABLE:
            return {"error": "statsmodels não disponível", "status": "skipped"}
        
        try:
            results = self.hetero_tester.test_heteroskedasticity_robustness(seed=seed)
            self.results["heteroskedasticity"] = results
            return results
        except Exception as e:
            logger.error(f"Erro no teste de heterocedasticidade: {e}")
            return {"error": str(e), "status": "failed"}
    
    def test_structural_breaks(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Testar detecção de quebras estruturais"""
        logger.info("🔬 Testando detecção de quebras estruturais...")
        
        if not STATSMODELS_AVAILABLE:
            return {"error": "statsmodels não disponível", "status": "skipped"}
        
        try:
            results = self.breaks_tester.test_structural_breaks_detection(seed=seed)
            self.results["structural_breaks"] = results
            return results
        except Exception as e:
            logger.error(f"Erro no teste de quebras estruturais: {e}")
            return {"error": str(e), "status": "failed"}
    
    def test_small_samples(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Testar propriedades com amostras pequenas"""
        logger.info("🔬 Testando propriedades com amostras pequenas...")
        
        if not STATSMODELS_AVAILABLE:
            return {"error": "statsmodels não disponível", "status": "skipped"}
        
        try:
            results = self.small_samples_tester.test_small_sample_properties(seed=seed)
            self.results["small_samples"] = results
            return results
        except Exception as e:
            logger.error(f"Erro no teste de amostras pequenas: {e}")
            return {"error": str(e), "status": "failed"}
    
    def test_nelson_plosser_benchmarks(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Testar benchmarks Nelson-Plosser"""
        logger.info("🔬 Testando benchmarks Nelson-Plosser...")
        
        if not STATSMODELS_AVAILABLE:
            return {"error": "statsmodels não disponível", "status": "skipped"}
        
        try:
            results = self.benchmarks_tester.test_nelson_plosser_series(seed=seed)
            self.results["nelson_plosser"] = results
            return results
        except Exception as e:
            logger.error(f"Erro no teste Nelson-Plosser: {e}")
            return {"error": str(e), "status": "failed"}
    
    def test_lag_selection(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Testar seleção de lags"""
        logger.info("🔬 Testando seleção de lags...")
        
        if not STATSMODELS_AVAILABLE:
            return {"error": "statsmodels não disponível", "status": "skipped"}
        
        try:
            results = self.lag_tester.test_lag_selection_criteria(seed=seed)
            self.results["lag_selection"] = results
            return results
        except Exception as e:
            logger.error(f"Erro no teste de seleção de lags: {e}")
            return {"error": str(e), "status": "failed"}
    
    def run_all_tests(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Executar todos os testes de validação"""
        logger.info("🔬 Executando todos os testes de validação científica...")
        
        all_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "seed": seed,
            "tests": {}
        }
        
        # Executar todos os testes
        test_functions = [
            ("size_properties", self.test_size_properties),
            ("power_properties", self.test_power_properties),
            ("heteroskedasticity", self.test_heteroskedasticity),
            ("structural_breaks", self.test_structural_breaks),
            ("small_samples", self.test_small_samples),
            ("nelson_plosser", self.test_nelson_plosser_benchmarks),
            ("lag_selection", self.test_lag_selection)
        ]
        
        for test_name, test_func in test_functions:
            logger.info(f"Executando {test_name}...")
            try:
                result = test_func(seed=seed)
                all_results["tests"][test_name] = result
                
                # Verificar se teste passou
                if "error" in result:
                    logger.warning(f"⚠️ {test_name} falhou: {result['error']}")
                else:
                    logger.info(f"✅ {test_name} concluído")
                    
            except Exception as e:
                logger.error(f"❌ {test_name} falhou com exceção: {e}")
                all_results["tests"][test_name] = {
                    "error": str(e),
                    "status": "failed"
                }
        
        # Calcular métricas agregadas
        all_results["summary"] = self._calculate_summary_metrics(all_results["tests"])
        
        return all_results
    
    def _calculate_summary_metrics(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular métricas resumo de todos os testes"""
        summary = {
            "total_tests": len(test_results),
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "overall_status": "unknown"
        }
        
        for test_name, result in test_results.items():
            if "error" in result:
                if result.get("status") == "skipped":
                    summary["skipped_tests"] += 1
                else:
                    summary["failed_tests"] += 1
            else:
                summary["passed_tests"] += 1
        
        # Determinar status geral
        if summary["failed_tests"] == 0:
            summary["overall_status"] = "passed"
        elif summary["passed_tests"] > 0:
            summary["overall_status"] = "partial"
        else:
            summary["overall_status"] = "failed"
        
        return summary
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Obter resumo da validação"""
        if not self.results:
            return {"message": "Nenhuma validação executada ainda"}
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_tests": len(self.results),
            "results": self.results
        }
        
        return summary
