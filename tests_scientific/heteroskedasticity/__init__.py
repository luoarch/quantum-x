"""
Pacote de validação científica para heteroskedasticidade
"""

from .test_heteroskedasticity import (
    hetero_size_experiment,
    gen_increasing_sigma,
    gen_decreasing_sigma,
    gen_breaks_sigma,
    gen_arch1,
    gen_garch11,
    run_adf,
    run_dfgls,
    run_kpss_c
)

__all__ = [
    "hetero_size_experiment",
    "gen_increasing_sigma",
    "gen_decreasing_sigma", 
    "gen_breaks_sigma",
    "gen_arch1",
    "gen_garch11",
    "run_adf",
    "run_dfgls",
    "run_kpss_c"
]
