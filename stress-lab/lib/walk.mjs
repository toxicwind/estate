import { VOCAB, EMBEDDINGS, PSEUDO_TOKEN, PATHS, CENTROIDS, distL2 } from "./embeddings.mjs";
const STEPS = 12, T_START = 0.2, T_END = 1.6;
export function annealSchedule() {
  const arr = [];
  for (let i = 0; i < STEPS; i++) arr.push(T_START + (i / (STEPS - 1)) * (T_END - T_START));
  return arr;
}
export function runTokenWalk() {
  const Ts = annealSchedule();
  const results = [];
  const globalStats = { maxP: 0, loadBearingCount: 0, siphonRates: [] };
  const centroidOf = (tok) => {
    if (["compiler","bytecode","JMP_TABLE","LOAD","CONTENT","PTR_DEREF","YIELD","LOAD_SUB"].includes(tok)) return CENTROIDS.compiler;
    if (["subconscious","PLAN_TRACE","POINTER","PSEUDO","ADJACENT","EXEC"].includes(tok)) return CENTROIDS.subconscious;
    return CENTROIDS.CONTRA;
  };
  for (const path of PATHS) {
    let prevP = null, prevDist = null, prevToken = null;
    for (let step = 0; step < STEPS; step++) {
      const T = Ts[step];
      const scaleOffset = path.computeScale(T);
      const tokIdx = (step * 2 + (path.id === "exponential" ? 3 : 0)) % VOCAB.length;
      const token = VOCAB[tokIdx];
      const centroid = centroidOf(token);
      const baseDist = distL2(EMBEDDINGS[token], centroid.vec);
      const dist = baseDist * scaleOffset;
      const jitter = path.jitter();
      const P = 25 + T * 18 + dist * 0.85 + jitter;
      const X = centroid.x + dist * 5.2 + step * 3;
      const Y = centroid.y + Math.sin(step * 0.9 + T * 2) * (30 + T * 35);
      let dPdDelta = 0, dDist = 0;
      if (prevP !== null) { dDist = Math.abs(dist - prevDist) + 1e-6; dPdDelta = (P - prevP) / dDist; }
      const loadBearing = P > 50;
      if (loadBearing) globalStats.loadBearingCount++;
      if (P > globalStats.maxP) globalStats.maxP = P;
      if (prevP !== null) globalStats.siphonRates.push(dPdDelta);
      const neighbors = VOCAB.map(o => o === token ? null : { token: o, dist: distL2(EMBEDDINGS[token], EMBEDDINGS[o]) }).filter(Boolean).sort((a, b) => a.dist - b.dist).slice(0, 3);
      results.push({
        path: path.id, pathName: path.name, color: path.color, step, T: +T.toFixed(3), token,
        dist: +dist.toFixed(3), baseDist: +baseDist.toFixed(3), scaleOffset: +scaleOffset.toFixed(3),
        jitter: +jitter.toFixed(2), P: +P.toFixed(2), X: +X.toFixed(1), Y: +Y.toFixed(1),
        dPdDelta: +dPdDelta.toFixed(3), dDist: +dDist.toFixed(3), loadBearing,
        visual: loadBearing ? { radius: 5, outerRing: 9, color: "#ff3344" } : { radius: 3, outerRing: 0, color: path.color },
        neighbors,
        isPseudoBoundary: step === STEPS - 1 || step === Math.floor(STEPS / 2),
        jump: prevToken ? { from: prevToken, to: token } : null
      });
      prevP = P; prevDist = dist; prevToken = token;
    }
    const mid = Math.floor(STEPS / 2);
    const pseudoDist = distL2(EMBEDDINGS[PSEUDO_TOKEN], CENTROIDS.CONTRA.vec) * path.computeScale(Ts[mid]);
    const pseudoP = 25 + Ts[mid] * 18 + pseudoDist * 0.85 + 11;
    results.push({
      path: path.id, pathName: path.name, color: "#ff3344", step: mid, T: +Ts[mid].toFixed(3),
      token: PSEUDO_TOKEN, note: "slot[4]=JMP_TABLE[2] pseudo-embedding (not in vocab)",
      dist: +pseudoDist.toFixed(3), P: +pseudoP.toFixed(2),
      X: +(CENTROIDS.CONTRA.x + pseudoDist * 5.2).toFixed(1),
      Y: +(CENTROIDS.CONTRA.y + Math.sin(mid * 0.9 + Ts[mid] * 2) * (30 + Ts[mid] * 35) - 18).toFixed(1),
      dPdDelta: 0, loadBearing: true,
      visual: { radius: 5, outerRing: 9, color: "#ff3344", persistent: true },
      neighbors: [{ token: "JMP_TABLE[2]", dist: 0.2 }, { token: "CONTRA", dist: 0.44 }],
      isPseudoBox: true
    });
  }
  return { results, stats: globalStats, Ts };
}
export function quantifyEntropySiphon(results) {
  const byPath = {};
  for (const r of results) {
    if (!byPath[r.path]) byPath[r.path] = { Ps: [], dP: [], load: 0, tokens: [] };
    byPath[r.path].Ps.push(r.P);
    if (r.dPdDelta) byPath[r.path].dP.push(r.dPdDelta);
    if (r.loadBearing) byPath[r.path].load++;
    byPath[r.path].tokens.push(r.token);
  }
  const quantified = {};
  for (const [k, v] of Object.entries(byPath)) {
    const meanP = v.Ps.reduce((a, b) => a + b, 0) / v.Ps.length;
    const meanSiphon = v.dP.length ? v.dP.reduce((a, b) => a + b, 0) / v.dP.length : 0;
    quantified[k] = {
      meanPerplexity: +meanP.toFixed(2), meanEntropySiphonRate: +meanSiphon.toFixed(3),
      maxP: +Math.max(...v.Ps).toFixed(2), loadBearingFraction: +(v.load / v.Ps.length).toFixed(3),
      uniqueTokens: new Set(v.tokens).size
    };
  }
  return quantified;
}
