# -*- coding: utf-8 -*-
"""Assemble the two self-contained HTML simulators (no external dependencies) from src/ and the observed INS data."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import sd1_model as M1
from common.tempo import AGRO, load_panel

read = lambda f: (HERE / "src" / f).read_text(encoding="utf-8")

PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>{css}</style></head><body>
<header class="top"><div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start"><h1>{h1}</h1><span id="themebtn"></span></div>
<p>{intro}</p><div class="badges">{badges}</div></header>
<div class="layout"><aside class="controls" id="controls"></aside><main class="stage" id="stage"></main></div>
<div class="foot">{foot}</div>
<script>const DATA = {data};</script>
<script>{common}</script><script>{core}</script><script>{app}</script></body></html>"""


def main():
    X = M1.real_series()
    data = {"years": list(range(2001, 2026)), "CH": X["CH"].tolist(), "CA": X["CA"].tolist(), "NH": X["NH"].tolist(), "NA": X["NA"].tolist(),
            "CAlte": X["COther"].tolist(), "Nt": X["Nt"].tolist(), "Ct": X["Ct"].tolist(),
            "SosA": np.nan_to_num(load_panel("S")[(AGRO, "TOTAL")]).tolist()}
    css, common = read("common.css"), read("common.js")

    def page(title, h1, intro, badges, foot, core, app):
        return PAGE.format(title=title, css=css, h1=h1, intro=intro, badges="".join(f'<span class="badge">{b}</span>' for b in badges),
                           foot=foot, data=json.dumps(data), common=common, core=core, app=app)

    p1 = page("SD Simulator 1 – hotel and agritourism capacity, Gorj",
              "Simulator 1: hotel and agritourism accommodation capacity, Gorj County",
              "System dynamics model with three stocks (hotel capacity, agritourism capacity, reputation), a Bass reputation loop (R1), a saturation "
              "brake (B1), substitution through the allocation of total demand and a public-policy channel. Change the parameters and compare the "
              "simulation with the observed INS data for 2001–2025.",
              ["<b>Observed data:</b> INS TEMPO-Online, 2001–2025", "<b>Step:</b> annual", "<b>Article:</b> Sections 3.5 and 4.3"],
              "Supplementary material of the article (see the repository README). Equations and parameters as in the article. Results are scenarios, not official forecasts.",
              read("sd1core.js"), read("sd1_app.js"))
    p2 = page("SD Simulator 2 – community quality of life, Gorj",
              "Simulator 2: community quality of life and acceptance of digital technologies",
              "Exploratory scenario model with two stocks: acceptance of digital technologies by residents (Bass diffusion, slowed by tourism pressure) and "
              "quality of life (life satisfaction, 1–10), coupled with the agritourism capacity of Model 1.",
              ["<b>Public benchmarks:</b> Eurofound life satisfaction 2003–2016; digital skills", "<b>Coupling:</b> capacity from Model 1",
               "<b>Article:</b> Section 5.3"],
              "Supplementary material of the article. Parameters tagged “scenario” are assumptions; the numerical results are illustrative and are not forecasts.",
              read("sd1core.js") + "\n" + read("sd2core.js"), read("sd2_app.js"))
    for name, html in (("simulator_model1_capacity.html", p1), ("simulator_model2_quality_of_life.html", p2)):
        (HERE / name).write_text(html, encoding="utf-8")
        print("written", name, round(len(html) / 1024), "KB")


if __name__ == "__main__":
    main()
