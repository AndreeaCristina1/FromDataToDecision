/* ===== Shared library of the simulators (no external dependencies) ===== */
const $ = (s, r = document) => r.querySelector(s);
function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === 'class') e.className = v; else if (k === 'html') e.innerHTML = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v);
  }
  for (const c of kids.flat()) if (c != null) e.append(c.nodeType ? c : document.createTextNode(c));
  return e;
}
const nf = (v, d = 0) => (v == null || !isFinite(v)) ? '–' : v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (v, d = 1) => nf(v * 100, d) + '%';
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

/* ---------- slider with label, value, help text and provenance tag ---------- */
const TAGS = { cal: ['calibrated', 'Value calibrated on the historical series'], est: ['estimate', 'Value computed or chosen from a public source'],
  real: ['real', 'Value from statistics or publications'], sc: ['scenario', 'Scenario or policy variable (assumption)'] };
function makeSlider(def, state, onChange) {
  const val = h('span', { class: 'val' });
  const inp = h('input', { type: 'range', min: def.min, max: def.max, step: def.step, value: state[def.key] });
  const show = () => { val.textContent = def.fmt ? def.fmt(state[def.key]) : nf(state[def.key], def.dec ?? 2); };
  inp.addEventListener('input', () => { state[def.key] = parseFloat(inp.value); show(); onChange(def.key); });
  show();
  const tg = TAGS[def.tag] || TAGS.cal;
  const el = h('div', { class: 'sl' },
    h('div', { class: 'row' }, h('label', {}, def.label, h('span', { class: 'tag ' + (def.tag || 'cal'), title: tg[1] }, tg[0])), val),
    inp, def.help ? h('div', { class: 'help' }, def.help) : null);
  el._set = v => { state[def.key] = v; inp.value = v; show(); };
  el._refresh = () => { inp.value = state[def.key]; show(); };
  return el;
}

/* ---------- line chart on canvas ---------- */
function niceTicks(lo, hi, n = 5) {
  if (hi === lo) { hi = lo + 1; }
  const span = hi - lo, step0 = span / n, mag = Math.pow(10, Math.floor(Math.log10(step0)));
  const m = step0 / mag, step = (m < 1.5 ? 1 : m < 3 ? 2 : m < 7 ? 5 : 10) * mag;
  const a = Math.ceil(lo / step - 1e-9) * step, out = [];
  for (let v = a; v <= hi + 1e-9; v += step) out.push(+v.toFixed(10));
  return out;
}
class Chart {
  constructor(canvas, tip) { this.c = canvas; this.tip = tip; this.hover = null; this.o = {}; this.series = [];
    canvas.addEventListener('mousemove', e => { const r = canvas.getBoundingClientRect(); this.hover = { x: e.clientX - r.left, y: e.clientY - r.top }; this.draw(); });
    canvas.addEventListener('mouseleave', () => { this.hover = null; this.draw(); });
    new ResizeObserver(() => this.draw()).observe(canvas); }
  set(series, o) { this.series = series; this.o = o || {}; this.draw(); }
  draw() {
    const c = this.c, dpr = window.devicePixelRatio || 1, W = c.clientWidth, H = c.clientHeight;
    if (!W) return;
    c.width = Math.round(W * dpr); c.height = Math.round(H * dpr);
    const g = c.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    const o = this.o, L = o.left || 58, R = 14, T = 12, B = 28, pw = W - L - R, ph = H - T - B;
    const pts = this.series.flatMap(s => s.data.filter(p => p.y != null && isFinite(p.y)));
    if (!pts.length) return;
    let x0 = o.xmin ?? Math.min(...pts.map(p => p.x)), x1 = o.xmax ?? Math.max(...pts.map(p => p.x));
    let ys = pts.map(p => p.y); (o.hlines || []).forEach(l => ys.push(l.y));
    let y0 = o.ymin ?? Math.min(0, ...ys), y1 = o.ymax ?? Math.max(...ys);
    if (o.ymin == null && o.tight) y0 = Math.min(...ys); if (y1 === y0) y1 = y0 + 1;
    const pad = (y1 - y0) * (o.ymax == null ? 0.06 : 0); y1 += pad; if (o.ymin == null && o.tight) y0 -= pad;
    const X = x => L + (x - x0) / (x1 - x0) * pw, Y = y => T + (1 - (y - y0) / (y1 - y0)) * ph;
    const ink2 = css('--ink2'), muted = css('--muted'), grid = css('--grid'), axis = css('--axis');
    (o.bands || []).forEach(b => { g.fillStyle = css('--chip'); g.globalAlpha = .7; g.fillRect(X(b.x0), T, X(b.x1) - X(b.x0), ph); g.globalAlpha = 1;
      if (b.label) { g.fillStyle = muted; g.font = '11px system-ui'; g.textAlign = 'center'; g.fillText(b.label, (X(b.x0) + X(b.x1)) / 2, T + 11); } });
    g.font = '11.5px system-ui'; g.textAlign = 'right'; g.textBaseline = 'middle';
    niceTicks(y0, y1, 5).forEach(v => { const y = Y(v); g.strokeStyle = grid; g.lineWidth = 1; g.beginPath(); g.moveTo(L, y); g.lineTo(L + pw, y); g.stroke();
      g.fillStyle = muted; g.fillText(o.yfmt ? o.yfmt(v) : nf(v, v % 1 ? 1 : 0), L - 6, y); });
    g.textAlign = 'center'; g.textBaseline = 'top';
    const xt = niceTicks(x0, x1, Math.max(3, Math.floor(pw / 80)));
    xt.forEach(v => { g.fillStyle = muted; g.fillText(o.xfmt ? o.xfmt(v) : String(v), X(v), T + ph + 7); g.strokeStyle = axis; g.beginPath(); g.moveTo(X(v), T + ph); g.lineTo(X(v), T + ph + 4); g.stroke(); });
    g.strokeStyle = axis; g.beginPath(); g.moveTo(L, T + ph); g.lineTo(L + pw, T + ph); g.stroke();
    (o.hlines || []).forEach(l => { g.strokeStyle = css(l.color || '--muted'); g.setLineDash([5, 4]); g.lineWidth = 1.2; g.beginPath(); g.moveTo(L, Y(l.y)); g.lineTo(L + pw, Y(l.y)); g.stroke(); g.setLineDash([]);
      if (l.label) { g.fillStyle = ink2; g.textAlign = 'right'; g.textBaseline = 'bottom'; g.font = '11px system-ui'; g.fillText(l.label, L + pw - 2, Y(l.y) - 2); } });
    if (o.vline != null) { g.strokeStyle = css('--ink2'); g.globalAlpha = .55; g.lineWidth = 1; g.beginPath(); g.moveTo(X(o.vline), T); g.lineTo(X(o.vline), T + ph); g.stroke(); g.globalAlpha = 1; }
    this.series.forEach(s => {
      const col = css(s.color); g.strokeStyle = col; g.fillStyle = col; g.lineWidth = s.width || 2.2; g.setLineDash(s.dash || []);
      if (s.dots) { s.data.forEach(p => { if (p.y == null) return; g.beginPath(); g.arc(X(p.x), Y(p.y), s.r || 2.6, 0, 7); g.fill(); }); }
      else { g.beginPath(); let st = false; s.data.forEach(p => { if (p.y == null || !isFinite(p.y)) { st = false; return; } st ? g.lineTo(X(p.x), Y(p.y)) : g.moveTo(X(p.x), Y(p.y)); st = true; }); g.stroke(); }
      g.setLineDash([]);
    });
    const tip = this.tip;
    if (this.hover && this.hover.x >= L && this.hover.x <= L + pw) {
      const xv = x0 + (this.hover.x - L) / pw * (x1 - x0);
      const xr = Math.round(xv); const rows = [];
      g.strokeStyle = css('--ink2'); g.globalAlpha = .4; g.beginPath(); g.moveTo(X(xr), T); g.lineTo(X(xr), T + ph); g.stroke(); g.globalAlpha = 1;
      this.series.forEach(s => { const p = s.data.find(q => q.x === xr); if (p && p.y != null && isFinite(p.y)) { rows.push([s.name, o.tipfmt ? o.tipfmt(p.y) : nf(p.y, o.dec ?? 0), s.color]); g.fillStyle = css(s.color); g.beginPath(); g.arc(X(xr), Y(p.y), 3.6, 0, 7); g.fill(); } });
      if (tip && rows.length) { tip.style.display = 'block';
        tip.innerHTML = '<b>' + (o.xlabel ? o.xlabel(xr) : xr) + '</b>' + rows.map(r => `<div><span style="color:${css(r[2])}">●</span> ${r[0]}: <b style="display:inline">${r[1]}</b></div>`).join('');
        const tw = tip.offsetWidth; let lx = X(xr) + 12; if (lx + tw > W) lx = X(xr) - tw - 12; tip.style.left = Math.max(0, lx) + 'px'; tip.style.top = '14px'; }
    } else if (tip) tip.style.display = 'none';
  }
}
function chartCard(title, sub, h260) {
  const canvas = h('canvas', {}); if (h260) canvas.style.height = h260 + 'px';
  const tip = h('div', { class: 'tip' }), legend = h('div', { class: 'legend' });
  const card = h('div', { class: 'card' }, h('h2', {}, title), sub ? h('p', { class: 'sub' }, sub) : null, h('div', { class: 'chartbox' }, canvas, tip), legend);
  const ch = new Chart(canvas, tip);
  ch.setLegend = items => { legend.innerHTML = ''; items.forEach(s => legend.append(h('span', {}, h('i', { class: s.dots ? 'dot' : s.dash ? 'dash' : '', style: 'border-color:' + css(s.color) }), s.name))); };
  const orig = ch.set.bind(ch); ch.set = (series, o) => { orig(series, o); ch.setLegend(series.filter(s => !s.hidden)); };
  return { card, chart: ch };
}

/* ---------- tornado chart (horizontal bars) ---------- */
class Tornado {
  constructor(canvas) { this.c = canvas; this.rows = []; new ResizeObserver(() => this.draw()).observe(canvas); }
  set(rows, base, fmt) { this.rows = rows; this.base = base; this.fmt = fmt; this.draw(); }
  draw() {
    const c = this.c, dpr = window.devicePixelRatio || 1, W = c.clientWidth, H = c.clientHeight; if (!W || !this.rows.length) return;
    c.width = W * dpr; c.height = H * dpr; const g = c.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    const L = 150, R = 20, T = 8, B = 24, pw = W - L - R, n = this.rows.length, bh = (H - T - B) / n;
    const lo = Math.min(...this.rows.map(r => Math.min(r.lo, r.hi)), this.base), hi = Math.max(...this.rows.map(r => Math.max(r.lo, r.hi)), this.base);
    const m = (hi - lo) * .06, X = v => L + (v - (lo - m)) / ((hi + m) - (lo - m)) * pw;
    g.font = '12px system-ui'; g.textBaseline = 'middle';
    niceTicks(lo - m, hi + m, 5).forEach(v => { g.strokeStyle = css('--grid'); g.beginPath(); g.moveTo(X(v), T); g.lineTo(X(v), H - B); g.stroke(); g.fillStyle = css('--muted'); g.textAlign = 'center'; g.fillText(this.fmt(v), X(v), H - 10); });
    this.rows.forEach((r, i) => { const y = T + i * bh + bh * .2, hh = bh * .6;
      g.fillStyle = css('--ink2'); g.textAlign = 'right'; g.fillText(r.label, L - 8, y + hh / 2);
      const a = Math.min(r.lo, r.hi), b = Math.max(r.lo, r.hi);
      g.fillStyle = css('--blue'); g.globalAlpha = .85; g.fillRect(X(a), y, Math.max(2, X(b) - X(a)), hh); g.globalAlpha = 1;
      g.fillStyle = css('--ink'); g.textAlign = 'left'; g.font = '11.5px system-ui'; g.fillText(this.fmt(a) + ' – ' + this.fmt(b), Math.min(X(b) + 6, W - 120), y + hh / 2); g.font = '12px system-ui'; });
    g.strokeStyle = css('--ink'); g.lineWidth = 1.4; g.beginPath(); g.moveTo(X(this.base), T); g.lineTo(X(this.base), H - B); g.stroke();
  }
}

function downloadCSV(name, header, rows) {
  const txt = [header.join(',')].concat(rows.map(r => r.map(v => (v == null ? '' : String(v))).join(','))).join('\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['﻿' + txt], { type: 'text/csv;charset=utf-8' })); a.download = name; a.click();
}
function themeToggle() {
  const b = h('button', { class: 'btn ghost', title: 'Switch light / dark theme', onclick: () => {
    const cur = document.documentElement.getAttribute('data-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark'); window.dispatchEvent(new Event('resize')); window.__redraw && window.__redraw(); } }, 'Theme');
  return b;
}
const fmt2 = v => nf(v, 2);
function r2score(real, sim) { let m = 0; real.forEach(v => m += v); m /= real.length; let a = 0, b = 0; real.forEach((v, i) => { a += (v - sim[i]) ** 2; b += (v - m) ** 2; }); return 1 - a / b; }
