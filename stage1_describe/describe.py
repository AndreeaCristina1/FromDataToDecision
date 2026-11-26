# -*- coding: utf-8 -*-
"""Stage 1: descriptive analysis of Gorj County, 2001-2025 (Sections 3.2-3.3 and 4.1 of the article).

Computes the completeness and additivity checks of the panel, Table 2 (selected indicators), Table 3 (response to the two shocks),
the structural indicators quoted in the text and a cross-check against the 2025 INS net utilisation report.

Usage:  python stage1_describe/describe.py
Output: stage1_describe/results/descriptive.json, table2_indicators.csv, table3_shocks.csv
"""
import csv
import sys
from pathlib import Path

import numpy as np
import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.paths import RAW, STAGE1_RESULTS, ensure, utf8_console, write_json
from common.tempo import AGRO, HOTELS, YEARS, load_panel, load_county_by_residence, split_locality, type_en

IX = {y: i for i, y in enumerate(YEARS)}


def pct(a, b):
    return float(100 * a / b)


def change(series, a, b):
    return float(100 * (series[IX[b]] / series[IX[a]] - 1))


def completeness_and_additivity(P):
    """Count the filled cells and compare every total with the sum of its components (county, type and locality totals)."""
    out = {}
    series = {k for k in P["C"] if k[0] != "Total" and k[1] != "TOTAL"}
    filled = sum(int(np.sum(~np.isnan(P["C"][k]))) for k in series)
    out["completeness"] = {"locality_type_series": len(series), "cells": len(series) * len(YEARS), "filled": filled,
                           "filled_pct": pct(filled, len(series) * len(YEARS))}
    for key in "CSN":
        panel = P[key]
        types = sorted({t for t, _ in panel if t != "Total"}); locs = sorted({u for _, u in panel if u != "TOTAL"})
        nz = lambda k: np.nan_to_num(panel[k]) if k in panel else np.zeros(len(YEARS))
        checks = [(nz(("Total", "TOTAL")), sum(nz(("Total", u)) for u in locs))]                  # county vs localities
        checks += [(nz((t, "TOTAL")), sum(nz((t, u)) for u in locs)) for t in types]               # type total vs localities
        checks += [(nz(("Total", u)), sum(nz((t, u)) for t in types)) for u in locs]               # locality total vs types
        n = sum(len(a) for a, _ in checks)
        bad = sum(int(np.sum(np.abs(a - b) > 0.5)) for a, b in checks)
        out.setdefault("additivity", {})[key] = {"checks": n, "discrepancies": bad, "types": len(types), "localities": len(locs)}
    return out


def ins_net_utilisation_2025():
    """County-level net utilisation indices published by INS for 2025 (report TUR1A, table T72)."""
    path = next((RAW / "tur1a_2025").glob("*IndiciZone*.xlsx"))
    ws = openpyxl.load_workbook(path, data_only=True).worksheets[0]
    found = {}
    for row in ws.iter_rows(values_only=True):
        if row and str(row[1]).strip() == "Judet GORJ":
            found[str(row[2]).strip()] = float(row[3])
    return {"county": found["TOTAL"], "hotels": found[HOTELS], "agro": found[AGRO]}


def main():
    utf8_console()
    out_dir = ensure(STAGE1_RESULTS)
    P = {k: load_panel(k) for k in "CSN"}
    R = completeness_and_additivity(P)
    total = lambda k, t="Total": np.nan_to_num(P[k][(t, "TOTAL")])
    C, S, N = (total(k) for k in "CSN")
    Ch, Sh, Nh = (total(k, HOTELS) for k in "CSN")
    Ca, Sa, Na = (total(k, AGRO) for k in "CSN")
    occ, stay = 100 * N / C, N / S
    occ_a = np.where(Ca > 0, 100 * Na / np.where(Ca > 0, Ca, 1), np.nan)

    # ---------------- Table 2
    table2 = []
    for y in YEARS:
        i = IX[y]
        table2.append({"year": y, "capacity": C[i], "arrivals": S[i], "overnight": N[i], "occupancy_pct": occ[i], "mean_stay": stay[i],
                       "agro_share_overnight_pct": pct(Na[i], N[i]), "agro_share_capacity_pct": pct(Ca[i], C[i]),
                       "agro_occupancy_pct": float(occ_a[i])})
    with open(out_dir / "table2_indicators.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table2[0])); w.writeheader()
        w.writerows([{k: (round(float(v), 3) if k != "year" else v) for k, v in r.items()} for r in table2])
    R["table2"] = {str(r["year"]): r for r in table2}

    # ---------------- county evolution
    R["growth"] = {"capacity": float(C[-1] / C[0]), "arrivals": float(S[-1] / S[0]), "overnight": float(N[-1] / N[0]),
                   "occupancy_ratio_2025_2001": float(occ[-1] / occ[0]),
                   "arrivals_peak": float(S.max()), "arrivals_peak_year": YEARS[int(S.argmax())],
                   "overnight_peak": float(N.max()), "overnight_peak_year": YEARS[int(N.argmax())],
                   "occupancy_min_year": YEARS[int(occ.argmin())], "occupancy_max_since_2014": float(occ[IX[2014]:].max())}
    foreign_n = load_county_by_residence("N"); foreign_s = load_county_by_residence("S")
    fn = foreign_n[("Total", "Straini")]; fs = foreign_s[("Total", "Straini")]
    R["foreign"] = {"max_share_overnight_pct": float(np.nanmax(100 * fn / N)), "share_overnight_2025_pct": pct(fn[-1], N[-1]),
                    "share_arrivals_county_2025_pct": pct(fs[-1], S[-1]),
                    "share_arrivals_agro_2025_pct": pct(foreign_s[(AGRO, "Straini")][-1], Sa[-1])}

    # ---------------- agritourism
    rel = occ_a / occ
    types = [t for t in sorted({t for t, _ in P["C"]}) if t != "Total" and (t, "TOTAL") in P["C"]]
    largest = {y: type_en(max(types, key=lambda t: np.nan_to_num(P["C"][(t, "TOTAL")])[IX[y]])) for y in YEARS}
    first_always = next(y for y in YEARS if all(largest[z] == "Agritourism guesthouses" for z in YEARS if z >= y))
    R["agro"] = {"capacity_2001": Ca[0], "capacity_2025": Ca[-1], "growth": float(Ca[-1] / Ca[0]), "overnight_2001": Na[0],
                 "share_capacity_2001_pct": pct(Ca[0], C[0]), "share_capacity_2025_pct": pct(Ca[-1], C[-1]),
                 "largest_type_by_capacity_since": first_always,
                 "share_overnight_2025_pct": pct(Na[-1], N[-1]), "share_arrivals_2025_pct": pct(Sa[-1], S[-1]),
                 "arrivals_2025": Sa[-1], "overnight_2025": Na[-1],
                 "hotels_share_overnight_2025_pct": pct(Nh[-1], N[-1]), "hotels_share_arrivals_2025_pct": pct(Sh[-1], S[-1]),
                 "stay_2025": float(Na[-1] / Sa[-1]), "stay_hotels_2025": float(Nh[-1] / Sh[-1]), "stay_county_2025": float(stay[-1]),
                 "stay_2015": float(Na[IX[2015]] / Sa[IX[2015]]), "occupancy_2015_pct": float(occ_a[IX[2015]]),
                 "occupancy_2025_pct": float(occ_a[-1]), "occupancy_hotels_2025_pct": pct(Nh[-1], Ch[-1]), "occupancy_county_2025_pct": float(occ[-1]),
                 "relative_occupancy_2014_2024_min": float(rel[IX[2014]:IX[2024] + 1].min()),
                 "relative_occupancy_2014_2024_max": float(rel[IX[2014]:IX[2024] + 1].max()), "relative_occupancy_2025": float(rel[-1]),
                 "capacity_ratio_2009_2008": float(Ca[IX[2009]] / Ca[IX[2008]]),
                 "capacity_change_2025_vs_2023_pct": change(Ca, 2023, 2025), "overnight_change_2025_vs_2023_pct": change(Na, 2023, 2025)}
    R["structure"] = {"hotel_share_capacity_2001_pct": pct(Ch[0], C[0]), "hotel_share_capacity_2025_pct": pct(Ch[-1], C[-1]),
                      "hotel_capacity_change_pct": change(Ch, 2001, 2025), "hotel_overnight_change_pct": change(Nh, 2001, 2025),
                      "agro_share_of_capacity_growth_pct": pct(Ca[-1] - Ca[0], C[-1] - C[0]),
                      "agro_share_of_overnight_growth_pct": pct(Na[-1] - Na[0], N[-1] - N[0])}
    yoy = lambda v: v[IX[2004]:][1:] / v[IX[2004]:][:-1] - 1      # annual relative changes in the years 2005-2025
    R["structure"]["correlation_yoy_hotels_agro_2005_2025"] = float(np.corrcoef(yoy(Nh), yoy(Na))[0, 1])

    # ---------------- localities
    locs = sorted({u for _, u in P["C"] if u != "TOTAL"})
    at = lambda k, t, u, i=-1: float(np.nan_to_num(P[k][(t, u)])[i]) if (t, u) in P[k] else 0.0
    agro_locs = [u for u in locs if (AGRO, u) in P["C"] and np.nansum(P["C"][(AGRO, u)]) > 0]
    obs_count = sum(int(np.sum(P["C"][(AGRO, u)] > 0)) for u in agro_locs)
    n_by_year = {y: sum(at("C", AGRO, u, IX[y]) > 0 for u in agro_locs) for y in YEARS}
    active = [u for u in locs if at("C", "Total", u) > 0]
    communes = [u for u in active if not any(w in u for w in ("MUNICIPIUL", "ORAS"))]
    main_type = {u: max(types, key=lambda t: at("C", t, u)) for u in communes}
    pilot = [u for u in agro_locs if split_locality(u)[1] in ("Baia de Fier", "Runcu", "Polovragi", "Novaci")]
    bf = next(u for u in agro_locs if split_locality(u)[1] == "Baia de Fier")
    tj = next(u for u in locs if split_locality(u)[1] == "Targu Jiu")
    small_occ = sorted((100 * at("N", AGRO, u) / at("C", AGRO, u), split_locality(u)[1]) for u in agro_locs if at("C", AGRO, u) > 0)
    R["localities"] = {
        "with_any_activity": sum(any(np.nansum(P["C"][(t, u)]) > 0 for t in types if (t, u) in P["C"]) for u in locs),
        "with_agro_any_year": len(agro_locs), "agro_locality_year_observations": obs_count,
        "with_agro_2025": n_by_year[2025], "with_agro_2016": n_by_year[2016], "with_agro_2019": n_by_year[2019],
        "targu_jiu_share_hotel_capacity_pct": pct(at("C", HOTELS, tj), Ch[-1]),
        "communes_with_accommodation_2025": len(communes),
        "communes_where_agro_is_main_type": sum(main_type[u] == AGRO for u in communes),
        "communes_where_agro_is_only_type": sum(abs(at("C", AGRO, u) - at("C", "Total", u)) < 0.5 for u in communes),
        "pilot_area_share_capacity_pct": pct(sum(at("C", AGRO, u) for u in pilot), Ca[-1]),
        "pilot_area_share_overnight_pct": pct(sum(at("N", AGRO, u) for u in pilot), Na[-1]),
        "baia_de_fier_share_capacity_pct": pct(at("C", AGRO, bf), Ca[-1]),
        "baia_de_fier_share_overnight_pct": pct(at("N", AGRO, bf), Na[-1]),
        "lowest_agro_occupancy_2025": [{"locality": n, "occupancy_pct": v} for v, n in small_occ[:6]],
    }

    # ---------------- Table 3: shocks
    table3 = []
    for window, a, b in (("economic crisis", 2008, 2010), ("pandemic", 2019, 2020)):
        for label, c_, n_ in (("Hotels", Ch, Nh), ("Agritourism guesthouses", Ca, Na), ("County total", C, N)):
            table3.append({"window": window, "years": f"{a}-{b}", "type": label, "capacity_change_pct": change(c_, a, b),
                           "overnight_change_pct": change(n_, a, b), "occupancy_start_pct": pct(n_[IX[a]], c_[IX[a]]),
                           "occupancy_end_pct": pct(n_[IX[b]], c_[IX[b]])})
    with open(out_dir / "table3_shocks.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table3[0])); w.writeheader()
        w.writerows([{k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()} for r in table3])
    R["table3"] = table3
    R["recovery"] = {"agro_overnight_2021_vs_2019_pct": change(Na, 2019, 2021), "hotels_overnight_2021_vs_2019_pct": change(Nh, 2019, 2021),
                     "hotels_first_year_above_2019": next((y for y in range(2021, 2026) if Nh[IX[y]] >= Nh[IX[2019]]), None)}
    R["ins_net_utilisation_2025"] = ins_net_utilisation_2025()
    write_json(out_dir / "descriptive.json", R)

    print("completeness:", R["completeness"])
    print("additivity:", R["additivity"])
    print("growth 2001-2025 (capacity, arrivals, overnight):", [round(R["growth"][k], 2) for k in ("capacity", "arrivals", "overnight")])
    print("occupancy 2001 -> 2025: %.1f%% -> %.1f%% | agritourism 2025: %.1f%%" % (occ[0], occ[-1], occ_a[-1]))
    print("INS net utilisation 2025:", R["ins_net_utilisation_2025"])


if __name__ == "__main__":
    main()
