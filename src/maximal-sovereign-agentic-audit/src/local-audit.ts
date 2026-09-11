/**
 * local-audit.ts — Local-First Repository Auditor
 *
 * Scans all local git repos without GitHub API calls.
 * Uses completions API on 25100 for analysis.
 * Supports full/parallel audits with auto-fix and pre-run checks.
 */

import { execFile } from "child_process";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { readdirSync, statSync } from "fs";
import { mkdir, writeFile, rm } from "fs/promises";
import { Table } from "apache-arrow";
import { ParquetWriter, ParquetSchema } from "parquetjs-lite";

// ============================================================================
// Types
// ============================================================================

interface RepoRecord {
  name: string;
  path: string;
  area: string;
  lastCommit: string;
  message: string;
  commit: string;
  author: string;
}

interface LocalAuditResult {
  repos: RepoRecord[];
  total: number;
  byArea: Record<string, number>;
  recent: number;
  stale: number;
  symlinks: SymlinkRecord[];
}

interface SymlinkRecord {
  name: string;
  path: string;
  target: string;
  status: "ok" | "broken";
}

interface AuditMode {
  type: "full" | "parallel";
  autoFix: boolean;
  preCheck: boolean;
  completions: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const PROJECTS_DIR = "/home/toxic/projects";
const SOVEREIGN_DIR = "/home/toxic/sovereign";
const COMPLETIONS_URL = "http://127.0.0.1:25100/v1/chat/completions";

// ============================================================================
// Git Scanner
// ============================================================================

function runGit(dir: string, args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile("git", ["-C", dir, ...args], { timeout: 5000 }, (err, stdout, stderr) => {
      if (err) { reject(err); return; }
      resolve(stdout.trim());
    });
  });
}

export function scanDir(dir: string): RepoRecord[] {
  try {
    // Find all .git directories under dir, then get their parent (the repo root)
    const output = Bun.$`find ${dir} -type d -name .git`.text();
    const gitDirs = output.trim().split('\n').filter(Boolean);
    const repos: RepoRecord[] = [];
    const seen = new Set<string>();
    for (const gitDir of gitDirs) {
      const repoDir = path.dirname(gitDir);
      // Normalize path to avoid duplicates due to symlinks or different traversals
      const normDir = path.resolve(repoDir);
      if (!seen.has(normDir)) {
        seen.add(normDir);
        repos.push(scanRepo(repoDir));
      }
    }
    return repos;
  } catch (err) {
    console.error(`Error scanning ${dir}:`, err);
    return [];
  }
}

// ============================================================================
// Symlink Scanner
// ============================================================================

function scanSymlinks(dir: string): SymlinkRecord[] {
  const records: SymlinkRecord[] = [];
  try {
    const entries = readdirSync(dir, { withFileTypes: true });
    for (const e of entries) {
      if (!e.isSymbolicLink()) continue;
      const target = e.name;
      try {
        const resolved = join(dir, e.name);
        statSync(resolved);
        records.push({ name: e.name, path: resolved, target, status: "ok" });
      } catch {
        records.push({ name: e.name, path: join(dir, e.name), target: "BROKEN", status: "broken" });
      }
    }
  } catch {}
  return records;
}

// ============================================================================
// Completions API
// ============================================================================

async function analyzeWithCompletions(data: string, prompt: string): Promise<string> {
  try {
    const body = JSON.stringify({
      model: "sovereign/audit-agent",
      messages: [{ role: "user", content: `${prompt}\n\nData:\n${data}` }],
      max_tokens: 4000,
      stream: false,
    });
    const resp = await fetch(COMPLETIONS_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    const json = await resp.json();
    return json.choices?.[0]?.message?.content || "";
  } catch {
    return "";
  }
}

// ============================================================================
// Auto-Fix
// ============================================================================

async function autoFix(result: LocalAuditResult): Promise<string[]> {
  const fixes: string[] = [];
  const stale = result.repos.filter(r => {
    if (!r.lastCommit) return true;
    const d = new Date(r.lastCommit);
    return d < new Date(Date.now() - 90 * 24 * 60 * 60 * 1000);
  });
  for (const repo of stale) {
    fixes.push(`archive:${repo.path} (stale >90d)`);
  }
  const symlinksBroken = result.symlinks.filter(s => s.status === "broken");
  for (const s of symlinksBroken) {
    fixes.push(`remove:${s.path} (broken symlink)`);
  }
  return fixes;
}

// ============================================================================
// Pre-Check
// ============================================================================

async function preCheck(): Promise<string[]> {
  const checks: string[] = [];
  const { existsSync } = await import("fs");
  if (!existsSync(PROJECTS_DIR)) checks.push("MISSING:projects_dir");
  if (!existsSync(SOVEREIGN_DIR)) checks.push("MISSING:sovereign_dir");
  return checks;
}

// ============================================================================
// Main Audit Function
// ============================================================================

export async function localAudit(
  paths: string[] = [PROJECTS_DIR, SOVEREIGN_DIR],
  mode: AuditMode = { type: "full", autoFix: false, preCheck: true, completions: false }
): Promise<LocalAuditResult> {
  const start = Bun.nanoseconds();

  // Pre-check
  if (mode.preCheck) {
    const checks = await preCheck();
    if (checks.length > 0) {
      console.log(`[WARN] Pre-check issues: ${checks.join(", ")}`);
    }
  }

  // Scan
  const allRepos: RepoRecord[] = [];
  for (const path of paths) {
    const area = path === PROJECTS_DIR ? "projects" : path === SOVEREIGN_DIR ? "sovereign" : "other";
    const repos = await scanDir(path, area);
    allRepos.push(...repos);
  }

  allRepos.sort((a, b) => b.lastCommit.localeCompare(a.lastCommit));

  const byArea: Record<string, number> = {};
  for (const r of allRepos) byArea[r.area] = (byArea[r.area] || 0) + 1;

  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
  const recent = allRepos.filter(r => r.lastCommit && new Date(r.lastCommit) >= sevenDaysAgo).length;
  const ninetyDaysAgo = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000);
  const stale = allRepos.filter(r => !r.lastCommit || new Date(r.lastCommit) < ninetyDaysAgo).length;
  const symlinks = scanSymlinks(PROJECTS_DIR);

  // Auto-fix if requested
  if (mode.autoFix) {
    const fixes = await autoFix({ repos: allRepos, total: allRepos.length, byArea, recent, stale, symlinks });
    for (const fix of fixes) console.log(`[AUTO-FIX] ${fix}`);
  }

  // Completions analysis if requested
  if (mode.completions) {
    const df = toDataFrame({ repos: allRepos, total: allRepos.length, byArea, recent, stale, symlinks });
    const analysis = await analyzeWithCompletions(JSON.stringify(df), "Analyze this repo data and identify stale/duplicate/archivable repos");
    if (analysis) console.log(`[COMPLETIONS] Analysis: ${analysis.slice(0, 200)}`);
  }

  const elapsed = Number(Bun.nanoseconds() - start) / 1_000_000;

  return { repos: allRepos, total: allRepos.length, byArea, recent, stale, symlinks };
}

// ============================================================================
// DataFrame
// ============================================================================

export function toDataFrame(result: LocalAuditResult): Record<string, unknown[]> {
  return {
    name: result.repos.map(r => r.name),
    path: result.repos.map(r => r.path),
    area: result.repos.map(r => r.area),
    lastCommit: result.repos.map(r => r.lastCommit),
    message: result.repos.map(r => r.message),
    commit: result.repos.map(r => r.commit),
    author: result.repos.map(r => r.author),
  };
}

// ============================================================================
// Parquet Export
// ============================================================================

export async function exportParquet(result: LocalAuditResult, path: string): Promise<void> {
  const schema = new ParquetSchema({
    name: { type: "UTF8" }, path: { type: "UTF8" }, area: { type: "UTF8" },
    lastCommit: { type: "UTF8" }, message: { type: "UTF8" },
    commit: { type: "UTF8" }, author: { type: "UTF8" },
  });
  const writer = await ParquetWriter.openFile(schema, path);
  for (const repo of result.repos) {
    await writer.appendRow({ name: repo.name, path: repo.path, area: repo.area, lastCommit: repo.lastCommit, message: repo.message, commit: repo.commit, author: repo.author });
  }
  await writer.close();
}

// ============================================================================
// CLI
// ============================================================================

const args = process.argv.slice(2);
function getArg(name: string, fallback: string): string {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 && idx + 1 < args.length ? args[idx + 1] : fallback;
}
function hasFlag(name: string): boolean { return args.includes(`--${name}`); }

const PATHS_STR = getArg("path", "");
const ALL = hasFlag("all");
const PARALLEL = hasFlag("parallel");
const AUTOFIX = hasFlag("autofix");
const PRECHECK = hasFlag("precheck");
const COMPLETIONS = hasFlag("completions");
const PARQUET_PATH = getArg("parquet", join(dirname(fileURLToPath(import.meta.url)), "..", "local-repos.parquet"));
const JSON_OUT = getArg("json", "");

const PATHS = ALL ? [PROJECTS_DIR, SOVEREIGN_DIR] : [PATHS_STR || PROJECTS_DIR];

async function main(): Promise<void> {
  const mode: AuditMode = {
    type: PARALLEL ? "parallel" : "full",
    autoFix: AUTOFIX,
    preCheck: PRECHECK !== false,
    completions: COMPLETIONS,
  };

  const start = Bun.nanoseconds();
  const result = await localAudit(PATHS, mode);
  const elapsed = Number(Bun.nanoseconds() - start) / 1_000_000;

  console.log(`\n🔍 local-audit — Local-First Repository Auditor`);
  console.log(`   Mode: ${mode.type} | AutoFix: ${mode.autoFix} | PreCheck: ${mode.preCheck} | Completions: ${mode.completions}`);
  console.log(`   Total repos: ${result.total} | Areas: ${Object.keys(result.byArea).join(", ")}`);
  console.log(`   Recent (<7d): ${result.recent} | Stale (>90d): ${result.stale}`);
  console.log(`   Scan time: ${elapsed.toFixed(1)}ms`);

  console.log(`\n🌿 LOCAL PROJECT TREE`);
  console.log(`   ${"─".repeat(70)}`);
  for (const area of Object.keys(result.byArea).sort()) {
    const count = result.byArea[area];
    console.log(`\n   📁 ${area.toUpperCase()} (${count} repos)`);
    const areaRepos = result.repos.filter(r => r.area === area).slice(0, 15);
    for (const repo of areaRepos) {
      const commit = repo.lastCommit ? repo.lastCommit.slice(0, 19) : "never";
      const name = repo.name.slice(0, 38);
      const msg = repo.message.slice(0, 28);
      console.log(`      ${name}  ${commit}  ${msg}`);
    }
  }

  if (result.symlinks.length > 0) {
    const broken = result.symlinks.filter(s => s.status === "broken");
    console.log(`\n🔗 SYMLINKS (${result.symlinks.length} total, ${broken.length} broken)`);
    for (const s of broken) console.log(`   ❌ ${s.name} -> ${s.target}`);
  }

  if (JSON_OUT) { await writeFile(JSON_OUT, JSON.stringify(result, null, 2)); console.log(`\n📄 JSON: ${JSON_OUT}`); }
  if (PARQUET_PATH) { await exportParquet(result, PARQUET_PATH); console.log(`\n📄 Parquet: ${PARQUET_PATH}`); }

  console.log(`\n✅ Audit complete in ${elapsed.toFixed(1)}ms`);
}

main().catch(e => { console.error("Error:", e.message); process.exit(1); });
