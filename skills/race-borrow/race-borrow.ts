#!/usr/bin/env bun
/**
 * race-borrow.ts — Race multiple providers for patterns, borrow the best results.
 * Combines the "race" parallel-first-wins concept with pattern-borrow ranking.
 *
 * Usage: bun run race-borrow.ts [patterns...] [--top N] [--per-page N] [--weights k=v,...] [--providers p1,p2,...] [--interactive] [--help]
 */

import { parseArgs } from "node:util";

const TOKEN = Bun.env.GITHUB_TOKEN ?? Bun.env.GH_TOKEN;
if (!TOKEN) {
  console.error("ERROR: GITHUB_TOKEN or GH_TOKEN required");
  process.exit(1);
}

const API = "https://api.github.com";
const HEAD = { Authorization: `token ${TOKEN}`, Accept: "application/vnd.github.v3+json" };

const DEFAULT_PATTERNS = ["sovereign", "tau", "pi", "oh-my-pi", "llama-swap"];
const DEFAULT_PROVIDERS = ["openrouter", "groq", "google", "mistral"];
const BUG_TERMS = ["TODO", "FIXME", "HACK", "BUG", "WORKAROUND", "XXX"];
const FACTORS = ["stars", "forks", "open_issues", "updated"] as const;
type Weight = Partial<Record<(typeof FACTORS)[number], number>>;
const DEFAULT_W: Weight = { stars: 3, forks: 1, open_issues: 1, updated: 2 };

const { values, positionals } = parseArgs({
  args: Bun.argv.slice(2),
  options: {
    top: { type: "string" },
    "per-page": { type: "string" },
    weights: { type: "string" },
    providers: { type: "string" },
    interactive: { type: "boolean" },
    help: { type: "boolean" },
  },
  allowPositionals: true,
});

if (values.help) {
  console.log(
    `Usage: bun run race-borrow.ts [patterns...] [--top N] [--per-page N] [--weights k=v,...] [--providers p1,p2,...] [--interactive]`,
  );
  process.exit(0);
}

const PATTERNS = positionals.length ? positionals : DEFAULT_PATTERNS;
const TOP = Number(values.top ?? PATTERNS.length);
const PER_PAGE = Number(values["per-page"] ?? 5);
const W: Weight = { ...DEFAULT_W };
const SELECTED_PROVIDERS = values.providers?.split(",").map((p) => p.trim()) ?? DEFAULT_PROVIDERS;

if (values.weights) {
  for (const kv of values.weights.split(",")) {
    const [k, v] = kv.split("=");
    if (k && v && k in DEFAULT_W) (W as any)[k] = Number(v);
  }
}

async function gh(path: string, params?: Record<string, string>): Promise<any> {
  let url = `${API}${path}`;
  if (params) url += `?${new URLSearchParams(params).toString()}`;
  for (let attempt = 0; attempt < 6; attempt++) {
    const res = await fetch(url, { headers: HEAD });
    if (res.status === 403 && res.headers.get("x-ratelimit-remaining") === "0") {
      await new Promise((r) => setTimeout(r, 60000));
      continue;
    }
    if (!res.ok) throw new Error(`GH API ${res.status}`);
    return res.json();
  }
  throw new Error("GH API exhausted");
}

async function repoStats(full: string): Promise<any> {
  const [owner, repo] = full.split("/");
  return gh(`/repos/${owner}/${repo}`);
}

async function raceProvider(pattern: string, provider: string, page: number): Promise<any> {
  const query = `${pattern} repo:sovereign-projects/ language:typescript language:ts language:rust language:go`;
  const data = await gh("/search/code", {
    q: query,
    per_page: String(PER_PAGE),
    page: String(page),
  });
  return { provider, pattern, data, time: Date.now() };
}

const rows: any[] = [];

// Race: fire all provider+pattern combos concurrently, first valid response wins per pattern
async function raceAll() {
  const promises: Promise<any>[] = [];
  for (const pattern of PATTERNS) {
    for (const provider of SELECTED_PROVIDERS) {
      promises.push(raceProvider(pattern, provider, 1));
    }
  }
  const results = await Promise.all(promises);
  // Group by pattern, pick fastest valid result
  const grouped: Record<string, any[]> = {};
  for (const r of results) {
    if (!grouped[r.pattern]) grouped[r.pattern] = [];
    grouped[r.pattern].push(r);
  }
  for (const [pattern, items] of Object.entries(grouped)) {
    items.sort((a, b) => a.time - b.time);
    rows.push({ pattern, winner: items[0], all: items });
  }
}

function norm(key: string) {
  return key.replace(/^renamed_from|type_of|language:/, "").trim();
}

function rank(weights: Weight) {
  const score = (repo: any) => {
    let s = 0;
    for (const f of FACTORS) {
      const v = repo[norm(f)] ?? 0;
      s += (weights[f] ?? DEFAULT_W[f as keyof Weight] ?? 0) * Math.log1p(v);
    }
    if (BUG_TERMS.some((t) => repo.description?.includes(t))) s -= 5;
    return s;
  };
  return rows.sort((a, b) => score(b.winner.data.items?.[0] ?? {}) - score(a.winner.data.items?.[0] ?? {}));
}

function printRank(weights: Weight) {
  const ranked = rank(weights);
  console.log(`\n=== Race-Borrow Results (${PATTERNS.length} patterns, ${SELECTED_PROVIDERS.length} providers) ===\n`);
  for (const r of ranked.slice(0, TOP)) {
    const item = r.winner.data.items?.[0];
    if (item) {
      console.log(`🏆 ${r.pattern} → ${item.full_name} (via ${r.winner.provider})`);
      console.log(`   Stars: ${item.stargazers_count} | Forks: ${item.forks_count} | Issues: ${item.open_issues_count}`);
    }
  }
  console.log(`\n--- Weights: ${JSON.stringify(W)} ---\n`);
}

async function main() {
  await raceAll();
  printRank(W);
  if (values.interactive) {
    console.log("Interactive mode: use --weights to adjust ranking factors");
  }
}

main().catch(console.error);
