# -*- coding: utf-8 -*-
"""Figures 1-5 of the article, built from the data and results of this repository.

Usage:  python figures/make_figures.py   (run after the four stages)     Output: figures/fig1..fig5 (300 dpi PNG)
Palette: Okabe-Ito (colour-blind safe); text in neutral colours.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "stage3_system_dynamics"))

BLUE, ORANGE, GREEN, VERM, PURPLE, SKY, GREY, INK = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#8a8a8a", "#222222"
plt.rcParams.update({
    "font.family": ["Arial", "DejaVu Sans"], "font.size": 8, "axes.edgecolor": "#555555", "axes.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.titlesize": 8.5, "axes.titleweight": "bold", "axes.titlelocation": "left", "savefig.dpi": 300, "figure.dpi": 150,
    "legend.frameon": False, "axes.grid": True, "grid.color": "#e3e3e3", "grid.linewidth": 0.5, "axes.axisbelow": True,
})
SHOCKS = ((2008.5, 2010.5), (2019.5, 2021.5))


def shade(ax):
    for a, b in SHOCKS:
        ax.axvspan(a, b, color="#d9d9d9", alpha=0.55, lw=0, zorder=0)


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("written", OUT / name)


# ------------------------------------------------------------------ Fig. 1: conceptual framework
def fig1():
    fig, ax = plt.subplots(figsize=(7.0, 4.3))
    ax.set_xlim(0, 100); ax.set_ylim(0, 56); ax.axis("off"); ax.grid(False)
    stages = [
        ("1  DESCRIBE", "What happened?", "Official INS data,\n2001–2025\n36 localities × 12\naccommodation types\nExploratory analysis;\nshock windows", "Stylised facts:\nsupply outpaces\ndemand", BLUE),
        ("2  FORECAST", "How far can demand\nbe predicted?", "Gradient boosting vs.\nsimple baselines\nTrain 2001–2019,\ntest 2020–2025", "Limits of prediction;\ncapacity is the\nmain signal", GREEN),
        ("3  EXPLAIN", "Why did supply\ngrow?", "System dynamics:\nreputation, saturation,\npublic-policy channel\nCalibrated on 100\nINS values", "Growth led by policy\nand supply; 89% of\nceiling reached", ORANGE),
        ("4  DESIGN", "What should\nbe built?", "QFD + Monte Carlo\nrobustness test\nBusiness model and\nbreak-even analysis\n9 mature technologies", "Staged platform;\nbreak-even at 19.2%\nof arrivals", VERM),
    ]
    w, gap, x0, ytop = 21.0, 4.4, 0.6, 50.0
    for i, (title, q, method, out, col) in enumerate(stages):
        x = x0 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 8), w, ytop - 8, boxstyle="round,pad=0.0,rounding_size=1.2", fc="white", ec=col, lw=1.4))
        ax.add_patch(FancyBboxPatch((x, ytop - 6.5), w, 6.5, boxstyle="round,pad=0.0,rounding_size=1.2", fc=col, ec=col, lw=1.4))
        ax.text(x + w / 2, ytop - 3.25, title, ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        ax.text(x + w / 2, ytop - 12.5, q, ha="center", va="center", color=INK, fontsize=7.2, fontweight="bold", linespacing=1.2)
        ax.text(x + 1.3, ytop - 21.2, method, ha="left", va="center", color=INK, fontsize=6.4, linespacing=1.4)
        ax.plot([x + 1.2, x + w - 1.2], [ytop - 30.2] * 2, color="#cccccc", lw=0.6)
        ax.text(x + w / 2, ytop - 35.8, out, ha="center", va="center", color=INK, fontsize=6.6, fontstyle="italic", linespacing=1.4)
        if i < 3:
            ax.add_patch(FancyArrowPatch((x + w + 0.4, 29), (x + w + gap - 0.4, 29), arrowstyle="-|>", mutation_scale=9, color="#555555", lw=1.1))
    # feedback loop
    xs, xe = x0 + 3 * (w + gap) + w / 2, x0 + w / 2
    ax.add_patch(FancyArrowPatch((xs, 8), (xe, 8), connectionstyle="arc3,rad=0.0", arrowstyle="-|>", mutation_scale=9, color="#555555", lw=1.1,
                                 shrinkA=0, shrinkB=0, linestyle=(0, (4, 2))))
    ax.plot([xs, xs], [8, 4.2], color="#555555", lw=1.1, ls=(0, (4, 2)))
    ax.plot([xe, xe], [8, 4.2], color="#555555", lw=1.1, ls=(0, (4, 2)))
    ax.plot([xe, xs], [4.2, 4.2], color="#555555", lw=1.1, ls=(0, (4, 2)))
    ax.text((xs + xe) / 2, 1.9, "Feedback: monthly, unit-level data from the platform replace annual aggregates and recalibrate stages 2 and 3",
            ha="center", va="center", fontsize=7, color=INK)
    save(fig, "fig1_framework.png")


# ------------------------------------------------------------------ Fig. 2: evolution 2001-2025
def fig2():
    rows = list(csv.DictReader(open(REPO / "data/processed/county_series.csv", encoding="utf-8")))
    yr = np.array([int(r["year"]) for r in rows])
    g = lambda k: np.array([float(r[k]) for r in rows])
    C, N, S, Ca, Na = g("capacity_total"), g("overnight_total"), g("arrivals_total"), g("capacity_agro"), g("overnight_agro")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.9), gridspec_kw={"wspace": 0.28})
    shade(a1)
    for v, lab, col, dy in ((C, "Capacity (bed-days)", VERM, 0), (S, "Arrivals", BLUE, 0), (N, "Overnight stays", GREEN, 0)):
        a1.plot(yr, 100 * v / v[0], color=col, lw=1.5)
        a1.text(2025.4, 100 * v[-1] / v[0] + dy, f"{lab}\n×{v[-1] / v[0]:.1f}", color=col, fontsize=6.8, va="center", ha="left", fontweight="bold")
    a1.set_xlim(2001, 2031.5); a1.set_ylabel("Index, 2001 = 100"); a1.set_title("(a) County totals")
    a1.set_xticks([2001, 2005, 2010, 2015, 2020, 2025])
    shade(a2)
    occ, occa = 100 * N / C, 100 * Na / Ca
    sc, sn = 100 * Ca / C, 100 * Na / N
    a2.plot(yr, sc, color=BLUE, lw=1.5); a2.plot(yr, sn, color=GREEN, lw=1.5)
    a2.plot(yr, occ, color=INK, lw=1.5); a2.plot(yr[4:], occa[4:], color=ORANGE, lw=1.5)
    a2.text(2025.4, sc[-1], f"Agritourism share\nof capacity {sc[-1]:.1f}%", color=BLUE, fontsize=6.6, va="center", fontweight="bold")
    a2.text(2025.4, sn[-1] - 3.3, f"…of overnight\nstays {sn[-1]:.1f}%", color=GREEN, fontsize=6.6, va="center", fontweight="bold")
    a2.text(2025.4, occ[-1] - 0.5, f"County occupancy\n{occ[-1]:.1f}%", color=INK, fontsize=6.6, va="center", fontweight="bold")
    a2.text(2025.4, occa[-1] - 4.6, f"Agritourism\noccupancy {occa[-1]:.1f}%", color=ORANGE, fontsize=6.6, va="center", fontweight="bold")
    a2.set_xlim(2001, 2031.5); a2.set_ylim(0, 40); a2.set_ylabel("%"); a2.set_title("(b) Occupancy and agritourism share")
    a2.set_xticks([2001, 2005, 2010, 2015, 2020, 2025])
    save(fig, "fig2_evolution.png")


# ------------------------------------------------------------------ Fig. 3: forecasting
def fig3():
    rows = list(csv.DictReader(open(REPO / "stage2_forecast/results/gbm_predictions.csv", encoding="utf-8")))
    te = [r for r in rows if r["set"] == "test"]
    x = np.array([float(r["observed_nights"]) for r in te]) + 1
    y = np.array([float(r["predicted_nights"]) for r in te]) + 1
    big = np.array([r["locality"] in ("Baia de Fier", "Runcu") for r in te])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 3.0), gridspec_kw={"wspace": 0.32, "width_ratios": [1, 1.1]})
    a1.scatter(x[~big], y[~big], s=11, color=BLUE, alpha=0.75, lw=0, label="Other localities")
    a1.scatter(x[big], y[big], s=16, color=ORANGE, lw=0.4, ec="white", label="Baia de Fier, Runcu")
    lim = [8, 4e4]
    a1.plot(lim, lim, color=GREY, ls="--", lw=0.9)
    a1.set_xscale("log"); a1.set_yscale("log"); a1.set_xlim(lim); a1.set_ylim(lim)
    a1.set_xlabel("Observed overnight stays (+1)"); a1.set_ylabel("Predicted overnight stays (+1)")
    a1.set_title("(a) Test set, locality-year (n = 130)"); a1.legend(loc="upper left", fontsize=6.6, handletextpad=0.2)
    B = json.load(open(REPO / "stage2_forecast/results/forecast_comparison.json", encoding="utf-8"))
    yrs = np.arange(2020, 2026); J = B["county"]
    a2.plot(yrs, np.array(B["county_observed_2020_2025"]) / 1e3, color=INK, lw=2.0, marker="o", ms=3)
    spec = (("gradient_boosting", "Gradient boosting", BLUE), ("naive", "Naive", GREEN), ("naive_capacity", "Naive + capacity", ORANGE), ("ARI_3_1", "ARI(3,1)", VERM))
    for k, lab, col in spec:
        a2.plot(yrs, np.array(J[k]["forecast"]) / 1e3, color=col, lw=1.3, marker="o", ms=2.5)
    ends = {k: J[k]["forecast"][-1] / 1e3 for k, _, _ in spec}
    ends["obs"] = B["county_observed_2020_2025"][-1] / 1e3
    order = sorted(ends, key=ends.get); pos = {}; last = -99
    for k in order:
        p = max(ends[k], last + 4.4); pos[k] = p; last = p
    for k, lab, col in spec + (("obs", "Observed", INK),):
        a2.text(2025.12, pos[k], lab, color=col, fontsize=6.6, fontweight="bold", va="center")
    a2.set_xlim(2019.8, 2028.3); a2.set_ylim(20, 85); a2.set_xticks(yrs)
    a2.set_ylabel("Overnight stays (thousands)"); a2.set_title("(b) County total, 2020–2025")
    save(fig, "fig3_forecast.png")


# ------------------------------------------------------------------ Fig. 4: System Dynamics
def fig4():
    import sd1_model as M
    X = M.real_series()
    yr = np.arange(2001, 2046)
    base = M.simulate(horizon=44)
    dbl = M.simulate(P=dict(delta=M.PARAMS["delta"] * 2), horizon=44)
    nop = M.simulate(P=dict(delta=0.0), horizon=44)
    KA = M.PARAMS["KA"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.9), gridspec_kw={"wspace": 0.3})
    shade(a1)
    y25 = np.arange(2001, 2026)
    a1.scatter(y25, np.array(X["CA"]) / 1e3, s=9, color=INK, zorder=3)
    a1.plot(y25, base["CA"][:25] / 1e3, color=BLUE, lw=1.6)
    a1.set_ylabel("Agritourism capacity (thousand bed-days)"); a1.set_xlim(2001, 2025.2)
    a1.text(2005.2, 330, "Observed (INS)", color=INK, fontsize=6.8, fontweight="bold")
    a1.text(2005.2, 305, f"Model 1 (R² = {M.r2(X['CA'], base['CA'][:25]):.2f})", color=BLUE, fontsize=6.8, fontweight="bold")
    a1.set_title("(a) Historical fit, 2001–2025"); a1.set_xticks([2001, 2005, 2010, 2015, 2020, 2025])
    a2.axhline(KA / 1e3, color=GREY, ls="--", lw=0.9); a2.text(2002, KA / 1e3 + 14, "Carrying capacity $K_A$ = 531 thousand bed-days", color="#555555", fontsize=6.5)
    a2.plot(yr, base["CA"] / 1e3, color=BLUE, lw=1.6); a2.plot(yr, dbl["CA"] / 1e3, color=GREEN, lw=1.3, ls=(0, (3, 1.2)))
    a2.plot(yr, nop["CA"] / 1e3, color=VERM, lw=1.6)
    a2.scatter(y25, np.array(X["CA"]) / 1e3, s=7, color=INK, zorder=3)
    a2.text(2026, 395, "Calibrated\n(policy channel on)", color=BLUE, fontsize=6.6, fontweight="bold", va="center")
    a2.text(2026, 255, "Without public\npolicy (δ = 0)", color=VERM, fontsize=6.6, fontweight="bold", va="center")
    a2.text(2001.5, 430, "Policy\nsensitivity ×2", color=GREEN, fontsize=6.6, fontweight="bold", va="center")
    a2.set_xlim(2001, 2046); a2.set_ylim(0, 600)
    a2.set_title("(b) Policy scenarios to 2045"); a2.set_xticks([2001, 2015, 2025, 2035, 2045])
    for a in (a1, a2):
        a.set_ylim(0, 600 if a is a2 else 520)
    save(fig, "fig4_system_dynamics.png")
    print("  CA 2025 sim:", base["CA"][24], "CA 2045 no policy:", nop["CA"][44], "max:", nop["CA"].max(), "dbl 2045:", dbl["CA"][44])


# ------------------------------------------------------------------ Fig. 5: QFD
NAMES = ["T1 Cloud", "T2 Web / PWA", "T3 API & integration", "T4 Online payments", "T5 Cybersecurity & data protection",
         "T6 Mapping (GIS/GPS)", "T7 Data analytics & BI", "T8 Digital marketing & CRM", "T9 Communication & localisation"]
STAGE = [1, 1, 1, 1, 1, 2, 3, 2, 1]
STCOL = {1: BLUE, 2: ORANGE, 3: GREEN}


def fig5():
    Q = json.load(open(REPO / "stage4_design/results/qfd_results.json", encoding="utf-8"))
    BT = np.array(Q["results"]["BT"]); lo = np.array(Q["monte_carlo"]["p05"]); hi = np.array(Q["monte_carlo"]["p95"])
    E = np.array(Q["results"]["effort"]); ratio = BT / E
    order = np.argsort(BT)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 3.3), gridspec_kw={"wspace": 0.62, "width_ratios": [1.15, 1]})
    for r, k in enumerate(order):
        a1.barh(r, BT[k], color=STCOL[STAGE[k]], height=0.62, zorder=2)
        a1.plot([lo[k], hi[k]], [r, r], color=INK, lw=1.1, zorder=3)
        a1.plot([lo[k]] * 2, [r - 0.17, r + 0.17], color=INK, lw=1.1, zorder=3); a1.plot([hi[k]] * 2, [r - 0.17, r + 0.17], color=INK, lw=1.1, zorder=3)
        a1.text(hi[k] + 0.5, r, f"{BT[k]:.1f}", va="center", fontsize=6.6, color=INK)
    a1.set_yticks(range(9)); a1.set_yticklabels([NAMES[k] for k in order], fontsize=6.8)
    a1.set_xlabel("Potential benefit BT (%); whiskers: 5–95% Monte Carlo"); a1.set_xlim(0, 22.5)
    a1.grid(axis="y", visible=False); a1.set_title("(a) Benefit and robustness")
    JIT = {3: -0.07, 5: 0.07}
    for k in range(9):
        a2.scatter(E[k] + JIT.get(k, 0), BT[k], s=22 * ratio[k] / 4 + 14, color=STCOL[STAGE[k]], alpha=0.9, lw=0.5, ec="white", zorder=3)
    for k in range(9):
        left = (k == 3)
        a2.text(E[k] + JIT.get(k, 0) + (-0.1 if left else 0.1), BT[k], NAMES[k].split()[0], fontsize=6.6, color=INK, va="center", ha="right" if left else "left")
    a2.text(2.47, 17.6, "Bubble area ∝ BT / effort", fontsize=6.3, color="#555555", ha="right")
    a2.set_xlim(0.7, 2.5); a2.set_xticks([1, 2]); a2.set_xticklabels(["1  (configure)", "2  (integrate)"], fontsize=6.8)
    a2.set_ylim(3, 18.5); a2.set_xlabel("Implementation effort"); a2.set_ylabel("Potential benefit BT (%)"); a2.set_title("(b) Benefit vs. effort")
    from matplotlib.lines import Line2D
    h = [Line2D([0], [0], marker="o", color="w", mfc=STCOL[s], ms=6, label=f"Stage {s}") for s in (1, 2, 3)]
    a2.legend(handles=h, loc="lower right", fontsize=6.6, handletextpad=0.2, borderaxespad=0.2)
    save(fig, "fig5_qfd.png")


if __name__ == "__main__":
    for f in (fig1, fig2, fig3, fig4, fig5):
        f()
