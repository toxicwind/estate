/**
 * pattern-borrow.ts — GitHub-wide pattern ranker / borrower (Bun mainline, estate).
 *
 * General-purpose: pass any shallow code keywords as positional args to find and
 * rank the strongest implementation patterns across the WHOLE of GitHub, then
 * borrow the top ones. Used for the pi-agent hot-reload fix (top 3: session
 * restore / durable session / hot reload) and for anything else (e.g. tiktoken).
 *
 *   F1  recency        newest repo push among top matches
 *   F2  complexity      matched-file size + modern-API token density
 *   F3  emergent        distinct repos using the pattern (prevalence)
 *   F4  stars           total stargazers across top repos
 *   F5  issues+PRs      total open issues/PRs across top repos
 *   F6  test coverage   fraction of top repos with a test dir
 *   F7  doc density     markdown mentions of the pattern in those repos
 *   F8  fork-applicable term overlap with our bug surface
 *   F9  bug-relevance   lexical closeness to reload/session/conversation
 *   F10 centrality      total forks (dependent/centrality proxy)
 *
 * CLI:
 *   bun run scripts/pattern-borrow.ts [patterns...] [--top N] [--per-page N]
 *                              [--weights k=v,...] [--interactive] [--help]
 *
 *   patterns...   override the default 8 search terms (positional)
 *   --top N       how many to print (default 8)
 *   --per-page N  GitHub results per pattern (default 5)
 *   --weights     comma list of factor=weight overrides (bugRel, stars, issues,
 *                 forks, nRepos, newest, avgSize, testFrac)
 *   --interactive re-rank live from stdin using cached fetches (type "w stars=0.3")
 *
 * Run: bun run scripts/pattern-borrow.ts "hot reload" "session restore" --top 3
 */
import { parseArgs } from "node:util";
import { existsSync, readFileSync } from "node:fs";

const { values, positionals } = parseArgs({
  args: Bun.argv.slice(2),
  options: {
    top: { type: "string" },
    perPage: { type: "string" },
    "per-page": { type: "string" },
    weights: { type: "string" },
    // 2026-10-15: JSON is now the DEFAULT output (agent-canonical, per the
    // ffs output doctrine: "text is for humans; json is canonical for tools").
    // Pass --text for the human rendering.
    text: { type: "boolean" },
    interactive: { type: "boolean" },
    help: { type: "boolean" },
  },
  allowPositionals: true,
  strict: false,
});

if (values.help) {
  console.log(
    `Usage: bun run pattern-borrow.ts [patterns...] [--top N] [--per-page N] [--weights k=v,...] [--text] [--interactive] (default output: JSON)`,
  );
  process.exit(0);
}

function resolveGitHubToken(): string {
  const envToken = Bun.env.GITHUB_TOKEN ?? Bun.env.GH_TOKEN;
  if (envToken?.trim()) return envToken.trim();

  const home = Bun.env.HOME ?? "/home/toxic";
  for (const envFile of [`${home}/.secrets`, `${home}/.bashrc.env`]) {
    if (existsSync(envFile)) {
      try {
        const content = readFileSync(envFile, "utf8");
        const hit = content.match(/^\s*(?:export\s+)?(?:GITHUB_TOKEN|GH_TOKEN)\s*=\s*["']?([^"'\n#]+)["']?/m);
        if (hit?.[1]?.trim()) return hit[1].trim();
      } catch {}
    }
  }

  const hostsPath = `${home}/.config/gh/hosts.yml`;
  if (existsSync(hostsPath)) {
    try {
      const content = readFileSync(hostsPath, "utf8");
      const match = content.match(/oauth_token:\s*([^\s]+)/);
      if (match && match[1]) return match[1].trim();
    } catch {}
  }

  try {
    const proc = Bun.spawnSync(["gh", "auth", "token"]);
    const tok = proc.stdout.toString().trim();
    if (tok && !tok.startsWith("HTTP") && !tok.includes("error")) return tok;
  } catch {}

  return "";
}

const TOKEN = resolveGitHubToken();
if (!TOKEN) {
  console.error("no GITHUB_TOKEN/GH_TOKEN found (checked env, ~/.secrets, ~/.bashrc.env, and gh auth token)");
  process.exit(1);
}

const API = "https://api.github.com";
const HEAD = {
  Authorization: `Bearer ${TOKEN}`,
  Accept: "application/vnd.github+json",
  "X-GitHub-Api-Version": "2022-11-28",
};

const DEFAULT_PATTERNS = [
  "hot reload",
  "session restore",
  "jsonl session",
  "conversation reload",
  "fs.watch",
  "process reload",
  "resume session",
  "durable session",
];
const BUG_TERMS = [
  "reload",
  "watch",
  "hot",
  "session",
  "conversation",
  "restore",
  "resume",
];
const FACTORS = [
  "newest",
  "avgSize",
  "nRepos",
  "stars",
  "issues",
  "forks",
  "testFrac",
  "bugRel",
] as const;
type Weight = Partial<Record<(typeof FACTORS)[number], number>>;
const DEFAULT_W: Weight = {
  newest: 0.1,
  avgSize: 0.1,
  nRepos: 0.12,
  stars: 0.14,
  issues: 0.12,
  forks: 0.08,
  testFrac: 0.06,
  bugRel: 0.28,
};

const STOPWORDS = new Set([
  "a", "an", "the", "and", "or", "for", "with", "via", "using", "how", "best",
  "in", "of", "to", "on", "at", "by", "from", "into", "code", "implement",
  "implementation", "pattern", "patterns", "example", "examples", "real",
  "world", "real-world", "github", "repo", "repos",
]);

/**
 * 2026-10-15 fix: multi-word positionals used to be searched on GitHub as ONE
 * quoted phrase (code search returns near-garbage for long phrases). Now
 * natural-language queries are split into focused code-search terms with
 * stopwords stripped, deduped, and capped.
 */
function toSearchTerms(positional: string[]): string[] {
  const out: string[] = [];
  for (const p of positional) {
    if (p.includes("-") && p.length <= 40 && !p.includes(" ")) {
      // looks like a code identifier (kebab/snake) — search as-is
      out.push(p);
      continue;
    }
    const words = p.split(/\s+/).filter((w) => w.length > 1 && !STOPWORDS.has(w.toLowerCase()));
    if (words.length <= 2) {
      out.push(words.join(" ") || p);
    } else {
      // focused bigrams keep code-search precision without the phrase trap
      out.push(words.slice(0, 4).join(" "));
    }
  }
  return [...new Set(out.filter(Boolean))].slice(0, 6);
}

const PATTERNS = positionals.length ? toSearchTerms(positionals) : DEFAULT_PATTERNS;
const TOP = Number(values.top ?? (positionals.length ? positionals.length : 5));
const PER_PAGE = Number(values.perPage ?? values["per-page"] ?? 5);
const W: Weight = { ...DEFAULT_W };
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
    if (
      res.status === 403 &&
      res.headers.get("x-ratelimit-remaining") === "0"
    ) {
      const reset = Number(res.headers.get("x-ratelimit-reset") ?? "0");
      const wait = Math.max(1, reset - Math.floor(Date.now() / 1000));
      console.error(`  rate limit; sleeping ${wait}s`);
      await Bun.sleep(wait * 1000 + 500);
      continue;
    }
    if (!res.ok) {
      console.error(`  ! ${res.status} ${url}`);
      return null;
    }
    return await res.json();
  }
  return null;
}

async function scanLocalCode(term: string, limit = 5): Promise<Array<{ file: string; line: string }>> {
  try {
    const estateRoot = Bun.env.ESTATE ?? "/home/toxic/estate";
    const proc = Bun.spawn(["ffs", "grep", term, "--root", estateRoot, "--limit", String(limit)], {
      stdout: "pipe",
      stderr: "pipe",
    });
    const out = await new Response(proc.stdout).text();
    const hits: Array<{ file: string; line: string }> = [];
    for (const raw of out.split("\n")) {
      const line = raw.trim();
      if (!line || line.startsWith("#") || line.startsWith("[")) continue;
      const parts = line.split(":");
      if (parts.length >= 2) {
        hits.push({ file: parts[0], line: parts.slice(1).join(":") });
      }
    }
    return hits;
  } catch {
    return [];
  }
}

async function repoStats(full: string): Promise<any> {
  const r = await gh(`/repos/${full}`);
  if (!r) return { stars: 0, issues: 0, forks: 0, pushed: 0, hasTest: 0, description: "", language: "", license: "", url: `https://github.com/${full}` };
  let hasTest = 0;
  const root = await gh(`/repos/${full}/contents/`);
  if (root && Array.isArray(root)) {
    const names = root.map((x: any) => x.name?.toLowerCase());
    hasTest = names.some((n: string) =>
      ["tests", "test", "__tests__", "spec", "crates", "packages"].includes(n),
    )
      ? 1
      : 0;
  }
  return {
    stars: r.stargazers_count ?? 0,
    issues: r.open_issues_count ?? 0,
    forks: r.forks_count ?? 0,
    pushed: r.pushed_at ? Date.parse(r.pushed_at) / 1000 : 0,
    hasTest,
    description: r.description ?? "",
    language: r.language ?? "",
    license: r.license?.spdx_id ?? r.license?.name ?? "",
    url: r.html_url ?? `https://github.com/${full}`,
  };
}

const rows: any[] = [];
for (const term of PATTERNS) {
  const [data, localHits] = await Promise.all([
    gh("/search/code", { q: term, per_page: String(PER_PAGE) }),
    scanLocalCode(term, PER_PAGE),
  ]);
  const repos: Record<string, any> = {};

  if (localHits.length) {
    for (const h of localHits) {
      const rel = h.file.replace("/home/toxic/estate/", "");
      repos[`local:${rel}`] = {
        stars: 9999, // First-class in-tree priority
        issues: 0,
        forks: 1,
        pushed: Math.floor(Date.now() / 1000),
        hasTest: 1,
        description: `In-tree pattern: ${h.line.trim().slice(0, 100)}`,
        language: rel.split(".").pop() ?? "ts",
        license: "estate",
        url: `file://${h.file}`,
      };
    }
  }
  const matchedFiles: Record<string, string[]> = {};
  const sizes: number[] = [];
  if (data?.items) {
    for (const it of data.items) {
      const full = it.repository?.full_name;
      // self-echo: skip our own public repos — the local-first scan above
      // already covers in-tree truth; GitHub copies add nothing but noise
      if (full && full.startsWith("toxicwind/")) continue;
      if (full) {
        if (!matchedFiles[full]) matchedFiles[full] = [];
        if (it.path) matchedFiles[full].push(it.path);
        if (!repos[full]) repos[full] = await repoStats(full);
      }
      if (typeof it.size === "number") sizes.push(it.size);
    }
  }
  const vals = Object.values(repos);
  const nRepos = vals.length;
  const totalStars = vals.reduce((a: number, v: any) => a + v.stars, 0);
  const totalIssues = vals.reduce((a: number, v: any) => a + v.issues, 0);
  const totalForks = vals.reduce((a: number, v: any) => a + v.forks, 0);
  const pushed = vals.map((v: any) => v.pushed).filter((x: number) => x > 0);
  const newest = pushed.length ? Math.max(...pushed) : 0;
  const testFrac = nRepos
    ? vals.reduce((a: number, v: any) => a + v.hasTest, 0) / nRepos
    : 0;
  const avgSize = sizes.length
    ? sizes.reduce((a: number, b: number) => a + b, 0) / sizes.length
    : 0;
  const bugRel = BUG_TERMS.reduce(
    (a: number, t: string) =>
      a + (term.toLowerCase().match(new RegExp(t, "g"))?.length ?? 0),
    0,
  );
  const repoList = Object.entries(repos).map(([fullName, st]) => ({
    fullName,
    ...st,
    matchedFiles: matchedFiles[fullName] ?? [],
  }));
  rows.push({
    term,
    nRepos,
    stars: totalStars,
    issues: totalIssues,
    forks: totalForks,
    newest,
    testFrac,
    avgSize,
    bugRel,
    repos: repoList,
  });
  console.log(`  scanned '${term}': ${nRepos} repos, ${totalStars} stars`);
  await Bun.sleep(1200);
}

function norm(key: string) {
  const vals = rows.map((r) => r[key]);
  if (rows.length <= 1) {
    for (const r of rows) r[`n_${key}`] = 1.0;
    return;
  }
  const mx = Math.max(...vals) || 1;
  const mn = Math.min(...vals);
  const rng = mx - mn || 1;
  for (const r of rows) r[`n_${key}`] = (r[key] - mn) / rng;
}

function rank(weights: Weight) {
  for (const k of FACTORS) norm(k);
  const wsum = FACTORS.reduce((a, k) => a + (weights[k] ?? 0), 0) || 1;
  for (const r of rows)
    r.score =
      FACTORS.reduce((a, k) => a + (r[`n_${k}`] ?? 0) * (weights[k] ?? 0), 0) /
      wsum;
  rows.sort((a: any, b: any) => b.score - a.score);
}

function printRank(weights: Weight) {
  rank(weights);
  const topRepos = collectTopRepos(TOP);
  if (!values.text) {
    console.log(JSON.stringify({ terms: rows.map((r) => r.term), topRepos }, null, 2));
    return;
  }
  // Output contract (2026-10-15): agent-shaped, not human-shaped.
  // No ANSI, repos first (the actionable unit), evidence + fetch-ready URLs.
  const termStr = rows.map((r) => r.term).join(" | ");
  console.log(`# pattern-borrow — terms: ${termStr}`);
  console.log(`# scored across ${rows.length} terms; factors: ${FACTORS.join(",")}`);
  console.log("");
  for (let i = 0; i < topRepos.length; i++) {
    const repo = topRepos[i];
    const isLocal = repo.fullName.startsWith("local:");
    console.log(`[${i + 1}] ${repo.fullName}  ★${repo.stars}  ${repo.language || "?"}  ${repo.license || "?"}`);
    if (repo.description) console.log(`    why: ${repo.description.slice(0, 140)}`);
    if (repo.terms?.length) console.log(`    matched terms: ${repo.terms.join(", ")}`);
    if (isLocal) {
      console.log(`    in-tree first-class: ${repo.url.replace("file://", "")}`);
    } else {
      console.log(`    repo: ${repo.url}`);
      const rawFiles = (repo.matchedFiles || []).slice(0, 3);
      if (rawFiles.length) {
        console.log(`    matching files:`);
        for (const f of rawFiles) {
          console.log(`      - https://raw.githubusercontent.com/${repo.fullName}/HEAD/${f}`);
        }
      }
    }
  }
  if (!topRepos.length) {
    console.log("no matches — refine terms (stopwords stripped; use code identifiers)");
  }
}

function collectTopRepos(limit: number) {
  const repoMap = new Map<string, any>();
  for (const r of rows.slice(0, TOP)) {
    for (const repo of r.repos || []) {
      const existing = repoMap.get(repo.fullName);
      if (!existing) {
        repoMap.set(repo.fullName, { ...repo, terms: [r.term] });
      } else {
        if (!existing.terms.includes(r.term)) existing.terms.push(r.term);
        for (const f of repo.matchedFiles) {
          if (!existing.matchedFiles.includes(f)) existing.matchedFiles.push(f);
        }
      }
    }
  }
  return Array.from(repoMap.values())
    .sort((a, b) => b.stars - a.stars)
    .slice(0, limit);
}

printRank(W);

if (values.interactive) {
  console.log(
    "\ninteractive: type 'w factor=weight' (e.g. 'w bugRel=0.4'), 'p' to reprint, 'q' quit",
  );
  const buf = (await import("node:tty")).stdin;
  buf?.on?.("data", (d: Buffer) => {
    const line = d.toString().trim();
    if (line === "q") process.exit(0);
    if (line === "p") return printRank(W);
    const m = line.match(/^w\s+(\w+)=([\d.]+)$/);
    if (m && (m[1] as any) in DEFAULT_W) {
      (W as any)[m[1]] = Number(m[2]);
      printRank(W);
    }
  });
}
