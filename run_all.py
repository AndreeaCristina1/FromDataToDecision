# -*- coding: utf-8 -*-
"""Rebuild all results of the repository (except the slow calibration of Model 1).

Usage (from the repository root):  python run_all.py
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    ("Processed data", "data/build_processed.py"),
    ("Stage 1: descriptive analysis", "stage1_describe/describe.py"),
    ("Stage 2: gradient boosting", "stage2_forecast/train_gbm.py"),
    ("Stage 2: baselines and diagnostics", "stage2_forecast/baselines.py"),
    ("Stage 3: system dynamics models", "stage3_system_dynamics/run_models.py"),
    ("Stage 3: HTML simulators", "stage3_system_dynamics/simulators/build_simulators.py"),
    ("Stage 4: QFD", "stage4_design/qfd_model.py"),
    ("Stage 4: financial model", "stage4_design/financial_model.py"),
    ("Stage 4: Business Model Canvas", "stage4_design/build_canvas_html.py"),
    ("Figures", "figures/make_figures.py"),
    ("Check of the article's numbers", "verification/check_article_numbers.py"),
]

if __name__ == "__main__":
    for title, script in STEPS:
        print(f"\n=== {title}  ({script})", flush=True)
        t0 = time.time()
        r = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT)
        if r.returncode != 0:
            sys.exit(f"Error in {script} (exit code {r.returncode})")
        print(f"--- done in {time.time() - t0:.1f} s", flush=True)
    print("\nAll steps completed.")
