/* ===== Simulator 2: community quality of life (exploratory scenario model) ===== */
const DEF2 = { ...SD2_DEFAULT };
const S = { ...DEF2, year: 2045 };
let REF = null, SIM = null, curScen = 'base';
const SLIDERS = [
  { grp: 'Acceptance of technologies by residents (Bass loop R2)', items: [
    { key: 'acc0', label: 'Initial acceptance (2025)', min: 0.05, max: 0.9, step: 0.01, fmt: v => pct(v, 1), tag: 'est', help: '31.84%: share of persons with at least basic digital skills in Romania (an imperfect proxy).' },
    { key: 'p_r', label: 'p_r – spontaneous adoption', min: 0, max: 0.06, step: 0.0005, dec: 4, tag: 'sc', help: 'Assumption: 0.01, below the meta-analysis mean of 0.03 (Sultan et al., 1990).' },
    { key: 'q_r', label: 'q_r – social imitation', min: 0, max: 0.5, step: 0.005, dec: 3, tag: 'sc', help: 'Assumption: 0.15 (meta-analysis mean: 0.38). The most influential assumed parameter.' },
    { key: 'r_r', label: 'r_r – resistance to tourism pressure', min: 0, max: 0.4, step: 0.005, dec: 3, tag: 'sc', help: 'Assumption: at the maximum pressure of the baseline, resistance stays below one percentage point per year (loop B1).' } ] },
  { grp: 'Quality of life', items: [
    { key: 'lam0', label: 'λ0 – annual decline at zero acceptance', min: 0, max: 0.03, step: 0.0005, fmt: v => nf(v * 100, 2) + '% per year', tag: 'sc', help: 'Assumption: 1% per year. At full acceptance the score grows by 0.49% per year (Romania, 6.1 in 2003 and 6.5 in 2016).' },
    { key: 'qol0', label: 'Initial score (2025)', min: 5.5, max: 7.5, step: 0.05, dec: 2, tag: 'est', help: '6.5: life satisfaction in Romania in 2016, scale 1–10 (Eurofound).' } ] },
  { grp: 'Budget and investment (constant 2025 RON)', items: [
    { key: 'eff', label: 'Investment efficiency η', min: 0.3, max: 1.3, step: 0.01, fmt: v => pct(v, 0), tag: 'sc', help: '100% = the whole investment capacity is used; 70% is an example of a 30% loss.' },
    { key: 'gamma', label: 'γ_eff – sensitivity to investment', min: 0, max: 0.04, step: 0.0005, dec: 4, tag: 'sc', help: 'Assumption: 0.01. No effect while the investment ratio is close to 1.' },
    { key: 'gBudget', label: 'Real growth of the budget', min: -0.03, max: 0.04, step: 0.0025, fmt: v => nf(v * 100, 2) + '% per year', tag: 'sc', help: 'Neutral assumption: 0% in real terms.' },
    { key: 'tax', label: 'Effective tourism tax share', min: 0, max: 0.08, step: 0.0025, fmt: v => nf(v * 100, 2) + '%', tag: 'sc', help: 'Assumption: 2%. Almost no effect on the result.' },
    { key: 'perTrip', label: 'Mean spending per stay (RON)', min: 100, max: 5000, step: 50, fmt: v => nf(v, 0), tag: 'sc', help: 'Assumption: RON 500; no local measurement; negligible effect.' },
    { key: 'budget0', label: 'Reference budget 2025 (billion RON)', min: 0.8, max: 3, step: 0.1, fmt: v => nf(v / 1e9, 1), tag: 'sc', help: 'Assumed order of magnitude: RON 1.5 billion; enters only the tax term.' } ] },
  { grp: 'Horizon', items: [
    { key: 'horizon', label: 'Final year', min: 2035, max: 2060, step: 1, fmt: v => String(v), tag: 'sc' } ] }
];
const SCEN = [
  { id: 'base', name: 'Baseline', desc: 'Diffusion from 31.84%, p_r = 0.01; q_r = 0.15; r_r = 0.08', patch: {} },
  { id: 'fast', name: 'Rapid diffusion', desc: 'Meta-analysis means: p_r = 0.03, q_r = 0.38', patch: { p_r: 0.03, q_r: 0.38 } },
  { id: 'edu', name: 'Information campaign', desc: 'p_r doubled (0.02) and q_r × 1.5 (0.225)', patch: { p_r: 0.02, q_r: 0.225 } },
  { id: 'res', name: 'High resistance', desc: 'r_r = 0.24: strong reaction to crowding', patch: { r_r: 0.24 } },
  { id: 'eff', name: 'Less efficient investment', desc: 'η = 0.7', patch: { eff: 0.7 } },
  { id: 'fro', name: 'No diffusion of acceptance', desc: 'Acceptance stays at its initial value', patch: { frozen: true } }
];
const PATHS_UI = [['calibrated', 'Calibrated (Model 1)'], ['doubled', 'Policy sensitivity doubled'], ['nopolicy', 'No public policy'], ['const', 'Constant at 2025 level']];
const sliderEls = {}, charts = {}, el = {};

function build() {
  const ctr = $('#controls');
  ctr.append(h('h3', {}, 'Scenarios'));
  const sc = h('div', { class: 'scen' });
  SCEN.forEach(s => sc.append(h('button', { class: 'btn', 'data-id': s.id, onclick: () => applyScenario(s.id) }, s.name, h('small', {}, s.desc))));
  ctr.append(sc);
  ctr.append(h('h3', {}, 'Agritourism capacity trajectory'));
  const pb = h('div', { class: 'toolbar' });
  PATHS_UI.forEach(p => pb.append(h('button', { class: 'btn' + (p[0] === S.path ? ' on' : ''), 'data-path': p[0], onclick: () => { S.path = p[0]; document.querySelectorAll('[data-path]').forEach(b => b.classList.toggle('on', b.dataset.path === S.path)); update(); } }, p[1])));
  ctr.append(pb, h('div', { class: 'note' }, 'Capacity comes from Model 1. Tourism pressure is measured relative to the 2025 capacity of the chosen trajectory.'));
  ctr.append(h('div', { class: 'toolbar' },
    h('button', { class: 'btn', onclick: () => { REF = sd2(S); update(); }, title: 'Keep the current trajectory as a dashed grey line' }, 'Pin as reference'),
    h('button', { class: 'btn ghost', onclick: () => { REF = null; update(); } }, 'Clear reference')));
  SLIDERS.forEach(g => { ctr.append(h('h3', {}, g.grp)); g.items.forEach(d => { const e = makeSlider(d, S, () => { curScen = ''; mark(); update(); }); sliderEls[d.key] = e; ctr.append(e); }); });
  ctr.append(h('div', { class: 'note' }, 'Tags: ', h('span', { class: 'tag est' }, 'estimate'), ' value computed or chosen from a public source; ', h('span', { class: 'tag sc' }, 'scenario'), ' assumed value.'));
}
function mark() { document.querySelectorAll('.scen button').forEach(b => b.classList.toggle('on', b.dataset.id === curScen)); }
function applyScenario(id) {
  const sc = SCEN.find(s => s.id === id); curScen = id; const yr = S.year, path = S.path;
  Object.keys(S).forEach(k => delete S[k]); Object.assign(S, DEF2, { year: yr, path }, sc.patch);
  Object.keys(sliderEls).forEach(k => sliderEls[k]._set(S[k])); mark(); update();
}
function buildStage() {
  const st = $('#stage');
  el.kpis = h('div', { class: 'kpis' });
  st.append(h('div', { class: 'card' }, h('h2', {}, 'Key results'), h('p', { class: 'sub' }, 'Life satisfaction (score 1–10) and acceptance of technologies by residents from 2025 to the final year. A scenario model, not a forecast.'), el.kpis));
  el.yr = h('span', { class: 'yr' }, '2045');
  el.scrub = h('input', { type: 'range', min: 2025, max: 2045, step: 1, value: 2045 });
  el.scrub.addEventListener('input', () => { S.year = +el.scrub.value; drawDiagram(); update(true); });
  el.diag = h('div', {});
  st.append(h('div', { class: 'card' }, h('h2', {}, 'Model structure with the values of the selected year'),
    h('p', { class: 'sub' }, 'Acceptance (ACC) and quality of life (QOL) are stocks. Move the slider to follow the chain: tourism → budget → investment ratio → rate of decline → QOL.'),
    h('div', { class: 'scrub' }, el.yr, el.scrub), el.diag,
    h('details', { class: 'how' }, h('summary', {}, 'How to read and use the simulator'), h('ul', {},
      h('li', {}, 'Choose a scenario or change the parameters; note the “J-curve”: quality of life first falls, then rises once acceptance passes a threshold (about 67% with baseline values).'),
      h('li', {}, 'The rate of decline λ is linear in acceptance: λ0 at ACC = 0, growth of 0.49% per year at ACC = 100%, zero at ACC* = λ0 / (λ0 + κ).'),
      h('li', {}, 'If tourism pressure exceeds the reference level, community resistance slows acceptance (loop B1).'),
      h('li', {}, 'The sensitivity chart is recalculated live and shows which assumptions matter most.')))));
  const grid = h('div', { class: 'charts' });
  const mk = (id, t, s) => { const c = chartCard(t, s); charts[id] = c.chart; grid.append(c.card); };
  mk('qol', 'Quality of life (score 1–10)', 'Simulated trajectory; dashed line = initial level');
  mk('acc', 'Acceptance of technologies by residents', 'Stock ACC (share of residents)');
  mk('flux', 'Dynamics of acceptance: social growth and resistance', 'Annual change of ACC, percentage points');
  mk('pres', 'Perceived tourism pressure', 'Agritourism capacity relative to 2025');
  mk('inv', 'Tourist spending and tourism taxes (million RON)', 'Spending of agritourism arrivals and taxes collected from it');
  mk('lam', 'Effective annual rate of decline λ', 'Negative values mean that quality of life grows');
  st.append(grid);
  const tcv = h('canvas', {}); tcv.style.height = '250px'; el.tor = new Tornado(tcv);
  st.append(h('div', { class: 'card' }, h('h2', {}, 'Sensitivity: which assumptions matter most?'), h('p', { class: 'sub' }, 'QoL in the final year when each assumed parameter varies by ±50% (initial acceptance: 21%–40%; budget growth: −1% to +1%); the others keep their current values. Black line = current scenario.'), tcv));
  const rc = chartCard('Acceptance and the rate of decline λ', 'Measured point: at ACC = 100%, growth of 0.49% per year (Romania, 2003–2016); assumed point: λ0 at ACC = 0', 250); charts.rep = rc.chart;
  st.append(rc.card);
  el.table = h('div', {});
  st.append(h('div', { class: 'card' }, h('h2', {}, 'Annual values'), h('div', { class: 'toolbar' }, h('button', { class: 'btn', onclick: exportCSV }, 'Download CSV')), el.table));
}
const P2 = (arr, years) => years.map((y, i) => ({ x: y, y: arr[i] }));
function update() {
  SIM = sd2(S); const Y = SIM.year, last = Y.length - 1;
  el.scrub.min = 2025; el.scrub.max = S.horizon; if (S.year > S.horizon) S.year = S.horizon; el.scrub.value = S.year; el.yr.textContent = S.year;
  let imin = 0; SIM.qol.forEach((v, i) => { if (v < SIM.qol[imin]) imin = i; });
  const cross = (() => { for (let i = imin; i <= last; i++) if (SIM.qol[i] > S.qol0) return Y[i]; return null; })();
  const kp = [['QoL in 2025', nf(SIM.qol[0], 2), 'Starting point'], ['Minimum QoL', nf(SIM.qol[imin], 2), 'in ' + Y[imin]], ['QoL in ' + S.horizon, nf(SIM.qol[last], 2), (SIM.qol[last] >= S.qol0 ? '+' : '') + nf(SIM.qol[last] - S.qol0, 2) + ' vs. 2025'],
    ['Back above the initial level', cross ?? 'not by ' + S.horizon, 'First year with QoL > ' + nf(S.qol0, 2)], ['Acceptance in ' + S.horizon, pct(SIM.acc[last], 1), 'Starting from ' + pct(S.acc0, 0)], ['Maximum pressure', nf(Math.max(...SIM.presiune), 2) + '×', 'relative to 2025 capacity']];
  el.kpis.innerHTML = ''; kp.forEach(k => el.kpis.append(h('div', { class: 'kpi' }, h('div', { class: 'k' }, k[0]), h('div', { class: 'v' }, k[1]), h('div', { class: 'd' }, k[2]))));
  const base = { vline: S.year, xmin: 2025, xmax: S.horizon, xlabel: y => 'Year ' + y };
  const ref = (k, f) => REF ? [{ name: 'Pinned reference', color: '--muted', dash: [6, 4], width: 1.8, data: P2(f ? REF[k].map(f) : REF[k], REF.year) }] : [];
  const lo = Math.min(...SIM.qol, ...(REF ? REF.qol : []), S.qol0);
  charts.qol.set([{ name: 'Simulated QoL', color: '--blue', data: P2(SIM.qol, Y) }, ...ref('qol')], { ...base, tight: true, ymin: Math.floor((lo - 0.15) * 10) / 10, hlines: [{ y: S.qol0, label: 'initial level', color: '--muted' }], yfmt: v => nf(v, 1), tipfmt: v => nf(v, 2), dec: 2 });
  charts.acc.set([{ name: 'Simulated acceptance', color: '--aqua', data: P2(SIM.acc.map(v => 100 * v), Y) }, ...ref('acc', v => 100 * v)], { ...base, ymin: 0, ymax: 100, yfmt: v => nf(v, 0) + '%', tipfmt: v => nf(v, 1) + '%' });
  const bass = SIM.acc.map(a => 100 * (S.p_r * (1 - a) + S.q_r * a * (1 - a)));
  charts.flux.set([{ name: 'Social growth (Bass)', color: '--aqua', data: P2(S.frozen ? bass.map(() => 0) : bass, Y) }, { name: 'Resistance (tourism pressure)', color: '--red', data: P2(SIM.resist.map(v => 100 * v), Y) }],
    { ...base, ymin: 0, yfmt: v => nf(v, 1), tipfmt: v => nf(v, 2) + ' pp/year' });
  charts.pres.set([{ name: 'CA / CA₂₀₂₅', color: '--orange', data: P2(SIM.presiune, Y) }], { ...base, ymin: 0.9, tight: true, hlines: [{ y: 1, label: 'reference level', color: '--muted' }], yfmt: v => nf(v, 2), tipfmt: v => nf(v, 3) });
  charts.inv.set([{ name: 'Spending of agritourism tourists', color: '--blue', data: P2(SIM.venit.map(v => v / 1e6), Y) }, { name: 'Tourism taxes', color: '--orange', data: P2(SIM.taxRev.map(v => v / 1e6), Y) }],
    { ...base, ymin: 0, yfmt: v => nf(v, 0), tipfmt: v => nf(v, 2) + ' million RON' });
  charts.lam.set([{ name: 'effective λ', color: '--violet', data: P2(SIM.lamEff.map(v => 100 * v), Y) }, { name: 'λ(ACC) without the investment adjustment', color: '--muted', dash: [5, 4], data: P2(SIM.lam.map(v => 100 * v), Y) }],
    { ...base, hlines: [{ y: 0, color: '--ink2' }], yfmt: v => nf(v, 1) + '%', tipfmt: v => nf(v, 2) + '% / an' });
  // relation lambda(ACC)
  const xs = [...Array(51).keys()].map(i => i * 2), lc = xs.map(x => ({ x, y: 100 * lam(x / 100, S.lam0) }));
  charts.rep.set([{ name: 'λ(ACC), % per year', color: '--blue', data: lc },
    { name: 'Initial acceptance', color: '--ink', dots: true, r: 5, data: [{ x: S.acc0 * 100, y: 100 * lam(S.acc0, S.lam0) }] },
    { name: 'Threshold λ = 0: ' + pct(accNeutral(S.lam0), 0), color: '--red', dots: true, r: 5, data: [{ x: accNeutral(S.lam0) * 100, y: 0 }] },
    { name: 'Measured point (ACC = 100%)', color: '--aqua', dots: true, r: 5, data: [{ x: 100, y: -KAPPA * 100 }] }],
    { xmin: 0, xmax: 100, tight: true, ymin: -0.8, ymax: Math.max(1.2, S.lam0 * 100 + 0.2), yfmt: v => nf(v, 1) + '%', tipfmt: v => nf(v, 2) + '% / an', dec: 2, xlabel: x => 'ACC ' + nf(x, 0) + '%' });
  // tornado
  const mul = (k) => [S[k] * 0.5, S[k] * 1.5];
  const lst = [['q_r', 'q_r (imitation)', ...mul('q_r')], ['lam0', 'λ0 (decline)', ...mul('lam0')], ['acc0', 'Initial acceptance', 0.21, 0.40], ['gBudget', 'Budget growth', -0.01, 0.01],
    ['r_r', 'r_r (resistance)', ...mul('r_r')], ['p_r', 'p_r (adoption)', ...mul('p_r')], ['gamma', 'γ_eff (investment)', ...mul('gamma')], ['tax', 'Tax share', ...mul('tax')]];
  const bq = SIM.qol[last], rows = lst.map(([k, lab, v0, v1]) => { const a = sd2({ ...S, [k]: v0 }).qol, b = sd2({ ...S, [k]: v1 }).qol; return { label: lab, lo: a[a.length - 1], hi: b[b.length - 1] }; });
  rows.sort((a, b) => Math.abs(b.hi - b.lo) - Math.abs(a.hi - a.lo)); el.tor.set(rows, bq, v => nf(v, 2));
  REF && (REF.year = REF.year); drawDiagram(); drawTable();
}
window.__redraw = () => { if (SIM) update(); };
function drawDiagram() {
  if (!SIM) return; const i = Math.min(S.year - 2025, SIM.year.length - 1), f0 = v => nf(v, 0), m = v => nf(v / 1e6, 1) + ' M';
  const col = n => css(n), cB = col('--blue'), cO = col('--orange'), cA = col('--aqua'), cV = col('--violet'), cR = col('--red'), cM = col('--muted');
  const id = c => 'b' + c.replace(/[^a-z0-9]/gi, '');
  const mark = [cB, cO, cA, cV, cR, cM].map(c => `<marker id="${id(c)}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${c}"/></marker>`).join('');
  const box = (x, y, w, hh, title, lines, c) => `<rect x="${x}" y="${y}" width="${w}" height="${hh}" rx="10" fill="${c}" fill-opacity=".14" stroke="${c}" stroke-width="2"/><text x="${x + w / 2}" y="${y + 20}" text-anchor="middle" font-size="13.5" font-weight="650">${title}</text>` + lines.map((l, k) => `<text x="${x + w / 2}" y="${y + 40 + k * 18}" text-anchor="middle" font-size="13.5" class="${k ? 't2' : 'num'}">${l}</text>`).join('');
  const ell = (cx, cy, rx, ry, t, v) => `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="none" stroke="${cM}" stroke-width="1.6" stroke-dasharray="4 3"/><text x="${cx}" y="${cy - 3}" text-anchor="middle" font-size="12.5" class="t2">${t}</text><text x="${cx}" y="${cy + 14}" text-anchor="middle" font-size="13" class="num">${v}</text>`;
  const arr = (d, c, dash, label, lx, ly, bold) => `<path d="${d}" fill="none" stroke="${c}" stroke-width="${bold ? 2.6 : 1.9}" ${dash ? 'stroke-dasharray="6 4"' : ''} marker-end="url(#${id(c)})"/>` + (label ? `<text x="${lx}" y="${ly}" font-size="12" class="t2">${label}</text>` : '');
  el.diag.innerHTML = `<svg class="diagram" viewBox="0 0 960 480" role="img" aria-label="Diagram of the quality of life model"><defs>${mark}</defs>
    ${ell(110, 52, 100, 30, 'Agro capacity CA (Model 1)', f0(SIM.ca[i]))}
    ${ell(110, 140, 100, 28, 'Agritourism arrivals', f0(SIM.venit[i] / S.perTrip))}
    ${arr('M110,82 L110,112', cO, false, '', 0, 0)}
    ${box(30, 330, 220, 86, 'ACC – resident acceptance', [pct(SIM.acc[i], 1), 'ΔACC = ' + nf(SIM.dacc[i] * 100, 2) + ' pp/year'], cA)}
    <path d="M80,330 C80,290 200,290 200,330" fill="none" stroke="${cA}" stroke-width="2.2" marker-end="url(#${id(cA)})"/><text x="140" y="284" text-anchor="middle" font-size="12.5" font-weight="700" fill="${cA}">R2 (Bass: p_r, q_r)</text>
    ${ell(400, 232, 112, 30, 'Tourism pressure CA/CA₂₀₂₅', nf(SIM.presiune[i], 3))}
    ${arr('M185,72 C240,130 235,190 300,214', cO, false, '', 0, 0)}
    ${arr('M310,256 C280,290 225,300 190,330', cR, false, 'B1: resistance −r_r·max(P−1,0)·ACC', 250, 312)}
    ${box(310, 20, 220, 62, 'Tourism spending', [m(SIM.venit[i]) + ' RON', '× tax share ' + pct(S.tax, 1)], cO)}
    ${arr('M205,138 L250,100 L310,70', cO, false, '', 0, 0)}
    ${box(600, 20, 330, 70, 'Effective budget', [m(SIM.bef[i]) + ' RON', 'budget + tourism taxes'], cB)}
    ${arr('M530,50 L600,50', cB, false, '', 0, 0)}
    ${box(600, 140, 330, 70, 'Investment ratio', [nf(SIM.raport[i], 4), 'η · effective budget / 2025 budget'], cB)}
    ${arr('M765,90 L765,140', cB, false, '', 0, 0)}
    ${box(600, 250, 330, 70, 'Effective rate of decline', ['λ = ' + nf(SIM.lamEff[i] * 100, 2) + '% / year', 'λ(ACC) + γ·(1 − ratio)'], cV)}
    ${arr('M765,210 L765,250', cB, false, '', 0, 0)}
    ${box(600, 360, 330, 84, 'QOL – quality of life (1–10)', [nf(SIM.qol[i], 3), 'QOL(t+1) = QOL(t)·exp(−λ)'], cV)}
    ${arr('M765,320 L765,360', cV, false, '', 0, 0, true)}
    ${arr('M250,380 L600,300', cA, false, 'λ(ACC), linear in acceptance', 330, 372, true)}
    <text x="30" y="466" font-size="12" class="mut">Above ACC* = ${pct(accNeutral(S.lam0), 0)} the rate of decline becomes negative and quality of life increases (“J-curve”).</text></svg>`;
  el.yr.textContent = S.year;
}
function drawTable() {
  const yrs = [2025, 2030, 2035, 2040, 2045, 2050, 2055, 2060].filter(y => y <= S.horizon);
  el.table.innerHTML = `<table class="dt"><thead><tr><th>Year</th><th>QoL</th><th>Acceptance</th><th>Pressure</th><th>Tourism spending (M RON)</th><th>Investment ratio</th></tr></thead><tbody>${yrs.map(y => { const i = y - 2025; return `<tr><td>${y}</td><td>${nf(SIM.qol[i], 2)}</td><td>${pct(SIM.acc[i], 1)}</td><td>${nf(SIM.presiune[i], 2)}</td><td>${nf(SIM.venit[i] / 1e6, 1)}</td><td>${nf(SIM.raport[i], 3)}</td></tr>`; }).join('')}</tbody></table>`;
}
function exportCSV() { downloadCSV('simulator_sd2.csv', ['year', 'QOL', 'ACC', 'pressure', 'tourism_spending', 'investment_ratio', 'lambda_effective'],
  SIM.year.map((y, i) => [y, SIM.qol[i].toFixed(4), SIM.acc[i].toFixed(4), SIM.presiune[i].toFixed(4), SIM.venit[i].toFixed(0), SIM.raport[i].toFixed(4), SIM.lamEff[i].toFixed(5)])); }
document.addEventListener('DOMContentLoaded', () => { $('#themebtn').append(themeToggle()); build(); buildStage(); applyScenario('base'); });
