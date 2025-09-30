"""
Pacote de validação científica para seleção de lags
"""

from .test_lag_selection import (
    run_experiment,
    select_lag_aic,
    select_lag_bic,
    select_lag_tstat,
    generate_ar,
    schwert_Lmax
)

__all__ = [
    "run_experiment",
    "select_lag_aic",
    "select_lag_bic",
    "select_lag_tstat",
    "generate_ar",
    "schwert_Lmax"
]
