#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
tests_scientific/small_samples/test_small_samples.py

Validação de testes de raiz unitária em amostras pequenas, replicando o padrão do pacote size_power.
"""

from __future__ import annotations
import os
import json
import argparse
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss
from arch.unitroot import DFGLS

# ---------- Utils ----------
def set_seed(seed: int = 42) -> None:
    np.random.seed(seed)

def generate_random_walk(T: int, sigma: float = 1.0) -> np.ndarray:
    eps = np.random.normal(0.0, sigma, T)
    return np.cumsum(eps)

def generate_ar1(T: int, phi: float, sigma: float = 1.0) -> np.ndarray:
    y = np.zeros(T)
    eps = np.random.normal(0.0, sigma, T)
    for t in range(1, T):
        y[t] = phi * y[t - 1] + eps[t]
    return y

def run_adf(series: np.ndarray) -> Dict[str, Any]:
    stat, pvalue, usedlag, nobs, crit, icbest = adfuller(series, autolag="AIC", regression="c")
    return {"pvalue": float(pvalue)}

def run_dfgls(series: np.ndarray) -> Dict[str, Any]:
    res = DFGLS(series, trend="c")
    return {"pvalue": float(res.pvalue)}

def run_kpss_c(series: np.ndarray) -> Dict[str, Any]:
    stat, pvalue, lags, crit = kpss(series, regression="c", nlags="auto")
    return {"pvalue": float(pvalue)}

# ---------- Experimentos ----------
def size_small(Ts: Tuple[int, ...], n_sims: int, alpha: float, seed: int) -> Dict[str, Any]:
    set_seed(seed)
    out: Dict[str, Any] = {"config": {"Ts": Ts, "n_sims": n_sims, "alpha": alpha, "seed": seed}, "results": {}}
    for T in Ts:
        rej_adf = rej_dfgls = rej_kpss = 0
        for _ in range(n_sims):
            rw = generate_random_walk(T)                  # H0 para ADF/DFGLS
            if run_adf(rw)["pvalue"] < alpha: rej_adf += 1
            if run_dfgls(rw)["pvalue"] < alpha: rej_dfgls += 1
            ar = generate_ar1(T, phi=0.7)                 # H0 para KPSS
            if run_kpss_c(ar)["pvalue"] < alpha: rej_kpss += 1
        out["results"][f"T_{T}"] = {
            "adf_size": rej_adf / n_sims,
            "dfgls_size": rej_dfgls / n_sims,
            "kpss_size": rej_kpss / n_sims,
        }
    return out

def power_small(Ts: Tuple[int, ...], n_sims: int, alpha: float, phis: Tuple[float, ...], seed: int) -> Dict[str, Any]:
    set_seed(seed)
    out: Dict[str, Any] = {"config": {"Ts": Ts, "n_sims": n_sims, "alpha": alpha, "phis": phis, "seed": seed}, "results": {}}
    for T in Ts:
        res_T: Dict[str, Any] = {}
        for phi in phis:
            rej_adf = rej_dfgls = 0
            for _ in range(n_sims):
                series = generate_ar1(T, phi=float(phi))  # H1 para ADF/DFGLS
                if run_adf(series)["pvalue"] < alpha: rej_adf += 1
                if run_dfgls(series)["pvalue"] < alpha: rej_dfgls += 1
            res_T[f"phi_{phi:.2f}"] = {
                "adf_power": rej_adf / n_sims,
                "dfgls_power": rej_dfgls / n_sims,
            }
        out["results"][f"T_{T}"] = res_T
    return out

# ---------- Export ----------
def ensure_dir(p: str) -> None:
    if p: os.makedirs(p, exist_ok=True)

def write_json(obj: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_size_csv(mapping: Dict[str, Any], path: str) -> None:
    rows: List[Dict[str, Any]] = []
    for T_key, vals in mapping["results"].items():
        row = {"T": int(T_key.split("_")[1]), **vals}
        rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)

def write_power_csv(mapping: Dict[str, Any], path: str) -> None:
    rows: List[Dict[str, Any]] = []
    for T_key, m in mapping["results"].items():
        T = int(T_key.split("_")[1])
        for phi_key, vals in m.items():
            phi = float(phi_key.split("_")[1])
            rows.append({"T": T, "phi": phi, **vals})
    pd.DataFrame(rows).to_csv(path, index=False)

# ---------- CLI ----------
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Small-sample validation for unit-root tests")
    ap.add_argument("--mode", choices=["size", "power", "both"], required=True)
    ap.add_argument("--Ts", type=str, default="25,50,75,100")
    ap.add_argument("--n-sims", type=int, default=1000)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--phis", type=str, default="0.95,0.90,0.85,0.80")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", type=str, default="")
    return ap.parse_args()

def main() -> None:
    args = parse_args()
    Ts = tuple(int(x) for x in args.Ts.split(",") if x.strip())
    phis = tuple(float(x) for x in args.phis.split(",") if x.strip())
    ensure_dir(args.out_dir)

    if args.mode in ("size", "both"):
        size_res = size_small(Ts, args.n_sims, args.alpha, args.seed)
        print("[SMALL SIZE]", size_res["results"])
        if args.out_dir:
            write_json(size_res, os.path.join(args.out_dir, "small_size_results.json"))
            write_size_csv(size_res, os.path.join(args.out_dir, "small_size_results.csv"))

    if args.mode in ("power", "both"):
        power_res = power_small(Ts, args.n_sims, args.alpha, phis, args.seed)
        print("[SMALL POWER]", power_res["results"])
        if args.out_dir:
            write_json(power_res, os.path.join(args.out_dir, "small_power_results.json"))
            write_power_csv(power_res, os.path.join(args.out_dir, "small_power_results.csv"))

if __name__ == "__main__":
    main()
