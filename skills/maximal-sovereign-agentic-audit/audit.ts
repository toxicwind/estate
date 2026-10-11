#!/usr/bin/env bun
/**
 * maximal-sovereign-agentic-audit — Maximal agentic audit tool.
 *
 * Features:
 *   - Multi-tier (High/Medium/Low) chained execution pipeline
 *   - AST-aware code search via ast-grep
 *   - Pattern borrowing from global sovereign patterns
 *   - Dual code search: exa (file tree) + gh (API code)
 *   - Bun.nanoseconds() microsecond-precision timing
 *   - Streaming with configurable batch/window
 *   - Agentic completion prompt generation
 *   - mitata benchmark integration
import { run, bench, group } from "mitata";
 *
 * Usage:
 *   bun run src/index.ts --user toxicwind --check-bun --output-parquet out/audit.parquet
 *   bun run src/index.ts --help
 */

import { execFile } from "child_process";
import { mkdir, writeFile, readFile, rm } from "fs/promises";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { Table } from "apache-arrow";
import { ParquetWriter, ParquetSchema } from "parquetjs-lite";

// ============================================================================
// Types
// ============================================================================

interface RepoRecord {
  name: string;
  private: boolean;
  visibility: string;
  fork: boolean;
  stargazers_count: number;
  language: string;
  description: string;
  classification: string;
  tier: Tier;
  bun_version: string;
  updated_at: string;
  ast_patterns: string[];
  exa_files: string[];
  gh_code_matches: string[];
}

interface TimingMetric {
  phase: string;
  start_ns: bigint;
  end_ns: bigint;
  elapsed_us: number;
}

interface TierConfig {
  name: Tier;
  priority: number;
  patterns: string[];
  ast_rules: string[];
  description: string;
}

interface PipelineStage {
  name: string;
  order: number;
  execute: (input: unknown) => Promise<unknown>;
  depends_on: string[];
}

interface AuditResult {
  repos: RepoRecord[];
  timing: TimingMetric[];
  anomalies: RepoRecord[];
  summary: AuditSummary;
  benchmarks: Record<string, number>;
}

interface AuditSummary {
  total: number;
  public: number;
  private: number;
  forks: number;
  ecosystem: number;
  internal: number;
  bun_enabled: number;
  ast_matches: number;
  exa_searches: number;
  gh_searches: number;
}

type Tier = "High" | "Medium" | "Low";

// ============================================================================
// Tier Definitions (Multi-Tier)
// ============================================================================

const TIERS: TierConfig[] = [
  {
    name: "High",
    priority: 3,
    patterns: ["sovereign", "tau", "mesh", "pi", "llama", "agent", "pitchfork", "qed"],
    ast_rules: ["typescript:console.log", "typescript:debugger", "typescript:any-type"],
    description: "Core ecosystem repos — highest audit priority",
  },
  {
    name: "Medium",
    priority: 2,
    patterns: ["config", "deploy", "script", "helper", "tool", "workflow"],
    ast_rules: ["typescript:TODO", "typescript:FIXME", "typescript:console.error"],
    description: "Infrastructure and tooling repos — medium priority",
  },
  {
    name: "Low",
    priority: 1,
    patterns: ["test", "benchmark", "example", "draft", "archive", "backup"],
    ast_rules: ["typescript:console.warn", "typescript:eslint-disable"],
    description: "Experimental and auxiliary repos — lowest priority",
  },
];

// ============================================================================
// Pattern Borrowing (from sovereign global patterns)
// ============================================================================

const GLOBAL_PATTERNS = [
  { term: "secret", weight: 10, category: "internal" as const },
  { term: "token", weight: 10, category: "internal" as const },
  { term: "credential", weight: 10, category: "internal" as const },
  { term: "config", weight: 5, category: "internal" as const },
  { term: "private", weight: 8, category: "internal" as const },
  { term: "sovereign", weight: 9, category: "ecosystem" as const },
  { term: "tau", weight: 9, category: "ecosystem" as const },
  { term: "mesh", weight: 9, category: "ecosystem" as const },
  { term: "herd", weight: 8, category: "ecosystem" as const },
  { term: "pi", weight: 9, category: "ecosystem" as const },
  { term: "llama", weight: 8, category: "ecosystem" as const },
  { term: "agent", weight: 8, category: "ecosystem" as const },
  { term: "pitchfork", weight: 8, category: "ecosystem" as const },
  { term: "qed", weight: 7, category: "ecosystem" as const },
  { term: "deploy", weight: 6, category: "infra" as const },
  { term: "ci", weight: 5, category: "infra" as const },
  { term: "workflow", weight: 5, category: "infra" as const },
  { term: "benchmark", weight: 4, category: "dev" as const },
  { term: "test", weight: 3, category: "dev" as const },
];

function loadGlobalPatterns(): typeof GLOBAL_PATTERNS {
  return GLOBAL_PATTERNS;
}

function classifyByPattern(name: string): { category: string; weight: number; matched: boolean } {
  const lower = name.toLowerCase();
  let best = { category: "general", weight: 0, matched: false };
  for (const p of loadGlobalPatterns()) {
    if (lower.includes(p.term) && p.weight > best.weight) {
      best = { category: p.category, weight: p.weight, matched: true };
    }
  }
  return best;
}

// ============================================================================
// CLI Args
// ============================================================================

const args = process.argv.slice(2);
function getArg(name: string, fallback: string): string {
  const idx = args.indexOf(`--${name}`);
  if (idx !== -1 && idx + 1 < args.length) return args[idx + 1];
  return fallback;
}
function hasFlag(name: string): boolean {
  return args.includes(`--${name}`);
}

const USER = getArg("user", "toxicwind");
const OUTPUT_PARQUET = getArg("output-parquet", join(dirname(fileURLToPath(import.meta.url)), "..", "repo-audit.parquet"));
const EXPORT_CSV = getArg("export-csv", join(dirname(fileURLToPath(import.meta.url)), "..", "repo-audit.csv"));
const CHECK_BUN = hasFlag("check-bun");
const PRIVACY_THRESHOLD = parseInt(getArg("privacy-threshold", "0"));
const OUTPUT_DIR = getArg("out-dir", join(dirname(fileURLToPath(import.meta.url)), "..", "output"));
const VERBOSE = hasFlag("verbose") || hasFlag("v");
const STREAM_ENABLED = hasFlag("stream");
const STREAM_BATCH_SIZE = parseInt(getArg("stream-batch-size", "50"));
const STREAM_WINDOW_MS = parseInt(getArg("stream-window-ms", "5000"));
const TIMING_ENABLED = hasFlag("timing") || hasFlag("latency");
const AGENTIC_ENABLED = hasFlag("agentic");
const COMPLETION_PROMPT = hasFlag("completion-prompt");
const JSON_OUTPUT = hasFlag("json-output");
const STREAM_COMPLETIONS = hasFlag("stream-completions");
const AST_SEARCH = hasFlag("ast-search") || hasFlag("ast");
const EXA_SEARCH = hasFlag("exa-search") || hasFlag("exa");
const GH_SEARCH = hasFlag("gh-search") || hasFlag("gh");
const BENCHMARK = hasFlag("bench");
const CHAIN = hasFlag("chain");
const PATTERN_BORROW = hasFlag("pattern-borrow") || hasFlag("borrow");
const TIER = getArg("tier", "all");
const REPOS = getArg("repos", "").split(",").filter(Boolean);
const USERS = getArg("users", "").split(",").filter(Boolean);

if (args.includes("--help") || args.includes("-h")) {
  console.log(`
maximal-sovereign-agentic-audit — Maximal agentic repo visibility & bun auditor

USAGE
  bun run src/index.ts [options]

TIERS
  --tier <High|Medium|Low|all>  Filter by priority tier (default: all)

SEARCH
  --ast-search, --ast            Enable AST-aware code search via ast-grep
  --exa-search, --exa            Enable exa file-tree code search
  --gh-search, --gh              Enable gh API code search
  --pattern-borrow, --borrow     Borrow patterns from global sovereign patterns
  --chain                        Enable chained pipeline execution

FEATURES
  --user <username>              GitHub user/org (default: toxicwind)
  --users <u1>,<u2>              Multiple GitHub users (comma-separated)
  --repos <o/r>,<o/r>            Specific repos to audit (owner/repo format)
  --output-parquet <path>        Output parquet file path
  --export-csv <path>            Export CSV alongside parquet
  --check-bun                    Scan repos for bun version references
  --privacy-threshold <n>        Min stars to flag public repos as anomalous
  --out-dir <dir>                Output directory (default: ./output)
  --verbose, -v                  Show detailed per-repo output
  --stream                       Enable batch streaming
  --stream-batch-size <n>        Records per batch (default: 50)
  --stream-window-ms <n>         Throughput window in ms (default: 5000)
  --timing, --latency            Enable timing and latency tracking
  --agentic                      Agentic mode with dynamic prompts
  --completion-prompt            Generate agentic completion prompts
  --json-output                  Output structured JSON
  --stream-completions           Stream completions to stdout
  --bench                        Run mitata benchmarks inline

EXAMPLES
  bun run src/index.ts --user toxicwind --check-bun --output-parquet audit.parquet
  bun run src/index.ts --users toxicwind,sovereign --check-bun --stream
  bun run src/index.ts --repos toxicwind/pi,toxicwind/tau --ast-search --gh-search
  bun run src/index.ts --users toxicwind,sovereign --check-bun --stream
  bun run src/index.ts --repos toxicwind/pi,toxicwind/tau --ast-search --gh-search
  bun run src/index.ts --user toxicwind --chain --pattern-borrow --bench --timing
  bun run src/index.ts --help

ARCHITECTURE
  • Multi-tier execution: High > Medium > Low priority chains
  • AST-aware search: ast-grep for structural code patterns
  • Pattern borrowing: Global sovereign pattern ranker
  • Dual search: exa (local file tree) + gh (GitHub API code)
  • Bun.nanoseconds(): Microsecond-precision timing
  • mitata: Structured benchmark runner
  • Streaming: Configurable batch/window pipeline
  • Agentic: Dynamic completion prompt generation
`);
  process.exit(0);
}

// ============================================================================
// Bun.nanoseconds() Timing (Microsecond Precision)
// ============================================================================

function nowNs(): bigint {
  return Bun.nanoseconds();
}

function elapsedUs(start: bigint): number {
  return Number(nowNs() - start) / 1000;
}

function elapsedMs(start: bigint): number {
  return elapsedUs(start) / 1000;
}

function timing(phase: string, startNs: bigint): TimingMetric {
  return {
    phase,
    start_ns: startNs,
    end_ns: nowNs(),
    elapsed_us: elapsedUs(startNs),
  };
}

// ============================================================================
// Helpers: execFile wrapper
// ============================================================================

function runGh(cmd: string[], timeout = 30000): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile("gh", cmd, { timeout, maxBuffer: 50 * 1024 * 1024, env: { ...process.env, GH_TOKEN: Bun.env.GITHUB_TOKEN || Bun.env.GH_TOKEN } }, (error, stdout, stderr) => {
      if (error) reject(new Error(`gh ${cmd.join(" ")}: ${stderr || error.message}`));
      else resolve(stdout.trim());
    });
  });
}

function runExa(args: string[], timeout = 15000): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile("eza", ["--tree", "--long", "--no-ignore", "--icons=never", "--group-directories-first", "--git", "--modified", "--permissions", "--links", "--classify", "--header", "--sort=modified", "--reverse", ...args], { timeout, maxBuffer: 50 * 1024 * 1024 }, (error, stdout, stderr) => {
      if (error) reject(new Error(`eza ${args.join(" ")}: ${stderr || error.message}`));
      else resolve(stdout.trim());
    });
  });
}

function runAstGrep(pattern: string, lang: string, path: string, timeout = 30000): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile("ast-grep", ["scan", "--pattern", pattern, "--lang", lang, "--json=stream", "--no-ignore", path], { timeout, maxBuffer: 50 * 1024 * 1024 }, (error, stdout, stderr) => {
      if (error) reject(new Error(`ast-grep scan --pattern ${pattern} --lang ${lang}: ${stderr || error.message}`));
      else resolve(stdout.trim());
    });
  });
}

// ============================================================================
// Fetch repos via gh API (paginated)
// ============================================================================

async function fetchReposForUser(username: string): Promise<Record<string, unknown>[]> {
  const start = nowNs();
  const allRepos: Record<string, unknown>[] = [];
  let page = 1;
  let fetched = 0;

  while (true) {
    const data = JSON.parse(await runGh([
      "api", `users/${username}/repos`,
      "--per-page", "100",
      "--page", String(page),
      "--jq", "[.[] | {name, private, fork, stargazers_count, language, description, updated_at}]"
    ]));
    if (!Array.isArray(data) || data.length === 0) break;
    allRepos.push(...data);
    fetched += data.length;
    if (data.length < 100) break;
    page++;
  }

  if (TIMING_ENABLED) {
    console.log(`[TIMING] Fetch ${username}: ${elapsedMs(start).toFixed(2)}ms for ${fetched} repos`);
  }
  return allRepos;
}

async function fetchReposForRepo(repoSpec: string): Promise<Record<string, unknown>[]> {
  const start = nowNs();
  const parts = repoSpec.split("/");
  if (parts.length !== 2) return [];
  const [owner, repo] = parts;
  const data = JSON.parse(await runGh([
    "api", "repos", owner, repo,
    "--jq", "{name, private, fork, stargazers_count, language, description, updated_at}"
  ]));
  if (TIMING_ENABLED) {
    console.log(`[TIMING] Fetch repo ${repoSpec}: ${elapsedMs(start).toFixed(2)}ms`);
  }
  return [data];
}

// ============================================================================
// Check bun version via GitHub API
// ============================================================================

async function checkBunVersion(owner: string, repo: string): Promise<string> {
  const start = nowNs();
  const candidates = [
    ["api", "repos", owner, repo, "contents", "package.json"],
    ["api", "repos", owner, repo, "contents", "bunfig.toml"],
    ["api", "repos", owner, repo, "contents", ".tool-versions"],
  ];
  for (const cmd of candidates) {
    try {
      const raw = await runGh(cmd);
      const data = JSON.parse(raw);
      if (data.content) {
        const decoded = Buffer.from(data.content, "base64").toString("utf-8");
        const versionMatch = decoded.match(/bun[\s"-v]?v?(\d+\.\d+\.\d+)/i)
          || decoded.match(/bun\s*=\s*"([^"]+)"/i)
          || decoded.match(/"bun":\s*"([^"]+)"/i);
        if (versionMatch) return versionMatch[1];
      }
    } catch { continue; }
  }
  return "";
}

// ============================================================================
// Classification with Tier Assignment
// ============================================================================

function classifyRepo(name: string, fork: boolean): { classification: string; tier: Tier } {
  const lower = name.toLowerCase();

  // Check internal patterns first
  for (const p of loadGlobalPatterns()) {
    if (p.category === "internal" && lower.includes(p.term)) {
      return { classification: "PRIVATE_INTERNAL", tier: "High" };
    }
  }

  // Check ecosystem patterns
  const ecosystemTerms = ["sovereign", "tau", "mesh", "herd", "pi", "llama", "agent", "pitchfork", "qed"];
  if (ecosystemTerms.some(kw => lower.includes(kw))) {
    return { classification: fork ? "PUBLIC_FORK" : "PUBLIC_ECOSYSTEM", tier: "High" };
  }

  // Check infra patterns
  const infraTerms = ["config", "deploy", "ci", "workflow", "script", "helper"];
  if (infraTerms.some(kw => lower.includes(kw))) {
    return { classification: fork ? "PUBLIC_FORK" : "PUBLIC_OPENSOURCE", tier: "Medium" };
  }

  // Check dev patterns
  const devTerms = ["test", "benchmark", "example", "draft", "archive", "backup"];
  if (devTerms.some(kw => lower.includes(kw))) {
    return { classification: "PUBLIC_OPENSOURCE", tier: "Low" };
  }

  // Default based on fork status
  return { classification: fork ? "PUBLIC_FORK" : "REVIEW_PRIVATE", tier: "Low" };
}

// ============================================================================
// AST-Aware Code Search
// ============================================================================

async function astSearch(repoName: string, rules: string[]): Promise<string[]> {
  if (!AST_SEARCH) return [];
  const matches: string[] = [];
  for (const rule of rules) {
    try {
      const result = await runAstGrep(rule, "typescript", `~/${repoName}`, 10000);
      if (result) matches.push(`${rule}: ${result.split("\n").length} matches`);
    } catch {
      if (VERBOSE) console.log(`[AST] No matches for ${rule} in ${repoName}`);
    }
  }
  return matches;
}

// ============================================================================
// Exa File-Tree Search
// ============================================================================

async function exaSearch(repoName: string): Promise<string[]> {
  if (!EXA_SEARCH) return [];
  try {
    const result = await runExa([
      "--tree", "--long", "--no-ignore",
      `--filter=*.ts`, `--filter=*.tsx`, `--filter=*.json`, `--filter=*.toml`,
      `/home/toxic/projects/${repoName}`
    ], 10000);
    return result.split("\n").filter(Boolean);
  } catch {
    return [];
  }
}

// ============================================================================
// GH API Code Search
// ============================================================================

async function ghCodeSearch(repoName: string): Promise<string[]> {
  if (!GH_SEARCH) return [];
  try {
    const result = JSON.parse(await runGh([
      "api", "search/code",
      "--limit", "5",
      "--jq", "[.items[:5].html_url]",
      "-q", `${repoName} repo:${USER}/${repoName} language:typescript`
    ], 15000));
    return Array.isArray(result) ? result : [];
  } catch {
    return [];
  }
}

// ============================================================================
// Pipeline Stages (Chained Execution)
// ============================================================================

async function chainedPipeline(repos: RepoRecord[]): Promise<RepoRecord[]> {
  if (!CHAIN) return repos;

  const stages: PipelineStage[] = [
    {
      name: "classify",
      order: 1,
      depends_on: [],
      execute: async (input: unknown) => {
        const records = input as RepoRecord[];
        for (const r of records) {
          const cls = classifyRepo(r.name, r.fork);
          r.classification = cls.classification;
          r.tier = cls.tier;
        }
        return records.filter(r => TIER === "all" || r.tier === TIER);
      },
    },
    {
      name: "pattern-borrow",
      order: 2,
      depends_on: ["classify"],
      execute: async (input: unknown) => {
        const records = input as RepoRecord[];
        if (!PATTERN_BORROW) return records;
        for (const r of records) {
          const pattern = classifyByPattern(r.name);
          if (pattern.matched && VERBOSE) {
            console.log(`[PATTERN-BORROW] ${r.name}: category=${pattern.category}, weight=${pattern.weight}`);
          }
        }
        return records;
      },
    },
    {
      name: "ast-search",
      order: 3,
      depends_on: ["pattern-borrow"],
      execute: async (input: unknown) => {
        const records = input as RepoRecord[];
        if (!AST_SEARCH) return records;
        const tierRules: Record<Tier, string[]> = {
          High: TIERS[0].ast_rules,
          Medium: TIERS[1].ast_rules,
          Low: TIERS[2].ast_rules,
        };
        const tierRepos = TIER === "all" ? records : records.filter(r => r.tier === TIER);
        for (const r of tierRepos) {
          const rules = tierRules[r.tier] || TIERS[0].ast_rules;
          r.ast_patterns = await astSearch(r.name, rules);
        }
        return records;
      },
    },
    {
      name: "exa-search",
      order: 4,
      depends_on: ["ast-search"],
      execute: async (input: unknown) => {
        const records = input as RepoRecord[];
        if (!EXA_SEARCH) return records;
        for (const r of records) {
          r.exa_files = await exaSearch(r.name);
        }
        return records;
      },
    },
    {
      name: "gh-search",
      order: 5,
      depends_on: ["exa-search"],
      execute: async (input: unknown) => {
        const records = input as RepoRecord[];
        if (!GH_SEARCH) return records;
        for (const r of records) {
          r.gh_code_matches = await ghCodeSearch(r.name);
        }
        return records;
      },
    },
  ];

  // Sort by order, execute sequentially respecting dependencies
  stages.sort((a, b) => a.order - b.order);
  let currentInput: unknown = repos;
  for (const stage of stages) {
    const depsDone = stage.depends_on.every(d =>
      stages.filter(s => s.name === d).every(s => s.order < stage.order)
    );
    if (!depsDone && VERBOSE) {
      console.log(`[CHAIN] Skipping ${stage.name}: dependencies not satisfied`);
      continue;
    }
    if (VERBOSE) console.log(`[CHAIN] Stage ${stage.name} (${stage.order})`);
    currentInput = await stage.execute(currentInput);
  }

  return currentInput as RepoRecord[];
}

// ============================================================================
// Build RepoRecord from gh API data
// ============================================================================

async function buildRecords(rawRepos: Record<string, unknown>[]): Promise<RepoRecord[]> {
  const start = nowNs();
  const records: RepoRecord[] = [];

  for (const repo of rawRepos) {
    const name = repo.name as string;
    const fork = repo.fork as boolean;
    const { classification, tier } = classifyRepo(name, fork);

    let bun_version = "";
    if (CHECK_BUN) {
      bun_version = await checkBunVersion(USER, name);
    }

    const record: RepoRecord = {
      name,
      private: repo.private as boolean,
      visibility: repo.private ? "private" : "public",
      fork,
      stargazers_count: repo.stargazers_count as number,
      language: (repo.language as string) || "",
      description: (repo.description as string) || "",
      classification,
      tier,
      bun_version,
      updated_at: repo.updated_at as string || "",
      ast_patterns: [],
      exa_files: [],
      gh_code_matches: [],
    };
    records.push(record);
  }

  if (TIMING_ENABLED) {
    console.log(`[TIMING] BuildRecords: ${elapsedMs(start).toFixed(2)}ms for ${records.length} repos`);
  }
  return records;
}

// ============================================================================
// Build Arrow Table
// ============================================================================

function buildArrowTable(records: RepoRecord[]): Table {
  return new Table({
    name: records.map(r => r.name),
    private: records.map(r => r.private),
    classification: records.map(r => r.classification),
    tier: records.map(r => r.tier),
    fork: records.map(r => r.fork),
    stargazers_count: records.map(r => r.stargazers_count),
    language: records.map(r => r.language),
    bun_version: records.map(r => r.bun_version),
    stargazers: records.map(r => r.stargazers_count),
    description: records.map(r => r.description),
  });
}

// ============================================================================
// Write Parquet
// ============================================================================

async function writeParquet(records: RepoRecord[], parquetPath: string): Promise<void> {
  const start = nowNs();
  await mkdir(join(parquetPath, ".."), { recursive: true });
  const table = buildArrowTable(records);
  const schema = new ParquetSchema({
    name: { type: "UTF8" },
    private: { type: "BOOLEAN" },
    classification: { type: "UTF8" },
    tier: { type: "UTF8" },
    fork: { type: "BOOLEAN" },
    stargazers_count: { type: "INT64" },
    language: { type: "UTF8" },
    bun_version: { type: "UTF8" },
    stargazers: { type: "INT64" },
    description: { type: "UTF8" },
  });
  const writer = await ParquetWriter.writeFile(schema, table.toArray(), parquetPath);
  await writer.close();
  if (TIMING_ENABLED) {
    console.log(`[TIMING] Parquet write: ${elapsedMs(start).toFixed(2)}ms`);
  }
}

// ============================================================================
// Export CSV
// ============================================================================

async function exportCSV(records: RepoRecord[], csvPath: string): Promise<void> {
  const headers = ["name", "private", "classification", "tier", "fork", "stargazers_count", "language", "bun_version", "description"];
  const rows = records.map(r => headers.map(h => String((r as Record<string, unknown>)[h] ?? "")).join(","));
  await writeFile(csvPath, headers.join(",") + "\n" + rows.join("\n"));
}

// ============================================================================
// Streaming Batch Processor
// ============================================================================

async function* streamBatches(records: RepoRecord[]): AsyncGenerator<{ records: RepoRecord[]; batch_size: number; latency_us: number }> {
  for (let i = 0; i < records.length; i += STREAM_BATCH_SIZE) {
    const start = nowNs();
    const batch = records.slice(i, i + STREAM_BATCH_SIZE);
    const latencyUs = elapsedUs(start);
    yield { records: batch, batch_size: batch.length, latency_us: latencyUs };
  }
}

// ============================================================================
// Agentic Completion Prompt Generator
// ============================================================================

function generateCompletionPrompts(records: RepoRecord[]): string[] {
  const prompts: string[] = [];
  const priority = TIER === "all" ? records : records.filter(r => r.tier === TIER);
  for (const r of priority) {
    if (r.classification === "PRIVATE_INTERNAL" || r.classification === "REVIEW_PRIVATE") {
      prompts.push(`Audit ${r.name}: classified as ${r.classification} (${r.tier} tier). Review privacy settings.`);
    }
    if (r.bun_version && !r.bun_version.startsWith("bun")) {
      prompts.push(`Update ${r.name}: bun version ${r.bun_version} may need upgrade.`);
    }
    if (r.ast_patterns.length > 0) {
      prompts.push(`Review ${r.name}: ${r.ast_patterns.length} AST pattern matches found.`);
    }
    if (r.exa_files.length > 0) {
      prompts.push(`Review ${r.name}: ${r.exa_files.length} files discovered via exa.`);
    }
    if (r.gh_code_matches.length > 0) {
      prompts.push(`Review ${r.name}: ${r.gh_code_matches.length} code matches via gh API.`);
    }
  }
  return prompts;
}

// ============================================================================
// Streaming Completions
// ============================================================================

async function streamCompletions(records: RepoRecord[]): Promise<void> {
  const prompts = generateCompletionPrompts(records);
  for (const prompt of prompts) {
    console.log(`[COMPLETION] ${prompt}`);
    await new Promise(r => setTimeout(r, STREAM_WINDOW_MS / prompts.length));
  }
}

// ============================================================================
// Mitata Benchmarks (inline)
// ============================================================================

async function runBenchmarks(): Promise<Record<string, number>> {
  if (!BENCHMARK) return {};
  // mitata imported statically above

  group("Repo Classification (Bun.nanoseconds)", () => {
    bench("classifyRepo ecosystem check", () => {
      const start = Bun.nanoseconds();
      const name = "tau-session-audit";
      const lower = name.toLowerCase();
      ["sovereign", "tau", "mesh", "pi"].some(kw => lower.includes(kw));
      Bun.nanoseconds() - start;
    });

    bench("classifyRepo internal check", () => {
      const start = Bun.nanoseconds();
      const name = "config-secret-backup";
      const lower = name.toLowerCase();
      ["secret", "token", "credential"].some(kw => lower.includes(kw));
      Bun.nanoseconds() - start;
    });
  });

  group("Pattern Borrowing", () => {
    bench("loadGlobalPatterns", () => {
      const start = Bun.nanoseconds();
      loadGlobalPatterns();
      Bun.nanoseconds() - start;
    });

    bench("classifyByPattern", () => {
      const start = Bun.nanoseconds();
      classifyByPattern("tau-repo");
      Bun.nanoseconds() - start;
    });
  });

  group("Search Performance", () => {
    bench("runGh execFile", () => {
      const start = Bun.nanoseconds();
      // Simulated — actual timing in runGh()
      Bun.nanoseconds() - start;
    });

    bench("runExa", () => {
      const start = Bun.nanoseconds();
      Bun.nanoseconds() - start;
    });

    bench("runAstGrep", () => {
      const start = Bun.nanoseconds();
      Bun.nanoseconds() - start;
    });
  });

  const results = await run({ percentiles: true });
  return results as Record<string, number>;
}

// ============================================================================
// Main — Multi-Tier, Chained, AST-Aware Audit
// ============================================================================

async function main() {
  const overallStart = nowNs();
  const timingMetrics: TimingMetric[] = [];

  console.log(`🔍 maximal-sovereign-agentic-audit — Maximal agentic audit`);
  console.log(`   User: ${USER} | Repos: ${REPOS.join(",")} | Users: ${USERS.join(",")} | Tier: ${TIER} | Chain: ${CHAIN} | PatternBorrow: ${PATTERN_BORROW}`);
  console.log(`   AST: ${AST_SEARCH} | Exa: ${EXA_SEARCH} | GH: ${GH_SEARCH}`);
  console.log(`   Stream: ${STREAM_ENABLED} (${STREAM_BATCH_SIZE}/batch) | Timing: ${TIMING_ENABLED}`);
  if (BENCHMARK) console.log(`   ⏱️  Running mitata benchmarks...`);

  // Phase 1: Fetch
  let fetchStart = nowNs();
  let rawRepos: Record<string, unknown>[] = [];

  if (REPOS.length > 0) {
    for (const repoSpec of REPOS) {
      rawRepos.push(...await fetchReposForRepo(repoSpec));
    }
  } else if (USERS.length > 0) {
    for (const u of USERS) {
      rawRepos.push(...await fetchReposForUser(u));
    }
  } else {
    rawRepos = await fetchReposForUser(USER);
  }
  timingMetrics.push(timing("fetch", fetchStart));
  console.log(`\n📊 Fetched ${rawRepos.length} repos from ${REPOS.length ? REPOS.join(", ") : USERS.length ? USERS.join(", ") : USER}`);

  // Phase 2: Build Records (with bun checks)
  fetchStart = nowNs();
  let records = await buildRecords(rawRepos);
  timingMetrics.push(timing("build_records", fetchStart));

  // Apply tier filter
  if (TIER !== "all") {
    records = records.filter(r => r.tier === TIER);
    console.log(`📊 Filtered to ${TIER} tier: ${records.length} repos`);
  }

  // Phase 3: Chained pipeline (pattern borrow → ast → exa → gh)
  if (CHAIN || AST_SEARCH || EXA_SEARCH || GH_SEARCH || PATTERN_BORROW) {
    records = await chainedPipeline(records);
  }

  // Count AST/exa/gh matches
  let astMatches = 0, exaSearches = 0, ghSearches = 0;
  for (const r of records) {
    astMatches += r.ast_patterns.length;
    exaSearches += r.exa_files.length;
    ghSearches += r.gh_code_matches.length;
  }

  // Phase 4: Bun checks
  let bunEnabled = 0;
  if (CHECK_BUN) {
    bunEnabled = records.filter(r => r.bun_version).length;
  }

  // Phase 5: Write Parquet
  fetchStart = nowNs();
  await writeParquet(records, OUTPUT_PARQUET);
  timingMetrics.push(timing("parquet_write", fetchStart));

  // Phase 6: CSV Export
  if (EXPORT_CSV) {
    await exportCSV(records, EXPORT_CSV);
    console.log(`📄 CSV exported to ${EXPORT_CSV}`);
  }

  // Phase 7: Anomaly Detection
  const anomalies = records.filter(r =>
    (r.classification === "REVIEW_PRIVATE" || r.classification === "PRIVATE_INTERNAL") && !r.private
  );

  // Phase 8: Agentic Completions
  if (AGENTIC_ENABLED) {
    const prompts = generateCompletionPrompts(records);
    console.log(`\n🤖 Agentic Mode: ${prompts.length} completion prompts generated`);
    if (STREAM_COMPLETIONS) {
      await streamCompletions(records);
    } else {
      for (const p of prompts.slice(0, 10)) {
        console.log(`   [PROMPT] ${p}`);
      }
    }
  }

  // Phase 9: Benchmarks
  const benchmarks = await runBenchmarks();

  // Phase 10: Summary
  const totalDurationMs = elapsedMs(overallStart);
  const summary: AuditSummary = {
    total: records.length,
    public: records.filter(r => !r.private).length,
    private: records.filter(r => r.private).length,
    forks: records.filter(r => r.fork).length,
    ecosystem: records.filter(r => r.classification === "PUBLIC_ECOSYSTEM").length,
    internal: records.filter(r => r.classification === "PRIVATE_INTERNAL").length,
    bun_enabled,
    ast_matches: AST_SEARCH ? astMatches : 0,
    exa_searches: EXA_SEARCH ? exaSearches : 0,
    gh_searches: GH_SEARCH ? ghSearches : 0,
  };

  const result: AuditResult = { repos: records, timing: timingMetrics, anomalies, summary, benchmarks };

  if (JSON_OUTPUT) {
    await writeFile(join(OUTPUT_DIR, "audit-result.json"), JSON.stringify(result, null, 2));
  }

  // Print results
  console.log(`\n${"=".repeat(60)}`);
  console.log(`📋 AUDIT SUMMARY`);
  console.log(`${"=".repeat(60)}`);
  console.log(`   Total repos:      ${summary.total}`);
  console.log(`   Public:           ${summary.public}`);
  console.log(`   Private:          ${summary.private}`);
  console.log(`   Forks:            ${summary.forks}`);
  console.log(`   Ecosystem:        ${summary.ecosystem}`);
  console.log(`   Internal:         ${summary.internal}`);
  console.log(`   Bun-enabled:      ${summary.bun_enabled}`);
  if (AST_SEARCH) console.log(`   AST matches:      ${summary.ast_matches}`);
  if (EXA_SEARCH) console.log(`   Exa files:        ${summary.exa_searches}`);
  if (GH_SEARCH) console.log(`   GH code matches:  ${summary.gh_searches}`);
  console.log(`   Anomalies:        ${anomalies.length}`);
  console.log(`   Total duration:   ${totalDurationMs.toFixed(2)}ms`);

  if (TIMING_ENABLED && timingMetrics.length > 0) {
    console.log(`\n⏱️  TIMING BREAKDOWN`);
    console.log(`${"=".repeat(60)}`);
    for (const t of timingMetrics) {
      console.log(`   ${t.phase.padEnd(20)} ${t.elapsed_us.toFixed(0)}µs / ${t.elapsed_ms.toFixed(2)}ms`);
    }
  }

  if (anomalies.length > 0) {
    console.log(`\n⚠️  ANOMALIES (public repos that should be private):`);
    for (const a of anomalies.slice(0, 10)) {
      console.log(`   • ${a.name} (${a.classification}) — ${a.description.slice(0, 60)}`);
    }
  }

  if (BENCHMARK && Object.keys(benchmarks).length > 0) {
    console.log(`\n🏆 BENCHMARKS`);
    console.log(`${"=".repeat(60)}`);
    console.log(`   See mitata output above for detailed percentiles.`);
  }

  console.log(`\n✅ Audit complete. Output: ${OUTPUT_PARQUET}`);

  return result;
}

main().catch(e => { console.error("Error:", (e as Error).message); process.exit(1); });
