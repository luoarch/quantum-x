#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
tests_scientific/size_power/test_size_power.py

Validação científica de size (erro tipo I) e power (potência) para ADF, DF-GLS e KPSS,
compatível com framework de Monte Carlo consolidado e com exportação de resultados.
"""

from __future__ import annotations
import os
import json
import argparse
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd

# Implementações validadas
from statsmodels.tsa.stattools import adfuller, kpss
from arch.unitroot import DFGLS

# ---------- Utils reproducibilidade ----------

def set_global_seed(seed: int = 42) -> None:
    np.random.seed(seed)

# ---------- Geradores de séries ----------

def generate_random_walk(T: int, sigma: float = 1.0) -> np.ndarray:
    eps = np.random.normal(0.0, sigma, T)
    return np.cumsum(eps)

def generate_ar1(T: int, phi: float, sigma: float = 1.0) -> np.ndarray:
    y = np.zeros(T)
    eps = np.random.normal(0.0, sigma, T)
    for t in range(1, T):
        y[t] = phi * y[t - 1] + eps[t]
    return y

# ---------- Wrappers de testes ----------

def run_adf(series: np.ndarray) -> Dict[str, Any]:
    stat, pvalue, usedlag, nobs, crit, icbest = adfuller(series, autolag="AIC", regression="c")
    return {"stat": float(stat), "pvalue": float(pvalue), "usedlag": int(usedlag)}

def run_dfgls(series: np.ndarray) -> Dict[str, Any]:
    res = DFGLS(series, trend="c")
    return {"stat": float(res.stat), "pvalue": float(res.pvalue), "lags": int(res.lags)}

def run_kpss_centered(series: np.ndarray) -> Dict[str, Any]:
    stat, pvalue, lags, crit = kpss(series, regression="c", nlags="auto")
    return {"stat": float(stat), "pvalue": float(pvalue), "lags": int(lags)}

# ---------- Experimentos de size/power ----------

@dataclass
class SizeConfig:
    T: int = 100
    n_sims: int = 1000
    alpha: float = 0.05
    seed: int = 42

@dataclass
class PowerConfig:
    T: int = 100
    n_sims: int = 1000
    alpha: float = 0.05
    phis: Tuple[float, ...] = (0.95, 0.90, 0.85, 0.80, 0.70, 0.50)
    seed: int = 42

def size_experiment(cfg: SizeConfig) -> Dict[str, Any]:
    set_global_seed(cfg.seed)
    rej_adf = rej_dfgls = rej_kpss = 0
    err_adf = err_dfgls = err_kpss = 0

    for _ in range(cfg.n_sims):
        # ADF/DFGLS: H0 = unit root -> gerar random walk
        rw = generate_random_walk(cfg.T)
        try:
            if run_adf(rw)["pvalue"] < cfg.alpha:
                rej_adf += 1
        except Exception:
            err_adf += 1
        try:
            if run_dfgls(rw)["pvalue"] < cfg.alpha:
                rej_dfgls += 1
        except Exception:
            err_dfgls += 1

        # KPSS: H0 = estacionária -> gerar AR(1) com |phi|<1
        ar = generate_ar1(cfg.T, phi=0.7)
        try:
            if run_kpss_centered(ar)["pvalue"] < cfg.alpha:
                rej_kpss += 1
        except Exception:
            err_kpss += 1

    valid_adf = cfg.n_sims - err_adf
    valid_dfgls = cfg.n_sims - err_dfgls
    valid_kpss = cfg.n_sims - err_kpss

    return {
        "config": asdict(cfg),
        "results": {
            "adf": {"rejection_rate": rej_adf / max(1, valid_adf), "errors": err_adf},
            "dfgls": {"rejection_rate": rej_dfgls / max(1, valid_dfgls), "errors": err_dfgls},
            "kpss": {"rejection_rate": rej_kpss / max(1, valid_kpss), "errors": err_kpss},
        },
        "expected_size": cfg.alpha,
    }

def power_experiment(cfg: PowerConfig) -> Dict[str, Any]:
    set_global_seed(cfg.seed)
    out: Dict[str, Any] = {"config": asdict(cfg), "results": {}}

    for phi in cfg.phis:
        rej_adf = rej_dfgls = 0
        err_adf = err_dfgls = 0

        for _ in range(cfg.n_sims):
            # H1: estacionário -> AR(1) com phi < 1
            series = generate_ar1(cfg.T, phi=float(phi))
            try:
                if run_adf(series)["pvalue"] < cfg.alpha:
                    rej_adf += 1
            except Exception:
                err_adf += 1
            try:
                if run_dfgls(series)["pvalue"] < cfg.alpha:
                    rej_dfgls += 1
            except Exception:
                err_dfgls += 1

        valid_adf = cfg.n_sims - err_adf
        valid_dfgls = cfg.n_sims - err_dfgls

        out["results"][f"phi_{phi:.2f}"] = {
            "adf_power": rej_adf / max(1, valid_adf),
            "dfgls_power": rej_dfgls / max(1, valid_dfgls),
            "errors_adf": err_adf,
            "errors_dfgls": err_dfgls,
        }

    return out

# ---------- Export helpers ----------

def ensure_out_dir(path: str) -> None:
    if path:
        os.makedirs(path, exist_ok=True)

def write_json(obj: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_csv_from_mapping(mapping: Dict[str, Any], path: str) -> None:
    # Achatar resultados para CSV
    rows: List[Dict[str, Any]] = []
    if "results" in mapping:
        res = mapping["results"]
        # size
        if all(k in res for k in ("adf", "dfgls", "kpss")):
            for test_name, v in res.items():
                rows.append({"test": test_name, **v})
        else:
            # power
            for key, v in res.items():
                rows.append({"hyp": key, **v})
    pd.DataFrame(rows).to_csv(path, index=False)

# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Size/Power Monte Carlo validation for unit-root tests")
    ap.add_argument("--mode", choices=["size", "power", "both"], required=True)
    ap.add_argument("--T", type=int, default=100)
    ap.add_argument("--n-sims", type=int, default=1000)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--phis", type=str, default="0.95,0.90,0.85,0.80,0.70,0.50")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", type=str, default="")
    return ap.parse_args()

def main() -> None:
    args = parse_args()
    ensure_out_dir(args.out_dir)

    if args.mode in ("size", "both"):
        size_cfg = SizeConfig(T=args.T, n_sims=args.n_sims, alpha=args.alpha, seed=args.seed)
        size_res = size_experiment(size_cfg)
        print("[SIZE] expected_alpha=", size_res["expected_size"], " results=", size_res["results"])
        if args.out_dir:
            write_json(size_res, os.path.join(args.out_dir, "size_results.json"))
            write_csv_from_mapping(size_res, os.path.join(args.out_dir, "size_results.csv"))

    if args.mode in ("power", "both"):
        phis = tuple(float(x) for x in args.phis.split(",") if x.strip())
        power_cfg = PowerConfig(T=args.T, n_sims=args.n_sims, alpha=args.alpha, phis=phis, seed=args.seed)
        power_res = power_experiment(power_cfg)
        print("[POWER]", power_res["results"])
        if args.out_dir:
            write_json(power_res, os.path.join(args.out_dir, "power_results.json"))
            write_csv_from_mapping(power_res, os.path.join(args.out_dir, "power_results.csv"))

if __name__ == "__main__":
    main()
