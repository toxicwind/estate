/**
 * embed-cluster.ts — embed + cluster the api-evangelist repo survey with a
 * freeinference bge-m3 embedding, so the tooling layer is found semantically
 * (cosine similarity to "API tooling/observability/probing" prototypes) not by
 * brittle description regex. This replaces the dump-vs-tooling regex guess.
 *
 * Run:  bun embed-cluster.ts [repoSampleSize]
 * Env:  FREEINFERENCE_API_KEY (or secretsmith service=freeinference)
 * Writes: out/embedding-clusters.json
 */
import { writeFileSync, mkdirSync } from "node:fs";

const ORG = "api-evangelist";
const EMBED_MODEL = "bge-m3";

export function embedKey(): string {
  const fromEnv = globalThis.process?.env?.FREEINFERENCE_API_KEY;
  if (fromEnv) return fromEnv;
  // secretsmith keyring (service=freeinference) then ~/.secrets
  try {
    const { execFileSync } =
      require("node:child_process") as typeof import("node:child_process");
    const out = execFileSync(
      "secretsmith",
      ["get", "--attr", "service=freeinference", "--show"],
      {
        encoding: "utf8",
        timeout: 5000,
        env: { ...process.env, GH_TOKEN: "", GITHUB_TOKEN: "" },
      },
    );
    const m = /^secret:\s*(.*)$/m.exec(out);
    if (m && m[1]) return m[1].trim();
  } catch {
    // fall through
  }
  try {
    const { readFileSync, existsSync } =
      require("node:fs") as typeof import("node:fs");
    const p = `${process.env.HOME ?? "/home/toxic"}/.secrets`;
    if (existsSync(p)) {
      const raw = readFileSync(p, "utf8");
      const m = /^FREEINFERENCE_API_KEY=(.*)$/m.exec(raw);
      if (m && m[1]) return m[1].trim().replace(/^["']|["']$/g, "");
    }
  } catch {
    // ignore
  }
  return "";
}

/** Fetch `n` repo metadata rows (alphabetical, not pushed-sorted, to sample the
 *  whole org not just the nightly dump waterfall). */
async function fetchRepos(
  n: number,
): Promise<Array<{ name: string; desc: string }>> {
  const rows: Array<{ name: string; desc: string }> = [];
  let page = 1;
  while (rows.length < n && page < 600) {
    const url = `https://api.github.com/users/${ORG}/repos?per_page=100&page=${page}`;
    const res = await fetch(url, {
      headers: { Accept: "application/vnd.github+json" },
    });
    if (!res.ok) break;
    const batch = (await res.json()) as Record<string, unknown>[];
    if (batch.length === 0) break;
    for (const r of batch) {
      rows.push({
        name: String(r.name ?? ""),
        desc: String(r.description ?? ""),
      });
      if (rows.length >= n) break;
    }
    page++;
  }
  return rows;
}

async function embedTexts(
  apiKey: string,
  texts: string[],
): Promise<number[][]> {
  const out: number[][] = [];
  const batch = 64;
  for (let i = 0; i < texts.length; i += batch) {
    const slice = texts.slice(i, i + batch);
    const res = await fetch("https://freeinference.org/v1/embeddings", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model: EMBED_MODEL, input: slice }),
    });
    const json = (await res.json()) as {
      data?: Array<{ index: number; embedding: number[] }>;
    };
    const byIndex = new Map(
      (json.data ?? []).map((d) => [d.index, d.embedding]),
    );
    for (let k = 0; k < slice.length; k++) {
      const e = byIndex.get(k);
      out.push(e ?? Array(1024).fill(0));
    }
  }
  return out;
}

function cosine(a: number[], b: number[]): number {
  let dot = 0;
  let na = 0;
  let nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) || 1);
}

const PROTOTYPES: Array<{ label: string; text: string }> = [
  {
    label: "tooling",
    text: "API tooling, observability, monitoring, probing, endpoint health, rate limits, schema catalog, developer index",
  },
  {
    label: "company-dump",
    text: "a company profile listing their public API surface and products",
  },
  {
    label: "openapi-spec",
    text: "OpenAPI specification and API reference documentation for a service",
  },
  {
    label: "ml-model",
    text: "machine learning model, NIM, LLM, generative AI, embeddings, inference",
  },
];

export async function main(sampleSize = 400): Promise<void> {
  const apiKey = embedKey();
  if (!apiKey)
    throw new Error(
      "FREEINFERENCE_API_KEY not set (or secretsmith service=freeinference)",
    );
  const repos = await fetchRepos(sampleSize);
  // embed repo summaries + the prototype texts
  const texts = repos.map((r) => `${r.name}: ${r.desc}`);
  const protos = PROTOTYPES.map((p) => p.text);
  const [repoVectors, protoVectors] = await Promise.all([
    embedTexts(apiKey, texts),
    embedTexts(apiKey, protos),
  ]);

  const classified = repos.map((r, i) => {
    const v = repoVectors[i]!;
    const sims = PROTOTYPES.map((p, j) => ({
      label: p.label,
      sim: cosine(v, protoVectors[j]!),
    }));
    const best = [...sims].sort((a, b) => b.sim - a.sim)[0]!;
    return {
      name: r.name,
      desc: r.desc.slice(0, 90),
      label: best.label,
      sim: best.sim,
      sims,
    };
  });

  mkdirSync("out", { recursive: true });
  writeFileSync(
    "out/embedding-clusters.json",
    JSON.stringify(
      { model: EMBED_MODEL, sample: classified.length, classified },
      null,
      2,
    ),
    "utf8",
  );

  // digest
  const counts: Record<string, number> = {};
  for (const c of classified) counts[c.label] = (counts[c.label] ?? 0) + 1;
  console.log(
    JSON.stringify(
      { model: EMBED_MODEL, sample: classified.length, counts },
      null,
      2,
    ),
  );
  for (const c of classified
    .filter((x) => x.label === "tooling")
    .slice(0, 20)) {
    console.log(`  tooling: ${c.name} (${c.sim.toFixed(2)})\t${c.desc}`);
  }
}

if (import.meta.main) await main(Number(process.argv[2] ?? 400));
