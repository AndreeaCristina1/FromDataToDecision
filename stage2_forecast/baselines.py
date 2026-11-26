# -*- coding: utf-8 -*-
"""Stage 2: the five baselines compared with gradient boosting (Table 4 of the article), plus forecast diagnostics.

  naive                   last year's value of the locality (training mean if there is none)
  naive_capacity          naive plus the change in log capacity, y(t-1) + b (ln C(t) - ln C(t-1)), with b = 1
  capacity_regression     OLS of ln(1+N) on ln C, estimated on 2001-2019
  linear_regression_14    OLS on the 14 features
  ARI_3_1                 autoregression on the first differences of the county series (county level only)

Usage:  python stage2_forecast/baselines.py      (run after train_gbm.py)
Output: results/forecast_comparison.json, results/diagnostics.json
"""
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.paths import STAGE2_RESULTS, ensure, utf8_console, write_json
from common.tempo import YEARS, split_locality
import features as F
import train_gbm as T
from ml_core import rmse, mae, r2, ols_fit, ols_predict

TEST_YEARS = list(range(2020, 2026))


def previous_year_values(rows):
    """For each row: (y, ln C) of the same locality in the immediately preceding year, or NaN."""
    lag_y = np.full(len(rows), np.nan); lag_c = np.full(len(rows), np.nan)
    last = {}
    for i, r in enumerate(rows):
        p = last.get(r["locality"])
        if p is not None and p[0] == r["year"] - 1:
            lag_y[i], lag_c[i] = p[1], p[2]
        last[r["locality"]] = (r["year"], r["y"], r["log_capacity_agro"])
    return lag_y, lag_c


def main():
    utf8_console()
    out = ensure(STAGE2_RESULTS)
    rows = F.build_panel()
    y = np.array([r["y"] for r in rows]); year = np.array([r["year"] for r in rows])
    N = np.array([r["N"] for r in rows]); C = np.array([r["C"] for r in rows])
    loc = np.array([r["locality"] for r in rows])
    itr = year <= F.TRAIN_LAST_YEAR; ite = ~itr
    logc = np.log(C)
    mean_tr = float(y[itr].mean())
    lag_y, lag_c = previous_year_values(rows)
    ok = ~np.isnan(lag_y)

    pred = {}
    pred["naive"] = np.where(ok, lag_y, mean_tr)
    pred["naive_capacity"] = np.where(ok, lag_y + (logc - lag_c), mean_tr)
    coef1 = ols_fit(logc[itr, None], y[itr])
    pred["capacity_regression"] = ols_predict(logc[:, None], coef1)
    X = F.to_matrix(rows, F.train_fill([r for r, m in zip(rows, itr) if m]))
    coef14 = ols_fit(X[itr], y[itr])
    pred["linear_regression_14"] = ols_predict(X, coef14)
    _, n_trees, _ = T.fit_early_stopping(rows)
    gbm, Xg, _ = T.fit_final(rows, n_trees)
    pred["gradient_boosting"] = gbm.predict(Xg)

    actual = np.array([N[year == k].sum() for k in TEST_YEARS])
    R = {"n_training": int(itr.sum()), "n_test": int(ite.sum()), "county_observed_2020_2025": actual, "locality_year": {}, "county": {}}
    for name, p in pred.items():
        R["locality_year"][name] = {"training": T.metrics(y[itr], p[itr]), "test": T.metrics(y[ite], p[ite])}
        a = np.array([np.expm1(p[year == k]).sum() for k in TEST_YEARS])
        R["county"][name] = {"forecast": a, "rmse": rmse(actual, a), "mae": mae(actual, a), "r2": r2(actual, a)}

    # ARI(3,1) on the county series, estimated on 2001-2019
    allN = np.array([N[year == k].sum() for k in YEARS], float)
    d = np.diff(allN[:19]); p_ = 3
    Xr = np.array([[1.0] + [d[i - k] for k in range(1, p_ + 1)] for i in range(p_, len(d))])
    co, *_ = np.linalg.lstsq(Xr, d[p_:], rcond=None)
    hist = list(d); level = allN[18]; fc = []
    for _ in TEST_YEARS:
        step = float(np.dot(co, [1.0] + [hist[-k] for k in range(1, p_ + 1)])); hist.append(step); level += step; fc.append(level)
    R["county"]["ARI_3_1"] = {"forecast": fc, "rmse": rmse(actual, fc), "mae": mae(actual, fc), "r2": r2(actual, fc)}
    write_json(out / "forecast_comparison.json", R)

    # ------------------------------------------------------------ diagnostics quoted in Section 4.2
    obs = N.astype(float); fit = np.expm1(pred["gradient_boosting"])
    names = np.array([split_locality(u)[1] for u in loc])
    te_loc = sorted(set(loc[ite]))
    mean_obs = np.array([obs[ite & (loc == u)].mean() for u in te_loc])
    mean_fit = np.array([fit[ite & (loc == u)].mean() for u in te_loc])
    cold = np.array([u not in set(loc[itr]) for u in te_loc])
    rel = 100 * np.abs(mean_fit - mean_obs) / mean_obs
    mtr = ok & itr
    b_fit = float(np.sum((y - lag_y)[mtr] * (logc - lag_c)[mtr]) / np.sum((logc - lag_c)[mtr] ** 2))
    p_fit = np.where(ok, lag_y + b_fit * (logc - lag_c), mean_tr)
    median_capacity = float(np.median(C))   # large / small: test observations above / below the median capacity of the panel
    groups = {}
    for label, m in (("large", ite & (C > median_capacity)), ("small", ite & (C <= median_capacity))):
        groups[label] = {"n": int(m.sum()), "r2_log": r2(y[m], pred["gradient_boosting"][m]),
                         "median_abs_relative_error_pct": float(100 * np.median(np.abs(fit[m] - obs[m]) / obs[m]))}
    skew = lambda v: float(stats.skew(v))
    D = {
        "skewness_nights": skew(obs), "skewness_log": skew(y),
        "n_observations": len(rows), "n_localities": len(set(loc)), "n_localities_training": len(set(loc[itr])),
        "n_localities_test": len(te_loc), "n_localities_without_training_data": int(cold.sum()),
        "test_mean_nights": float(obs[ite].mean()),
        "underestimation_pct_of_observed": float(100 * (obs[ite].sum() - fit[ite].sum()) / obs[ite].sum()),
        "share_observed_BaiaDeFier_Runcu_pct": float(100 * obs[ite & np.isin(names, ["Baia de Fier", "Runcu"])].sum() / obs[ite].sum()),
        "training_obs_above_14000": int((obs[itr] > 14000).sum()), "test_obs_above_14000": int((obs[ite] > 14000).sum()),
        "max_training_capacity": float(C[itr].max()),
        "test_obs_above_14000_and_above_training_capacity": int(((obs > 14000) & (C > C[itr].max()) & ite).sum()),
        "max_prediction_test": float(fit[ite].max()),
        "spearman_locality_means": float(stats.spearmanr(mean_obs, mean_fit)[0]),
        "median_rel_error_localities_without_training_pct": float(np.median(rel[cold])),
        "median_rel_error_other_localities_pct": float(np.median(rel[~cold])),
        "large_small_threshold_median_capacity": median_capacity, "groups": groups,
        "elasticity_full_panel": float(ols_fit(logc[:, None], y)[1]),
        "elasticity_regression_14": float(coef14[1 + F.FEATURES.index("log_capacity_agro")]),
        "elasticity_capacity_regression": float(coef1[1]),
        "naive_capacity_fitted_elasticity": b_fit, "naive_capacity_fitted_test_rmse_log": rmse(y[ite], p_fit[ite]),
        "county_mean_observed_2020_2025": float(actual.mean()),
        "gbm_years_with_county_underestimate": int((R["county"]["gradient_boosting"]["forecast"] < actual).sum()),
    }
    write_json(out / "diagnostics.json", D)

    print(f"{'model':<22}{'RMSE log':>10}{'R2 log':>9}{'RMSE nights':>13}{'RMSE county':>13}")
    for name in pred:
        t = R["locality_year"][name]["test"]
        print(f"{name:<22}{t['rmse_log']:>10.3f}{t['r2_log']:>9.3f}{t['rmse_nights']:>13.0f}{R['county'][name]['rmse']:>13.0f}")
    print(f"{'ARI(3,1)':<22}{'':>10}{'':>9}{'':>13}{R['county']['ARI_3_1']['rmse']:>13.0f}")


if __name__ == "__main__":
    main()
