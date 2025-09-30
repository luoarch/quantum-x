#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Avaliação de size sob heterocedasticidade: increasing, decreasing, breaks, ARCH(1), GARCH(1,1).
"""

from __future__ import annotations
import os
import json
import argparse
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss
from arch.unitroot import DFGLS

# --------- Utils ----------
def set_seed(seed: int = 42) -> None:
    np.random.seed(seed)

# --------- Geradores de heterocedasticidade ----------
def gen_increasing_sigma(T: int) -> np.ndarray:
    return np.array([0.5 + 0.01 * t for t in range(T)], dtype=float)

def gen_decreasing_sigma(T: int) -> np.ndarray:
    return np.array([max(0.1, 2.0 - 0.015 * t) for t in range(T)], dtype=float)

def gen_breaks_sigma(T: int, low: float = 0.5, high: float = 2.0) -> np.ndarray:
    s = np.ones(T) * low
    s[T // 2 :] = high
    return s

def gen_arch1(T: int, omega: float = 0.1, alpha: float = 0.3) -> np.ndarray:
    eps = np.zeros(T)
    sigma2 = np.zeros(T)
    sigma2[0] = omega / (1 - alpha)
    eps[0] = np.random.normal(0.0, np.sqrt(sigma2[0]))
    for t in range(1, T):
        sigma2[t] = omega + alpha * eps[t - 1] ** 2
        eps[t] = np.random.normal(0.0, np.sqrt(sigma2[t]))
    return eps

def gen_garch11(T: int, omega: float = 0.05, alpha: float = 0.1, beta: float = 0.85) -> np.ndarray:
    eps = np.zeros(T)
    sigma2 = np.zeros(T)
    sigma2[0] = omega / (1 - alpha - beta)
    eps[0] = np.random.normal(0.0, np.sqrt(sigma2[0]))
    for t in range(1, T):
        sigma2[t] = omega + alpha * eps[t - 1] ** 2 + beta * sigma2[t - 1]
        eps[t] = np.random.normal(0.0, np.sqrt(sigma2[t]))
    return eps

# --------- Construção das séries sob H0 ----------
def rw_with_sigma(sigmas: np.ndarray) -> np.ndarray:
    return np.cumsum(np.random.normal(0.0, sigmas))

def ar1_with_sigma(T: int, phi: float, sigmas: np.ndarray) -> np.ndarray:
    y = np.zeros(T)
    for t in range(1, T):
        eps_t = np.random.normal(0.0, sigmas[t])
        y[t] = phi * y[t - 1] + eps_t
    return y

# --------- Wrappers de testes ----------
def run_adf(series: np.ndarray, alpha: float) -> bool:
    p = adfuller(series, autolag="AIC", regression="c")[1]
    return p < alpha

def run_dfgls(series: np.ndarray, alpha: float) -> bool:
    p = DFGLS(series, trend="c").pvalue
    return p < alpha

def run_kpss_c(series: np.ndarray, alpha: float) -> bool:
    p = kpss(series, regression="c", nlags="auto")[1]
    return p < alpha

# --------- Experimento ----------
def hetero_size_experiment(patterns: List[str], T: int, n_sims: int, alpha: float, seed: int) -> Dict[str, Any]:
    set_seed(seed)
    results: Dict[str, Any] = {}

    for pattern in patterns:
        rej_adf = rej_dfgls = rej_kpss = 0

        for _ in range(n_sims):
            if pattern == "increasing":
                sigmas = gen_increasing_sigma(T)
                rw = rw_with_sigma(sigmas)
                ar = ar1_with_sigma(T, phi=0.7, sigmas=sigmas)
            elif pattern == "decreasing":
                sigmas = gen_decreasing_sigma(T)
                rw = rw_with_sigma(sigmas)
                ar = ar1_with_sigma(T, phi=0.7, sigmas=sigmas)
            elif pattern == "breaks":
                sigmas = gen_breaks_sigma(T)
                rw = rw_with_sigma(sigmas)
                ar = ar1_with_sigma(T, phi=0.7, sigmas=sigmas)
            elif pattern == "arch":
                eps = gen_arch1(T)
                rw = np.cumsum(eps)
                # para KPSS (H0 estacionária), usamos AR(1) com eps ARCH
                # aproximando com variância média:
                sigmas = np.sqrt(np.maximum(1e-8, np.var(eps))) * np.ones(T)
                ar = ar1_with_sigma(T, phi=0.7, sigmas=sigmas)
            elif pattern == "garch":
                eps = gen_garch11(T)
                rw = np.cumsum(eps)
                sigmas = np.sqrt(np.maximum(1e-8, np.var(eps))) * np.ones(T)
                ar = ar1_with_sigma(T, phi=0.7, sigmas=sigmas)
            else:
                raise ValueError(f"Padrão desconhecido: {pattern}")

            # ADF / DFGLS sob H0 (random walk)
            if run_adf(rw, alpha): rej_adf += 1
            if run_dfgls(rw, alpha): rej_dfgls += 1
            # KPSS sob H0 (estacionária)
            if run_kpss_c(ar, alpha): rej_kpss += 1

        results[pattern] = {
            "adf_size": rej_adf / n_sims,
            "dfgls_size": rej_dfgls / n_sims,
            "kpss_size": rej_kpss / n_sims,
        }

    return {
        "config": {"patterns": patterns, "T": T, "n_sims": n_sims, "alpha": alpha, "seed": seed},
        "results": results,
    }

# --------- Export ----------
def ensure_dir(path: str) -> None:
    if path: os.makedirs(path, exist_ok=True)

def write_json(obj: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_csv(mapping: Dict[str, Any], path: str) -> None:
    rows: List[Dict[str, Any]] = []
    for pat, vals in mapping["results"].items():
        rows.append({"pattern": pat, **vals})
    pd.DataFrame(rows).to_csv(path, index=False)

# --------- CLI ----------
def parse_args() -> argparse.Namespace:
    import argparse
    ap = argparse.ArgumentParser(description="Heteroskedasticity size validation")
    ap.add_argument("--patterns", type=str, default="increasing,decreasing,breaks,arch,garch")
    ap.add_argument("--T", type=int, default=100)
    ap.add_argument("--n-sims", type=int, default=1000)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", type=str, default="")
    return ap.parse_args()

def main() -> None:
    args = parse_args()
    patterns = [p.strip() for p in args.patterns.split(",") if p.strip()]
    ensure_dir(args.out_dir)

    res = hetero_size_experiment(patterns, args.T, args.n_sims, args.alpha, args.seed)
    print("[HETERO SIZE]", res["results"])
    if args.out_dir:
        write_json(res, os.path.join(args.out_dir, "hetero_size_results.json"))
        write_csv(res, os.path.join(args.out_dir, "hetero_size_results.csv"))

if __name__ == "__main__":
    main()
