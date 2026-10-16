import { HF_TOKEN, resolveMaybe, FREEINF_BASE, FREEINF_KEY } from "./hf-lib";

export const HF_HUB = "https://huggingface.co/api/models";
export const HF_TASKS = "https://huggingface.co/api/tasks";
export const HF_INFERENCE = "https://router.huggingface.co/hf-inference";
export const USER_AGENT = "pattern-forge/hf-1.0";

export interface HfModel {
  id: string;
  downloads: number;
  likes: number;
  trending: number;
  createdAt?: string;
  modifiedAt?: string;
  pipelineTag?: string; // zero-shot-classification, text-classification, fill-mask…
  libraryName?: string; // transformers, sentence-transformers, tiktoken…
  tags: string[];
  sha?: string;
  task?: string;
}

const TASK_ALIASES: Record<string, string[]> = {
  "zero-shot": ["zero-shot-classification"],
  zsc: ["zero-shot-classification"],
  class: ["zero-shot-classification", "text-classification", "token-classification"],
  embed: ["feature-extraction", "sentence-similarity"],
  retriever: ["feature-extraction", "sentence-similarity"],
  nli: ["zero-shot-classification", "text-classification"],
  search: ["feature-extraction"],
  rerank: ["text-classification"],
  quant: ["generation", "text-generation"],
  gen: ["generation", "text-generation"],
};

function resolveTask(term: string | undefined): string[] {
  if (!term) return [];
  const t = term.toLowerCase();
  if (TASK_ALIASES[t]) return TASK_ALIASES[t];
  return [t];
}

export function buildSearchParams(query: string, opts: { sort?: string; direction?: string; limit?: number; task?: string; library?: string } = {}): URLSearchParams {
  const p = new URLSearchParams();
  if (query) p.set("search", query);
  p.set("sort", opts.sort ?? "downloads");
  p.set("direction", opts.direction ?? "-1");
  p.set("limit", String(opts.limit ?? 12));
  const tasks = resolveTask(opts.task);
  if (tasks.length === 1) p.set("pipeline_tag", tasks[0]);
  const lib = opts.library;
  if (lib) p.set("library_name", lib.toLowerCase());
  return p;
}

export async function hfSearch(query: string, opts: { sort?: string; direction?: string; limit?: number; task?: string; library?: string } = {}): Promise<HfModel[]> {
  const params = buildSearchParams(query, opts);
  const url = `${HF_HUB}?${params.toString()}`;
  const res = await fetch(url, { headers: { "User-Agent": USER_AGENT, "Authorization": `Bearer ${HF_TOKEN}` } });
  if (!res.ok) throw new Error(`HF models API ${res.status}: ${await res.text().catch(() => "")}`);
  const rows = await res.json() as any[];
  return rows.map(mapRow);
}

function mapRow(r: any): HfModel {
  return {
    id: r.id ?? "",
    downloads: r.downloads ?? 0,
    likes: r.likes ?? 0,
    trending: r.trendingScore ?? 0,
    createdAt: r.createdAt,
    modifiedAt: r.lastModified,
    pipelineTag: r.pipeline_tag,
    libraryName: r.library_name,
    tags: r.tags ?? [],
    sha: r.sha,
    task: r.pipeline_tag,
  };
}

/** Model self-eval rank for "best 2026": downloads*growth + likes + recency, normalized. */
export function rankModel(m: HfModel, now = Date.now()): number {
  const downloads = Math.log1p(m.downloads ?? 0);
  const likes = Math.log1p(m.likes ?? 0);
  const trending = Math.log1p(m.trending ?? 0);
  let recency = 0;
  if (m.modifiedAt) {
    const ageDays = (now - Date.parse(m.modifiedAt)) / 86_400_000;
    recency = Math.max(0, 1 - ageDays / 365);
  }
  return downloads * 2 + likes * 3 + trending * 2 + recency * 4;
}

export function sortByRank(models: HfModel[]): HfModel[] {
  return [...models].sort((a, b) => rankModel(b) - rankModel(a));
}

/**
 * Zero-shot classification against a single HF Inference model via the
 * raw router. Returns a [label, score] pair. Called concurrently by
 * `classify` to race candidate models.
 */
export interface ZeroShotInput {
  text: string;
  labels: string[];
  candidateThreshold?: number; // multi_label; first label above this wins
}

export interface ClassifyVerdict {
  candidate: string;
  label: string;
  score: number;
  ok: boolean;
  ms: number;
  error?: string;
}

export async function classifyOne(modelId: string, input: ZeroShotInput, timeoutMs = 15_000): Promise<ClassifyVerdict> {
  const started = Date.now();
  const body = {
    inputs: input.text,
    parameters: { candidate_labels: input.labels, multi_label: (input.candidateThreshold ?? 0) > 0 },
  };
  try {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), timeoutMs);
    const res = await fetch(`${HF_INFERENCE}/models/${modelId}`, {
      method: "POST",
      headers: { "User-Agent": USER_AGENT, "Authorization": `Bearer ${HF_TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ac.signal,
    });
    clearTimeout(timer);
    if (res.status === 503) {
      const wait = Number(res.headers.get("x-wait-to-load") ?? 8_000);
      await new Promise((r) => setTimeout(r, Math.min(wait, 20_000)));
      return classifyOne(modelId, input, timeoutMs); // retry once after model load
    }
    if (!res.ok) return { candidate: modelId, label: "", score: 0, ok: false, ms: Date.now() - started, error: `HTTP ${res.status}` };
    const data = await res.json();
    const cand: string[] = Array.isArray(data.labels)
      ? data.labels
      : Array.isArray(data.scores)
        ? (data.scores as string[]).map((_: string, i: number) => `label${i}`)
        : [];
    const scores: number[] = Array.isArray(data.scores) ? data.scores as number[] : [];
    let best = -1;
    let bestScore = -Infinity;
    for (let i = 0; i < cand.length; i++) {
      const s = Number(scores[i] ?? 0);
      if (s > bestScore) { bestScore = s; best = i; }
    }
    return { candidate: modelId, label: best >= 0 ? String(cand[best]) : "", score: bestScore, ok: best >= 0, ms: Date.now() - started };
  } catch (e: any) {
    return { candidate: modelId, label: "", score: 0, ok: false, ms: Date.now() - started, error: e?.message ?? "timeout/aborted" };
  }
}

/** Each candidate model returns: model + verdict of classifying a probe input. */
export interface ClassifierCandidate {
  model: string;
  rank: number;
  downloads: number;
  likes: number;
  verdict?: ClassifyVerdict;
}

/** @returns displayable confidence 0..1 that the winner is 'the best' of candidates. */
export async function classifyRace(input: ZeroShotInput, models: string[], concurrency = 3): Promise<{ winner: string; candidates: ClassifierCandidate[]; agreed: number }> {
  const results: ClassifierCandidate[] = [];
  for (let i = 0; i < models.length; i += concurrency) {
    const batch = models.slice(i, i + concurrency);
    const done = await Promise.all(batch.map((m) => classifyOne(m, input)));
    results.push(...done.map((v, j) => ({
      model: batch[j],
      rank: 0,
      downloads: 0,
      likes: 0,
      verdict: v,
    })));
  }
  const ok = results.filter((r) => r.verdict?.ok);
  const byLabel = new Map<string, number>();
  let winnerLabel = "";
  let agreed = 0;
  for (const r of ok) {
    byLabel.set(r.verdict!.label, (byLabel.get(r.verdict!.label) ?? 0) + 1);
  }
  for (const [label, count] of byLabel) {
    if (count > agreed) { agreed = count; winnerLabel = label; }
  }
  const winner = ok.find((r) => r.verdict!.label === winnerLabel)?.model ?? "";
  return { winner, candidates: results, agreed };
}

/** Completion-based classifier via FreeInference (free, OpenAI-compatible, no HF
 *  credit gate). Strict single-token system prompt enumerates the label set and
 *  the LLM replies verbatim; we pick the emitted label. BEST-match label
 *  normalizes punctuation/case. Returns the FreeInference model used. */
export interface CompletionsResult {
  ok: boolean;
  winner: string;
  score: number;
  model: string;
  raw: string;
  error?: string;
  ms: number;
}
export async function completionsClassify(text: string, labels: string[], opts: { model?: string; timeoutMs?: number } = {}): Promise<CompletionsResult> {
  if (!FREEINF_KEY) return { ok: false, winner: "", score: 0, model: "", raw: "", error: "no FREEINFERENCE_API_KEY", ms: 0 };
  const model = opts.model ?? "glm-5.3-flash";
  const started = Date.now();
  const list = labels.join("\n");
  const system = "You are a precise classifier. Read the user's input and answer with EXACTLY one of the allowed labels, verbatim, with no punctuation, quotes, markdown, or explanation.";
  const body = {
    model,
    messages: [
      { role: "system", content: system },
      { role: "user", content: `Allowed labels:\n${list}\n\nClassify this:\n${text}\n\nAnswer with exactly one label:` },
    ],
    max_tokens: 8,
  };
  try {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), opts.timeoutMs ?? 25_000);
    const res = await fetch(`${FREEINF_BASE}/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${FREEINF_KEY}` },
      body: JSON.stringify(body),
      signal: ac.signal,
    });
    clearTimeout(timer);
    if (!res.ok) return { ok: false, winner: "", score: 0, model, raw: "", error: `HTTP ${res.status}`, ms: Date.now() - started };
    const data = await res.json();
    const raw = (data?.choices?.[0]?.message?.content ?? "").toString();
    const winner = pickLabel(raw, labels);
    return { ok: !!winner, winner, score: winner ? 1 : 0, model, raw: raw.slice(0, 40), ms: Date.now() - started };
  } catch (e: any) {
    return { ok: false, winner: "", score: 0, model, raw: "", error: e?.message ?? "timeout", ms: Date.now() - started };
  }
}

/** Parse the LLM's reply into one of the allowed labels (case/punct-insensitive, prefix-tolerant for multi-word labels). */
export function pickLabel(raw: string, labels: string[]): string {
  const clean = raw.trim().replace(/^["'`\s]+|["'`\s.,;:!?]+$/g, "");
  const lower = clean.toLowerCase();
  for (const l of labels) {
    const ll = l.toLowerCase();
    if (lower.startsWith(ll)) return l;         // exact or prefix (handles trailing noise)
    if (ll.split(/\s+/).some((w) => w.length > 3 && lower.includes(w))) return l; // distinctive word
  }
  // fuzzy: any label token appearing anywhere
  for (const l of labels) {
    if (l.split(/\s+/).some((w) => w.length >= 3 && lower.includes(w.toLowerCase()))) return l;
  }
  return "";
}

/** List models available on FreeInference (/v1/models). */
export async function freeinfModels(): Promise<string[]> {
  if (!FREEINF_KEY) return [];
  try {
    const res = await fetch(`${FREEINF_BASE}/models`, { headers: { "Authorization": `Bearer ${FREEINF_KEY}` } });
    if (!res.ok) return [];
    const d = await res.json();
    return (d.data ?? []).map((m: any) => m.id);
  } catch {
    return [];
  }
}

export interface EmbedResult {
  ok: boolean;
  winner: string;
  score: number;   // cosine to winner
  margin: number;  // winner minus runner-up
  ranked: { label: string; score: number }[];
  model: string;
  dims: number;
  error?: string;
  ms: number;
}

export function cosine(a: number[], b: number[]): number {
  let dot = 0, an = 0, bn = 0;
  for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; an += a[i] * a[i]; bn += b[i] * b[i]; }
  return dot / (Math.sqrt(an) * Math.sqrt(bn) || 1);
}

/** Embedding-based classifier via FreeInference bge-m3. Embed the probe text and
 *  each candidate label, pick the nearest by cosine. Deterministic, fast, and
 *  credit-free — the "actual bge-m3" path, not an LLM. Margin-gated. */
export async function embedClassify(text: string, labels: string[], opts: { model?: string; labelDesc?: boolean; timeoutMs?: number } = {}): Promise<EmbedResult> {
  if (!FREEINF_KEY) return { ok: false, winner: "", score: 0, margin: 0, ranked: [], model: opts.model ?? "bge-m3", dims: 0, error: "no FREEINFERENCE_API_KEY", ms: 0 };
  const model = opts.model ?? "bge-m3";
  const started = Date.now();
  const inputs = [text, ...labels.map((l) => (opts.labelDesc ? `label: ${l}` : l))];
  try {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), opts.timeoutMs ?? 30_000);
    const res = await fetch(`${FREEINF_BASE}/embeddings`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${FREEINF_KEY}` },
      body: JSON.stringify({ model, input: inputs }),
      signal: ac.signal,
    });
    clearTimeout(timer);
    if (!res.ok) return { ok: false, winner: "", score: 0, margin: 0, ranked: [], model, dims: 0, error: `HTTP ${res.status}`, ms: Date.now() - started };
    const d = await res.json();
    const vecs: number[][] = (d.data ?? []).map((x: any) => x.embedding);
    const dims = vecs[0]?.length ?? 0;
    const probe = vecs[0];
    if (dims === 0) return { ok: false, winner: "", score: 0, margin: 0, ranked: [], model, dims: 0, error: "empty embedding", ms: Date.now() - started };
    const ranked = labels.map((l, i) => ({
      label: l,
      score: vecs[i + 1] ? cosine(probe, vecs[i + 1]) : 0,
    })).sort((a, b) => b.score - a.score);
    const top = ranked[0];
    const margin = (top?.score ?? 0) - (ranked[1]?.score ?? 0);
    const confident = (top?.score ?? 0) > 0.2 && margin > 0.02;
    return { ok: confident, winner: confident ? top.label : "", score: top?.score ?? 0, margin, ranked, model, dims, ms: Date.now() - started };
  } catch (e: any) {
    return { ok: false, winner: "", score: 0, margin: 0, ranked: [], model, dims: 0, error: e?.message ?? "timeout", ms: Date.now() - started };
  }
}

/** Resolve classifier model ids: explicit list wins; else curated 2026 default. */
export async function bestClassifyModels(explicit: string[], labels: string[]): Promise<string[]> {
  if (explicit.length) return explicit;
  const curated = [
    "facebook/bart-large-mnli",           // classic zero-shot NLI
    "MoritzLaurer/deberta-v3-base-zeroshot-v2.0", // multilingual zero-shot
    "cross-encoder/nli-deberta-v3-xlarge", // strong NLI scorer
    "sentence-transformers/all-MiniLM-L6-v2", // fallback embed (via inference-classify proxy)
  ];
  return curated;
}

/** Pure-Bun, zero-dep, offline zero-shot scorer. Deterministic, free, no 402 gate.
 *  Scores each label via idf-weighted word overlap + normalized character n-gram
 *  similarity against the probe text. Returns labels sorted desc; used when HF
 *  serverless is 402-gated (no inference credits) or unreachable so that
 *  `forge hf classify` NEVER fails bare.
 *  BORROWED (2026-10, pattern-borrow — github lodestone/MaggieAppleton + freenary):
 *   - classifies against the label's RICH DESCRIPTION, not the short id  (lodestone)
 *   - gates with an explicit ACCEPT-CONFIDENCE threshold, and refuses to emit a
 *     winner below it instead of inventing a best label                  (freenary)
 *  NOTE (2026-10): the HF token has zero Inference-Provider credits — the free
 *  router returns HTTP 402 for every model. localZeroShot is the PRIMARY engine,
 *  not a fallback. */
export interface LabelConfig { id: string; desc: string }
export interface LocalVerdict {
  winner: string;
  score: number;
  margin: number;
  ranked: { label: string; score: number }[];
  confident: boolean;
}
// Lexical scorers don't hit high absolute values — confidence is a RELATIVE
// margin (top vs runner-up), mirroring freenary's concentration (the decision,
// not an absolute). Scores are normalized idf-weighted Jaccard + char-ngram.
const MIN_SCORE = 0.05;      // a winner must at least have SOME signal
const MIN_MARGIN = 0.08;     // and must beat the runner-up by this much

export function localZeroShot(text: string, labels:string[]|LabelConfig[], opts: { minScore?: number; minMargin?: number } = {}): LocalVerdict {
  const minScore = opts.minScore ?? MIN_SCORE;
  const minMargin = opts.minMargin ?? MIN_MARGIN;
  const configs: { id: string; desc: string }[] = labels.map((l) => typeof l === "string" ? { id: l, desc: l } : l);
  const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();
  const t = norm(text);
  const textWords = t.split(/\s+/).filter(Boolean);

  const STOP = new Set(["a","an","the","for","of","and","or","to","in","on","with","this","that","your","our","from","as","is","are","be","by","it","at","its"]);
  const df = new Map<string, number>();
  for (const w of textWords) if (!STOP.has(w)) df.set(w, (df.get(w) ?? 0) + 1);

  const charGrams = (s: string, n: number) => {
    const out = new Set<string>();
    const normed = norm(s);
    for (let i = 0; i + n <= normed.length; i++) out.add(normed.slice(i, i + n));
    return out;
  };
  const tBigrams = charGrams(t, 2);
  const tTrigrams = charGrams(t, 3);

  const scored: { label: string; score: number }[] = configs.map((c) => {
    // class against id + description, but down-weight the description so
    // filler words don't dilute the short-id signal (borrowed bidirectionally)
    const idTokens = norm(c.id).split(/\s+/).filter(Boolean);
    const lSet = new Set(idTokens);
    for (const w of norm(c.desc).split(/\s+/)) if (!STOP.has(w)) lSet.add(w);
    let idfOverlap = 0;
    let idfUnion = 0;
    for (const w of lSet) {
      const wIdf = STOP.has(w) ? 0 : Math.log2(1 + (textWords.length + 1) / ((df.get(w) ?? 0) + 1));
      idfUnion += wIdf || (STOP.has(w) ? 0.15 : 1);
      if (textWords.includes(w)) idfOverlap += wIdf || (STOP.has(w) ? 0.15 : 1);
    }
    const jaccard = idfUnion === 0 ? 0 : idfOverlap / idfUnion;

    const lb = charGrams(c.desc, 2);
    const lt = charGrams(c.desc, 3);
    let bCommon = 0;
    for (const g of lb) if (tBigrams.has(g)) bCommon++;
    let tCommon = 0;
    for (const g of lt) if (tTrigrams.has(g)) tCommon++;
    const bigramSim = lb.size ? bCommon / lb.size : 0;
    const trigramSim = lt.size ? tCommon / lt.size : 0;

    // id-token Jaccard is the strongest lexical signal for short labels; the
    // char-ngram on description adds fuzzy-catch. Weigh id tokens up.
    const score = jaccard * 0.7 + bigramSim * 0.25 + trigramSim * 0.05;
    return { label: c.id, score };
  });
  scored.sort((a, b) => b.score - a.score);
  const top = scored[0];
  const second = scored[1];
  const margin = (top?.score ?? 0) - (second?.score ?? 0);
  const confident = (top?.score ?? 0) >= minScore && margin >= minMargin;
  return { winner: confident ? top.label : "", score: top?.score ?? 0, margin, ranked: scored, confident };
}

/** Top candidate zero-shot/text-classification models from HF Hub by rank. */
export async function findClassifierCandidates(text: string, labels: string[], task: string, limit = 8): Promise<HfModel[]> {
  void text; void labels;
  const tasks = resolveTask(task);
  const searchTerms = tasks.length ? ["zeroshot", "zero-shot", "nli", "deberta", "bge", "embedding"] : ["classifier", "text-classification"];
  const pool: HfModel[] = [];
  for (const t of tasks.length ? tasks : ["zero-shot-classification", "text-classification"]) {
    for (const q of searchTerms) {
      try {
        const rows = await hfSearch(q, { sort: "downloads", limit: 4, task: t });
        pool.push(...rows);
      } catch { /* keep others */ }
    }
  }
  const dedupe = new Map<string, HfModel>();
  for (const m of pool) if (m.id && !dedupe.has(m.id)) dedupe.set(m.id, m);
  return sortByRank([...dedupe.values()]).slice(0, limit);
}