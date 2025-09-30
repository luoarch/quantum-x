"""
Pacote de validação científica para propriedades de size e power
"""

from .test_size_power import (
    size_experiment,
    power_experiment,
    SizeConfig,
    PowerConfig,
    run_adf,
    run_dfgls,
    run_kpss_centered
)

__all__ = [
    "size_experiment",
    "power_experiment", 
    "SizeConfig",
    "PowerConfig",
    "run_adf",
    "run_dfgls",
    "run_kpss_centered"
]
