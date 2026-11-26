# -*- coding: utf-8 -*-
"""System dynamics Model 2 (exploratory, Section 5.3 of the article): residents' acceptance of digital technologies (ACC)
and community quality of life (QOL), coupled with the capacity trajectory of Model 1.

This is a scenario model, not a forecast: no local series of quality of life or acceptance exists, and the parameters
marked "assumption" below are chosen values. Monetary values are in constant 2025 RON.
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.tempo import AGRO, load_panel
import sd1_model as M1

# Life satisfaction in Romania on a 1-10 scale (Eurofound, European Quality of Life Survey): 6.1 in 2003 and 6.5 in 2016.
QOL_2003, QOL_2016 = 6.1, 6.5
KAPPA = math.log(QOL_2016 / QOL_2003) / 13.0          # observed annual growth rate (applies at full acceptance), about 0.49% per year

DEFAULTS = dict(
    p_r=0.01, q_r=0.15,      # assumption: spontaneous adoption and social imitation
    r_r=0.08,                # assumption: resistance to tourism pressure
    gamma_eff=0.01,          # assumption: sensitivity of quality of life to the investment ratio
    lam0=0.01,               # assumption: annual decline of quality of life at zero acceptance
    g_budget=0.0, tax=0.02, eff=1.0, budget25=1.5e9, spend=500.0,   # assumptions: budget, tax share, efficiency, spend per trip
    acc0=0.3184,             # share of persons with at least basic digital skills in Romania (proxy)
    qol0=6.5, start=2025, horizon=20, acc_frozen=False)


def lam(acc, lam0=None):
    """Annual rate of decline of QOL, linear in acceptance: lam0 at ACC = 0 and -KAPPA (growth) at ACC = 1."""
    l0 = DEFAULTS["lam0"] if lam0 is None else lam0
    return l0 - (l0 + KAPPA) * acc


def acc_neutral(lam0=None):
    """Acceptance threshold above which quality of life increases."""
    l0 = DEFAULTS["lam0"] if lam0 is None else lam0
    return l0 / (l0 + KAPPA)


def agro_series(sd1_params=None, demand_growth=0.0, horizon_year=2060):
    """Agritourism capacity (simulated trajectory of Model 1) and arrivals (observed until 2025, then proportional to capacity)."""
    arrivals_obs = np.nan_to_num(load_panel("S")[(AGRO, "TOTAL")])
    s1 = M1.simulate(sd1_params, horizon=horizon_year - 2001, demand_growth=demand_growth)
    capacity = np.asarray(s1["CA"][:horizon_year - 2001 + 1], dtype=float)
    ratio = arrivals_obs[24] / M1.real_series()["CA"][24]
    arrivals = np.concatenate([arrivals_obs, capacity[25:] * ratio])
    return dict(years=np.arange(2001, horizon_year + 1), CA=capacity, S=arrivals)


def simulate(changes=None, series=None):
    P = {**DEFAULTS, **(changes or {})}
    A = series or agro_series()
    year0 = P["start"]; n = P["horizon"] + 1; i0 = year0 - 2001
    ca_ref = A["CA"][i0]
    acc = np.zeros(n + 1); qol = np.zeros(n + 1)
    acc[0], qol[0] = P["acc0"], P["qol0"]
    keys = ("year", "budget", "tourism_spending", "effective_budget", "investment_ratio", "pressure", "d_acc", "lam", "lam_effective", "resistance")
    out = {k: np.zeros(n) for k in keys}
    for k in range(n):
        year = year0 + k
        budget = P["budget25"] * (1 + P["g_budget"]) ** (year - year0)
        spending = A["S"][i0 + k] * P["spend"]
        effective = budget + P["tax"] * spending
        ratio = P["eff"] * effective / P["budget25"]
        pressure = A["CA"][i0 + k] / ca_ref
        resistance = P["r_r"] * max(pressure - 1, 0) * acc[k]
        d_acc = 0.0 if P["acc_frozen"] else (P["p_r"] * (1 - acc[k]) + P["q_r"] * acc[k] * (1 - acc[k]) - resistance)
        l = lam(acc[k], P["lam0"]); l_eff = l + P["gamma_eff"] * (1 - ratio)
        acc[k + 1] = min(max(acc[k] + d_acc, 0.0), 1.0)
        qol[k + 1] = qol[k] * math.exp(-l_eff)
        for key, v in zip(keys, (year, budget, spending, effective, ratio, pressure, d_acc, l, l_eff, resistance)):
            out[key][k] = v
    out["acc"], out["qol"] = acc[:n], qol[:n]
    return out


SCENARIOS = [("baseline", {}), ("rapid diffusion", dict(p_r=0.03, q_r=0.38)), ("information campaign", dict(p_r=0.02, q_r=0.225)),
             ("high resistance", dict(r_r=0.24)), ("investment efficiency 70%", dict(eff=0.7)), ("no diffusion of acceptance", dict(acc_frozen=True))]
