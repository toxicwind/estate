/**
 * analyze.ts — evangelist-recon: classify the api-evangelist 34,531-repo org.
 * Turns the raw repo list into a categorized catalog: tooling layer vs the
 * mass of per-company API-surface dumps, plus probing-relevant repos.
 */
import { DataFrame } from "dataframe-js";
import { writeFileSync, mkdirSync } from "node:fs";

const ORG = "api-evangelist";
const DUMP_RE =
  /company profile|independent third-party profile of a public api/i;

async function fetchPage(
  page: number,
  per = 100,
): Promise<Record<string, unknown>[]> {
  const url = `https://api.github.com/users/${ORG}/repos?per_page=${per}&page=${page}&sort=pushed`;
  const res = await fetch(url, {
    headers: { Accept: "application/vnd.github+json" },
  });
  if (res.status === 403 || res.status === 429)
    throw new Error(`rate-limited page ${page}: ${res.status}`);
  const json = (await res.json()) as unknown[];
  return Array.isArray(json) ? (json as Record<string, unknown>[]) : [];
}

export async function collectRepos(
  limit: number,
): Promise<Record<string, unknown>[]> {
  const all: Record<string, unknown>[] = [];
  for (let page = 1; all.length < limit && page < 400; page++) {
    let rows: Record<string, unknown>[];
    try {
      rows = await fetchPage(page);
    } catch (e) {
      console.error(String(e));
      break;
    }
    if (rows.length === 0) break;
    for (const r of rows) {
      all.push({ ...r, desc: (r.description as string) ?? "" });
      if (all.length >= limit) break;
    }
  }
  return all;
}

export function classify(rows: Record<string, unknown>[]): DataFrame {
  return new DataFrame(
    rows.map((r) => {
      const desc = String(r.desc ?? "");
      const isDump = DUMP_RE.test(desc);
      return {
        name: r.name,
        desc: desc.slice(0, 100),
        created: String(r.created_at ?? "").slice(0, 10),
        pushed: String(r.pushed_at ?? "").slice(0, 10),
        stars: Number(r.stargazers_count ?? 0),
        isDump,
        isTooling: !isDump,
        probing: /probe|monitor|observ|endpoint|rate.?limit|health/i.test(
          `${r.name} ${desc}`,
        ),
      };
    }),
  );
}

export function themeCounts(df: DataFrame): Record<string, number> {
  const themes = [
    "probe|monitor|observ|health",
    "rate.?limit|thrott",
    "schema|openapi|swagger",
    "index|catalog|directory",
    "mcp|agent|post",
    "unified|gateway|proxy|router",
  ];
  const out: Record<string, number> = {};
  for (const t of themes) {
    const re = new RegExp(t, "i");
    out[t] = df
      .filter(
        (r) =>
          r.get("isTooling") && re.test(`${r.get("name")} ${r.get("desc")}`),
      )
      .count();
  }
  return out;
}

export async function main(limit = 600): Promise<void> {
  const rows = await collectRepos(limit);
  const df = classify(rows);
  const total = df.count();
  const dumps = df.filter((r) => r.get("isDump")).count();
  const tooling = df.filter((r) => r.get("isTooling")).count();
  const probing = df.filter((r) => r.get("probing")).count();
  const probeRelevantNames = df
    .filter((r) => r.get("isTooling") && r.get("probing"))
    .toCollection()
    .map((row: { get: (c: string) => unknown }) => String(row.get("name")))
    .slice(0, 30);
  const report = {
    analyzed: total,
    classification: { dumps, tooling },
    probingRelated: probing,
    toolingThemes: themeCounts(df),
    probeRelevantNames,
  };
  mkdirSync("out", { recursive: true });
  writeFileSync("out/findings.json", JSON.stringify(report, null, 2), "utf8");
  writeFileSync("out/catalog.csv", df.toCSV(true), "utf8");
  console.log(JSON.stringify(report, null, 2));
}

if (import.meta.main) await main(Number(process.argv[2] ?? 600));
