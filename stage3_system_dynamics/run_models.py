# -*- coding: utf-8 -*-
"""Run both system dynamics models with the calibrated parameters (Section 4.3, Table 5 and Section 5.3 of the article).

Model 1: historical fit 2001-2025, policy scenarios to 2045, one-at-a-time sensitivity analysis.
Model 2: acceptance and quality-of-life scenarios 2025-2045.

Usage:  python stage3_system_dynamics/run_models.py
Output: stage3_system_dynamics/results/
"""
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.paths import SD_RESULTS, ensure, utf8_console, write_json
import sd1_model as M1
import sd2_model as M2

SCENARIOS_1 = [("calibrated", {}), ("policy sensitivity doubled", dict(delta=2 * M1.PARAMS["delta"])), ("no public-policy channel", dict(delta=0.0))]


def first_year(series, threshold):
    idx = np.nonzero(series >= threshold)[0]
    return int(2001 + idx[0]) if len(idx) else None


def main():
    utf8_console()
    out = ensure(SD_RESULTS)
    X = M1.real_series()
    KA = M1.PARAMS["KA"]
    R = {}

    # ---------------- Model 1: fit and scenarios (to 2060; Table 5 reports 2025 and 2045)
    base = M1.simulate(horizon=59)
    R["model1_fit"] = {k: {"r2": M1.r2(X[k], base[k][:25]), "rmse": M1.rmse(X[k], base[k][:25])} for k in ("CH", "CA", "NH", "NA")}
    R["model1_parameters"] = M1.PARAMS
    R["model1_scenarios"] = {}
    runs = {}
    for name, change in SCENARIOS_1:
        s = M1.simulate(change, horizon=59); runs[name] = s
        ca = s["CA"]
        R["model1_scenarios"][name] = {"CA_2025": ca[24], "CA_2045": ca[44], "CA_2060": ca[59], "CA_max": ca.max(),
                                       "CA_max_year": int(2001 + ca.argmax()),
                                       "year_90pct_KA": first_year(ca, 0.90 * KA), "year_95pct_KA": first_year(ca, 0.95 * KA),
                                       "year_99pct_KA": first_year(ca, 0.99 * KA)}
    R["observed_CA_2025"] = X["CA"][24]
    R["observed_share_of_KA_pct"] = 100 * X["CA"][24] / KA
    R["reputation_year_90pct"] = first_year(base["REP"], 0.90)
    R["reputation_year_99pct"] = first_year(base["REP"], 0.99)
    with open(out / "model1_trajectories.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "CH_observed", "CH_simulated", "CA_observed", "CA_simulated", "NH_observed", "NH_simulated", "NA_observed", "NA_simulated",
                    "reputation", "policy_ramp", "CA_policy_doubled", "CA_no_policy"])
        for t in range(60):
            obs = lambda k: round(float(X[k][t]), 1) if t < 25 else ""
            sim = lambda s, k: round(float(s[k][t]), 1)
            w.writerow([2001 + t, obs("CH"), sim(base, "CH"), obs("CA"), sim(base, "CA"), obs("NH"), sim(base, "NH"), obs("NA"), sim(base, "NA"),
                        round(float(base["REP"][t]), 4), round(float(base["pol"][t]), 4),
                        sim(runs["policy sensitivity doubled"], "CA"), sim(runs["no public-policy channel"], "CA")])

    # ---------------- Model 1: one-at-a-time sensitivity of CA in 2025
    sens = []
    for name in ("p", "q", "A0", "bH", "gamma", "delta", "dH", "KA"):
        for factor in (0.5, 1.5):
            ca = M1.simulate({name: M1.PARAMS[name] * factor})["CA"][24]
            sens.append({"parameter": name, "change": f"x{factor}", "CA_2025": ca, "difference_pct": 100 * (ca / base["CA"][24] - 1)})
    for shift in (-5, 5):
        ca = M1.simulate(dict(pol_mid=M1.PARAMS["pol_mid"] + shift))["CA"][24]
        sens.append({"parameter": "pol_mid", "change": f"{shift:+d} years", "CA_2025": ca, "difference_pct": 100 * (ca / base["CA"][24] - 1)})
    R["model1_sensitivity_CA_2025"] = sens
    with open(out / "model1_sensitivity.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sens[0])); w.writeheader()
        w.writerows([{**r, "CA_2025": round(float(r["CA_2025"])), "difference_pct": round(float(r["difference_pct"]), 2)} for r in sens])

    # ---------------- Model 2
    A = M2.agro_series()
    R["model2_acceptance_threshold"] = M2.acc_neutral()
    R["model2_parameters"] = M2.DEFAULTS
    R["model2_scenarios"] = {}
    with open(out / "model2_scenarios.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["scenario", "year", "acceptance", "quality_of_life", "tourism_pressure"])
        for name, change in M2.SCENARIOS:
            o = M2.simulate(change, A)
            for i in range(len(o["year"])):
                w.writerow([name, int(o["year"][i]), round(float(o["acc"][i]), 4), round(float(o["qol"][i]), 4), round(float(o["pressure"][i]), 4)])
            j = int(np.argmin(o["qol"]))
            R["model2_scenarios"][name] = {"QOL_min": o["qol"][j], "QOL_min_year": int(o["year"][j]), "QOL_2045": o["qol"][-1], "ACC_2045": o["acc"][-1]}
    write_json(out / "sd_summary.json", R)

    print("Model 1 fit (R2):", {k: round(v["r2"], 3) for k, v in R["model1_fit"].items()})
    for k, v in R["model1_scenarios"].items():
        print(f"  {k:<28} CA2025 {v['CA_2025']:>9,.0f}  CA2045 {v['CA_2045']:>9,.0f}  90/95/99% of KA: {v['year_90pct_KA']}/{v['year_95pct_KA']}/{v['year_99pct_KA']}")
    for k, v in R["model2_scenarios"].items():
        print(f"Model 2, {k:<28} QOL min {v['QOL_min']:.2f} ({v['QOL_min_year']}) | 2045: {v['QOL_2045']:.2f}")


if __name__ == "__main__":
    main()
