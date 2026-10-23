export const DIM = 128;
function mulberry32(a) {
  return function () {
    let t = (a += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(0xC0FFEE);
function randn() {
  let u = 0, v = 0;
  while (u === 0) u = rand();
  while (v === 0) v = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}
export function randRange(a, b) { return a + rand() * (b - a); }
function randomVec(scale = 1.0) {
  const v = new Float32Array(DIM);
  for (let i = 0; i < DIM; i++) v[i] = randn() * scale;
  return v;
}
function add(a, b, scaleB = 1) {
  const out = new Float32Array(DIM);
  for (let i = 0; i < DIM; i++) out[i] = a[i] + b[i] * scaleB;
  return out;
}
export function distL2(a, b) {
  let s = 0;
  for (let i = 0; i < DIM; i++) { const d = a[i] - b[i]; s += d * d; }
  return Math.sqrt(s);
}
const VOCAB = ["compiler","bytecode","JMP_TABLE","LOAD","CONTENT","PTR_DEREF","YIELD","subconscious","CONTRA","slot[4]","JMP_TABLE[2]","PLAN_TRACE","POINTER","PSEUDO","ADJACENT","EXEC","LOAD_SUB","ADJ_EDGE","RESOLVE","JMP"];
const inCompiler = new Set(["compiler","bytecode","JMP_TABLE","LOAD","CONTENT","PTR_DEREF","YIELD","LOAD_SUB"]);
const inSub = new Set(["subconscious","PLAN_TRACE","POINTER","PSEUDO","ADJACENT","EXEC"]);
const CENTROIDS = {
  compiler: { vec: randomVec(0.8), x: 150, y: 140 },
  subconscious: { vec: add(randomVec(0.8), randomVec(0.8), 0.3), x: 600, y: 180 },
  CONTRA: { vec: add(randomVec(0.8), randomVec(0.8), 0.3), x: 1000, y: 160 }
};
function centroidOf(tok) {
  if (inCompiler.has(tok)) return CENTROIDS.compiler;
  if (inSub.has(tok)) return CENTROIDS.subconscious;
  return CENTROIDS.CONTRA;
}
const EMBEDDINGS = {};
for (const tok of VOCAB) EMBEDDINGS[tok] = add(centroidOf(tok).vec, randomVec(0.35), 1);
const PSEUDO_TOKEN = "__PSEUDO_SLOT4__";
EMBEDDINGS[PSEUDO_TOKEN] = add(CENTROIDS.CONTRA.vec, randomVec(0.15), 1);
const PATHS = [
  { name: "Conservative Linear", id: "linear", computeScale: (T) => T * 0.55, jitter: () => randRange(0, 4), color: "#4ade80" },
  { name: "Aggressive Exponential", id: "exponential", computeScale: (T) => (Math.exp(T * 0.82) - 1) * 0.9, jitter: () => randRange(2, 9), color: "#f97316" },
  { name: "Stochastic Walk", id: "stochastic", computeScale: (T) => T * (0.3 + rand() * 1.25), jitter: () => randRange(-1, 14), color: "#38bdf8" }
];
export { VOCAB, EMBEDDINGS, PSEUDO_TOKEN, PATHS, CENTROIDS };
