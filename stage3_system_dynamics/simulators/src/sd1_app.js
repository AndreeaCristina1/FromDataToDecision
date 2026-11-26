/* ===== Simulator 1: hotel and agritourism capacity ===== */
const DEF = { ...SD1_DEFAULT, horizon: 2045, growth: 0, shocks: true };
let S = { ...DEF, year: 2025 };
let REF = null;

const SLIDERS = [
  { grp: 'Reputation of agritourism (Bass loop, R1)', items: [
    { key: 'p', label: 'p – innovation', min: 0.0005, max: 0.1, step: 0.0005, dec: 4, tag: 'cal', help: 'Spontaneous growth of reputation, independent of recommendations by others.' },
    { key: 'q', label: 'q – imitation', min: 0.02, max: 1.5, step: 0.01, dec: 2, tag: 'cal', help: 'Word-of-mouth effect: the higher the reputation, the faster it grows.' },
    { key: 'A0', label: 'A0 – base attractiveness', min: 0.02, max: 2, step: 0.01, dec: 2, tag: 'cal', help: 'Attractiveness of one agritourism bed-day relative to a hotel bed-day at zero reputation.' } ] },
  { grp: 'Investment and public policy (agritourism)', items: [
    { key: 'gamma', label: 'γ – investment from reputation', min: 0, max: 150000, step: 500, fmt: v => nf(v, 0), tag: 'cal', help: 'Bed-days built per unit of reputation growth (reputation is measured from 0 to 1).' },
    { key: 'delta', label: 'δ – policy sensitivity', min: 0, max: 1, step: 0.01, dec: 2, tag: 'sc', help: 'Share of existing capacity added each year at full public support (rural development funding). 0 = no policy channel.' },
    { key: 'polMid', label: 'Midpoint of the policy ramp (year)', min: 0, max: 24, step: 0.5, fmt: v => String((2001 + v).toFixed(1)), tag: 'sc', help: 'Year in which the ramp reaches one half. Assumption: mid-2013, the middle of the two European programming periods. The data cannot identify it.' },
    { key: 'polK', label: 'Slope of the ramp', min: 0.1, max: 1.2, step: 0.05, dec: 2, tag: 'sc', help: '0.4 corresponds to a rise from 10% to 90% in about 11 years.' },
    { key: 'KA', label: 'K_A – carrying capacity', min: 300000, max: 1500000, step: 5000, fmt: v => nf(v, 0), tag: 'cal', help: 'Structural ceiling of agritourism capacity (bed-days); slows investment (loop B1).' } ] },
  { grp: 'Hotel sector', items: [
    { key: 'bH', label: 'β_H – hotel investment', min: 0.02, max: 2.0, step: 0.01, dec: 2, tag: 'cal', help: 'Capacity added each year in proportion to the occupancy rate.' },
    { key: 'dH', label: 'δ_H – hotel depreciation', min: 0.02, max: 0.35, step: 0.005, dec: 3, tag: 'cal', help: 'Fraction of hotel capacity that goes out of use each year.' } ] },
  { grp: 'Exogenous shocks (capacity multipliers)', items: [
    { key: 'shockH2020', label: 'Hotels 2020', min: -0.5, max: 0.5, step: 0.01, dec: 2, tag: 'cal' },
    { key: 'shockH2021', label: 'Hotels 2021', min: -0.5, max: 0.5, step: 0.01, dec: 2, tag: 'cal' },
    { key: 'shockA2020', label: 'Agritourism 2020', min: -0.5, max: 0.5, step: 0.01, dec: 2, tag: 'cal' },
    { key: 'shockA2021', label: 'Agritourism 2021', min: -0.5, max: 0.5, step: 0.01, dec: 2, tag: 'cal' } ] },
  { grp: 'Horizon and demand', items: [
    { key: 'horizon', label: 'Final year of the simulation', min: 2025, max: 2060, step: 1, fmt: v => String(v), tag: 'sc', help: 'Until 2025 the model uses observed demand; afterwards demand follows the assumption below.' },
    { key: 'growth', label: 'Demand growth after 2025', min: -0.03, max: 0.06, step: 0.001, fmt: v => nf(v * 100, 1) + '% per year', tag: 'sc', help: 'Neutral scenario: demand stays at its 2025 level. It affects overnight stays and occupancy, not agritourism capacity.' } ] }
];
const SCEN = [
  { id: 'base', name: 'Calibrated (baseline)', desc: 'Parameters calibrated on 2001–2025, to 2045', patch: {} },
  { id: 'nopol', name: 'No public-policy channel', desc: 'δ = 0: reputation only (to 2060)', patch: { delta: 0, horizon: 2060 } },
  { id: 'dubl', name: 'Policy sensitivity doubled', desc: 'δ × 2: the ceiling is reached earlier (to 2060)', patch: { delta: 0.80044, horizon: 2060 } },
  { id: 'nosoc', name: 'No shocks 2020–2021', desc: 'Counterfactual without shock multipliers', patch: { shocks: false } },
  { id: 'sat', name: 'Long-run saturation', desc: 'Same calibration, horizon 2060', patch: { horizon: 2060 } }
];
const el = {}; let sliderEls = {}, charts = {}, curScen = 'base';
function build() {
  const ctr = $('#controls');
  ctr.append(h('h3', {}, 'Scenarios'));
  const sc = h('div', { class: 'scen' });
  SCEN.forEach(s => { const b = h('button', { class: 'btn' + (s.id === curScen ? ' on' : ''), 'data-id': s.id, onclick: () => applyScenario(s.id) }, s.name, h('small', {}, s.desc)); sc.append(b); });
  ctr.append(sc);
  ctr.append(h('div', { class: 'toolbar' },
    h('button', { class: 'btn', onclick: () => { REF = sd1(S, S.horizon, S.growth, S.shocks); update(); }, title: 'Keep the current trajectory as a dashed grey line for comparison' }, 'Pin as reference'),
    h('button', { class: 'btn ghost', onclick: () => { REF = null; update(); } }, 'Clear reference')));
  SLIDERS.forEach(g => { ctr.append(h('h3', {}, g.grp)); g.items.forEach(d => { const e = makeSlider(d, S, () => { curScen = ''; markScen(); update(); }); sliderEls[d.key] = e; ctr.append(e); }); });
  ctr.append(h('div', { class: 'note' }, 'Tags: ', h('span', { class: 'tag cal' }, 'calibrated'), ' value estimated from the INS series 2001–2025; ', h('span', { class: 'tag sc' }, 'scenario'), ' assumed or varied value.'));
}
function markScen() { document.querySelectorAll('.scen button').forEach(b => b.classList.toggle('on', b.dataset.id === curScen)); }
function applyScenario(id) {
  const sc = SCEN.find(s => s.id === id); curScen = id; const yr = S.year;
  Object.keys(S).forEach(k => delete S[k]); Object.assign(S, DEF, { year: yr }, sc.patch);
  Object.keys(sliderEls).forEach(k => sliderEls[k]._set(S[k])); markScen(); update();
}

function buildStage() {
  const st = $('#stage');
  el.kpis = h('div', { class: 'kpis' });
  st.append(h('div', { class: 'card' }, h('h2', {}, 'Key results'), h('p', { class: 'sub' }, 'Fit to the observed INS series (2001–2025) and milestones of the simulated trajectory.'), el.kpis));
  // diagrama
  el.yr = h('span', { class: 'yr' }, '2025');
  el.scrub = h('input', { type: 'range', min: 2001, max: S.horizon, step: 1, value: S.year });
  el.scrub.addEventListener('input', () => { S.year = +el.scrub.value; drawDiagram(); update(true); });
  el.diag = h('div', {});
  st.append(h('div', { class: 'card' }, h('h2', {}, 'Model structure with the values of the selected year'),
    h('p', { class: 'sub' }, 'Rectangles are stocks, arrows are flows and influences, ellipses are exogenous variables. Move the slider to see how the values change over time.'),
    h('div', { class: 'scrub' }, el.yr, el.scrub), el.diag,
    h('details', { class: 'how' }, h('summary', {}, 'How to read and use the simulator'), h('ul', {},
      h('li', {}, 'Choose a scenario on the left or change any parameter; the charts update immediately.'),
      h('li', {}, 'Points in the charts are observed INS data; lines are model results.'),
      h('li', {}, 'Loop R1 (reputation): reputation grows by imitation and attracts investment. Loop B1: as CA approaches K_A, investment is slowed.'),
      h('li', {}, 'Substitution: total demand is shared among sectors in proportion to capacity times attractiveness; the capacity of other structures is the observed one.'),
      h('li', {}, 'Public policy is a channel separate from occupancy: agritourism investment does not depend on current occupancy.')))));
  // charts
  const grid = h('div', { class: 'charts' });
  const mk = (id, title, sub) => { const c = chartCard(title, sub); charts[id] = c.chart; grid.append(c.card); };
  mk('ca', 'Agritourism capacity (bed-days)', 'Simulated and observed; the dashed line is the carrying capacity K_A');
  mk('ch', 'Hotel capacity (bed-days)', 'Poor fit; the projection after 2025 is not validated');
  mk('n', 'Overnight stays', 'Allocation of total demand among sectors');
  mk('occ', 'Occupancy rate (%)', 'Overnight stays / capacity, by sector');
  mk('rep', 'Reputation, policy ramp and saturation brake', 'REP/M (R1), policy ramp and (1 − CA/K_A) (B1)');
  mk('share', 'Agritourism share of overnight stays (%)', 'Demand allocation: capacity × attractiveness');
  st.append(grid);
  el.table = h('div', {});
  st.append(h('div', { class: 'card' }, h('h2', {}, 'Annual values'), h('p', { class: 'sub' }, 'Selected years of the current trajectory.'),
    h('div', { class: 'toolbar' }, h('button', { class: 'btn', onclick: exportCSV }, 'Download CSV')), el.table));
}
let SIM = null;
function pts(arr, years) { return years.map((y, i) => ({ x: y, y: arr[i] })); }
function realPts(arr) { return DATA.years.map((y, i) => ({ x: y, y: arr[i] })); }
function update(keepScrub) {
  SIM = sd1(S, S.horizon, S.growth, S.shocks);
  const Y = SIM.year, last = Y.length - 1;
  el.scrub.max = S.horizon; if (S.year > S.horizon) S.year = S.horizon; el.scrub.value = S.year; el.yr.textContent = S.year;
  const n25 = 25, r2 = (k, real) => r2score(real, SIM[k].slice(0, n25));
  const sh = (SIM.year[0] === 2001);
  const kp = [
    ['R² agritourism capacity', nf(r2('CA', DATA.CA), 3), 'Observed vs. simulated, 2001–2025'], ['R² agritourism nights', nf(r2('NA', DATA.NA), 3), '2001–2025'],
    ['R² hotel capacity', nf(r2('CH', DATA.CH), 3), 'Poor fit, as reported in the article'], ['R² hotel nights', nf(r2('NH', DATA.NH), 3), '2001–2025'],
    ['CA in 2025', nf(SIM.CA[24], 0), 'Observed: ' + nf(DATA.CA[24], 0)],
    ['CA in ' + S.horizon, nf(SIM.CA[last], 0), pct(SIM.CA[last] / S.KA, 0) + ' of K_A'],
    ['90% / 95% / 99% of K_A', [0.9, 0.95, 0.99].map(f => yearReach(SIM, f, S.KA) ?? '–').join(' / '), 'First year in which CA reaches the level'],
    ['Reputation REP/M in 2025', pct(SIM.REP[24] / S.M, 2), 'Loop R1 almost exhausted']
  ];
  el.kpis.innerHTML = ''; kp.forEach(k => el.kpis.append(h('div', { class: 'kpi' }, h('div', { class: 'k' }, k[0]), h('div', { class: 'v' }, k[1]), h('div', { class: 'd' }, k[2]))));
  const bands = [{ x0: 2019.5, x1: 2021.5, label: 'Pandemic' }, { x0: 2008.5, x1: 2010.5, label: 'Crisis' }];
  const base = { bands, vline: S.year, xmin: 2001, xmax: S.horizon, xlabel: y => 'Year ' + y };
  const ref = k => REF ? [{ name: 'Pinned reference', color: '--muted', dash: [6, 4], width: 1.8, data: pts(REF[k], REF.year) }] : [];
  const thousands = v => nf(v / 1000, 0) + 'k';
  charts.ca.set([{ name: 'Simulated', color: '--orange', data: pts(SIM.CA, Y) }, ...ref('CA'), { name: 'Observed (INS)', color: '--ink2', dots: true, data: realPts(DATA.CA) }],
    { ...base, hlines: [{ y: S.KA, label: 'K_A', color: '--red' }], yfmt: thousands, tipfmt: v => nf(v, 0) });
  charts.ch.set([{ name: 'Simulated', color: '--blue', data: pts(SIM.CH, Y) }, ...ref('CH'), { name: 'Observed (INS)', color: '--ink2', dots: true, data: realPts(DATA.CH) }],
    { ...base, yfmt: thousands, tipfmt: v => nf(v, 0) });
  charts.n.set([{ name: 'Hotels, simulated', color: '--blue', data: pts(SIM.NH, Y) }, { name: 'Agritourism, simulated', color: '--orange', data: pts(SIM.NA, Y) },
    { name: 'Hotels, observed', color: '--blue', dots: true, r: 2.2, data: realPts(DATA.NH) }, { name: 'Agritourism, observed', color: '--orange', dots: true, r: 2.2, data: realPts(DATA.NA) }],
    { ...base, yfmt: thousands, tipfmt: v => nf(v, 0) });
  const occReal = (N, C) => N.map((v, i) => 100 * v / C[i]);
  charts.occ.set([{ name: 'Hotels, simulated', color: '--blue', data: pts(SIM.occH.map(v => 100 * v), Y) }, { name: 'Agritourism, simulated', color: '--orange', data: pts(SIM.occA.map(v => 100 * v), Y) },
    { name: 'Hotels, observed', color: '--blue', dots: true, r: 2.2, data: realPts(occReal(DATA.NH, DATA.CH)) }, { name: 'Agritourism, observed', color: '--orange', dots: true, r: 2.2, data: realPts(occReal(DATA.NA, DATA.CA)) }],
    { ...base, ymin: 0, yfmt: v => nf(v, 0) + '%', tipfmt: v => nf(v, 1) + '%' });
  charts.rep.set([{ name: 'REP / M (reputation)', color: '--aqua', data: pts(SIM.REP.map(v => v / S.M), Y) }, { name: 'Public-policy ramp', color: '--violet', data: pts(SIM.pol, Y) },
    { name: '1 − CA/K_A (remaining room)', color: '--red', data: pts(SIM.room, Y) }], { ...base, ymin: 0, ymax: 1.05, yfmt: v => nf(v, 1), tipfmt: v => nf(v, 3) });
  charts.share.set([{ name: 'Agritourism, simulated', color: '--orange', data: pts(SIM.cotaA.map(v => 100 * v), Y) },
    { name: 'Agritourism, observed', color: '--orange', dots: true, data: realPts(DATA.NA.map((v, i) => 100 * v / DATA.Nt[i])) }],
    { ...base, ymin: 0, yfmt: v => nf(v, 0) + '%', tipfmt: v => nf(v, 1) + '%' });
  REF && (REF.year = REF.year);
  drawDiagram(); drawTable();
}
window.__redraw = () => { if (SIM) update(); };

function drawDiagram() {
  if (!SIM) return; const i = Math.min(S.year - 2001, SIM.year.length - 1);
  const f0 = v => nf(v, 0), f1 = v => nf(v, 1);
  const col = n => css(n);
  const box = (x, y, w, hh, title, lines, c) => `<rect x="${x}" y="${y}" width="${w}" height="${hh}" rx="10" fill="${c}" fill-opacity=".14" stroke="${c}" stroke-width="2"/>
    <text x="${x + w / 2}" y="${y + 20}" text-anchor="middle" font-size="13.5" font-weight="650">${title}</text>` +
    lines.map((l, k) => `<text x="${x + w / 2}" y="${y + 40 + k * 18}" text-anchor="middle" font-size="13.5" class="${k ? 't2' : 'num'}">${l}</text>`).join('');
  const ell = (cx, cy, rx, ry, title, val) => `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="none" stroke="${col('--muted')}" stroke-width="1.6" stroke-dasharray="4 3"/>
    <text x="${cx}" y="${cy - 3}" text-anchor="middle" font-size="12.5" class="t2">${title}</text><text x="${cx}" y="${cy + 14}" text-anchor="middle" font-size="13" class="num">${val}</text>`;
  const arr = (d, c, dash, label, lx, ly, bold) => `<path d="${d}" fill="none" stroke="${c}" stroke-width="${bold ? 2.6 : 1.9}" ${dash ? 'stroke-dasharray="6 4"' : ''} marker-end="url(#ar${c.replace(/[^a-z0-9]/gi, '')})"/>` + (label ? `<text x="${lx}" y="${ly}" font-size="12" class="t2">${label}</text>` : '');
  const cB = col('--blue'), cO = col('--orange'), cA = col('--aqua'), cV = col('--violet'), cR = col('--red'), cM = col('--muted');
  const mark = [cB, cO, cA, cV, cR, cM].map(c => `<marker id="ar${c.replace(/[^a-z0-9]/gi, '')}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${c}"/></marker>`).join('');
  const nhS = SIM.NH[i], naS = SIM.NA[i];
  const svg = `<svg class="diagram" viewBox="0 0 960 496" role="img" aria-label="Stock-and-flow diagram of the model">
    <defs>${mark}</defs>
    ${ell(100, 52, 92, 30, 'Public policy (ramp)', nf(SIM.pol[i], 2))}
    ${box(30, 150, 210, 78, 'REP – agritourism reputation', [nf(SIM.REP[i], 2) + ' of M = ' + nf(S.M, 2), 'ΔREP = ' + nf(SIM.dREP[i], 3) + ' / year'], cA)}
    <path d="M110,150 C110,108 190,108 190,150" fill="none" stroke="${cA}" stroke-width="2.2" marker-end="url(#ar${cA.replace(/[^a-z0-9]/gi, '')})"/><text x="150" y="100" text-anchor="middle" font-size="12.5" font-weight="700" fill="${cA}">R1 (Bass)</text>
    ${box(330, 36, 200, 70, 'Agritourism investment', [f0(SIM.invA[i]) + ' bed-days/year', '(γ·ΔREP + δ·Pol·CA)·(1−CA/K_A)'], cV)}
    ${box(640, 28, 290, 92, 'CA – agritourism capacity', [f0(SIM.CA[i]) + ' bed-days', 'Remaining room (1−CA/K_A) = ' + nf(SIM.room[i], 3)], cO)}
    ${arr('M185,62 L330,62', cV, false, '', 0, 0, true)}
    ${arr('M240,172 C290,172 300,110 330,98', cA, false, 'γ·ΔREP', 262, 150)}
    ${arr('M530,70 L640,70', cO, false, '', 0, 0, true)}
    ${arr('M785,120 C785,150 480,150 460,108', cR, true, 'B1: saturation brake', 540, 158)}
    ${ell(290, 300, 108, 32, 'Attractiveness', nf(SIM.att[i], 3))}
    ${arr('M135,228 C135,262 190,290 182,292', cA, false, '', 0, 0)}
    ${arr('M395,300 L430,300', cM, false, '', 0, 0)}
    ${box(430, 258, 200, 86, 'Demand shares', ['Hotels ' + nf(SIM.cotaH[i] * 100, 1) + '%', 'Agritourism ' + nf(SIM.cotaA[i] * 100, 1) + '%'], cM)}
    ${ell(110, 410, 100, 34, 'Total demand (exogenous)', f0(SIM.cerere[i]) + ' nights')}
    ${arr('M200,396 C300,380 380,350 430,332', cM, true, '', 0, 0)}
    ${arr('M640,330 L690,290', cM, false, '', 0, 0)}
    ${arr('M740,92 C860,160 880,210 790,252', cO, true, '', 0, 0)}
    ${box(690, 240, 240, 96, 'Simulated overnight stays', ['Hotels ' + f0(nhS) + ' (occupancy ' + nf(SIM.occH[i] * 100, 1) + '%)', 'Agro ' + f0(naS) + ' (occupancy ' + nf(SIM.occA[i] * 100, 1) + '%)'], cM)}
    ${box(640, 372, 290, 92, 'CH – hotel capacity', [f0(SIM.CH[i]) + ' bed-days', '+ inv. ' + f0(SIM.invH[i]) + ' − depr. ' + f0(SIM.depH[i])], cB)}
    ${arr('M810,336 C810,352 810,360 810,372', cB, false, 'β_H · occupancy', 822, 358)}
    ${box(330, 402, 210, 60, 'Other structures (observed)', [f0(SIM.calte[i]) + ' bed-days'], cM)}
    ${arr('M470,402 L500,346', cM, true, '', 0, 0)}
    <text x="30" y="486" font-size="12" class="mut">No link from agritourism occupancy to agritourism investment: investment is driven by reputation and policy.</text>
  </svg>`;
  el.diag.innerHTML = svg; el.yr.textContent = S.year;
}
function drawTable() {
  const yrs = [2001, 2005, 2010, 2015, 2020, 2025, 2030, 2035, 2040, 2045, 2050, 2060].filter(y => y <= S.horizon);
  const rows = yrs.map(y => { const i = y - 2001; return `<tr><td>${y}</td><td>${nf(SIM.CA[i])}</td><td>${nf(SIM.CH[i])}</td><td>${nf(SIM.NA[i])}</td><td>${nf(SIM.NH[i])}</td><td>${nf(SIM.occA[i] * 100, 1)}%</td><td>${nf(SIM.occH[i] * 100, 1)}%</td><td>${nf(SIM.cotaA[i] * 100, 1)}%</td></tr>`; }).join('');
  el.table.innerHTML = `<table class="dt"><thead><tr><th>Year</th><th>CA</th><th>CH</th><th>Agro nights</th><th>Hotel nights</th><th>Agro occupancy</th><th>Hotel occupancy</th><th>Agro share</th></tr></thead><tbody>${rows}</tbody></table>`;
}
function exportCSV() {
  downloadCSV('simulator_sd1.csv', ['year', 'CA', 'CH', 'REP', 'nights_agro', 'nights_hotels', 'occupancy_agro', 'occupancy_hotels', 'share_agro', 'invest_agro', 'invest_hotels'],
    SIM.year.map((y, i) => [y, SIM.CA[i].toFixed(0), SIM.CH[i].toFixed(0), SIM.REP[i].toFixed(4), SIM.NA[i].toFixed(0), SIM.NH[i].toFixed(0), (SIM.occA[i] * 100).toFixed(2), (SIM.occH[i] * 100).toFixed(2), (SIM.cotaA[i] * 100).toFixed(2), SIM.invA[i].toFixed(0), SIM.invH[i].toFixed(0)]));
}
document.addEventListener('DOMContentLoaded', () => { $('#themebtn').append(themeToggle()); build(); buildStage(); applyScenario('base'); });
