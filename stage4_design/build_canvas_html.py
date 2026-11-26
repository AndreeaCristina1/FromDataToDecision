# -*- coding: utf-8 -*-
"""Build the self-contained HTML Business Model Canvas (no external dependencies) from canvas_data.py and financial_model.py."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canvas_data as CD
import financial_model as FM

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "business_model_canvas.html")
v = FM.v
DATA = {
    "tags": CD.TAGS,
    "blocks": [{"id": b["id"], "title": b["title"], "items": [{"t": t, "g": g, "r": r} for t, g, r in b["items"]]} for b in CD.BLOCKS],
    "kpi": [list(k) for k in CD.KPI],
    "params": {
        "s": 20.0, "price": v["price"], "commission": v["commission"] * 100, "guesthouses": v["guesthouses"], "subscribers": v["subscribers"] * 100,
        "fee": v["monthly_fee"], "promotion": v["promotion"], "reports": v["reports"], "investment": v["investment"],
        "staff": v["staff"], "cloud": v["cloud"], "marketing": v["marketing"], "legal": v["legal"],
    },
    "const": {"arrivals": v["arrivals_agro"], "stay": v["mean_stay"], "cpct": v["payment_pct"], "cfix": v["payment_fix"], "subRef": v["subscribers"],
              "nights": v["nights_agro"], "occAgro": v["occupancy_agro"], "occCounty": v["occupancy_county"]},
    "ramp": {"s": [0.25, 0.6, 1.0, 1.25, 1.5], "a": [0.375, 0.75, 1.0, 1.125, 1.25]},
}

PAGE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Business Model Canvas – agritourism platform, Gorj</title>
<style>
:root{--bg:#f6f5f1;--surface:#fff;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--line:#e1e0d9;--axis:#c3c2b7;--chip:#efeee9;--accent:#2a78d6;
--blue:#2a78d6;--orange:#eb6834;--aqua:#1baf7a;--violet:#6250d6;--yellow:#eda100;--red:#e34948;
--t-R:#d5f0e4;--tc-R:#0c6844;--t-M:#e4e0fa;--tc-M:#3a2d98;--t-O:#dbe8f9;--tc-O:#144b92;--t-E:#fbe3d6;--tc-E:#8a3410;--radius:12px;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#898781;--line:#2c2c2a;--axis:#383835;--chip:#262624;--accent:#3987e5;
--blue:#3987e5;--orange:#d95926;--aqua:#199e70;--violet:#9085e9;--yellow:#c98500;--red:#e66767;--t-R:#123d2c;--tc-R:#8ddcb7;--t-M:#2c2760;--tc-M:#bdb6f5;--t-O:#1c3556;--tc-O:#9cc4f5;--t-E:#4a2515;--tc-E:#f2b394;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#898781;--line:#2c2c2a;--axis:#383835;--chip:#262624;--accent:#3987e5;
--blue:#3987e5;--orange:#d95926;--aqua:#199e70;--violet:#9085e9;--yellow:#c98500;--red:#e66767;--t-R:#123d2c;--tc-R:#8ddcb7;--t-M:#2c2760;--tc-M:#bdb6f5;--t-O:#1c3556;--tc-O:#9cc4f5;--t-E:#4a2515;--tc-E:#f2b394;color-scheme:dark}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header.top{padding:18px 20px 6px;max-width:1500px;margin:0 auto}
header.top h1{font-size:22px;margin:0 0 4px;font-weight:650;letter-spacing:-.01em}
header.top p{margin:0;color:var(--ink2);max-width:1000px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;max-width:1500px;margin:10px auto 0;padding:0 20px}
button.btn{font:inherit;font-size:13.5px;padding:7px 12px;border-radius:9px;border:1px solid var(--line);background:var(--surface);color:var(--ink);cursor:pointer}
button.btn:hover{border-color:var(--accent)}button.btn.on{background:var(--accent);border-color:var(--accent);color:#fff}
.sep{width:1px;height:22px;background:var(--line);margin:0 4px}
.status{font-size:12.5px;color:var(--muted)}
.chip{display:inline-block;font-size:11px;font-weight:650;padding:1px 7px;border-radius:7px;cursor:pointer;user-select:none;white-space:nowrap}
.chip.R{background:var(--t-R);color:var(--tc-R)}.chip.M{background:var(--t-M);color:var(--tc-M)}.chip.O{background:var(--t-O);color:var(--tc-O)}.chip.E{background:var(--t-E);color:var(--tc-E)}
.filter .chip{padding:3px 10px;font-size:12.5px;opacity:.55;border:1px solid transparent}.filter .chip.on{opacity:1;border-color:currentColor}
main{max-width:1500px;margin:0 auto;padding:10px 20px 40px}
.canvas{display:grid;grid-template-columns:repeat(10,1fr);gap:8px;grid-template-areas:
"par par act act val val rel rel seg seg" "par par res res val val can can seg seg" "cos cos cos cos cos ven ven ven ven ven"}
.blk{background:var(--surface);border:1px solid var(--line);border-top:4px solid var(--bc);border-radius:var(--radius);padding:10px 12px;min-width:0}
.blk h2{font-size:13px;text-transform:uppercase;letter-spacing:.05em;margin:0 0 6px;color:var(--bc);display:flex;justify-content:space-between;align-items:center;gap:6px}
.blk ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:7px}
.blk li{display:flex;gap:6px;align-items:flex-start;font-size:13px;line-height:1.38}
.blk li.dim{opacity:.22}
.blk li .tw{flex:1;min-width:0}.blk li .t{display:block;outline:none;border-radius:4px;padding:0 2px}.blk li .t:focus{background:var(--chip)}
.blk li .src{display:block;font-size:11px;color:var(--muted)}
.blk li .x{border:0;background:none;color:var(--muted);cursor:pointer;font-size:15px;line-height:1;padding:0 2px;opacity:0}.blk li:hover .x{opacity:1}
.add{border:1px dashed var(--axis);background:none;color:var(--muted);border-radius:7px;font-size:12px;padding:1px 8px;cursor:pointer}.add:hover{color:var(--accent);border-color:var(--accent)}
.a-par{grid-area:par;--bc:var(--violet)}.a-act{grid-area:act;--bc:var(--violet)}.a-res{grid-area:res;--bc:var(--violet)}.a-val{grid-area:val;--bc:var(--orange)}
.a-rel{grid-area:rel;--bc:var(--aqua)}.a-can{grid-area:can;--bc:var(--aqua)}.a-seg{grid-area:seg;--bc:var(--aqua)}.a-cos{grid-area:cos;--bc:var(--red)}.a-ven{grid-area:ven;--bc:var(--blue)}
@media (max-width:1000px){.canvas{grid-template-columns:1fr 1fr;grid-template-areas:"val val" "seg rel" "can par" "act res" "cos ven"}}
@media (max-width:620px){.canvas{grid-template-columns:1fr;grid-template-areas:"seg" "val" "can" "rel" "par" "act" "res" "cos" "ven"}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:14px;margin-top:14px}
.card h2{font-size:16px;margin:0 0 2px;font-weight:650}.card .sub{font-size:12.5px;color:var(--muted);margin:0 0 10px}
.fin{display:grid;grid-template-columns:330px 1fr;gap:16px}@media (max-width:980px){.fin{grid-template-columns:1fr}}
.sl{margin:8px 0 10px}.sl .row{display:flex;justify-content:space-between;gap:8px;font-size:13.5px}.sl label{font-weight:550}.sl .val{font-variant-numeric:tabular-nums}
.sl input[type=range]{width:100%;accent-color:var(--accent)}.sl .help{font-size:12px;color:var(--muted);line-height:1.35}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:12px}
.kpi{background:var(--chip);border-radius:10px;padding:9px 11px}.kpi .k{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.kpi .v{font-size:19px;font-weight:650;font-variant-numeric:tabular-nums}.kpi .d{font-size:12px;color:var(--ink2)}.kpi.neg .v{color:var(--red)}.kpi.pos .v{color:var(--aqua)}
.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:14px}@media (max-width:520px){.charts{grid-template-columns:1fr}}
svg{width:100%;height:auto;display:block}svg text{fill:var(--ink2);font:11px system-ui,sans-serif}svg .ax{stroke:var(--axis)}svg .gr{stroke:var(--line)}
.legend{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:12.5px;color:var(--ink2);margin:4px 0 0}.legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.note{font-size:12.5px;color:var(--muted);margin-top:8px}.foot{max-width:1500px;margin:0 auto;padding:0 20px 30px;font-size:12.5px;color:var(--muted)}
@media print{body{background:#fff;color:#000}.bar,.fin .controls,.add,.x{display:none!important}.blk,.card{break-inside:avoid;border-color:#999}.canvas{gap:6px}}
</style></head><body>
<header class="top"><h1>Business Model Canvas – destination platform for agritourism in Gorj County</h1>
<p>Business model of the platform specified in the article, in nine blocks; every block is a hypothesis. Texts can be edited (click on the text); the provenance tag changes when clicked
(R = real data, M = result of the analyses and models, O = online source, E = estimate). The financial panel recalculates the result and the break-even share.</p></header>
<div class="bar"><span class="filter" id="filter"></span><span class="sep"></span>
<button class="btn" id="bTheme">Theme</button><button class="btn" id="bPrint">Print</button><button class="btn" id="bExp">Export JSON</button>
<button class="btn" id="bImp">Import JSON</button><button class="btn" id="bReset">Reset</button><span class="status" id="status"></span>
<input type="file" id="file" accept="application/json" style="display:none"></div>
<main><div class="canvas" id="canvas"></div>
<section class="card"><h2>Simplified financial model and break-even share</h2>
<p class="sub">Equations 21–24 of the article. Values tagged “estimate” are assumptions to be replaced by measured data; arrivals and length of stay are official INS data.</p>
<div class="fin"><div class="controls" id="controls"></div><div><div class="kpis" id="kpis"></div><div class="charts"><div><div id="c1"></div><div class="legend" id="l1"></div></div><div><div id="c2"></div><div class="legend" id="l2"></div></div></div>
<div style="overflow:auto;margin-top:12px"><table id="tbl"></table></div><p class="note" id="gap"></p></div></div></section>
<section class="card"><h2>Indicators to track</h2><p class="sub">Baseline values and targets for year 3.</p><div style="overflow:auto"><table id="kpit"></table></div></section></main>
<div class="foot">Supplementary material of the article (see the repository README). Costs, prices, commission, subscription and revenue assumptions are illustrative estimates; the results are not forecasts.</div>
<script>
const D = __DATA__;
const KEY = "canvas_agritourism_gorj_en_v1";
let st = {blocks: JSON.parse(JSON.stringify(D.blocks)), params: Object.assign({}, D.params), theme: "auto"};
let flt = null; // highlighted tag
const $ = id => document.getElementById(id);
const fmt = (x, d=0) => x.toLocaleString("en-US", {minimumFractionDigits: d, maximumFractionDigits: d});
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const TAGS = Object.keys(D.tags);
function save(){try{localStorage.setItem(KEY, JSON.stringify(st)); $("status").textContent = "Changes saved in this browser";}catch(e){$("status").textContent = "Browser storage is not available (use Export JSON)";}}
function load(){try{const s = JSON.parse(localStorage.getItem(KEY) || "null"); if(s && s.blocks && s.params){st.blocks = s.blocks; st.params = Object.assign({}, D.params, s.params); st.theme = s.theme || "auto";}}catch(e){}}
function applyTheme(){const r = document.documentElement; if(st.theme === "auto") r.removeAttribute("data-theme"); else r.setAttribute("data-theme", st.theme); $("bTheme").textContent = "Theme: " + {auto:"automatic", light:"light", dark:"dark"}[st.theme];}

// ------------------------ canvas ------------------------
const CLS = {par:"a-par", act:"a-act", res:"a-res", val:"a-val", rel:"a-rel", can:"a-can", seg:"a-seg", cos:"a-cos", ven:"a-ven"};
function renderCanvas(){
  const el = $("canvas"); el.innerHTML = "";
  st.blocks.forEach((b, bi) => {
    const sec = document.createElement("section"); sec.className = "blk " + CLS[b.id];
    sec.innerHTML = `<h2><span>${esc(b.title)}</span><button class="add" title="Add a row">+ row</button></h2><ul></ul>`;
    const ul = sec.querySelector("ul");
    b.items.forEach((it, ii) => {
      const li = document.createElement("li"); if(flt && it.g !== flt) li.className = "dim";
      li.innerHTML = `<span class="chip ${it.g}" title="Click to change provenance (${esc(D.tags[it.g])})">${it.g}</span><span class="tw"><span class="t" contenteditable="true" spellcheck="false">${esc(it.t)}</span><span class="src">${esc(it.r || "")}</span></span><button class="x" title="Delete row">×</button>`;
      li.querySelector(".chip").onclick = () => {it.g = TAGS[(TAGS.indexOf(it.g) + 1) % TAGS.length]; save(); renderCanvas();};
      const t = li.querySelector(".t");
      t.onblur = () => {const txt = t.innerText.trim(); if(txt){it.t = txt; save();} else {t.textContent = it.t;}};
      li.querySelector(".x").onclick = () => {b.items.splice(ii, 1); save(); renderCanvas();};
      ul.appendChild(li);
    });
    sec.querySelector(".add").onclick = () => {b.items.push({t:"New text", g:"E", r:"assumption"}); save(); renderCanvas();};
    el.appendChild(sec);
  });
}
function renderFilter(){
  const f = $("filter"); f.innerHTML = "Provenance: ";
  TAGS.forEach(g => {const c = document.createElement("span"); c.className = "chip " + g + (flt === g ? " on" : ""); c.textContent = g + " · " + D.tags[g];
    c.onclick = () => {flt = flt === g ? null : g; renderFilter(); renderCanvas();}; f.appendChild(c); f.appendChild(document.createTextNode(" "));});
}

// ------------------------ financial model (same formulas as financial_model.py) ------------------------
const C = D.const;
function econ(p, s, a, dat){
  const fixed = p.staff + p.cloud + p.marketing + p.legal;
  const arrivals = C.arrivals * s, gmv = arrivals * C.stay * p.price;
  const r_com = p.commission / 100 * gmv, r_abo = p.guesthouses * a * p.fee * 12, r_prom = p.promotion * Math.min(1, a / C.subRef), r_date = dat;
  const venit = r_com + r_abo + r_prom + r_date, c_plata = C.cpct * gmv + C.cfix * arrivals;
  return {s, arrivals, gmv, r_com, r_abo, r_prom, r_date, venit, c_plata, fixed, rez: venit - c_plata - fixed};
}
function prag(p, a, dat){let lo = 0, hi = 1; for(let i = 0; i < 80; i++){const m = (lo + hi) / 2; if(econ(p, m, a, dat).rez < 0) lo = m; else hi = m;} return hi;}
const SL = [
  ["s","Share of agritourism arrivals booked through the platform (year 3)",0,50,0.5,v=>fmt(v,1)+"%","estimate","Year-3 target; the five-year trajectory uses 25%, 60%, 100%, 125% and 150% of this value."],
  ["price","Price per person-night (RON)",80,250,5,v=>fmt(v)+" RON","estimate","The most uncertain assumption; replace it with guesthouse tariffs."],
  ["commission","Commission on direct bookings",3,15,0.5,v=>fmt(v,1)+"%","estimate","Large intermediaries charge about 15%."],
  ["guesthouses","Agritourism guesthouses in the county",50,400,5,v=>fmt(v),"estimate","About 150, derived from 472,302 bed-days; replace with the official register."],
  ["subscribers","Hosts with a paid subscription (year 3)",0,100,1,v=>fmt(v)+"%","estimate",""],
  ["fee","Subscription fee (RON per month)",0,300,1,v=>fmt(v)+" RON","estimate",""],
  ["promotion","Promotion revenue (RON per year)",0,50000,500,v=>fmt(v),"estimate",""],
  ["reports","Reports for authorities (RON per year, from year 2)",0,100000,1000,v=>fmt(v),"estimate","Institutional revenue; without it the break-even share rises."],
  ["investment","Initial investment (RON)",0,600000,5000,v=>fmt(v),"estimate",""],
  ["staff","Staff (RON per year)",0,300000,2000,v=>fmt(v),"estimate",""],
  ["cloud","Cloud and licences (RON per year)",0,100000,1000,v=>fmt(v),"estimate",""],
  ["marketing","Marketing and content (RON per year)",0,150000,1000,v=>fmt(v),"estimate",""],
  ["legal","Legal, accounting, data protection (RON per year)",0,60000,500,v=>fmt(v),"estimate",""],
];
function renderControls(){
  const el = $("controls"); el.innerHTML = '<div class="status" style="margin-bottom:6px">Payment cost: 1.5% + RON 1 per transaction (fixed in the model). Mean stay: 1.90 nights; arrivals: 31,073 (2025).</div>';
  SL.forEach(([k, lab, mn, mx, stp, f, tg, help]) => {
    const d = document.createElement("div"); d.className = "sl";
    d.innerHTML = `<div class="row"><label for="in_${k}">${lab}</label><span class="val" id="v_${k}"></span></div><input type="range" id="in_${k}" min="${mn}" max="${mx}" step="${stp}">${help ? `<div class="help">${help}</div>` : ""}`;
    el.appendChild(d); const i = d.querySelector("input"); i.value = st.params[k]; $("v_" + k).textContent = f(+st.params[k]);
    i.oninput = () => {st.params[k] = +i.value; $("v_" + k).textContent = f(+i.value); save(); renderFin();};
  });
}
function line(x1, y1, x2, y2, cls){return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="${cls}"/>`;}
function renderFin(){
  const p = st.params, a3 = p.subscribers / 100, s3 = p.s / 100, d3 = p.reports;
  const e3 = econ(p, s3, a3, d3), pr = prag(p, a3, d3), prNo = prag(p, a3, 0);
  const rows = []; let cum = -p.investment, minCum = cum;
  D.ramp.s.forEach((fs, i) => {const a = Math.min(1, a3 * D.ramp.a[i]), r = econ(p, s3 * fs, a, i === 0 ? 0 : d3); cum += r.rez; minCum = Math.min(minCum, cum); rows.push(Object.assign({an: i + 1, cum}, r));});
  const k = (cls, kk, vv, dd) => `<div class="kpi ${cls}"><div class="k">${kk}</div><div class="v">${vv}</div><div class="d">${dd}</div></div>`;
  $("kpis").innerHTML = k("", "Arrivals via platform", fmt(e3.arrivals), "in year 3") + k("", "Value of bookings", fmt(e3.gmv / 1000) + "k RON", "commission base") +
    k("", "Revenue / costs", fmt(e3.venit / 1000) + "k / " + fmt((e3.fixed + e3.c_plata) / 1000) + "k RON", "year 3") +
    k(e3.rez < 0 ? "neg" : "pos", "Result in year 3", fmt(e3.rez / 1000, 1) + "k RON", e3.rez < 0 ? "below break-even" : "above break-even") +
    k("", "Break-even share", fmt(pr * 100, 1) + "%", "of agritourism arrivals; without reports: " + fmt(prNo * 100, 1) + "%") +
    k(minCum < 0 ? "neg" : "pos", "Maximum financing need", fmt(Math.max(0, -minCum) / 1000) + "k RON", "investment + cumulative losses");
  // chart 1: revenue and costs by share s
  const W = 520, H = 280, L = 44, Rr = 12, T = 14, B = 34, grid = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40];
  const cols = ["var(--blue)", "var(--violet)", "var(--aqua)", "var(--yellow)"], names = ["commission", "subscriptions", "promotion", "reports for authorities"];
  const sc = grid.map(s => econ(p, s, a3, d3)), ymax = Math.max(...sc.map(e => Math.max(e.venit, e.fixed + e.c_plata))) * 1.1;
  const X = i => L + (i + 0.5) * (W - L - Rr) / grid.length, Y = v => T + (H - T - B) * (1 - v / ymax), bw = (W - L - Rr) / grid.length * 0.62;
  let g = ""; for(let i = 0; i <= 4; i++){const vv = ymax * i / 4; g += line(L, Y(vv), W - Rr, Y(vv), "gr") + `<text x="${L - 6}" y="${Y(vv) + 4}" text-anchor="end">${fmt(vv / 1000)}</text>`;}
  sc.forEach((e, i) => {let b = 0; [e.r_com, e.r_abo, e.r_prom, e.r_date].forEach((vv, j) => {g += `<rect x="${X(i) - bw / 2}" y="${Y(b + vv)}" width="${bw}" height="${Math.max(0, Y(b) - Y(b + vv))}" fill="${cols[j]}"><title>${names[j]}: ${fmt(vv / 1000, 1)}k RON</title></rect>`; b += vv;});
    g += `<text x="${X(i)}" y="${H - B + 14}" text-anchor="middle">${fmt(grid[i] * 100)}%</text>`;});
  g += `<polyline fill="none" stroke="var(--red)" stroke-width="2.2" points="${sc.map((e, i) => X(i) + "," + Y(e.fixed + e.c_plata)).join(" ")}"/>` + sc.map((e, i) => `<circle cx="${X(i)}" cy="${Y(e.fixed + e.c_plata)}" r="3.5" fill="var(--red)"><title>costs: ${fmt((e.fixed + e.c_plata) / 1000, 1)}k RON</title></circle>`).join("");
  g += `<text x="${(L + W - Rr) / 2}" y="${H - 4}" text-anchor="middle">share of agritourism arrivals via the platform · thousand RON per year</text>`;
  $("c1").innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Revenue and costs by share of arrivals">${g}</svg>`;
  $("l1").innerHTML = names.map((n, j) => `<span><i style="background:${cols[j]}"></i>${n}</span>`).join("") + `<span><i style="background:var(--red)"></i>costs (fixed + payments)</span>`;
  // chart 2: five years
  const ys = rows.map(r => r.cum / 1000).concat(rows.map(r => r.rez / 1000), [0]), y0 = Math.min(...ys) * 1.1, y1 = Math.max(...ys, 10) * 1.2;
  const X2 = i => L + (i + 0.5) * (W - L - Rr) / 5, Y2 = v => T + (H - T - B) * (1 - (v - y0) / (y1 - y0)), bw2 = (W - L - Rr) / 5 * 0.4;
  let g2 = ""; for(let i = 0; i <= 4; i++){const vv = y0 + (y1 - y0) * i / 4; g2 += line(L, Y2(vv), W - Rr, Y2(vv), "gr") + `<text x="${L - 6}" y="${Y2(vv) + 4}" text-anchor="end">${fmt(vv, 0)}</text>`;}
  g2 += line(L, Y2(0), W - Rr, Y2(0), "ax");
  rows.forEach((r, i) => {const vv = r.rez / 1000; g2 += `<rect x="${X2(i) - bw2 / 2}" y="${Math.min(Y2(0), Y2(vv))}" width="${bw2}" height="${Math.abs(Y2(vv) - Y2(0))}" fill="${vv < 0 ? "var(--red)" : "var(--aqua)"}"><title>Year ${r.an}: result ${fmt(vv, 1)}k RON</title></rect><text x="${X2(i)}" y="${H - B + 14}" text-anchor="middle">year ${r.an}</text>`;});
  g2 += `<polyline fill="none" stroke="var(--ink)" stroke-width="2" points="${rows.map((r, i) => X2(i) + "," + Y2(r.cum / 1000)).join(" ")}"/>` + rows.map((r, i) => `<circle cx="${X2(i)}" cy="${Y2(r.cum / 1000)}" r="3.5" fill="var(--ink)"><title>Cumulative balance: ${fmt(r.cum / 1000, 0)}k RON</title></circle><text x="${X2(i)}" y="${Y2(r.cum / 1000) + 15}" text-anchor="middle">${fmt(r.cum / 1000)}</text>`).join("");
  g2 += `<text x="${(L + W - Rr) / 2}" y="${H - 4}" text-anchor="middle">annual result and cumulative balance (with initial investment) · thousand RON</text>`;
  $("c2").innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Five-year trajectory">${g2}</svg>`;
  $("l2").innerHTML = `<span><i style="background:var(--red)"></i>negative result</span><span><i style="background:var(--aqua)"></i>positive result</span><span><i style="background:var(--ink)"></i>cumulative balance</span>`;
  $("tbl").innerHTML = "<tr><th>Year</th><th class='n'>Share</th><th class='n'>Arrivals via platform</th><th class='n'>Value of bookings</th><th class='n'>Revenue</th><th class='n'>Costs</th><th class='n'>Result</th><th class='n'>Cumulative balance</th></tr>" +
    rows.map(r => `<tr><td>${r.an}</td><td class="n">${fmt(r.s * 100)}%</td><td class="n">${fmt(r.arrivals)}</td><td class="n">${fmt(r.gmv / 1000)}</td><td class="n">${fmt(r.venit / 1000)}</td><td class="n">${fmt((r.fixed + r.c_plata) / 1000)}</td><td class="n">${fmt(r.rez / 1000)}</td><td class="n">${fmt(r.cum / 1000)}</td></tr>`).join("") + "<tr><td colspan='8' class='status'>thousand RON, except arrivals</td></tr>";
  const fac = C.occCounty / C.occAgro, ex = C.nights * (fac - 1), exS = ex / C.stay, exV = ex * p.price;
  $("gap").innerHTML = `<b>Value for the destination.</b> If agritourism occupancy rose from ${fmt(C.occAgro, 1)}% to the county level (${fmt(C.occCounty, 1)}%) without new capacity, overnight stays would be ${fmt(fac, 2)} times higher: about ${fmt(ex)} extra overnight stays (${fmt(exS)} arrivals) per year, or about RON ${fmt(exV / 1e6, 2)} million of revenue for hosts, of which the platform commission would be about RON ${fmt(exV * p.commission / 100 / 1000)}k.`;
}
function renderKpi(){
  $("kpit").innerHTML = "<tr><th>Indicator</th><th>Baseline</th><th>Target (year 3)</th><th>Measurement source</th></tr>" + D.kpi.map(r => "<tr>" + r.map(c => `<td>${esc(c)}</td>`).join("") + "</tr>").join("");
}

// ------------------------ buttons ------------------------
$("bTheme").onclick = () => {st.theme = {auto:"light", light:"dark", dark:"auto"}[st.theme]; applyTheme(); save();};
$("bPrint").onclick = () => window.print();
$("bReset").onclick = () => {if(confirm("Restore the initial content and assumptions?")){st.blocks = JSON.parse(JSON.stringify(D.blocks)); st.params = Object.assign({}, D.params); flt = null; try{localStorage.removeItem(KEY);}catch(e){} init(); $("status").textContent = "Content restored";}};
$("bExp").onclick = () => {const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(st, null, 1)], {type: "application/json"})); a.download = "agritourism-platform-canvas.json"; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);};
$("bImp").onclick = () => $("file").click();
$("file").onchange = e => {const f = e.target.files[0]; if(!f) return; const r = new FileReader(); r.onload = () => {try{const s = JSON.parse(r.result); if(!s.blocks || !s.params) throw 0; st.blocks = s.blocks; st.params = Object.assign({}, D.params, s.params); st.theme = s.theme || "auto"; save(); init(); $("status").textContent = "File imported";}catch(x){alert("Unsuitable JSON file.");}}; r.readAsText(f);};
function init(){applyTheme(); renderFilter(); renderCanvas(); renderControls(); renderFin(); renderKpi();}
load(); init();
</script></body></html>"""

html = PAGE.replace("__DATA__", json.dumps(DATA, ensure_ascii=False))
open(OUT, "w", encoding="utf-8").write(html)
print("written", os.path.basename(OUT), round(len(html) / 1024), "KB")
