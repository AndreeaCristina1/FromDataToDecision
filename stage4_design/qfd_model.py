# -*- coding: utf-8 -*-
"""Quality function deployment (QFD) of the destination platform (Sections 3.6 and 4.4 of the article, Equations 18-20).

Chain: requirements (R, 10) -> platform features (C, 10) -> digital technologies (T, 9).
  * requirement weights PA (%) are computed ONLY from four evidence scores (0-3), K1-K4:
      K1 gap documented in the official data (stages 1-2);   K2 role in the bottlenecks of the system dynamics model (stage 3);
      K3 legal or risk-related obligation;                   K4 low digital skills and weak rural connectivity;
  * RC (10x10) and CT (10x9) are the authors' judgements; every row sums to 100;
  * potential benefit of technology k:  BT_k = sum_i (PA_i/100) sum_j (RC_ij/100) CT_jk,  i.e.  BT = (PA/100) @ (RC/100) @ CT;
  * robustness: six alternative weighting schemes and a Monte Carlo simulation (Dirichlet noise on weights and matrix rows).

The implementation is verified by computing BT twice (nested loops and matrix product) and by a small test case with a known result.

Usage:  python stage4_design/qfd_model.py
Output: stage4_design/results/qfd_results.json, qfd_matrices_and_results.xlsx
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.paths import DESIGN_RESULTS, ensure, utf8_console, write_json

# ------------------------------------------------------------------ test case (code verification)
R_TEST = np.array([25, 20, 15, 25, 15], float)
RC_TEST = np.array([[20, 15, 0, 20, 15, 0, 10, 10, 10],
                    [15, 15, 10, 10, 0, 10, 10, 15, 15],
                    [10, 0, 0, 20, 0, 0, 50, 10, 10],
                    [10, 15, 0, 10, 60, 0, 0, 0, 5],
                    [10, 0, 70, 10, 0, 0, 0, 0, 10]], float)
CT_TEST = np.array([[30, 10, 0, 10, 0, 10, 30, 10], [20, 0, 20, 0, 0, 0, 40, 20], [10, 20, 0, 30, 0, 0, 20, 20],
                    [20, 0, 10, 10, 0, 20, 30, 10], [30, 0, 10, 10, 0, 0, 30, 20], [20, 0, 10, 10, 0, 40, 10, 10],
                    [20, 0, 10, 20, 0, 10, 30, 10], [10, 0, 10, 20, 0, 0, 40, 20], [10, 0, 0, 30, 20, 20, 10, 10]], float)
BT_TEST = np.array([20.3000, 3.8500, 7.4750, 15.3000, 1.9500, 8.1000, 28.1500, 14.8750])   # computed by hand

# ------------------------------------------------------------------ the platform model
REQ = [  # (code, requirement)
    ("R1", "Simple interface, easy to use by hosts and tourists"),
    ("R2", "Agritourism-specific functions (direct booking, activities, local products)"),
    ("R3", "Fast customer support for tourists and hosts"),
    ("R4", "Adaptation to mobile devices and operation with weak rural signal"),
    ("R5", "Varied and secure payment options"),
    ("R6", "Visibility and market access for small and isolated guesthouses"),
    ("R7", "Openness to foreign tourists and new markets"),
    ("R8", "Demand and capacity management (off-season, occupancy, tourism pressure)"),
    ("R9", "Security, trust and protection of personal data"),
    ("R10", "Collaboration and shared data for the destination (hosts, community, authorities)"),
]
FEATURES = [  # (code, platform feature)
    ("C1", "Integrated booking system with real-time availability and calendar synchronisation with intermediaries"),
    ("C2", "Interactive maps, rural itineraries and GPS navigation"),
    ("C3", "Secure and varied online payments (card, digital wallet, transfer), with advance payment or guarantee"),
    ("C4", "User account, profile, history and rule-based recommendations"),
    ("C5", "Progressive web application (PWA), fast and usable with weak signal"),
    ("C6", "Multilingual content and cultural inclusion"),
    ("C7", "Chat, frequently asked questions, notifications and reviews"),
    ("C8", "Digital marketing and visibility (search engines, social networks, campaigns)"),
    ("C9", "Analytics, reporting and administration panel for the operator"),
    ("C10", "Shared destination calendar, off-season offers and capacity-pressure indicators"),
]
TECH = [  # (code, technology, short name, implementation effort 1-3, implementation stage 1-3)
    ("T1", "Cloud computing (hosting and managed services)", "Cloud", 1, 1),
    ("T2", "Responsive web and progressive web applications (PWA)", "Web/PWA", 2, 1),
    ("T3", "Application programming interfaces (API) and integration with existing systems", "API/integration", 2, 1),
    ("T4", "Online payment processors", "Online payments", 1, 1),
    ("T5", "Cybersecurity and data protection", "Cybersecurity", 2, 1),
    ("T6", "Mapping and localisation services (GIS/GPS)", "GIS/GPS", 1, 2),
    ("T7", "Data analytics and business intelligence", "Analytics/BI", 2, 3),
    ("T8", "Digital marketing and customer relationship management (CRM)", "Marketing/CRM", 1, 2),
    ("T9", "Digital communication and language localisation", "Communication/localisation", 1, 1),
]

#              C1  C2  C3  C4  C5  C6  C7  C8  C9 C10
RC = np.zeros((10, 10))
RC[:5, :9] = RC_TEST                           # R1-R5
RC[1, 8] = 10.0
RC[1, 9] = 5.0
RC[5] = [15, 5, 0, 5, 5, 10, 10, 35, 5, 10]    # R6 visibility
RC[6] = [10, 10, 15, 5, 5, 40, 5, 10, 0, 0]    # R7 foreign tourists
RC[7] = [20, 0, 5, 5, 0, 0, 5, 10, 25, 30]     # R8 demand and capacity
RC[8] = [10, 0, 35, 25, 5, 0, 5, 0, 10, 10]    # R9 security
RC[9] = [5, 10, 0, 5, 0, 5, 10, 5, 25, 35]     # R10 collaboration

#              Cloud PWA API Pay Sec GIS BI Mkt Com
CT = np.array([[25, 10, 30, 5, 10, 0, 5, 0, 15],     # C1 booking
               [10, 20, 15, 0, 0, 45, 5, 0, 5],      # C2 maps
               [10, 5, 15, 40, 25, 0, 0, 0, 5],      # C3 payments
               [15, 15, 10, 0, 25, 0, 15, 10, 10],   # C4 account
               [20, 60, 5, 0, 5, 5, 5, 0, 0],        # C5 PWA
               [10, 10, 15, 0, 0, 0, 0, 15, 50],     # C6 multilingual
               [10, 5, 10, 0, 5, 0, 10, 10, 50],     # C7 support
               [5, 15, 10, 0, 0, 5, 20, 40, 5],      # C8 marketing
               [20, 5, 15, 5, 10, 0, 40, 0, 5],      # C9 analytics
               [20, 10, 25, 0, 10, 10, 15, 5, 5]],   # C10 shared calendar
              float)

# evidence scores 0-3 (K1, K2, K3, K4)
EVIDENCE = {
    "R1": (0, 2, 0, 3), "R2": (2, 2, 0, 0), "R3": (0, 1, 0, 2), "R4": (0, 0, 0, 3), "R5": (0, 0, 2, 1),
    "R6": (3, 3, 0, 0), "R7": (3, 2, 0, 0), "R8": (3, 3, 0, 0), "R9": (0, 1, 3, 0), "R10": (2, 3, 1, 0),
}
SCHEMES = [("Evidence K1-K4 (base)", None), ("Without K4 (K1-K3)", (1, 1, 1, 0)), ("K1 only", (1, 0, 0, 0)), ("K2 only", (0, 1, 0, 0)),
           ("K3 only", (0, 0, 1, 0)), ("K4 only", (0, 0, 0, 1)), ("Equal weights (10% each)", "equal")]
MC_DRAWS, KAPPA_WEIGHTS, KAPPA_MATRICES, SEED = 20000, 60.0, 40.0, 2026


def qfd_loops(R, RC, CT):
    """Literal version with loops: RT[i,j,k] = CT[j,k] RC[i,j] / 100;  BT[k] = sum_i (R_i/100) sum_j RT[i,j,k]."""
    n, m = RC.shape
    p = CT.shape[1]
    RT = np.zeros((n, m, p))
    for k in range(p):
        for i in range(n):
            for j in range(m):
                RT[i, j, k] = CT[j, k] * RC[i, j] / 100
    BT = np.zeros(p)
    for k in range(p):
        for i in range(n):
            s = 0.0
            for j in range(m):
                s += RT[i, j, k]
            BT[k] += s * R[i] / 100
    return RT, BT


def qfd(R, RC, CT):
    """Matrix version: BT = (R/100) @ (RC/100) @ CT."""
    RT = RC[:, :, None] * CT[None, :, :] / 100
    return RT, (R / 100) @ (RC / 100) @ CT


def evidence_matrix():
    return np.array([EVIDENCE[r[0]] for r in REQ], float)


def weights_from_evidence(w=(1, 1, 1, 1)):
    """Requirement weights (%) from the evidence scores, with weights w on the criteria K1-K4 (Equation 18)."""
    total = (evidence_matrix() * np.array(w, float)[None, :]).sum(1)
    return 100 * total / total.sum(), total


def monte_carlo(R, RC, CT, n=MC_DRAWS, kappa_r=KAPPA_WEIGHTS, kappa_m=KAPPA_MATRICES, seed=SEED):
    """Perturb the weights and every matrix row with Dirichlet noise on the non-zero entries (row sums stay 100)."""
    rng = np.random.default_rng(seed)

    def perturb(row, kappa):
        out = np.zeros_like(row)
        idx = row > 0
        out[idx] = rng.dirichlet(row[idx] / row[idx].sum() * kappa) * row.sum()
        return out
    BT = np.zeros((n, CT.shape[1]))
    for t in range(n):
        Rp = perturb(R, kappa_r)
        RCp = np.vstack([perturb(r, kappa_m) for r in RC])
        CTp = np.vstack([perturb(r, kappa_m) for r in CT])
        BT[t] = (Rp / 100) @ (RCp / 100) @ CTp
    return BT


def rank_frequencies(BT):
    """Frequency of every rank (1..p) for every technology."""
    n, p = BT.shape
    order = (-BT).argsort(axis=1).argsort(axis=1)
    return np.array([[np.mean(order[:, k] == r) for r in range(p)] for k in range(p)])


def spearman(a, b):
    ra, rb = a.argsort().argsort().astype(float), b.argsort().argsort().astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


def main():
    utf8_console()
    out = {}
    PA, total = weights_from_evidence()
    assert abs(PA.sum() - 100) < 1e-9
    assert np.allclose(RC.sum(1), 100) and np.allclose(CT.sum(1), 100)
    _, b1 = qfd_loops(R_TEST, RC_TEST, CT_TEST)
    _, b2 = qfd(R_TEST, RC_TEST, CT_TEST)
    assert np.allclose(b1, b2) and np.allclose(b1, BT_TEST, atol=1e-9), b1
    RT, BT = qfd(PA, RC, CT)
    RT_l, BT_l = qfd_loops(PA, RC, CT)
    assert np.allclose(BT, BT_l) and np.allclose(RT, RT_l)
    out["verification"] = {"test_case_BT": b1, "max_difference_loops_vs_matrix": float(np.abs(BT - BT_l).max()), "sum_BT": float(BT.sum())}

    CI = (PA / 100) @ RC                       # importance of the features
    rank = (-BT).argsort().argsort() + 1
    effort = np.array([t[3] for t in TECH], float)
    out["results"] = {"requirements": [r[0] for r in REQ], "evidence": evidence_matrix(), "evidence_total": total, "PA": PA,
                      "feature_importance": CI, "BT": BT, "rank": rank, "effort": effort, "BT_per_effort": BT / effort,
                      "stage": [t[4] for t in TECH], "RC": RC, "CT": CT}
    schemes = []
    for name, w in SCHEMES:
        pa = PA if w is None else (np.full(10, 10.0) if w == "equal" else weights_from_evidence(w)[0])
        bt = qfd(pa, RC, CT)[1]
        schemes.append({"scheme": name, "PA": pa, "BT": bt, "top3": [TECH[k][0] for k in (-bt).argsort()[:3]],
                        "spearman_with_base": spearman(bt, BT)})
    out["weighting_schemes"] = schemes

    MC = monte_carlo(PA, RC, CT)
    freq = rank_frequencies(MC)
    base_order = (-BT).argsort()
    order = (-MC).argsort(axis=1)
    top3, bottom3 = set(base_order[:3]), set(base_order[-3:])
    out["monte_carlo"] = {
        "draws": MC_DRAWS, "mean": MC.mean(0), "p05": np.percentile(MC, 5, axis=0), "p95": np.percentile(MC, 95, axis=0),
        "rank_frequencies": freq, "p_top3": freq[:, :3].sum(1), "p_rank1": freq[:, 0],
        "p_exact_top3_set": float(np.mean([set(r[:3]) == top3 for r in order])),
        "p_bottom3_within_lowest4": float(np.mean([bottom3 <= set(r[-4:]) for r in order])),
        "median_spearman_with_base": float(np.median([spearman(m, BT) for m in MC])),
    }
    res = ensure(DESIGN_RESULTS)
    write_json(res / "qfd_results.json", out)

    # ---------------- Excel workbook
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    wb = Workbook(); wb.remove(wb.active)

    def sheet(title, header, rows, widths):
        ws = wb.create_sheet(title); ws.append(header)
        for c in ws[1]:
            c.font = Font(bold=True); c.fill = PatternFill("solid", fgColor="F2F2F2"); c.alignment = Alignment(wrap_text=True, vertical="top")
        for r in rows:
            ws.append([x.item() if hasattr(x, "item") else x for x in r])
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
    sheet("Requirements", ["Code", "Requirement", "K1", "K2", "K3", "K4", "Total", "PA (%)"],
          [[c, t, *EVIDENCE[c], total[i], round(float(PA[i]), 2)] for i, (c, t) in enumerate(REQ)], [6, 80, 6, 6, 6, 6, 8, 9])
    sheet("Features", ["Code", "Feature", "Importance (%)"], [[c, t, round(float(CI[j]), 2)] for j, (c, t) in enumerate(FEATURES)], [6, 100, 15])
    sheet("RC", ["Requirement / Feature"] + [c[0] for c in FEATURES], [[REQ[i][0]] + RC[i].tolist() for i in range(10)], [24] + [7] * 10)
    sheet("CT", ["Feature / Technology"] + [t[0] for t in TECH], [[FEATURES[j][0]] + CT[j].tolist() for j in range(10)], [24] + [7] * 9)
    mc = out["monte_carlo"]
    sheet("Benefits", ["Code", "Technology", "BT (%)", "Rank", "Effort (1-3)", "BT / effort", "MC 5%", "MC 95%", "P(top 3)", "Stage"],
          [[t[0], t[1], round(float(BT[k]), 3), rank[k], t[3], round(float(BT[k] / t[3]), 2), round(float(mc["p05"][k]), 2),
            round(float(mc["p95"][k]), 2), round(float(mc["p_top3"][k]), 3), t[4]] for k, t in enumerate(TECH)], [6, 78, 9, 6, 12, 11, 9, 9, 9, 7])
    sheet("Weighting schemes", ["Scheme"] + [t[0] for t in TECH] + ["Spearman"],
          [[s["scheme"]] + [round(float(x), 2) for x in s["BT"]] + [round(s["spearman_with_base"], 3)] for s in schemes], [28] + [8] * 10)
    wb.save(res / "qfd_matrices_and_results.xlsx")

    print("PA (%):", np.round(PA, 1))
    print("BT (%):", np.round(BT, 2), "| ranks:", rank.tolist())
    print("Monte Carlo P(top 3):", np.round(mc["p_top3"], 2))
    print("code verification (test case, loops = matrix): OK")


if __name__ == "__main__":
    main()
