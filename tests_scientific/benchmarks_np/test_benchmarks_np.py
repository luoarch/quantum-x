#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import os
import json
import argparse
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss
from arch.unitroot import DFGLS

# ---------- Utils ----------
def set_seed(seed: int = 42) -> None:
    np.random.seed(seed)

def generate_rw(T: int, drift: float = 0.0, sigma: float = 1.0) -> np.ndarray:
    eps = np.random.normal(0.0, sigma, T)
    y = np.cumsum(eps) + drift * np.arange(T)
    return y

def generate_ar1(T: int, phi: float, sigma: float = 1.0) -> np.ndarray:
    y = np.zeros(T)
    eps = np.random.normal(0.0, sigma, T)
    for t in range(1, T):
        y[t] = phi * y[t - 1] + eps[t]
    return y

# ---------- Test wrappers ----------
def adf_unit_root(series: np.ndarray, alpha: float = 0.05) -> bool:
    # retorna True se NÃO rejeita H0 (unit root)
    p = adfuller(series, autolag="AIC", regression="c")[1]
    return p >= alpha

def dfgls_unit_root(series: np.ndarray, alpha: float = 0.05) -> bool:
    # retorna True se NÃO rejeita H0 (unit root)
    p = DFGLS(series, trend="c").pvalue
    return p >= alpha

def kpss_stationary(series: np.ndarray, alpha: float = 0.05) -> bool:
    # retorna True se NÃO rejeita H0 (stationary)
    p = kpss(series, regression="c", nlags="auto")[1]
    return p >= alpha

# ---------- Benchmark harness ----------
def run_benchmarks(T: int, n_sims: int, seed: int, alpha: float) -> Dict[str, Any]:
    set_seed(seed)
    specs = {
        "real_gdp_like": {"gen": lambda: generate_rw(T, drift=0.01), "expected_unit_root": True},
        "price_level_like": {"gen": lambda: generate_rw(T, drift=0.0), "expected_unit_root": True},
        "unemployment_like": {"gen": lambda: generate_ar1(T, phi=0.85), "expected_unit_root": False},
        "interest_rate_like": {"gen": lambda: generate_ar1(T, phi=0.90), "expected_unit_root": False},
    }

    results: Dict[str, Any] = {}
    for name, cfg in specs.items():
        agree = 0
        total = 0
        for _ in range(n_sims):
            y = cfg["gen"]()
            # consenso simples: ADF/DFGLS sugerem unit root (não rejeitar),
            # KPSS sugere estacionariedade (não rejeitar H0 stationarity).
            unit_root_votes = 0
            if adf_unit_root(y, alpha): unit_root_votes += 1
            if dfgls_unit_root(y, alpha): unit_root_votes += 1
            stationary_vote = kpss_stationary(y, alpha)

            # decisão: unit root se (ADF ou DFGLS) votarem unit root e KPSS rejeitar estacionariedade
            # para smoke test, usar maioria simples: 2+ votos coerentes com expected
            predicted_unit_root = (unit_root_votes >= 1) and (not stationary_vote)
            # fallback: se conflito, usar regra: if unit_root_votes >= 2 → unit root
            if (unit_root_votes >= 2) and stationary_vote:
                predicted_unit_root = True

            expected = cfg["expected_unit_root"]
            if predicted_unit_root == expected:
                agree += 1
            total += 1

        results[name] = {
            "expected_unit_root": bool(specs[name]["expected_unit_root"]),
            "agreement_rate": agree / total,
            "T": T,
            "n_sims": n_sims,
        }

    return {"config": {"T": T, "n_sims": n_sims, "seed": seed, "alpha": alpha}, "results": results}

# ---------- Export ----------
def ensure_dir(path: str) -> None:
    if path: os.makedirs(path, exist_ok=True)

def write_json(obj: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_csv(mapping: Dict[str, Any], path: str) -> None:
    rows: List[Dict[str, Any]] = []
    for name, vals in mapping["results"].items():
        rows.append({"series": name, **vals})
    pd.DataFrame(rows).to_csv(path, index=False)

# ---------- CLI ----------
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Nelson–Plosser-style simulated benchmarks")
    ap.add_argument("--T", type=int, default=100)
    ap.add_argument("--n-sims", type=int, default=100)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", type=str, default="")
    return ap.parse_args()

def main() -> None:
    args = parse_args()
    ensure_dir(args.out_dir)

    res = run_benchmarks(args.T, args.n_sims, args.seed, args.alpha)
    print("[BENCHMARKS NP]", res["results"])
    if args.out_dir:
        write_json(res, os.path.join(args.out_dir, "benchmarks_results.json"))
        write_csv(res, os.path.join(args.out_dir, "benchmarks_results.csv"))

if __name__ == "__main__":
    main()
