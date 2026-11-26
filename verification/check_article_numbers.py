# -*- coding: utf-8 -*-
"""Compare the numbers quoted in the article with the values computed by this repository.

Every entry gives the value as printed in the article; the computed value is rounded to the same number of decimals.
Status: "match" if they agree after rounding, "differs" otherwise.

Usage:  python verification/check_article_numbers.py      (run after the four stages)
Output: verification/article_check.md
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.paths import DESIGN_RESULTS, SD_RESULTS, STAGE1_RESULTS, STAGE2_RESULTS, VERIFICATION, utf8_console

load = lambda p: json.loads(p.read_text(encoding="utf-8"))
ROWS = []


def check(where, what, article, value, scale=1.0):
    """article: the printed string, e.g. "117", "0.689", "-31.1", "41,000"."""
    text = article.replace(",", "")
    decimals = len(text.split(".")[1]) if "." in text else 0
    got = round(float(value) * scale, decimals)
    ok = abs(got - float(text)) < 0.5 * 10 ** (-decimals) - 1e-12
    ROWS.append((where, what, article, f"{got:,.{decimals}f}", "match" if ok else "differs"))


def stage1():
    d = load(STAGE1_RESULTS / "descriptive.json")
    s = "3.2 data"
    check(s, "filled capacity cells", "817", d["completeness"]["filled"]); check(s, "possible cells", "2,100", d["completeness"]["cells"])
    check(s, "filled cells (%)", "38.9", d["completeness"]["filled_pct"])
    for k in "CSN":
        check(s, f"additivity checks ({k})", "1,225", d["additivity"][k]["checks"])
        check(s, f"additivity discrepancies ({k})", "0", d["additivity"][k]["discrepancies"])
    L = d["localities"]
    check(s, "localities with activity", "36", L["with_any_activity"]); check(s, "localities with agritourism", "29", L["with_agro_any_year"])
    check(s, "agritourism locality-years (capacity)", "293", L["agro_locality_year_observations"]); check(s, "agritourism localities 2025", "24", L["with_agro_2025"])
    for k, a in (("county", "14.8"), ("hotels", "21.8"), ("agro", "12.5")):
        check(s, f"INS net utilisation 2025, {k} (%)", a, d["ins_net_utilisation_2025"][k])
    s = "4.1 county"
    t2 = {"2001": ("409.6", "46.4", "103.3", "25.2", "2.23", "0.1"), "2008": ("443.4", "63.2", "119.7", "27.0", "1.89", "10.1"),
          "2010": ("556.4", "55.0", "105.7", "19.0", "1.92", "14.3"), "2015": ("735.3", "78.4", "147.2", "20.0", "1.88", "13.2"),
          "2019": ("1,046.0", "112.3", "204.9", "19.6", "1.82", "24.7"), "2020": ("848.0", "80.7", "143.1", "16.9", "1.77", "31.0"),
          "2023": ("1,305.0", "151.1", "242.6", "18.6", "1.61", "28.6"), "2025": ("1,443.4", "132.2", "214.1", "14.8", "1.62", "27.5")}
    for y, vals in t2.items():
        r = d["table2"][y]
        for (key, scale), a in zip((("capacity", 1e-3), ("arrivals", 1e-3), ("overnight", 1e-3), ("occupancy_pct", 1), ("mean_stay", 1),
                                    ("agro_share_overnight_pct", 1)), vals):
            check("Table 2", f"{y} {key}", a, r[key], scale)
    G = d["growth"]
    check(s, "capacity growth (times)", "3.5", G["capacity"]); check(s, "arrivals growth", "2.8", G["arrivals"]); check(s, "overnight growth", "2.1", G["overnight"])
    check(s, "occupancy ratio 2025/2001", "0.59", G["occupancy_ratio_2025_2001"]); check(s, "max occupancy since 2014 (%)", "22.2", G["occupancy_max_since_2014"])
    check(s, "foreign share of overnight stays 2025 (%)", "2.9", d["foreign"]["share_overnight_2025_pct"])
    A = d["agro"]
    for what, a, key in (("agro capacity 2001", "4,016", "capacity_2001"), ("agro capacity 2025", "472,302", "capacity_2025"),
                         ("share of capacity 2001 (%)", "1.0", "share_capacity_2001_pct"), ("share of capacity 2025 (%)", "32.7", "share_capacity_2025_pct"),
                         ("largest type by capacity since", "2020", "largest_type_by_capacity_since"), ("share of overnight stays 2025 (%)", "27.5", "share_overnight_2025_pct"),
                         ("share of arrivals 2025 (%)", "23.5", "share_arrivals_2025_pct"), ("hotel share of overnight stays (%)", "31.3", "hotels_share_overnight_2025_pct"),
                         ("hotel share of arrivals (%)", "33.4", "hotels_share_arrivals_2025_pct"), ("agro mean stay", "1.90", "stay_2025"),
                         ("hotel mean stay", "1.52", "stay_hotels_2025"), ("county mean stay", "1.62", "stay_county_2025"), ("agro mean stay 2015", "2.64", "stay_2015"),
                         ("agro occupancy 2015 (%)", "18.2", "occupancy_2015_pct"), ("agro occupancy 2025 (%)", "12.5", "occupancy_2025_pct"),
                         ("relative occupancy min 2014-24", "0.90", "relative_occupancy_2014_2024_min"), ("relative occupancy max 2014-24", "1.00", "relative_occupancy_2014_2024_max"),
                         ("relative occupancy 2025", "0.84", "relative_occupancy_2025"), ("capacity 2009/2008", "2.4", "capacity_ratio_2009_2008"),
                         ("capacity 2025 vs 2023 (%)", "22.8", "capacity_change_2025_vs_2023_pct"), ("overnight 2025 vs 2023 (%)", "-14.9", "overnight_change_2025_vs_2023_pct"),
                         ("agro arrivals 2025", "31,073", "arrivals_2025")):
        check(s, what, a, A[key])
    check(s, "agro growth (more than N-fold)", "117", int(A["growth"]))
    check(s, "foreign share of agro arrivals (%)", "1.5", d["foreign"]["share_arrivals_agro_2025_pct"])
    check(s, "foreign share of county arrivals (%)", "3.6", d["foreign"]["share_arrivals_county_2025_pct"])
    S = d["structure"]
    for what, a, key in (("hotel share of capacity 2001 (%)", "70.7", "hotel_share_capacity_2001_pct"), ("hotel share of capacity 2025 (%)", "21.3", "hotel_share_capacity_2025_pct"),
                         ("hotel capacity change (%)", "6.1", "hotel_capacity_change_pct"), ("hotel overnight change (%)", "-14.3", "hotel_overnight_change_pct"),
                         ("agro share of capacity growth (%)", "45.3", "agro_share_of_capacity_growth_pct"), ("agro share of overnight growth (%)", "53.1", "agro_share_of_overnight_growth_pct"),
                         ("correlation of annual changes", "-0.01", "correlation_yoy_hotels_agro_2005_2025")):
        check(s, what, a, S[key])
    for what, a, key in (("Targu Jiu share of hotel capacity (%)", "77.7", "targu_jiu_share_hotel_capacity_pct"), ("communes with accommodation", "23", "communes_with_accommodation_2025"),
                         ("communes: agritourism main type", "20", "communes_where_agro_is_main_type"), ("communes: agritourism only type", "14", "communes_where_agro_is_only_type"),
                         ("four localities, capacity (%)", "65.5", "pilot_area_share_capacity_pct"), ("four localities, overnight (%)", "72.0", "pilot_area_share_overnight_pct"),
                         ("Baia de Fier capacity (%)", "28.9", "baia_de_fier_share_capacity_pct"), ("Baia de Fier overnight (%)", "36.2", "baia_de_fier_share_overnight_pct"),
                         ("localities with agritourism 2016", "9", "with_agro_2016"), ("localities with agritourism 2019", "20", "with_agro_2019")):
        check(s, what, a, L[key])
    t3 = [("3.0", "-21.7", "28.6", "21.8"), ("79.8", "24.3", "25.4", "17.6"), ("25.5", "-11.7", "27.0", "19.0"),
          ("-18.7", "-31.1", "23.6", "20.0"), ("-6.1", "-12.3", "18.0", "16.9"), ("-18.9", "-30.2", "19.6", "16.9")]
    for r, vals in zip(d["table3"], t3):
        for key, a in zip(("capacity_change_pct", "overnight_change_pct", "occupancy_start_pct", "occupancy_end_pct"), vals):
            check("Table 3", f"{r['years']} {r['type']} {key}", a, r[key])
    check(s, "agro overnight 2021 vs 2019 (%)", "14.9", d["recovery"]["agro_overnight_2021_vs_2019_pct"])
    check(s, "hotel overnight 2021 vs 2019 (%)", "-16.9", d["recovery"]["hotels_overnight_2021_vs_2019_pct"])


def stage2():
    m = load(STAGE2_RESULTS / "gbm_metrics.json"); c = load(STAGE2_RESULTS / "forecast_comparison.json"); d = load(STAGE2_RESULTS / "diagnostics.json")
    table4 = {"naive": ("0.710", "0.998", "1,381", "9,215"), "naive_capacity": ("0.664", "1.073", "1,205", "9,078"),
              "gradient_boosting": ("0.689", "1.032", "2,358", "10,429"), "linear_regression_14": ("0.638", "1.115", None, "21,511"),
              "capacity_regression": ("0.612", "1.154", "2,732", "20,948"), "ARI_3_1": (None, None, None, "11,441")}
    for name, vals in table4.items():
        src = c["locality_year"].get(name, {}).get("test", {})
        got = (src.get("r2_log"), src.get("rmse_log"), src.get("rmse_nights"), c["county"][name]["rmse"])
        for label, a, g in zip(("R2 log", "RMSE log", "RMSE nights", "RMSE county"), vals, got):
            if a is not None:
                check("Table 4", f"{name} {label}", a, g)
    s = "3.4 / 4.2 forecasting"
    check(s, "observations", "292", d["n_observations"]); check(s, "training observations", "162", m["n_training"]); check(s, "test observations", "130", m["n_test"])
    check(s, "training localities", "23", d["n_localities_training"]); check(s, "test localities", "28", d["n_localities_test"])
    check(s, "test localities without training data", "6", d["n_localities_without_training_data"])
    check(s, "skewness of overnight stays", "3.49", d["skewness_nights"]); check(s, "skewness of log target", "-0.32", d["skewness_log"])
    check(s, "number of trees", "74", m["n_trees"]); check(s, "validation R2, lowest of six", "0.708", min(x["r2_val"] for x in m["sensitivity"]))
    check(s, "validation R2, highest of six", "0.756", max(x["r2_val"] for x in m["sensitivity"]))
    check(s, "training R2", "0.918", m["training"]["r2_log"]); check(s, "test MAE (overnight stays)", "1,055", m["test"]["mae_nights"])
    check(s, "test mean (overnight stays)", "2,715", d["test_mean_nights"])
    imp = m["feature_importance"]
    for what, a, key in (("importance: capacity (%)", "52.2", "log_capacity_agro"), ("importance: previous year (%)", "7.5", "lag1_log_overnight"),
                         ("importance: historical stay (%)", "6.6", "hist_mean_stay"), ("importance: trend (%)", "6.1", "trend")):
        check(s, what, a, imp[key], 100)
    check(s, "underestimation (%, article: about 14-15)", "15", d["underestimation_pct_of_observed"])
    check(s, "Baia de Fier + Runcu share of observed (%)", "58", d["share_observed_BaiaDeFier_Runcu_pct"])
    check(s, "training observations above 14,000", "4", d["training_obs_above_14000"]); check(s, "test observations above 14,000", "8", d["test_obs_above_14000"])
    check(s, "maximum training capacity", "114,455", d["max_training_capacity"])
    check(s, "Spearman correlation of locality means", "0.81", d["spearman_locality_means"])
    check(s, "large localities R2", "0.77", d["groups"]["large"]["r2_log"]); check(s, "small localities R2", "0.52", d["groups"]["small"]["r2_log"])
    check(s, "large: median relative error (%)", "39.7", d["groups"]["large"]["median_abs_relative_error_pct"])
    check(s, "small: median relative error (%)", "59.2", d["groups"]["small"]["median_abs_relative_error_pct"])
    check(s, "localities without history: median error (%)", "46", d["median_rel_error_localities_without_training_pct"])
    check(s, "other localities: median error (%)", "31", d["median_rel_error_other_localities_pct"])
    check(s, "elasticity, full panel", "1.26", d["elasticity_full_panel"]); check(s, "elasticity, 14-variable regression", "1.20", d["elasticity_regression_14"])
    check(s, "elasticity, capacity regression", "1.28", d["elasticity_capacity_regression"])
    check(s, "fitted elasticity of naive-capacity rule", "1.22", d["naive_capacity_fitted_elasticity"])
    check(s, "mean county overnight stays 2020-2025", "58,823", d["county_mean_observed_2020_2025"])


def stage3():
    r = load(SD_RESULTS / "sd_summary.json"); s = "4.3 Model 1"
    for k, a in (("CA", "0.960"), ("NA", "0.880"), ("CH", "0.039"), ("NH", "0.225")):
        check(s, f"R2 {k}", a, r["model1_fit"][k]["r2"])
    check(s, "carrying capacity K_A", "531,349", r["model1_parameters"]["KA"])
    check(s, "reputation 90% in", "2009", r["reputation_year_90pct"]); check(s, "reputation 99% in", "2010", r["reputation_year_99pct"])
    check(s, "observed capacity as % of K_A", "89", r["observed_share_of_KA_pct"])
    sc = r["model1_scenarios"]
    for name, vals in (("calibrated", ("480,502", "531,346", "2025", "2027", "2030")), ("policy sensitivity doubled", ("530,082", "531,349", "2019", "2020", "2021"))):
        for key, a in zip(("CA_2025", "CA_2045", "year_90pct_KA", "year_95pct_KA", "year_99pct_KA"), vals):
            check("Table 5", f"{name} {key}", a, sc[name][key])
    n = sc["no public-policy channel"]
    check("Table 5", "no policy CA_2025", "69,110", n["CA_2025"]); check("Table 5", "no policy CA_2045", "69,110", n["CA_2045"])
    check(s, "no policy: peak capacity", "81,291", n["CA_max"]); check(s, "no policy: peak year", "2021", n["CA_max_year"])
    sens = {(x["parameter"], x["change"]): x["CA_2025"] for x in r["model1_sensitivity_CA_2025"]}
    for what, a, key in (("K_A x 0.5", "250,055", ("KA", "x0.5")), ("K_A x 1.5", "687,888", ("KA", "x1.5")),
                         ("ramp midpoint +5 years", "329,185", ("pol_mid", "+5 years")), ("ramp midpoint -5 years", "508,094", ("pol_mid", "-5 years"))):
        check(s, f"sensitivity, CA 2025: {what}", a, sens[key])
    runs = sorted(SD_RESULTS.glob("calibration_base_*.json"))
    for f in runs:
        check(s, f"calibration error ({f.stem})", "30.149", load(f)["objective"])
    s = "5.3 Model 2"; m = r["model2_scenarios"]
    check(s, "baseline minimum", "6.33", m["baseline"]["QOL_min"]); check(s, "baseline minimum year", "2035", m["baseline"]["QOL_min_year"])
    check(s, "acceptance threshold (%)", "67", r["model2_acceptance_threshold"], 100); check(s, "baseline 2045", "6.45", m["baseline"]["QOL_2045"])
    check(s, "no diffusion 2045", "5.85", m["no diffusion of acceptance"]["QOL_2045"]); check(s, "rapid diffusion 2045", "6.84", m["rapid diffusion"]["QOL_2045"])


def stage4():
    q = load(DESIGN_RESULTS / "qfd_results.json"); f = load(DESIGN_RESULTS / "financial_model.json")
    for i, a in enumerate(("11.1", "8.9", "6.7", "6.7", "6.7", "13.3", "11.1", "13.3", "8.9", "13.3")):
        check("Table 6", f"PA R{i + 1}", a, q["results"]["PA"][i])
    table7 = {"T3": ("15.8", "12.8", "19.0", "86"), "T1": ("15.0", "12.0", "18.2", "76"), "T9": ("14.1", "11.0", "17.5", "58"), "T2": ("13.8", "10.8", "17.2", "52"),
              "T7": ("12.5", "9.7", "15.6", "26"), "T5": ("9.8", "7.3", "12.8", "3"), "T8": ("8.0", "5.7", "10.7", "0"), "T4": ("5.6", "3.4", "8.4", "0"), "T6": ("5.2", "3.5", "7.3", "0")}
    mc = q["monte_carlo"]
    for t, vals in table7.items():
        k = int(t[1:]) - 1
        for label, a, g, sc in (("BT", vals[0], q["results"]["BT"][k], 1), ("MC 5%", vals[1], mc["p05"][k], 1), ("MC 95%", vals[2], mc["p95"][k], 1),
                                ("P(top 3) %", vals[3], mc["p_top3"][k], 100)):
            check("Table 7", f"{t} {label}", a, g, sc)
    s = "4.4 QFD"
    check(s, "T3 ranks first (%)", "43", mc["p_rank1"][2], 100); check(s, "exact top-3 set (%)", "28", mc["p_exact_top3_set"], 100)
    check(s, "three lowest among lowest four (%)", "96", mc["p_bottom3_within_lowest4"], 100); check(s, "median Spearman", "0.90", mc["median_spearman_with_base"])
    ws = {x["scheme"]: x for x in q["weighting_schemes"]}
    check(s, "K3 only: security BT", "18.0", ws["K3 only"]["BT"][4]); check(s, "K3 only: payments BT", "17.4", ws["K3 only"]["BT"][3])
    check(s, "K3 only: Spearman", "0.25", ws["K3 only"]["spearman_with_base"])
    check(s, "feature C10 importance (%)", "11.3", q["results"]["feature_importance"][9]); check(s, "feature C8 importance (%)", "10.9", q["results"]["feature_importance"][7])
    check(s, "feature C5 importance (%)", "7.3", q["results"]["feature_importance"][4])
    s = "4.5 finance"
    check(s, "break-even share (%)", "19.2", f["break_even_share"], 100); check(s, "break-even arrivals", "5,978", f["break_even_arrivals"])
    check(s, "break-even without reports (%)", "25.8", f["break_even_share_without_reports"], 100); check(s, "maximum financing need (RON)", "423,416", f["max_financing_need"])
    table8 = [("1,554", "443", "63", "212", "-149", "-369"), ("3,729", "1,063", "169", "224", "-55", "-423"), ("6,215", "1,771", "240", "237", "3", "-420"),
              ("7,768", "2,214", "280", "245", "35", "-385"), ("9,322", "2,657", "320", "253", "67", "-318")]
    for r, vals in zip(f["trajectory"], table8):
        for (key, sc), a in zip((("arrivals", 1), ("booking_value", 1e-3), ("revenue", 1e-3), ("costs", 1e-3), ("result", 1e-3), ("cumulative_balance", 1e-3)), vals):
            check("Table 8", f"year {r['year']} {key}", a, r[key], sc)
    sens = f["sensitivity"]; flat = [x for row in sens["break_even_share"] for x in row]
    check(s, "lowest break-even share (%)", "9", min(flat), 100); check(s, "highest break-even share (%)", "50", max(flat), 100)
    check(s, "combinations below 15%", "7", sens["combinations_below_15pct"])
    g = f["occupancy_gap"]
    check(s, "extra overnight stays (about, hundreds)", "108", g["extra_nights"], 0.01); check(s, "extra arrivals (about, hundreds)", "57", g["extra_arrivals"], 0.01)
    check(s, "extra host revenue (million RON)", "1.62", g["extra_host_revenue"], 1e-6); check(s, "extra commission (thousand RON)", "114", g["extra_commission"], 1e-3)


def main():
    utf8_console()
    for fn in (stage1, stage2, stage3, stage4):
        fn()
    n_ok = sum(r[4] == "match" for r in ROWS)
    lines = ["# Article numbers vs. repository results", "",
             "Generated by `verification/check_article_numbers.py`. The computed value is rounded to the precision printed in the article.", "",
             f"**{n_ok} of {len(ROWS)} values match; {len(ROWS) - n_ok} differ.**", ""]
    diff = [r for r in ROWS if r[4] != "match"]
    header = ["| Section / table | Quantity | Article | Repository | Status |", "|---|---|---|---|---|"]
    row = lambda r: "| " + " | ".join(r) + " |"
    lines += ["## Values that differ", ""] + header + [row(r) for r in diff] + ["", "## All checked values", ""] + header + [row(r) for r in ROWS]
    (VERIFICATION / "article_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{n_ok} of {len(ROWS)} article values match; {len(diff)} differ")
    for r in diff:
        print("  differs:", " | ".join(r[:4]))


if __name__ == "__main__":
    main()
