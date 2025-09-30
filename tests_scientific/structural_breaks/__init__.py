"""
Pacote de validação científica para quebras estruturais
"""

from .test_structural_breaks import (
    breaks_experiment,
    gen_single_level,
    gen_trend_break,
    gen_double_level,
    gen_mixed_breaks,
    detect_break_za
)

__all__ = [
    "breaks_experiment",
    "gen_single_level",
    "gen_trend_break",
    "gen_double_level",
    "gen_mixed_breaks",
    "detect_break_za"
]
