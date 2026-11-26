
/* ===== Core of SD Model 2 (technology acceptance and quality of life); requires sd1core.js ===== */
const KAPPA = Math.log(6.5 / 6.1) / 13;   // annual growth of life satisfaction in Romania, 2003-2016 (6.1 -> 6.5)
const SD2_DEFAULT = { p_r: 0.01, q_r: 0.15, r_r: 0.08, gamma: 0.01, lam0: 0.01, gBudget: 0.0, tax: 0.02, eff: 1.0, budget0: 1.5e9, perTrip: 500,
  acc0: 0.3184, qol0: 6.5, horizon: 2045, frozen: false, path: 'calibrated' };
const START = 2025;
const lam = (acc, l0) => l0 - (l0 + KAPPA) * acc;
const accNeutral = l0 => l0 / (l0 + KAPPA);

/* agritourism capacity and arrivals: simulated capacity of Model 1; observed arrivals until 2025, then proportional to capacity */
function agroPath(kind, hy = 2060) {
  const P = { ...SD1_DEFAULT };
  if (kind === 'nopolicy') P.delta = 0; if (kind === 'doubled') P.delta = SD1_DEFAULT.delta * 2;
  const o = sd1(P, hy, 0, true), n = o.CA.length, CA = [], Sos = [];
  const ratio = DATA.SosA[24] / DATA.CA[24];
  for (let t = 0; t < n; t++) {
    let ca = o.CA[t];                      // continuous simulated trajectory (calibrated on 2001-2025)
    if (kind === 'const' && t >= 25) ca = o.CA[24];
    CA.push(ca); Sos.push(t < 25 ? DATA.SosA[t] : ca * ratio);
  }
  return { CA, Sos };
}
const PATHS = {}; function getPath(kind) { return PATHS[kind] || (PATHS[kind] = agroPath(kind, 2060)); }

function sd2(P) {
  const A = getPath(P.path), i0 = START - 2001, n = P.horizon - START + 1, ref = A.CA[i0];
  const acc = [P.acc0], qol = [P.qol0];
  const o = { year: [], budget: [], venit: [], bef: [], raport: [], presiune: [], resist: [], dacc: [], lam: [], lamEff: [], ca: [], taxRev: [] };
  for (let k = 0; k < n; k++) {
    const yr = START + k, ca = A.CA[i0 + k], sos = A.Sos[i0 + k];
    const bud = P.budget0 * Math.pow(1 + P.gBudget, yr - START), ven = sos * P.perTrip, bef = bud + ven * P.tax;
    const raport = P.eff * bef / P.budget0, pres = ca / ref;
    const res = P.r_r * Math.max(pres - 1, 0) * acc[k];
    const dacc = P.frozen ? 0 : P.p_r * (1 - acc[k]) + P.q_r * acc[k] * (1 - acc[k]) - res;
    const l = lam(acc[k], P.lam0), le = l + P.gamma * (1 - raport);
    acc.push(Math.min(Math.max(acc[k] + dacc, 0), 1)); qol.push(qol[k] * Math.exp(-le));
    o.year.push(yr); o.budget.push(bud); o.venit.push(ven); o.bef.push(bef); o.raport.push(raport);
    o.presiune.push(pres); o.resist.push(res); o.dacc.push(dacc); o.lam.push(l); o.lamEff.push(le); o.ca.push(ca); o.taxRev.push(ven * P.tax);
  }
  o.acc = acc.slice(0, n); o.qol = qol.slice(0, n); return o;
}
