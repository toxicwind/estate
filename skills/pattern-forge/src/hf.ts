import { HF_TOKEN, resolveMaybe } from "./hf-lib";

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
 *  Scores each label via normalized character n-gram overlap + word Jaccard against
 *  the probe text. Returns labels sorted desc; used when HF serverless is 402-gated
 *  or unreachable so `forge hf classify` NEVER fails bare. */
export function localZeroShot(text: string, labels: string[]): { label: string; score: number }[] {
  const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();
  const t = norm(text);
  const words = (s: string) => new Set(norm(s).split(/\s+/).filter(Boolean));
  const tw = words(t);
  const charGrams = (s: string, n: number) => {
    const out = new Set<string>();
    const normed = norm(s);
    for (let i = 0; i + n <= normed.length; i++) out.add(normed.slice(i, i + n));
    return out;
  };
  const tBigrams = charGrams(t, 2);
  const tTrigrams = charGrams(t, 3);

  const scored = labels.map((label) => {
    const lw = words(label);
    let overlap = 0;
    for (const w of lw) if (tw.has(w)) overlap++;
    const jaccard = tw.size + lw.size === 0 ? 0 : overlap / (tw.size + lw.size - overlap);

    const lb = charGrams(label, 2);
    const lt = charGrams(label, 3);
    let bCommon = 0;
    for (const g of lb) if (tBigrams.has(g)) bCommon++;
    let tCommon = 0;
    for (const g of lt) if (tTrigrams.has(g)) tCommon++;
    const bigramSim = lb.size ? bCommon / lb.size : 0;
    const trigramSim = lt.size ? tCommon / lt.size : 0;

    const score = jaccard * 0.6 + bigramSim * 0.3 + trigramSim * 0.1;
    return { label, score };
  });
  return scored.sort((a, b) => b.score - a.score);
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