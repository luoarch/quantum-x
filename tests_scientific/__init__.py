"""
Pacote de validação científica para modelo FED-Selic
"""

# Importar subpacotes
from . import size_power
from . import small_samples
from . import heteroskedasticity
from . import structural_breaks
from . import lag_selection
from . import benchmarks_np

__all__ = ["size_power", "small_samples", "heteroskedasticity", "structural_breaks", "lag_selection", "benchmarks_np"]
