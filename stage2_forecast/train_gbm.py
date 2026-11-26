# -*- coding: utf-8 -*-
"""Stage 2, main model: stochastic gradient boosting for ln(1 + overnight stays) in agritourism guesthouses, by locality and year.

  1. locality x year panel with 14 features (features.py); training 2001-2019, test 2020-2025;
  2. number of trees chosen by early stopping: fit on 2001-2016, validate on 2017-2019, patience 25 iterations;
  3. final model refitted on 2001-2019 with that number of trees and evaluated on 2020-2025;
  4. sensitivity to hyperparameters: six configurations (depth, learning rate, subsampling).

Usage:  python stage2_forecast/train_gbm.py
Output: stage2_forecast/results/gbm_*.json / .csv
"""
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.paths import STAGE2_RESULTS, ensure, utf8_console, write_json
from common.tempo import split_locality
import features as F
from ml_core import GradientBoostingRegressor, rmse, mae, r2

HYPER = dict(learning_rate=0.05, max_depth=3, min_samples_leaf=6, subsample=0.8, random_state=42)
MAX_TREES = 300
EARLY_STOP = 25


def prepare(rows, fill_mask):
    """Feature matrix; missing values are filled with means computed ONLY on the rows selected by fill_mask."""
    return F.to_matrix(rows, F.train_fill([r for r, m in zip(rows, fill_mask) if m]))


def fit_early_stopping(rows, hyper=None):
    """Fit on 2001-2016, validate on 2017-2019; return the model, the chosen number of trees and the validation scores."""
    h = {**HYPER, **(hyper or {})}
    year = np.array([r["year"] for r in rows]); y = np.array([r["y"] for r in rows])
    fit_m = year < F.VALID_FIRST_YEAR
    val_m = (year >= F.VALID_FIRST_YEAR) & (year <= F.TRAIN_LAST_YEAR)
    X = prepare(rows, fit_m)
    gbm = GradientBoostingRegressor(n_estimators=MAX_TREES, n_iter_no_change=EARLY_STOP, **h)
    gbm.fit(X[fit_m], y[fit_m], X[val_m], y[val_m])
    p = gbm.predict(X[val_m])
    return gbm, gbm.best_n_estimators_, {"rmse_val": rmse(y[val_m], p), "r2_val": r2(y[val_m], p), "n_val": int(val_m.sum())}


def fit_final(rows, n_trees, hyper=None):
    h = {**HYPER, **(hyper or {})}
    year = np.array([r["year"] for r in rows]); y = np.array([r["y"] for r in rows])
    tr_m = year <= F.TRAIN_LAST_YEAR
    X = prepare(rows, tr_m)
    gbm = GradientBoostingRegressor(n_estimators=n_trees, **h)
    gbm.fit(X[tr_m], y[tr_m])
    return gbm, X, tr_m


def metrics(y, p):
    """Scores on the logarithmic scale and on the original scale (overnight stays)."""
    return {"rmse_log": rmse(y, p), "mae_log": mae(y, p), "r2_log": r2(y, p),
            "rmse_nights": rmse(np.expm1(y), np.expm1(p)), "mae_nights": mae(np.expm1(y), np.expm1(p))}


def main():
    utf8_console()
    out = ensure(STAGE2_RESULTS)
    rows = F.build_panel()
    year = np.array([r["year"] for r in rows]); y = np.array([r["y"] for r in rows])
    tr_m = year <= F.TRAIN_LAST_YEAR; te_m = ~tr_m
    print(f"panel: {len(rows)} observations | training {tr_m.sum()} | test {te_m.sum()}")

    gbm_es, n_trees, val = fit_early_stopping(rows)
    print(f"early stopping: {n_trees} trees | validation RMSE {val['rmse_val']:.3f} | validation R2 {val['r2_val']:.3f}")
    with open(out / "gbm_learning_curve.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["trees", "mse_training", "mse_validation"])
        for i, (a, b) in enumerate(zip(gbm_es.train_loss_, gbm_es.val_loss_), 1):
            w.writerow([i, f"{a:.6f}", f"{b:.6f}"])

    gbm, X, _ = fit_final(rows, n_trees)
    pred = gbm.predict(X)
    res = {"n_trees": int(n_trees), "hyperparameters": HYPER, "early_stopping_validation": val,
           "n_training": int(tr_m.sum()), "n_test": int(te_m.sum()),
           "training": metrics(y[tr_m], pred[tr_m]), "test": metrics(y[te_m], pred[te_m])}
    print("test:", {k: round(v, 3) for k, v in res["test"].items()})

    imp = sorted(zip(F.FEATURES, gbm.feature_importances_), key=lambda z: -z[1])
    res["feature_importance"] = {k: float(v) for k, v in imp}
    with open(out / "gbm_feature_importance.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["feature", "importance"])
        for k, v in imp:
            w.writerow([k, f"{v:.5f}"])
    print("feature importance (top 5):", [(k, round(float(v), 3)) for k, v in imp[:5]])
    with open(out / "gbm_predictions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["siruta", "locality", "year", "set", "observed_nights", "predicted_nights", "y_observed_ln1p", "y_predicted_ln1p"])
        for r, p, tr in zip(rows, pred, tr_m):
            siruta, name = split_locality(r["locality"])
            w.writerow([siruta, name, r["year"], "training" if tr else "test", int(r["N"]), round(float(np.expm1(p)), 1), round(r["y"], 4), round(float(p), 4)])

    configs = [("chosen (lr 0.05, depth 3)", {}), ("lr 0.10, depth 3", dict(learning_rate=0.10)), ("lr 0.02, depth 3", dict(learning_rate=0.02)),
               ("lr 0.05, depth 2", dict(max_depth=2)), ("lr 0.05, depth 5", dict(max_depth=5)), ("lr 0.05, no subsampling", dict(subsample=1.0))]
    sens = []
    for name, hp in configs:
        _, n_, v_ = fit_early_stopping(rows, hp)
        sens.append({"configuration": name, "n_trees": int(n_), "rmse_val": v_["rmse_val"], "r2_val": v_["r2_val"]})
    with open(out / "gbm_sensitivity.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["configuration", "trees", "validation_rmse", "validation_r2"])
        for s in sens:
            w.writerow([s["configuration"], s["n_trees"], f"{s['rmse_val']:.4f}", f"{s['r2_val']:.4f}"])
    res["sensitivity"] = sens
    for s in sens:
        print(f"  {s['configuration']:<28} trees {s['n_trees']:>3}  validation RMSE {s['rmse_val']:.3f}  R2 {s['r2_val']:.3f}")
    write_json(out / "gbm_metrics.json", res)


if __name__ == "__main__":
    main()
