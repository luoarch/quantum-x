"""
Interfaces e Abstrações para Análise de Regimes
Implementa princípios SOLID para análise científica de regimes econômicos
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from dataclasses import dataclass
from enum import Enum


class RegimeType(Enum):
    """Tipos de regimes econômicos"""
    RECESSION = "recession"
    RECOVERY = "recovery"
    EXPANSION = "expansion"
    CONTRACTION = "contraction"
    UNKNOWN = "unknown"


@dataclass
class RegimeCharacteristics:
    """Características de um regime econômico"""
    name: str
    duration_months: int
    frequency: float
    mean_values: Dict[str, float]
    std_values: Dict[str, float]
    confidence: float
    typical_periods: List[str]


@dataclass
class ModelValidationResult:
    """Resultado de validação de modelo"""
    is_valid: bool
    aic: float
    bic: float
    log_likelihood: float
    convergence: bool
    linearity_test: Dict[str, Any]
    regime_number_test: Dict[str, Any]
    out_of_sample_metrics: Dict[str, Any]


@dataclass
class RegimeAnalysisResult:
    """Resultado completo da análise de regimes"""
    current_regime: RegimeType
    regime_probabilities: Dict[RegimeType, float]
    regime_characteristics: Dict[RegimeType, RegimeCharacteristics]
    transition_matrix: Dict[RegimeType, Dict[RegimeType, float]]
    model_validation: ModelValidationResult
    confidence: float
    timestamp: str
    data_quality: Dict[str, float]


class IRegimeModel(ABC):
    """Interface para modelos de regime"""
    
    @abstractmethod
    async def fit(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Ajusta o modelo aos dados"""
        pass
    
    @abstractmethod
    async def predict(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Prediz regimes para novos dados"""
        pass
    
    @abstractmethod
    async def validate(self, data: pd.DataFrame) -> ModelValidationResult:
        """Valida o modelo estatisticamente"""
        pass


class IRegimeValidator(ABC):
    """Interface para validação de regimes"""
    
    @abstractmethod
    async def validate_linearity(self, model: Any, data: pd.DataFrame) -> Dict[str, Any]:
        """Testa se modelo não-linear é necessário"""
        pass
    
    @abstractmethod
    async def validate_regime_number(self, model: Any, data: pd.DataFrame) -> Dict[str, Any]:
        """Testa número ótimo de regimes"""
        pass
    
    @abstractmethod
    async def validate_out_of_sample(self, model: Any, data: pd.DataFrame) -> Dict[str, Any]:
        """Validação fora da amostra"""
        pass


class IRegimeCharacterizer(ABC):
    """Interface para caracterização de regimes"""
    
    @abstractmethod
    async def characterize_regimes(self, model: Any, data: pd.DataFrame) -> Dict[RegimeType, RegimeCharacteristics]:
        """Caracteriza regimes baseado nos dados"""
        pass
    
    @abstractmethod
    async def identify_regime_name(self, characteristics: Dict[str, float]) -> RegimeType:
        """Identifica nome do regime baseado nas características"""
        pass


class IRegimeAnalyzer(ABC):
    """Interface principal para análise de regimes"""
    
    @abstractmethod
    async def analyze_regimes(self, data: pd.DataFrame, country: str) -> RegimeAnalysisResult:
        """Análise completa de regimes"""
        pass
    
    @abstractmethod
    async def get_regime_forecast(self, data: pd.DataFrame, horizon: int) -> List[Dict[str, Any]]:
        """Previsão de regimes futuros"""
        pass


class IDataPreprocessor(ABC):
    """Interface para pré-processamento de dados"""
    
    @abstractmethod
    async def preprocess(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepara dados para análise"""
        pass
    
    @abstractmethod
    async def validate_data_quality(self, data: pd.DataFrame) -> Dict[str, float]:
        """Valida qualidade dos dados"""
        pass


class IUncertaintyQuantifier(ABC):
    """Interface para quantificação de incerteza"""
    
    @abstractmethod
    async def calculate_uncertainty(self, model: Any, data: pd.DataFrame) -> Dict[str, Any]:
        """Calcula incerteza nas identificações de regime"""
        pass
    
    @abstractmethod
    async def bootstrap_confidence_intervals(self, model: Any, data: pd.DataFrame) -> Dict[str, Any]:
        """Calcula intervalos de confiança via bootstrap"""
        pass


class IAustrianRegimeAnalyzer(ABC):
    """Interface para análise compatível com escola austríaca"""
    
    @abstractmethod
    async def detect_credit_expansion(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detecta expansão artificial de crédito"""
        pass
    
    @abstractmethod
    async def detect_production_distortions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detecta distorções na estrutura de produção"""
        pass
    
    @abstractmethod
    async def detect_malinvestment_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detecta sinais de má-alocação de capital"""
        pass
    
    @abstractmethod
    async def analyze_monetary_policy_cycle(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analisa ciclo de política monetária"""
        pass
