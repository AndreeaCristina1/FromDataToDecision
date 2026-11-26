# -*- coding: utf-8 -*-
"""System dynamics Model 1: hotel and agritourism capacity in Gorj County (Section 3.5, Equations 10-16 of the article).

Stocks: CH (hotel capacity), CA (agritourism capacity), REP (accumulated reputation of agritourism, 0-1).
Exogenous: total demand D_t (observed county overnight stays) and the capacity of the other accommodation types.
Annual step; t = 0 is the year 2001.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.tempo import AGRO, HOTELS, load_panel

# Parameters calibrated on the INS series 2001-2025 (see sd1_calibrate.py, option --wide).
PARAMS = dict(A0=0.31739, M=1.0, p=0.01063, q=1.0, bH=1.38773, gamma=80622.07, delta=0.40022, dH=0.32805, dA=0.0, KA=531348.70,
              shockH2020=0.15244, shockH2021=0.34400, shockA2020=0.02654, shockA2021=-0.14985,
              rep0=0.0, pol_k=0.4, pol_mid=12.5,      # fixed: slope and midpoint (mid-2013) of the policy ramp
              bA=0.0)                                  # coefficient of the occupancy term of the extended variant (not used)


def real_series():
    PC, PN = load_panel("C"), load_panel("N")
    g = lambda P, t: np.nan_to_num(P[(t, "TOTAL")])
    Ct, Nt = g(PC, "Total"), g(PN, "Total")
    CH, CA, NH, NA = g(PC, HOTELS), g(PC, AGRO), g(PN, HOTELS), g(PN, AGRO)
    return dict(Ct=Ct, Nt=Nt, CH=CH, CA=CA, NH=NH, NA=NA, COther=Ct - CH - CA)


def policy(t, k=0.4, mid=12.5):
    return 1.0 / (1.0 + np.exp(-k * (t - mid)))


def simulate(P=None, horizon=24, demand_growth=0.0, shocks=True, exog=None, start_year=2001):
    """Simulate t = 0..horizon. Until 2025 demand and other structures are the observed ones; afterwards demand grows by
    demand_growth per year and the capacity of the other structures is held constant. Returns a dict of series."""
    P = {**PARAMS, **(P or {})}
    X = exog or real_series()
    n = horizon + 1
    CH = np.zeros(n + 1); CA = np.zeros(n + 1); REP = np.zeros(n + 1)
    CH[0], CA[0], REP[0] = X["CH"][0], X["CA"][0], P["rep0"]
    out = {k: np.zeros(n) for k in ("NH", "NA", "occH", "occA", "shareH", "shareA", "invA", "invH", "depH", "dREP", "pol", "demand", "COther")}
    for t in range(n):
        if t < 25:
            demand, other = X["Nt"][t], X["COther"][t]
        else:
            demand = X["Nt"][24] * (1 + demand_growth) ** (t - 24); other = X["COther"][24]
        att = P["A0"] * (1 + REP[t] / P["M"])                                                   # Eq. 10
        den = CH[t] + CA[t] * att + other
        shH, shA = CH[t] / den, CA[t] * att / den                                               # Eq. 11
        NH, NA = shH * demand, shA * demand
        occH = NH / CH[t]
        dREP = P["p"] * (P["M"] - REP[t]) + P["q"] * REP[t] * (P["M"] - REP[t]) / P["M"]        # Eq. 12
        pol = policy(t, P["pol_k"], P["pol_mid"])                                               # Eq. 13
        room = max(1.0 - CA[t] / P["KA"], 0.0)
        invA = (P["gamma"] * dREP + P["delta"] * pol * CA[t] + P["bA"] * NA) * room             # Eq. 14 (bA = 0)
        invH = P["bH"] * occH * CH[t]; depH = P["dH"] * CH[t]; depA = P["dA"] * CA[t]
        sH = sA = 0.0
        if shocks:
            year = start_year + t
            sH = {2020: P["shockH2020"], 2021: P["shockH2021"]}.get(year, 0.0)
            sA = {2020: P["shockA2020"], 2021: P["shockA2021"]}.get(year, 0.0)
        CH[t + 1] = CH[t] + invH - depH + sH * CH[t]                                            # Eq. 16
        CA[t + 1] = CA[t] + invA - depA + sA * CA[t]                                            # Eq. 15
        REP[t + 1] = min(REP[t] + dREP, P["M"])
        for k, v in (("NH", NH), ("NA", NA), ("occH", occH), ("occA", NA / CA[t]), ("shareH", shH), ("shareA", shA), ("invA", invA),
                     ("invH", invH), ("depH", depH), ("dREP", dREP), ("pol", pol), ("demand", demand), ("COther", other)):
            out[k][t] = v
    out.update(CH=CH[:n], CA=CA[:n], REP=REP[:n])
    return out


def r2(y, f):
    y, f = np.asarray(y, float), np.asarray(f, float)
    return float(1 - ((y - f) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def rmse(y, f):
    return float(np.sqrt(np.mean((np.asarray(y, float) - np.asarray(f, float)) ** 2)))


if __name__ == "__main__":
    X = real_series(); s = simulate()
    for k in ("CH", "CA", "NH", "NA"):
        print(f"{k}: R2 = {r2(X[k], s[k][:25]):.3f}  RMSE = {rmse(X[k], s[k][:25]):,.0f}")
    print("CA 2025 simulated:", round(s["CA"][24]), "| observed:", round(X["CA"][24]))
