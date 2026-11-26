# -*- coding: utf-8 -*-
"""Build the CSV files in data/processed/ from the raw TEMPO files in data/raw/tempo_panel/.

  panel_long.csv            all series (type x locality x year): capacity (bed-days), arrivals, overnight stays
  panel_model_agro.csv      forecasting panel (agritourism guesthouses, locality x year) with 14 features and the target
  county_series.csv         annual county series for hotels, agritourism guesthouses and the total (inputs of the SD models)
  county_by_residence.csv   county arrivals and overnight stays by type of structure and residence of the tourists

Empty cells (marked ":" in the source) remain empty.    Usage:  python data/build_processed.py
"""
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stage2_forecast"))
from common.paths import PROCESSED, ensure, utf8_console
from common.tempo import AGRO, HOTELS, YEARS, LABEL, load_panel, load_county_by_residence, split_locality, type_en
import features as F


def val(x):
    return "" if x is None or (isinstance(x, float) and np.isnan(x)) else (int(x) if float(x).is_integer() else round(float(x), 6))


def writer(path, header):
    f = open(path, "w", newline="", encoding="utf-8")
    w = csv.writer(f)
    w.writerow(header)
    return f, w


def main():
    utf8_console()
    out = ensure(PROCESSED)
    P = {k: load_panel(k) for k in "CSN"}

    keys = sorted(set().union(*[set(p) for p in P.values()]))
    f, w = writer(out / "panel_long.csv", ["structure_type", "siruta", "locality", "year", LABEL["C"], LABEL["S"], LABEL["N"]])
    n = 0
    with f:
        for (t, u) in keys:
            siruta, name = split_locality(u)
            for i, y in enumerate(YEARS):
                row = [val(P[k][(t, u)][i]) if (t, u) in P[k] else "" for k in "CSN"]
                if any(r != "" for r in row):
                    w.writerow([type_en(t), siruta, name, y, *row]); n += 1
    print("panel_long.csv:", n, "rows")

    rows = F.build_panel()
    f, w = writer(out / "panel_model_agro.csv", ["siruta", "locality", "year", LABEL["C"], LABEL["S"], LABEL["N"]] + F.FEATURES + ["y_ln1p_overnight_stays"])
    with f:
        for r in rows:
            siruta, name = split_locality(r["locality"])
            w.writerow([siruta, name] + [val(r[c]) for c in ["year", "C", "S", "N"] + F.FEATURES + ["y"]])
    print("panel_model_agro.csv:", len(rows), "rows")

    g = lambda k, t: np.nan_to_num(P[k][(t, "TOTAL")])
    Ct, Nt, St = g("C", "Total"), g("N", "Total"), g("S", "Total")
    CH, CA, NH, NA = g("C", HOTELS), g("C", AGRO), g("N", HOTELS), g("N", AGRO)
    SH, SA = g("S", HOTELS), g("S", AGRO)
    f, w = writer(out / "county_series.csv", ["year", "capacity_total", "arrivals_total", "overnight_total", "capacity_hotels", "arrivals_hotels",
                                              "overnight_hotels", "capacity_agro", "arrivals_agro", "overnight_agro", "capacity_other"])
    with f:
        for i, y in enumerate(YEARS):
            w.writerow([y] + [val(v) for v in (Ct[i], St[i], Nt[i], CH[i], SH[i], NH[i], CA[i], SA[i], NA[i], Ct[i] - CH[i] - CA[i])])
    print("county_series.csv:", len(YEARS), "rows")

    who_en = {"Total": "all", "Romani": "Romanian", "Straini": "foreign"}
    f, w = writer(out / "county_by_residence.csv", ["indicator", "structure_type", "residence", "year", "value"])
    with f:
        for key in ("S", "N"):
            for (t, o), arr in load_county_by_residence(key).items():
                for i, y in enumerate(YEARS):
                    if not np.isnan(arr[i]):
                        w.writerow([LABEL[key], type_en(t), who_en.get(o, o), y, val(arr[i])])
    print("county_by_residence.csv written")


if __name__ == "__main__":
    main()
