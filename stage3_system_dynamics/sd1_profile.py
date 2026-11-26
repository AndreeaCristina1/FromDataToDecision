# -*- coding: utf-8 -*-
"""Profile of the calibration error over the midpoint of the policy ramp (2005-2018), recalibrating the other parameters.

Usage:  python stage3_system_dynamics/sd1_profile.py        (slow)
Output: results/calibration_profile_policy_midpoint.json
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.argv = [sys.argv[0], "--wide"]
import sd1_calibrate as C
import sd1_model as M

if __name__ == "__main__":
    out = {}
    rng = np.random.default_rng(5)
    for year in range(2005, 2019):
        M.PARAMS["pol_mid"] = float(year - 2001); M.PARAMS["pol_k"] = 0.4
        value, params = C.search(rng, 15000, 5)
        out[year] = {"objective": value, "params": {k: float(v) for k, v in params.items()}}
        print(year, round(value, 3), flush=True)
    json.dump(out, open(C.SD_RESULTS / "calibration_profile_policy_midpoint.json", "w"), indent=1)
