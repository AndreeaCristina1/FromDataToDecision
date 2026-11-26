/* ===== Core of SD Model 1 (hotels - agritourism), annual step, t = 0 is 2001; same equations as sd1_model.py ===== */
const SD1_DEFAULT = { A0: 0.31739, M: 1, p: 0.01063, q: 1.0, bH: 1.38773, gamma: 80622.07, delta: 0.40022, dH: 0.32805, dA: 0, KA: 531348.70,
  shockH2020: 0.15244, shockH2021: 0.344, shockA2020: 0.02654, shockA2021: -0.14985, rep0: 0, polK: 0.4, polMid: 12.5 };

function sd1(P, horizonYear = 2045, demandGrowth = 0, shocks = true) {
  const n = horizonYear - 2001 + 1;
  const CH = new Array(n + 1).fill(0), CA = new Array(n + 1).fill(0), REP = new Array(n + 1).fill(0);
  const o = { year: [], NH: [], NA: [], occH: [], occA: [], cotaH: [], cotaA: [], invA: [], invH: [], depH: [], dREP: [], pol: [], cerere: [], calte: [], att: [], room: [] };
  CH[0] = DATA.CH[0]; CA[0] = DATA.CA[0]; REP[0] = P.rep0;
  for (let t = 0; t < n; t++) {
    const cer = t < 25 ? DATA.Nt[t] : DATA.Nt[24] * Math.pow(1 + demandGrowth, t - 24);
    const calte = t < 25 ? DATA.CAlte[t] : DATA.CAlte[24];
    const att = P.A0 * (1 + REP[t] / P.M);
    const den = CH[t] + CA[t] * att + calte;
    const cH = CH[t] / den, cA = CA[t] * att / den;
    const NH = cH * cer, NA = cA * cer, occH = NH / CH[t];
    const dREP = P.p * (P.M - REP[t]) + P.q * REP[t] * (P.M - REP[t]) / P.M;
    const pol = 1 / (1 + Math.exp(-P.polK * (t - P.polMid)));
    const room = Math.max(1 - CA[t] / P.KA, 0);
    const invA = (P.gamma * dREP + P.delta * pol * CA[t]) * room;
    const invH = P.bH * occH * CH[t], depH = P.dH * CH[t], depA = P.dA * CA[t];
    const yr = 2001 + t; let sH = 0, sA = 0;
    if (shocks) { if (yr === 2020) { sH = P.shockH2020; sA = P.shockA2020; } else if (yr === 2021) { sH = P.shockH2021; sA = P.shockA2021; } }
    CH[t + 1] = CH[t] + invH - depH + sH * CH[t];
    CA[t + 1] = CA[t] + invA - depA + sA * CA[t];
    REP[t + 1] = Math.min(REP[t] + dREP, P.M);
    o.year.push(yr); o.NH.push(NH); o.NA.push(NA); o.occH.push(occH); o.occA.push(NA / CA[t]); o.cotaH.push(cH); o.cotaA.push(cA);
    o.invA.push(invA); o.invH.push(invH); o.depH.push(depH); o.dREP.push(dREP); o.pol.push(pol); o.cerere.push(cer); o.calte.push(calte); o.att.push(att); o.room.push(room);
  }
  o.CH = CH.slice(0, n); o.CA = CA.slice(0, n); o.REP = REP.slice(0, n);
  return o;
}
/* first year in which CA reaches the fraction f of the carrying capacity */
function yearReach(o, f, KA) { for (let i = 0; i < o.CA.length; i++) if (o.CA[i] >= f * KA) return o.year[i]; return null; }
