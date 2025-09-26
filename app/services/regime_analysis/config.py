"""
Configurações para Análise de Regimes Econômicos
Configurações centralizadas para todos os componentes
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    """Níveis de validação"""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


class AnalysisType(Enum):
    """Tipos de análise"""
    SCIENTIFIC = "scientific"
    AUSTRIAN = "austrian"
    HYBRID = "hybrid"


@dataclass
class RegimeAnalysisConfig:
    """Configuração para análise de regimes"""
    
    # Configurações do modelo
    max_regimes: int = 5
    min_observations: int = 20
    confidence_threshold: float = 0.6
    
    # Configurações de validação
    validation_level: ValidationLevel = ValidationLevel.STRICT
    test_linearity: bool = True
    test_regime_number: bool = True
    test_out_of_sample: bool = True
    
    # Configurações de pré-processamento
    outlier_method: str = "iqr"  # iqr, zscore, isolation
    imputation_method: str = "knn"  # knn, linear, forward_fill
    scaling_method: str = "robust"  # robust, standard, minmax
    
    # Configurações de validação bootstrap
    n_bootstrap: int = 1000
    bootstrap_confidence_level: float = 0.95
    
    # Configurações austríacas
    credit_expansion_threshold: float = 0.1
    yield_curve_threshold: float = 0.5
    malinvestment_threshold: float = 0.15
    
    # Configurações de cache
    cache_ttl: int = 3600  # 1 hora em segundos
    enable_cache: bool = True
    
    # Configurações de logging
    log_level: str = "INFO"
    enable_debug_logs: bool = False


@dataclass
class DataQualityThresholds:
    """Limiares para qualidade dos dados"""
    
    # Completude
    min_completeness: float = 0.8
    excellent_completeness: float = 0.95
    
    # Consistência temporal
    min_temporal_consistency: float = 0.7
    excellent_temporal_consistency: float = 0.9
    
    # Variabilidade
    min_variability: float = 0.1
    max_variability: float = 2.0
    
    # Estacionariedade
    min_stationarity: float = 0.5
    
    # Qualidade geral
    min_overall_quality: float = 0.6
    good_overall_quality: float = 0.8
    excellent_overall_quality: float = 0.9


@dataclass
class ModelValidationThresholds:
    """Limiares para validação de modelos"""
    
    # Testes de significância
    significance_level: float = 0.05
    marginal_significance_level: float = 0.1
    
    # Critérios de informação
    aic_penalty: float = 2.0
    bic_penalty: float = 1.0
    
    # Convergência
    min_convergence_rate: float = 0.8
    max_iterations: int = 1000
    
    # Validação fora da amostra
    min_out_of_sample_accuracy: float = 0.6
    min_forecast_rmse: float = 0.1
    
    # Robustez
    min_robustness_score: float = 0.7
    min_parameter_stability: float = 0.8


@dataclass
class AustrianAnalysisConfig:
    """Configuração para análise austríaca"""
    
    # Indicadores de crédito
    credit_indicators: List[str] = None
    
    # Indicadores de produção
    production_indicators: List[str] = None
    
    # Indicadores de investimento
    investment_indicators: List[str] = None
    
    # Indicadores monetários
    monetary_indicators: List[str] = None
    
    def __post_init__(self):
        if self.credit_indicators is None:
            self.credit_indicators = [
                'credit', 'loan', 'debt', 'lending', 'credito', 'emprestimo'
            ]
        
        if self.production_indicators is None:
            self.production_indicators = [
                'production', 'industrial', 'manufacturing', 'prod', 'industria'
            ]
        
        if self.investment_indicators is None:
            self.investment_indicators = [
                'investment', 'capital', 'investimento', 'capital'
            ]
        
        if self.monetary_indicators is None:
            self.monetary_indicators = [
                'interest', 'rate', 'selic', 'juros', 'monetary', 'money', 'supply'
            ]


# Configurações padrão
DEFAULT_CONFIG = RegimeAnalysisConfig()
DEFAULT_DATA_QUALITY_THRESHOLDS = DataQualityThresholds()
DEFAULT_MODEL_VALIDATION_THRESHOLDS = ModelValidationThresholds()
DEFAULT_AUSTRIAN_CONFIG = AustrianAnalysisConfig()

# Configurações por país
COUNTRY_CONFIGS = {
    'BRA': {
        'indicators': ['ipca', 'selic', 'pib', 'desemprego', 'cambio'],
        'frequency': 'monthly',
        'timezone': 'America/Sao_Paulo'
    },
    'USA': {
        'indicators': ['gdp', 'unemployment', 'inflation', 'fed_funds_rate'],
        'frequency': 'monthly',
        'timezone': 'America/New_York'
    },
    'GLOBAL': {
        'indicators': ['cli', 'vix', 'yield_curve', 'dollar_index'],
        'frequency': 'monthly',
        'timezone': 'UTC'
    }
}

# Configurações de indicadores
INDICATOR_CONFIGS = {
    'ipca': {
        'name': 'IPCA',
        'description': 'Índice Nacional de Preços ao Consumidor Amplo',
        'frequency': 'monthly',
        'unit': 'percent',
        'source': 'IBGE'
    },
    'selic': {
        'name': 'SELIC',
        'description': 'Taxa Selic',
        'frequency': 'monthly',
        'unit': 'percent',
        'source': 'BCB'
    },
    'pib': {
        'name': 'PIB',
        'description': 'Produto Interno Bruto',
        'frequency': 'quarterly',
        'unit': 'percent',
        'source': 'IBGE'
    },
    'desemprego': {
        'name': 'Taxa de Desemprego',
        'description': 'Taxa de Desemprego',
        'frequency': 'monthly',
        'unit': 'percent',
        'source': 'IBGE'
    },
    'cli': {
        'name': 'CLI',
        'description': 'Composite Leading Indicator',
        'frequency': 'monthly',
        'unit': 'index',
        'source': 'OECD'
    },
    'vix': {
        'name': 'VIX',
        'description': 'Volatility Index',
        'frequency': 'daily',
        'unit': 'index',
        'source': 'CBOE'
    }
}

# Configurações de regimes
REGIME_CONFIGS = {
    'RECESSION': {
        'name': 'Recessão',
        'description': 'Período de declínio econômico',
        'color': '#dc3545',
        'icon': '📉'
    },
    'RECOVERY': {
        'name': 'Recuperação',
        'description': 'Período de recuperação pós-recessão',
        'color': '#ffc107',
        'icon': '📈'
    },
    'EXPANSION': {
        'name': 'Expansão',
        'description': 'Período de crescimento econômico',
        'color': '#28a745',
        'icon': '🚀'
    },
    'CONTRACTION': {
        'name': 'Contração',
        'description': 'Período de desaceleração econômica',
        'color': '#fd7e14',
        'icon': '⚠️'
    },
    'UNKNOWN': {
        'name': 'Desconhecido',
        'description': 'Regime não identificado',
        'color': '#6c757d',
        'icon': '❓'
    }
}

# Configurações de API
API_CONFIGS = {
    'rate_limits': {
        'regime_analysis': 10,  # requests per minute
        'scientific_validation': 5,  # requests per minute
        'bootstrap_validation': 2   # requests per minute
    },
    'timeouts': {
        'regime_analysis': 300,  # 5 minutes
        'scientific_validation': 600,  # 10 minutes
        'bootstrap_validation': 1800  # 30 minutes
    },
    'cache_settings': {
        'regime_analysis': 3600,  # 1 hour
        'scientific_validation': 1800,  # 30 minutes
        'bootstrap_validation': 7200  # 2 hours
    }
}

# Configurações de logging
LOGGING_CONFIGS = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'regime_analysis.log',
            'level': 'DEBUG'
        }
    }
}

# Configurações de métricas
METRICS_CONFIGS = {
    'regime_analysis': [
        'current_regime',
        'regime_probabilities',
        'regime_confidence',
        'transition_matrix',
        'model_validation'
    ],
    'scientific_validation': [
        'linearity_test',
        'regime_number_test',
        'out_of_sample_validation',
        'bootstrap_validation',
        'data_quality'
    ],
    'austrian_analysis': [
        'credit_expansion',
        'production_distortions',
        'malinvestment_signals',
        'monetary_policy_cycle'
    ]
}

def get_config(country: str = 'BRA', analysis_type: AnalysisType = AnalysisType.SCIENTIFIC) -> RegimeAnalysisConfig:
    """
    Obtém configuração para país e tipo de análise específicos
    
    Args:
        country: País para análise
        analysis_type: Tipo de análise
        
    Returns:
        Configuração específica
    """
    config = RegimeAnalysisConfig()
    
    # Ajustar configurações baseadas no país
    if country in COUNTRY_CONFIGS:
        country_config = COUNTRY_CONFIGS[country]
        # Aplicar configurações específicas do país
        pass
    
    # Ajustar configurações baseadas no tipo de análise
    if analysis_type == AnalysisType.AUSTRIAN:
        config.validation_level = ValidationLevel.LENIENT
        config.test_linearity = False
        config.test_regime_number = False
    
    return config

def get_indicator_config(indicator: str) -> Dict[str, Any]:
    """
    Obtém configuração para indicador específico
    
    Args:
        indicator: Nome do indicador
        
    Returns:
        Configuração do indicador
    """
    return INDICATOR_CONFIGS.get(indicator, {
        'name': indicator.upper(),
        'description': f'Indicador {indicator}',
        'frequency': 'monthly',
        'unit': 'index',
        'source': 'Unknown'
    })

def get_regime_config(regime: str) -> Dict[str, Any]:
    """
    Obtém configuração para regime específico
    
    Args:
        regime: Nome do regime
        
    Returns:
        Configuração do regime
    """
    return REGIME_CONFIGS.get(regime.upper(), REGIME_CONFIGS['UNKNOWN'])
