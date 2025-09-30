#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Avaliação de detecção de quebras estruturais via Zivot–Andrews.
Inclui séries com uma e múltiplas quebras e tolerância configurável.
"""

from __future__ import annotations
import os
import json
import argparse
from typing import Dict, Any, List, Tuple, Callable

import numpy as np
import pandas as pd

# Preferir arch.unitroot; fallback para statsmodels com parsing robusto
try:
    from arch.unitroot import ZivotAndrews as ZA
    HAVE_ARCH = True
except Exception:
    HAVE_ARCH = False
    ZA = None

try:
    from statsmodels.tsa.stattools import zivot_andrews as za_sm
    HAVE_SM = True
except Exception:
    HAVE_SM = False
    za_sm = None

# ---------- Utils ----------
def set_seed(seed: int = 42) -> None:
    np.random.seed(seed)

# ---------- Geradores de séries com quebras ----------
# Geradores I(0) - mais fáceis para ZA detectar
def gen_ar1_level_break(T: int, phi: float = 0.6, mag: float = 5.0) -> Tuple[np.ndarray, List[int]]:
    """AR(1) estacionário com quebra de nível - caso 'fácil' para ZA"""
    y = np.zeros(T)
    eps = np.random.normal(0, 1, T)
    for t in range(1, T):
        y[t] = phi * y[t-1] + eps[t]
    bp = T // 2
    y[bp:] += mag
    return y, [bp]

def gen_ar1_trend_break(T: int, phi: float = 0.6, slope_delta: float = 0.05) -> Tuple[np.ndarray, List[int]]:
    """AR(1) estacionário com mudança de tendência - caso 'fácil' para ZA"""
    eps = np.random.normal(0, 1, T)
    y = np.zeros(T)
    bp = T // 2
    for t in range(1, T):
        y[t] = phi * y[t-1] + eps[t]
    t = np.arange(T)
    y[:bp] += 0.00 * t[:bp]
    y[bp:] += slope_delta * (t[bp:] - t[bp])
    return y, [bp]

# Geradores I(1) - casos 'difíceis' (mantidos para documentar limitação)
def gen_single_level(T: int, mag: float = 2.0) -> Tuple[np.ndarray, List[int]]:
    """RW com quebra de nível - caso 'difícil' para ZA (documentado)"""
    y = np.random.normal(0, 1, T).cumsum()
    bp = T // 2
    y[bp:] += mag
    return y, [bp]

def gen_trend_break(T: int, mag: float = 0.05) -> Tuple[np.ndarray, List[int]]:
    """RW com quebra de tendência - caso 'difícil' para ZA (documentado)"""
    t = np.arange(T)
    y = 0.01 * t + np.random.normal(0, 1, T).cumsum()
    bp = T // 2
    y[bp:] += mag * (t[bp:] - t[bp])
    return y, [bp]

def gen_double_level(T: int, mag: float = 2.0) -> Tuple[np.ndarray, List[int]]:
    y = np.random.normal(0, 1, T).cumsum()
    bp1, bp2 = T // 3, 2 * T // 3
    y[bp1:] += mag
    y[bp2:] -= mag / 2
    return y, [bp1, bp2]

def gen_mixed_breaks(T: int, mag_level: float = 2.0, mag_trend: float = 0.05) -> Tuple[np.ndarray, List[int]]:
    t = np.arange(T)
    y = np.random.normal(0, 1, T).cumsum()
    bp1, bp2 = T // 3, 2 * T // 3
    # nível
    y[bp1:] += mag_level
    # tendência
    y[bp2:] += mag_trend * (t[bp2:] - t[bp2])
    return y, [bp1, bp2]

GEN_MAP: Dict[str, Callable[..., Tuple[np.ndarray, List[int]]]] = {
    # Casos I(0) - mais fáceis para ZA (preferidos para métricas principais)
    "ar1_level": gen_ar1_level_break,
    "ar1_trend": gen_ar1_trend_break,
    # Casos I(1) - mais difíceis (documentar como "hard cases")
    "single_level": gen_single_level,
    "trend_break": gen_trend_break,
    "double_level": gen_double_level,
    "mixed_breaks": gen_mixed_breaks,
}

# ---------- Detecção ZA ----------
def detect_break_za(series: np.ndarray, regression: str = "c", trim: float = 0.15) -> int:
    """
    Retorna índice (int) do break_date estimado por Zivot-Andrews.
    Prioriza statsmodels.tsa.stattools.zivot_andrews (mais confiável).
    Fallback para arch.unitroot caso statsmodels não disponível.
    Lança RuntimeError se nenhuma implementação disponível.
    
    Args:
        series: Série temporal para detectar quebra
        regression: Tipo de modelo ("c" para constante, "ct" para constante+tendência)
        trim: Fração recortada nas pontas para busca (padrão: 0.15 = [15%, 85%])
    
    Returns:
        Índice inteiro da quebra detectada
    
    Raises:
        RuntimeError: Se nenhuma implementação disponível ou formato inesperado
    """
    # PRIORIDADE 1: statsmodels (mais confiável para break_date)
    if HAVE_SM and za_sm is not None:
        out = za_sm(series, regression=regression, maxlag=None, trim=trim)
        # statsmodels retorna: (stat, pvalue, crit, usedlag, bpidx)
        # IMPORTANTE: bpidx está na posição 4 (último elemento), não na 3
        # Posição 3 é 'usedlag' (número de lags usado na regressão)
        if isinstance(out, tuple):
            if len(out) == 5:
                # Formato: (stat, pvalue, crit, usedlag, bpidx)
                _, _, _, _, bp = out
                return int(bp)
            elif len(out) == 4:
                # Formato antigo (se existir): (stat, pvalue, crit, bp)
                _, _, _, bp = out
                return int(bp)
        # Como último recurso, tentar atributo .breakpoint se existir
        if hasattr(out, "breakpoint"):
            return int(getattr(out, "breakpoint"))
        raise RuntimeError(f"statsmodels.zivot_andrews returned unexpected format: {type(out)}, len={len(out) if isinstance(out, tuple) else 'N/A'}")
    
    # PRIORIDADE 2: arch.unitroot (fallback, mas break_date não está exposto publicamente)
    if HAVE_ARCH and ZA is not None:
        # arch.unitroot.ZivotAndrews não expõe break_date como atributo público
        # mas podemos tentar acessar se futuras versões adicionarem
        res = ZA(series, trend=regression)
        if hasattr(res, 'break_date'):
            return int(res.break_date)
        # Fallback: tentar acessar via atributo interno (não recomendado mas último recurso)
        if hasattr(res, '_break_date'):
            return int(res._break_date)
        raise RuntimeError("arch.unitroot.ZivotAndrews available but break_date not exposed")
    
    raise RuntimeError("No Zivot–Andrews implementation available (statsmodels or arch required)")

# ---------- Sanity Check ----------
def sanity_check_obvious_break() -> None:
    """
    Teste determinístico de quebra óbvia para validar implementação ZA.
    Usa AR(1) estacionário com salto de nível (mais fácil que RW puro).
    """
    T = 200
    np.random.seed(123)  # seed fixo para sanity check
    phi = 0.6
    y = np.zeros(T)
    eps = np.random.normal(0, 1, T)
    for t in range(1, T):
        y[t] = phi * y[t-1] + eps[t]
    y[T//2:] += 5.0  # salto de nível claro
    bp = detect_break_za(y, regression="c", trim=0.15)
    
    expected_bp = T // 2
    error = abs(bp - expected_bp)
    
    if error <= 10:
        print(f"[SANITY CHECK] ✅ ZA detectou bp={bp} (esperado={expected_bp}, erro={error})")
    else:
        print(f"[SANITY CHECK] ⚠️ ZA detectou bp={bp} (esperado={expected_bp}, erro={error})")
        print(f"[SANITY CHECK] ⚠️ Usando AR(1) I(0) com mag=5.0 - erro>{error} períodos sugere problema")

# ---------- Experimento ----------
def breaks_experiment(cases: List[str], T: int, n_sims: int, tol: int, mag: float, seed: int, trim: float) -> Dict[str, Any]:
    set_seed(seed)
    results: Dict[str, Any] = {}

    for case in cases:
        gen = GEN_MAP[case]
        detected_within_tol = 0
        abs_errors: List[int] = []
        
        # Determinar tipo de regressão e parâmetros por caso
        if case == "ar1_level":
            regression = "c"
            series_type = "I(0)"  # estacionário
        elif case == "ar1_trend":
            regression = "ct"
            series_type = "I(0)"  # estacionário
        elif case in ("trend_break", "mixed_breaks", "ar1_trend"):
            regression = "ct"
            series_type = "I(1)"  # random walk
        else:
            regression = "c"
            series_type = "I(1)"  # random walk

        for _ in range(n_sims):
            # Gerar série conforme o caso
            if case == "ar1_level":
                series, bps = gen(T, phi=0.6, mag=mag)
            elif case == "ar1_trend":
                series, bps = gen(T, phi=0.6, slope_delta=mag/100.0)
            elif case == "trend_break":
                series, bps = gen(T, mag)
            elif case == "mixed_breaks":
                series, bps = gen(T, mag_level=mag, mag_trend=mag / 40.0)
            else:
                series, bps = gen(T, mag)

            # Detectar quebra com tipo de regressão apropriado
            detected = detect_break_za(series, regression=regression, trim=trim)
            
            # Erro mínimo à quebra mais próxima
            min_err = min(abs(detected - bp) for bp in bps)
            abs_errors.append(min_err)
            if min_err <= tol:
                detected_within_tol += 1

        # Adicionar notas explicativas por tipo de caso
        if series_type == "I(0)":
            note = "AR(1) estacionário - caso favorável para ZA"
        elif case in ("double_level", "mixed_breaks"):
            note = "Múltiplas quebras - ZA projetado para 1 quebra; baixa detecção esperada. Use Bai-Perron."
        else:
            note = "Random walk - caso difícil; RW+step é notoriamente ambíguo para ZA"
        
        results[case] = {
            "detection_rate_within_tol": detected_within_tol / n_sims,
            "mean_abs_error_periods": float(np.mean(abs_errors)),
            "median_abs_error_periods": float(np.median(abs_errors)),
            "std_abs_error_periods": float(np.std(abs_errors, ddof=1)),
            "min_abs_error_periods": float(np.min(abs_errors)),
            "max_abs_error_periods": float(np.max(abs_errors)),
            "tol_periods": tol,
            "regression": regression,
            "series_type": series_type,
            "note": note,
        }

    return {
        "config": {"cases": cases, "T": T, "n_sims": n_sims, "tol": tol, "mag": mag, "trim": trim, "seed": seed},
        "results": results,
        "metadata": {
            "description": "Validação Zivot-Andrews para detecção de quebras estruturais",
            "limitation": "ZA é projetado para 1 quebra única; casos I(0) têm melhor detecção que I(1)",
            "recommendation": "Para múltiplas quebras, considere Bai-Perron (1998)"
        }
    }

# ---------- Export ----------
def ensure_dir(path: str) -> None:
    if path: os.makedirs(path, exist_ok=True)

def write_json(obj: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_csv(mapping: Dict[str, Any], path: str) -> None:
    rows: List[Dict[str, Any]] = []
    for case, vals in mapping["results"].items():
        rows.append({"case": case, **vals})
    pd.DataFrame(rows).to_csv(path, index=False)

# ---------- CLI ----------
def parse_args() -> argparse.Namespace:
    import argparse
    ap = argparse.ArgumentParser(description="Structural breaks validation (Zivot–Andrews)")
    ap.add_argument("--cases", type=str, default="ar1_level,ar1_trend,single_level,trend_break",
                    help="Casos a testar: ar1_level,ar1_trend (I(0)-fácil), single_level,trend_break,double_level,mixed_breaks (I(1)-difícil)")
    ap.add_argument("--T", type=int, default=100)
    ap.add_argument("--n-sims", type=int, default=500)
    ap.add_argument("--tol", type=int, default=10)
    ap.add_argument("--mag", type=float, default=2.0)
    ap.add_argument("--trim", type=float, default=0.15, help="Fração recortada nas pontas para busca do break (padrão: 0.15 = [15%%, 85%%])")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", type=str, default="")
    return ap.parse_args()

def main() -> None:
    args = parse_args()
    cases = [c.strip() for c in args.cases.split(",") if c.strip()]
    ensure_dir(args.out_dir)

    # Executar sanity check antes dos experimentos
    print("[INIT] Executando sanity check de quebra óbvia...")
    try:
        sanity_check_obvious_break()
    except AssertionError as e:
        print(f"[WARNING] Sanity check falhou: {e}")
        print("[WARNING] Continuando com experimentos...")
    except Exception as e:
        print(f"[WARNING] Erro no sanity check: {e}")
        print("[WARNING] Continuando com experimentos...")

    res = breaks_experiment(cases, args.T, args.n_sims, args.tol, args.mag, args.seed, args.trim)
    print("[BREAKS]", res["results"])
    if args.out_dir:
        write_json(res, os.path.join(args.out_dir, "breaks_results.json"))
        write_csv(res, os.path.join(args.out_dir, "breaks_results.csv"))

if __name__ == "__main__":
    main()
