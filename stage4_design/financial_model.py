# -*- coding: utf-8 -*-
"""Simplified financial model of the destination platform (Sections 3.7 and 4.5 of the article, Equations 21-24, Table 8).

Only arrivals, mean stay, occupancy and payment costs are observed or taken from public sources. All parameters marked
"estimate" are assumptions chosen as examples and must be replaced by measured values before any real decision.

Usage:  python stage4_design/financial_model.py
Output: stage4_design/results/financial_model.json, table8_trajectory.csv
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.paths import DESIGN_RESULTS, ensure, utf8_console, write_json

# name: (value, status, note)
PARAMETERS = {
    "arrivals_agro": (31073, "observed", "INS, arrivals in agritourism guesthouses, 2025"),
    "mean_stay": (1.90, "observed", "INS, nights per tourist in agritourism guesthouses, 2025 (rounded)"),
    "nights_agro": (58870, "derived", "27.5% (rounded share) of 214,072 county overnight stays, 2025; the exact series value is 58,972"),
    "occupancy_agro": (12.5, "observed", "occupancy of agritourism guesthouses, 2025 (%)"),
    "occupancy_county": (14.8, "observed", "county occupancy, 2025 (%)"),
    "price": (150.0, "estimate", "price per person-night, RON"),
    "commission": (0.07, "estimate", "commission on direct bookings; large intermediaries charge about 15%"),
    "guesthouses": (150, "estimate", "472,302 bed-days / (about 12 beds x about 260 operating days)"),
    "subscribers": (0.40, "estimate", "share of hosts with a paid subscription in year 3"),
    "monthly_fee": (99.0, "estimate", "subscription fee, RON per month"),
    "promotion": (15000.0, "estimate", "promotion revenue per year, RON (year 3)"),
    "reports": (30000.0, "estimate", "aggregated reports for public authorities, RON per year (from year 2)"),
    "investment": (220000.0, "estimate", "initial investment, RON"),
    "payment_pct": (0.015, "online source", "payment processing, share of the transaction value"),
    "payment_fix": (1.0, "online source", "payment processing, RON per transaction"),
    "staff": (132000.0, "estimate", "platform coordinator and part-time developer, RON per year"),
    "cloud": (24000.0, "estimate", "hosting and licences, RON per year"),
    "marketing": (36000.0, "estimate", "campaigns and multilingual content, RON per year"),
    "legal": (12000.0, "estimate", "accounting, data protection, terms, RON per year"),
}
v = {k: x[0] for k, x in PARAMETERS.items()}
FIXED_COSTS = v["staff"] + v["cloud"] + v["marketing"] + v["legal"]
RAMP = [  # year, share of arrivals s, share of subscribers, revenue from reports
    (1, 0.05, 0.15, 0.0), (2, 0.12, 0.30, 30000.0), (3, 0.20, 0.40, 30000.0), (4, 0.25, 0.45, 30000.0), (5, 0.30, 0.50, 30000.0)]


def annual_result(s, subscribers, reports, price=None, commission=None):
    """Result of one year for a share s of agritourism arrivals booked through the platform (Equations 21-22)."""
    price = v["price"] if price is None else price
    commission = v["commission"] if commission is None else commission
    arrivals = v["arrivals_agro"] * s
    bookings = arrivals * v["mean_stay"] * price
    rev_commission = commission * bookings
    rev_subscription = v["guesthouses"] * subscribers * v["monthly_fee"] * 12
    rev_promotion = v["promotion"] * min(1.0, subscribers / v["subscribers"])
    revenue = rev_commission + rev_subscription + rev_promotion + reports
    payment_costs = v["payment_pct"] * bookings + v["payment_fix"] * arrivals
    costs = payment_costs + FIXED_COSTS
    return dict(share=s, arrivals=arrivals, booking_value=bookings, rev_commission=rev_commission, rev_subscription=rev_subscription,
                rev_promotion=rev_promotion, rev_reports=reports, revenue=revenue, payment_costs=payment_costs, fixed_costs=FIXED_COSTS,
                costs=costs, result=revenue - costs)


def break_even_share(subscribers=0.40, reports=30000.0, **kw):
    """Share s at which the annual result is zero (bisection; the result is linear in s, Equation 23)."""
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if annual_result(mid, subscribers, reports, **kw)["result"] < 0:
            lo = mid
        else:
            hi = mid
    return hi


def main():
    utf8_console()
    out = {"parameters": {k: {"value": x[0], "status": x[1], "note": x[2]} for k, x in PARAMETERS.items()}, "fixed_costs": FIXED_COSTS}
    cumulative = -v["investment"]
    rows = []
    for year, s, a, d in RAMP:
        r = annual_result(s, a, d)
        cumulative += r["result"]
        rows.append({"year": year, **r, "cumulative_balance": cumulative})
    out["trajectory"] = rows
    out["break_even_share"] = break_even_share()
    out["break_even_arrivals"] = out["break_even_share"] * v["arrivals_agro"]
    out["break_even_share_without_reports"] = break_even_share(reports=0.0)
    out["max_financing_need"] = float(max(0.0, -min(r["cumulative_balance"] for r in rows)))
    prices, commissions = [100, 125, 150, 175, 200], [0.05, 0.06, 0.07, 0.08, 0.10]
    grid = [[break_even_share(price=p, commission=c) for c in commissions] for p in prices]
    out["sensitivity"] = {"price": prices, "commission": commissions, "break_even_share": grid,
                          "combinations_below_15pct": sum(x < 0.15 for row in grid for x in row)}
    factor = v["occupancy_county"] / v["occupancy_agro"]                                   # Equation 24
    extra = v["nights_agro"] * (factor - 1)
    out["occupancy_gap"] = {"extra_nights": extra, "extra_arrivals": extra / v["mean_stay"], "extra_host_revenue": extra * v["price"],
                            "extra_commission": extra * v["price"] * v["commission"], "host_gain_over_commission": 1 / v["commission"]}
    res = ensure(DESIGN_RESULTS)
    write_json(res / "financial_model.json", out)
    with open(res / "table8_trajectory.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader()
        w.writerows([{k: (round(x, 3) if isinstance(x, float) else x) for k, x in r.items()} for r in rows])

    print(f"break-even share: {out['break_even_share']:.1%} ({out['break_even_arrivals']:,.0f} arrivals) | without reports: {out['break_even_share_without_reports']:.1%}")
    print(f"maximum financing need: {out['max_financing_need']:,.0f} RON")
    for r in rows:
        print(f"  year {r['year']}: share {r['share']:.0%}  result {r['result'] / 1000:8.1f}  cumulative {r['cumulative_balance'] / 1000:8.1f} (thousand RON)")
    print("occupancy gap:", {k: round(x, 1) for k, x in out["occupancy_gap"].items()})


if __name__ == "__main__":
    main()
