"""
Módulo de Análise Científica de Regimes Econômicos
Implementa princípios SOLID e validação estatística robusta
"""

from .interfaces import (
    IRegimeModel,
    IRegimeValidator,
    IRegimeCharacterizer,
    IDataPreprocessor,
    IRegimeAnalyzer,
    IUncertaintyQuantifier,
    IAustrianRegimeAnalyzer,
    RegimeType,
    RegimeCharacteristics,
    ModelValidationResult,
    RegimeAnalysisResult
)

from .markov_switching_model import ScientificMarkovSwitchingModel
from .regime_validator import ScientificRegimeValidator
from .regime_characterizer import ScientificRegimeCharacterizer
from .data_preprocessor import ScientificDataPreprocessor
from .regime_analyzer import ScientificRegimeAnalyzer
from .austrian_regime_analyzer import AustrianCompatibleRegimeAnalyzer

__all__ = [
    # Interfaces
    'IRegimeModel',
    'IRegimeValidator', 
    'IRegimeCharacterizer',
    'IDataPreprocessor',
    'IRegimeAnalyzer',
    'IUncertaintyQuantifier',
    'IAustrianRegimeAnalyzer',
    
    # Data Classes
    'RegimeType',
    'RegimeCharacteristics',
    'ModelValidationResult',
    'RegimeAnalysisResult',
    
    # Implementations
    'ScientificMarkovSwitchingModel',
    'ScientificRegimeValidator',
    'ScientificRegimeCharacterizer', 
    'ScientificDataPreprocessor',
    'ScientificRegimeAnalyzer',
    'AustrianCompatibleRegimeAnalyzer'
]

__version__ = "1.0.0"
__author__ = "Quantum-X Team"
__description__ = "Análise científica de regimes econômicos com validação estatística robusta"
