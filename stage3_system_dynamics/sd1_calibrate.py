# -*- coding: utf-8 -*-
"""Calibration of Model 1 on the INS series 2001-2025: random search followed by Nelder-Mead with restarts (Equation 17).

Objective: weighted sum of squared differences between the logarithms of simulated and observed values of hotel capacity (2.0),
hotel overnight stays (1.5), agritourism capacity (1.0) and agritourism overnight stays (1.0).
The reputation scale is normalised (M = 1) because M and gamma cannot be identified separately.

Usage:  python stage3_system_dynamics/sd1_calibrate.py <seed> <random draws> [--wide] [--occupancy-term] [--no-shocks] [--unweighted]
        The article uses:  <seed> 30000 --wide   (three seeds)
Output: results/calibration_<variant>_<seed>.json
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.paths import SD_RESULTS, ensure
import sd1_model as M

X = M.real_series()
NAMES = ["A0", "p", "q", "bH", "gamma", "delta", "dH", "KA", "shockH2020", "shockH2021", "shockA2020", "shockA2021"]
LOW = [0.02, 0.0005, 0.02, 0.02, 0.0, 0.0, 0.02, 600000, -0.50, -0.10, -0.30, -0.10]
HIGH = [2.0, 0.10, 0.45, 2.0, 2.0e6, 1.0, 0.35, 3.0e6, 0.10, 0.50, 0.10, 0.40]
FLAGS = set(sys.argv[1:])
if "--wide" in FLAGS:      # widened bounds, to check whether the optimum lies on a bound
    HIGH[2] = 1.0                      # q
    LOW[7] = 480000                    # K_A (above the largest observed capacity, 472,302)
    LOW[8:12] = [-0.5] * 4; HIGH[8:12] = [0.5] * 4
if "--no-shocks" in FLAGS:             # variant without the 2020-2021 shock terms
    NAMES, LOW, HIGH = NAMES[:8], LOW[:8], HIGH[:8]
if "--occupancy-term" in FLAGS:        # extended variant: investment also depends on current occupancy (beta_A)
    NAMES, LOW, HIGH = NAMES + ["bA"], LOW + [0.0], HIGH + [5.0]
LOW, HIGH = np.array(LOW, float), np.array(HIGH, float)
LOGSCALE = {"A0", "p", "gamma", "KA"}
WEIGHTS = dict(CH=1.0, NH=1.0, CA=1.0, NA=1.0) if "--unweighted" in FLAGS else dict(CH=2.0, NH=1.5, CA=1.0, NA=1.0)
FIXED = dict(M=1.0, bA=0.0)


def to_dict(v):
    return {**FIXED, **dict(zip(NAMES, v))}


def objective(v):
    pen = 0.0
    for x, lo, hi in zip(v, LOW, HIGH):
        if x < lo: pen += ((lo - x) / (hi - lo)) ** 2 * 1e4
        if x > hi: pen += ((x - hi) / (hi - lo)) ** 2 * 1e4
    clipped = np.clip(v, LOW, HIGH)
    s = M.simulate(to_dict(clipped), horizon=24, exog=X, shocks="--no-shocks" not in FLAGS)
    total = 0.0
    for key, w in WEIGHTS.items():
        a, b = np.log(np.maximum(s[key][:25], 1.0)), np.log(np.maximum(X[key], 1.0))
        total += w * np.sum((a - b) ** 2)
    return float(total) + pen if np.isfinite(total) else 1e9


def sample(rng):
    u = rng.random(len(NAMES)); v = np.empty(len(NAMES))
    for i, n in enumerate(NAMES):
        if n in LOGSCALE:
            lo = max(LOW[i], 1e-6)
            v[i] = np.exp(np.log(lo) + u[i] * (np.log(HIGH[i]) - np.log(lo)))
        else:
            v[i] = LOW[i] + u[i] * (HIGH[i] - LOW[i])
    return v


def search(rng, n_random, n_starts):
    """Random search, then three consecutive Nelder-Mead runs from each of the n_starts best draws."""
    cand = sorted(((objective(v), v) for v in (sample(rng) for _ in range(n_random))), key=lambda z: z[0])
    best = cand[0]
    for k in range(n_starts):
        x0 = cand[k][1]
        for _ in range(3):
            r = minimize(objective, x0, method="Nelder-Mead", options=dict(maxiter=8000, maxfev=8000, xatol=1e-7, fatol=1e-8, adaptive=True))
            x0 = r.x
        if r.fun < best[0]:
            best = (r.fun, r.x)
    return float(best[0]), to_dict(np.clip(best[1], LOW, HIGH))


if __name__ == "__main__":
    seed, n_random = int(sys.argv[1]), int(sys.argv[2])
    variant = "occupancy_term" if "--occupancy-term" in FLAGS else "no_shocks" if "--no-shocks" in FLAGS else "base"
    t0 = time.time()
    value, params = search(np.random.default_rng(seed), n_random, 10)
    s = M.simulate(params, horizon=24, exog=X, shocks="--no-shocks" not in FLAGS)
    fit = {k: {"r2": M.r2(X[k], s[k][:25]), "rmse": M.rmse(X[k], s[k][:25])} for k in ("CH", "CA", "NH", "NA")}
    print(variant, "seed", seed, "| weighted log-error", round(value, 4), "|", round(time.time() - t0), "s")
    print(json.dumps({k: round(float(v), 5) for k, v in params.items()}))
    out = ensure(SD_RESULTS) / f"calibration_{variant}_{seed}.json"
    json.dump({"objective": value, "params": {k: float(v) for k, v in params.items()}, "fit": fit}, open(out, "w"), indent=1)
