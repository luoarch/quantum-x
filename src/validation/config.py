"""
Configuração para validação científica
"""

import yaml
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ValidationConfig:
    """Configuração para validação científica"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "configs/validation.yaml"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carregar configuração do arquivo YAML"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                logger.info(f"Configuração carregada de {self.config_path}")
                return config
            else:
                logger.warning(f"Arquivo de configuração não encontrado: {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuração padrão"""
        return {
            "general": {
                "data_path": "data/raw/fed_selic_combined.csv",
                "output_dir": "reports/validation",
                "figures_dir": "figures",
                "registry_dir": "registry"
            },
            "simulation": {
                "n_simulations": 1000,
                "sample_sizes": [25, 50, 75, 100, 200, 500],
                "horizons": [1, 3, 6, 12],
                "significance_levels": [0.01, 0.05, 0.10],
                "tolerances": {
                    "size_test": 0.05,
                    "power_test": 0.10,
                    "small_sample": 0.08,
                    "heteroskedasticity": 0.05
                }
            },
            "promotion_criteria": {
                "min_coverage_80": 0.80,
                "min_coverage_95": 0.85,
                "max_ece": 0.10,
                "max_brier_score": 0.25,
                "max_crps": 0.30,
                "min_directional_accuracy": 0.60,
                "max_coefficient_instability": 0.20
            }
        }
    
    def load_from_file(self, config_path: str):
        """Carregar configuração de arquivo específico"""
        self.config_path = config_path
        self.config = self._load_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obter valor da configuração usando notação de ponto"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_simulation_config(self) -> Dict[str, Any]:
        """Obter configuração de simulação"""
        return self.config.get("simulation", {})
    
    def get_promotion_criteria(self) -> Dict[str, Any]:
        """Obter critérios de promoção"""
        return self.config.get("promotion_criteria", {})
    
    def get_test_config(self, test_name: str) -> Dict[str, Any]:
        """Obter configuração de teste específico"""
        return self.config.get("tests", {}).get(test_name, {})
    
    def get_tolerances(self) -> Dict[str, float]:
        """Obter tolerâncias dos testes"""
        return self.config.get("simulation", {}).get("tolerances", {})
    
    @property
    def data_path(self) -> str:
        """Caminho dos dados"""
        return self.get("general.data_path", "data/raw/fed_selic_combined.csv")
    
    @property
    def output_dir(self) -> str:
        """Diretório de saída"""
        return self.get("general.output_dir", "reports/validation")
    
    @property
    def figures_dir(self) -> str:
        """Diretório de figuras"""
        return self.get("general.figures_dir", "figures")
    
    @property
    def n_simulations(self) -> int:
        """Número de simulações"""
        return self.get("simulation.n_simulations", 1000)
    
    @property
    def sample_sizes(self) -> List[int]:
        """Tamanhos de amostra"""
        return self.get("simulation.sample_sizes", [25, 50, 75, 100, 200, 500])
    
    @property
    def horizons(self) -> List[int]:
        """Horizontes de previsão"""
        return self.get("simulation.horizons", [1, 3, 6, 12])
    
    @property
    def significance_levels(self) -> List[float]:
        """Níveis de significância"""
        return self.get("simulation.significance_levels", [0.01, 0.05, 0.10])
    
    @property
    def promotion_criteria(self) -> Dict[str, Any]:
        """Critérios de promoção"""
        return self.get_promotion_criteria()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter configuração para dicionário"""
        return self.config.copy()
    
    def save_to_file(self, file_path: str):
        """Salvar configuração em arquivo"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            logger.info(f"Configuração salva em {file_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
            raise
