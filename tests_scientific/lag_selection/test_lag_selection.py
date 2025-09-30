#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import os
import json
import argparse
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.ar_model import AutoReg

# ---------- Utils ----------
def set_seed(seed: int = 42) -> None:
    np.random.seed(seed)

def schwert_Lmax(T: int) -> int:
    return int(np.floor(12 * (T / 100.0) ** 0.25))

def generate_ar(T: int, coeffs: List[float], sigma: float = 1.0) -> np.ndarray:
    p = len(coeffs)
    y = np.zeros(T)
    eps = np.random.normal(0.0, sigma, T)
    # warm-up
    for t in range(p):
        y[t] = eps[t]
    for t in range(p, T):
        y[t] = sum(coeffs[j] * y[t - j - 1] for j in range(p)) + eps[t]
    return y

# ---------- Seletores ----------
def select_lag_aic(series: np.ndarray, Lmax: int) -> int:
    best_aic, best_lag = np.inf, 0
    for L in range(0, Lmax + 1):
        try:
            res = AutoReg(series, lags=L, old_names=False).fit()
            aic = res.aic
            if aic < best_aic:
                best_aic, best_lag = aic, L
        except Exception:
            continue
    return best_lag

def select_lag_bic(series: np.ndarray, Lmax: int) -> int:
    best_bic, best_lag = np.inf, 0
    for L in range(0, Lmax + 1):
        try:
            res = AutoReg(series, lags=L, old_names=False).fit()
            bic = res.bic
            if bic < best_bic:
                best_bic, best_lag = bic, L
        except Exception:
            continue
    return best_lag

def select_lag_tstat(series: np.ndarray, Lmax: int, tau: float = 1.6) -> int:
    # backward elimination no último lag
    L = Lmax
    while L > 0:
        try:
            res = AutoReg(series, lags=L, old_names=False).fit()
            tvals = res.tvalues
            # último coeficiente corresponde ao último lag
            t_last = float(tvals.iloc[-1]) if hasattr(tvals, "iloc") else float(tvals[-1])
            if abs(t_last) >= tau:
                return L
        except Exception:
            pass
        L -= 1
    return 0

# ---------- Experimento ----------
def run_experiment(Ts: Tuple[int, ...], ps: Tuple[int, ...], n_sims: int, seed: int) -> Dict[str, Any]:
    set_seed(seed)
    results: Dict[str, Any] = {}
    distributions: Dict[str, Dict[str, List[int]]] = {}

    # coeficientes padrão por p
    coeff_map: Dict[int, List[float]] = {
        1: [0.7],
        2: [0.7, -0.2],
        3: [0.5, -0.2, 0.1],
        4: [0.5, -0.2, 0.1, -0.05],
    }

    for T in Ts:
        Lmax = max(1, schwert_Lmax(T))
        for p in ps:
            key = f"T_{T}_p_{p}"
            acc_exact = {"aic": 0, "bic": 0, "tstat": 0}
            acc_pm1 = {"aic": 0, "bic": 0, "tstat": 0}
            hist = {"aic": [], "bic": [], "tstat": []}
            coeffs = coeff_map[p]

            for _ in range(n_sims):
                y = generate_ar(T, coeffs)
                aic_L = select_lag_aic(y, Lmax)
                bic_L = select_lag_bic(y, Lmax)
                t_L = select_lag_tstat(y, Lmax)

                hist["aic"].append(aic_L)
                hist["bic"].append(bic_L)
                hist["tstat"].append(t_L)

                for name, Lsel in [("aic", aic_L), ("bic", bic_L), ("tstat", t_L)]:
                    if Lsel == p:
                        acc_exact[name] += 1
                    if abs(Lsel - p) <= 1:
                        acc_pm1[name] += 1

            results[key] = {
                "exact_accuracy": {k: v / n_sims for k, v in acc_exact.items()},
                "pm1_accuracy": {k: v / n_sims for k, v in acc_pm1.items()},
                "Lmax": Lmax,
            }
            distributions[key] = hist

    return {"config": {"Ts": Ts, "ps": ps, "n_sims": n_sims, "seed": seed}, "results": results, "distributions": distributions}

# ---------- Export ----------
def ensure_dir(path: str) -> None:
    if path: os.makedirs(path, exist_ok=True)

def write_json(obj: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_csv(mapping: Dict[str, Any], path: str) -> None:
    rows: List[Dict[str, Any]] = []
    for key, vals in mapping["results"].items():
        T = int(key.split("_")[1])
        p = int(key.split("_")[3])
        row = {"T": T, "p_true": p, "Lmax": vals["Lmax"]}
        row.update({f"exact_{k}": v for k, v in vals["exact_accuracy"].items()})
        row.update({f"pm1_{k}": v for k, v in vals["pm1_accuracy"].items()})
        rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)

# ---------- CLI ----------
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Lag selection validation (AIC, BIC, t-stat, Schwert)")
    ap.add_argument("--Ts", type=str, default="50,100,200")
    ap.add_argument("--ps", type=str, default="1,2,3,4")
    ap.add_argument("--n-sims", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", type=str, default="")
    return ap.parse_args()

def main() -> None:
    args = parse_args()
    Ts = tuple(int(x) for x in args.Ts.split(",") if x.strip())
    ps = tuple(int(x) for x in args.ps.split(",") if x.strip())
    ensure_dir(args.out_dir)

    res = run_experiment(Ts, ps, args.n_sims, args.seed)
    print("[LAG SELECTION]", {k: v["exact_accuracy"] for k, v in res["results"].items()})
    if args.out_dir:
        write_json(res, os.path.join(args.out_dir, "lag_selection_results.json"))
        write_csv(res, os.path.join(args.out_dir, "lag_selection_results.csv"))
        write_json(res["distributions"], os.path.join(args.out_dir, "lag_distributions.json"))

if __name__ == "__main__":
    main()
