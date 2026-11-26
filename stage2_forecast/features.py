# -*- coding: utf-8 -*-
"""Forecasting panel (locality x year, agritourism guesthouses) and its 14 features.

Target:  y = ln(1 + N), N = overnight stays in the agritourism guesthouses of a locality in a year.
A row exists only if the locality has, in that year, positive capacity, arrivals and overnight stays (292 observations, 2001-2025).
Features based on the history of a locality use earlier years only, so no future information enters.
"""
import numpy as np

from common.tempo import AGRO, YEARS, load_panel

FEATURES = ["trend", "crisis_dummy", "pandemic_dummy", "log_capacity_agro", "years_of_experience",
            "log_capacity_county", "log_overnight_county", "agro_share_county_capacity", "hist_mean_log_overnight",
            "hist_mean_occupancy", "hist_mean_stay", "has_lag", "lag1_log_overnight", "lag1_log_capacity"]
HISTORY = ["hist_mean_log_overnight", "hist_mean_occupancy", "hist_mean_stay", "lag1_log_overnight", "lag1_log_capacity"]
CRISIS_YEARS = (2008, 2009, 2010)   # see README, "Differences between the article and this implementation"
TRAIN_LAST_YEAR = 2019              # training 2001-2019, test 2020-2025
VALID_FIRST_YEAR = 2017             # early-stopping validation window 2017-2019 (inside the training period)


def build_panel(crisis_years=CRISIS_YEARS):
    PC, PS, PN = (load_panel(k) for k in "CSN")
    CT, NT = PC[("Total", "TOTAL")], PN[("Total", "TOTAL")]
    CA = np.nan_to_num(PC[(AGRO, "TOTAL")])
    rows = []
    for (t, u), c in PC.items():
        if t != AGRO or u == "TOTAL":
            continue
        s, n = PS[(t, u)], PN[(t, u)]
        ok = [i for i in range(len(YEARS)) if c[i] > 0 and s[i] > 0 and n[i] > 0]
        prev = []
        for i in ok:
            r = {"locality": u, "year": YEARS[i], "C": c[i], "S": s[i], "N": n[i]}
            r["trend"] = i
            r["crisis_dummy"] = 1.0 if YEARS[i] in crisis_years else 0.0
            r["pandemic_dummy"] = 1.0 if YEARS[i] in (2020, 2021) else 0.0
            r["log_capacity_agro"] = np.log(c[i])
            r["years_of_experience"] = float(len(prev))
            r["log_capacity_county"] = np.log(CT[i]); r["log_overnight_county"] = np.log(NT[i])
            r["agro_share_county_capacity"] = 100 * CA[i] / CT[i]
            if prev:
                r["hist_mean_log_overnight"] = np.mean([np.log1p(p["N"]) for p in prev])
                r["hist_mean_occupancy"] = np.mean([100 * p["N"] / p["C"] for p in prev])
                r["hist_mean_stay"] = np.mean([p["N"] / p["S"] for p in prev])
            else:
                for k in HISTORY[:3]:
                    r[k] = np.nan
            last = prev[-1] if prev else None
            if last is not None and last["year"] == YEARS[i] - 1:
                r["has_lag"] = 1.0; r["lag1_log_overnight"] = np.log1p(last["N"]); r["lag1_log_capacity"] = np.log(last["C"])
            else:
                r["has_lag"] = 0.0; r["lag1_log_overnight"] = np.nan; r["lag1_log_capacity"] = np.nan
            r["y"] = np.log1p(n[i])
            rows.append(r); prev.append(r)
    rows.sort(key=lambda r: (r["year"], r["locality"]))
    return rows


def to_matrix(rows, fill):
    """Feature matrix; missing history features are filled with the means computed on the training rows (`fill`)."""
    X = np.array([[r[f] for f in FEATURES] for r in rows], float)
    for j, f in enumerate(FEATURES):
        if f in fill:
            m = np.isnan(X[:, j]); X[m, j] = fill[f]
    return X


def train_fill(training_rows):
    return {f: float(np.nanmean([r[f] for r in training_rows])) for f in HISTORY}
