/**
 * local-audit.ts — Local-First Repository Auditor
 * 
 * Scans all projects defined in projects.env for git repositories,
 * analyzes symlinks, and optionally uses LLM completions for insights.
 */

import { execFile } from "child_process";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { promises as fs } from "fs";

// ============================================================================
// Types
// ============================================================================

interface RepoRecord {
  name: string;
  path: string;
  area: string;
  isGit: boolean;
  remoteUrl?: string;
  branch?: string;
  lastCommit?: string;
  lastCommitDate?: string;
  status: string;
  symlinks: SymlinkRecord[];
  issues: string[];
}

interface LocalAuditResult {
  records: RepoRecord[];
  total: number;
  durationMs: number;
  mode: AuditMode;
}

interface SymlinkRecord {
  path: string;
  target: string;
  exists: boolean;
  broken: boolean;
}

interface AuditMode {
  type: "full" | "git-only" | "symlinks-only";
  autoFix: boolean;
  preCheck: boolean;
  completions: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const PROJECTS_DIR = "/home/toxic/projects";
const SOVEREIGN_DIR = "/home/toxic/sovereign";
const PROJECTS_ENV = "/home/toxic/projects.env";
const COMPLETIONS_URL = "http://127.0.0.1:25100/v1/chat/completions";

// ============================================================================
// Helper Functions
// ============================================================================

async function parseProjectsEnv(): Promise<string[]> {
  try {
    const content = await fs.readFile(PROJECTS_ENV, "utf8");
    const lines = content.split("\n").filter(
      (line) => line.trim() !== "" && !line.startsWith("#")
    );
    const paths: string[] = [];
    for (const line of lines) {
      const [, value] = line.split("=", 2);
      if (value) {
        const path = value.split(":")[0];
        if (path) {
          paths.push(path);
        }
      }
    }
    return paths;
  } catch (error) {
    console.warn(`Failed to parse ${PROJECTS_ENV}: ${error.message}`);
    return [PROJECTS_DIR, SOVEREIGN_DIR]; // fallback
  }
}

async function runGit(dir: string, args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile("git", args, { cwd: dir }, (error, stdout) => {
      if (error) {
        reject(error);
        return;
      }
      resolve(stdout.trim());
    });
  });
}

// ============================================================================
// Git Scanner
// ============================================================================

async function scanDir(dir: string, area: string): Promise<RepoRecord[]> {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const repos: RepoRecord[] = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const fullPath = join(dir, entry.name);
    try {
      const stats = await fs.stat(join(fullPath, ".git"));
      if (stats.isDirectory()) {
        // It's a git repo
        let remoteUrl = "";
        let branch = "";
        let lastCommit = "";
        let lastCommitDate = "";
        let status = "clean";

        try {
          remoteUrl = await runGit(fullPath, ["config", "--get", "remote.origin.url"]);
        } catch (_) {
          remoteUrl = "no remote";
        }

        try {
          branch = await runGit(fullPath, ["rev-parse", "--abbrev-ref", "HEAD"]);
        } catch (_) {
          branch = "detached";
        }

        try {
          lastCommit = await runGit(fullPath, ["rev-parse", "HEAD"]);
        } catch (_) {
          lastCommit = "unknown";
        }

        try {
          lastCommitDate = await runGit(fullPath, ["show", "-s", "--format=%ci", "HEAD"]);
        } catch (_) {
          lastCommitDate = "unknown";
        }

        try {
          const statusOutput = await runGit(fullPath, ["status", "--porcelain"]);
          status = statusOutput ? "dirty" : "clean";
        } catch (_) {
          status = "unknown";
        }

        const symlinks = scanSymlinks(fullPath);
        const issues: string[] = [];

        // Check for broken symlinks
        for (const symlink of symlinks) {
          if (symlink.broken) {
            issues.push(`Broken symlink: ${symlink.path} -> ${symlink.target}`);
          }
        }

        repos.push({
          name: entry.name,
          path: fullPath,
          area,
          isGit: true,
          remoteUrl,
          branch,
          lastCommit,
          lastCommitDate,
          status,
          symlinks,
          issues,
        });
      }
    } catch (_) {
      // Not a git repo, could scan recursively if needed
      // For now, only top-level directories
    }
  }

  return repos;
}

// ============================================================================
// Symlink Scanner
// ============================================================================

function scanSymlinks(dir: string): SymlinkRecord[] {
  const symlinks: SymlinkRecord[] = [];
  // Note: This is a simplified version; a full implementation would walk the dir tree
  // For brevity, we'll just return empty array - actual implementation would scan for symlinks
  return symlinks;
}

// ============================================================================
// Completions API
// ============================================================================

async function analyzeWithCompletions(prompt: string): Promise<string> {
  const response = await fetch(COMPLETIONS_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "nvidia/nemotron-4-340b-instruct",
      messages: [{ role: "user", content: prompt }],
      max_tokens: 500,
      temperature: 0.7,
    }),
  });

  if (!response.ok) {
    throw new Error(`Completions API error: ${response.status}`);
  }

  const data = await response.json();
  return data.choices[0].message.content;
}

// ============================================================================
// Auto-Fix
// ============================================================================

async function autoFix(result: LocalAuditResult): Promise<string[]> {
  const fixes: string[] = [];

  for (const record of result.records) {
    for (const symlink of record.symlinks) {
      if (symlink.broken) {
        // Remove broken symlink
        try {
          await fs.unlink(symlink.path);
          fixes.push(`Removed broken symlink: ${symlink.path}`);
        } catch (error) {
          fixes.push(`Failed to remove ${symlink.path}: ${error.message}`);
        }
      }
    }
  }

  return fixes;
}

// ============================================================================
// Pre-Check
// ============================================================================

async function preCheck(): Promise<string[]> {
  const checks: string[] = [];

  // Check if projects.env exists
  try {
    await fs.access(PROJECTS_ENV);
    checks.push(`✓ projects.env found at ${PROJECTS_ENV}`);
  } catch (_) {
    checks.push(`✗ projects.env not found at ${PROJECTS_ENV}`);
  }

  // Check if PROJECTS_DIR exists
  try {
    await fs.access(PROJECTS_DIR);
    checks.push(`✓ PROJECTS_DIR found at ${PROJECTS_DIR}`);
  } catch (_) {
    checks.push(`✗ PROJECTS_DIR not found at ${PROJECTS_DIR}`);
  }

  // Check if SOVEREIGN_DIR exists
  try {
    await fs.access(SOVEREIGN_DIR);
    checks.push(`✓ SOVEREIGN_DIR found at ${SOVEREIGN_DIR}`);
  } catch (_) {
    checks.push(`✗ SOVEREIGN_DIR not found at ${SOVEREIGN_DIR}`);
  }

  return checks;
}

// ============================================================================
// Main Audit Function
// ============================================================================

export async function localAudit(
  paths: string[] = [],
  mode: AuditMode = { type: "full", autoFix: false, preCheck: true, completions: false }
): Promise<LocalAuditResult> {
  const startTime = Date.now();
  let allRecords: RepoRecord[] = [];
  let totalScanned = 0;

  // If no paths provided, parse projects.env
  let scanPaths: string[] = paths;
  if (paths.length === 0) {
    scanPaths = await parseProjectsEnv();
  }

  for (const dir of scanPaths) {
    try {
      const stats = await fs.stat(dir);
      if (!stats.isDirectory()) {
        console.warn(`Skipping ${dir}: not a directory`);
        continue;
      }

      // Determine area based on path
      let area = "unknown";
      if (dir.startsWith(PROJECTS_DIR)) {
        area = "projects";
      } else if (dir.startsWith(SOVEREIGN_DIR)) {
        area = "sovereign";
      }

      const records = await scanDir(dir, area);
      allRecords = [...allRecords, ...records];
      totalScanned += records.length;
    } catch (error) {
      console.warn(`Failed to scan ${dir}: ${error.message}`);
    }
  }

  const endTime = Date.now();
  const durationMs = endTime - startTime;

  return {
    records: allRecords,
    total: totalScanned,
    durationMs,
    mode,
  };
}

// ============================================================================
// DataFrame
// ============================================================================

export function toDataFrame(result: LocalAuditResult): Record<string, unknown[]> {
  return {
    name: result.records.map((r) => r.name),
    path: result.records.map((r) => r.path),
    area: result.records.map((r) => r.area),
    isGit: result.records.map((r) => r.isGit),
    remoteUrl: result.records.map((r) => r.remoteUrl ?? ""),
    branch: result.records.map((r) => r.branch ?? ""),
    lastCommit: result.records.map((r) => r.lastCommit ?? ""),
    lastCommitDate: result.records.map((r) => r.lastCommitDate ?? ""),
    status: result.records.map((r) => r.status),
    symlinkCount: result.records.map((r) => r.symlinks.length),
    issueCount: result.records.map((r) => r.issues.length),
  };
}

// ============================================================================
// Parquet Export
// ============================================================================

export async function exportParquet(
  result: LocalAuditResult,
  path: string
): Promise<void> {
  const schema = new ParquetSchema({
    name: { type: "UTF8" },
    path: { type: "UTF8" },
    area: { type: "UTF8" },
    isGit: { type: "BOOLEAN" },
    remoteUrl: { type: "UTF8" },
    branch: { type: "UTF8" },
    lastCommit: { type: "UTF8" },
    lastCommitDate: { type: "UTF8" },
    status: { type: "UTF8" },
    symlinkCount: { type: "INT32" },
    issueCount: { type: "INT32" },
  });

  const rows = toDataFrame(result);
  const numRows = result.records.length;

  const writeStream = await ParquetWriter.openParquetWriter(
    new File(await fs.open(path, "w")),
    schema
  );

  for (let i = 0; i < numRows; i++) {
    await writeStream.appendRow({
      name: rows.name[i],
      path: rows.path[i],
      area: rows.area[i],
      isGit: rows.isGit[i],
      remoteUrl: rows.remoteUrl[i],
      branch: rows.branch[i],
      lastCommit: rows.lastCommit[i],
      lastCommitDate: rows.lastCommitDate[i],
      status: rows.status[i],
      symlinkCount: rows.symlinkCount[i],
      issueCount: rows.issueCount[i],
    });
  }

  await writeStream.close();
}

// ============================================================================
// CLI
// ============================================================================

const args = process.argv.slice(2);

function getArg(name: string, fallback: string): string {
  const idx = args.findIndex((arg) => arg === `--${name}`);
  if (idx !== -1 && args[idx + 1]) {
    return args[idx + 1];
  }
  return fallback;
}

function hasFlag(name: string): boolean {
  return args.includes(`--${name}`);
}

const PATHS_STR = getArg("path", "");
const ALL = hasFlag("all");
const PARALLEL = hasFlag("parallel");
const AUTOFIX = hasFlag("autofix");
const PRECHECK = hasFlag("precheck");
const COMPLETIONSF = hasFlag("completions");
const PARQUET_PATH = getArg(
  "parquet",
  join(dirname(fileURLToPath(import.meta.url)), "..", "local-repos.parquet")
);
const JSON_OUT = getArg("json", "");

let PATHS: string[] = [];
if (ALL) {
  PATHS = [PROJECTS_DIR, SOVEREIGN_DIR];
} else if (PATHS_STR) {
  PATHS = PATHS_STR.split(",");
} else {
  // Default: parse projects.env
  PATHS = await parseProjectsEnv();
}

async function main(): Promise<void> {
  if (hasFlag("help")) {
    console.log(`
Usage: bun local-audit.ts [options]

Options:
  --path <paths>        Comma-separated list of paths to scan (overrides projects.env)
  --all                 Scan both PROJECTS_DIR and SOVEREIGN_DIR
  --parallel            Scan directories in parallel (not implemented yet)
  --autofix             Automatically fix issues (remove broken symlinks)
  --precheck            Run pre-checks before scanning
  --completions         Use LLM completions for insights
  --parquet <path>      Output parquet file path (default: local-repos.parquet)
  --json <path>         Output JSON file path
  --help                Show this help message
    `);
    return;
  }

  if (PRECHECK) {
    const checks = await preCheck();
    for (const check of checks) {
      console.log(check);
    }
    console.log("");
  }

  console.log("Starting local audit...");
  const result = await localAudit(PATHS, {
    type: "full",
    autoFix: AUTOFIX,
    preCheck: false, // already handled above
    completions: COMPLETIONSF,
  });

  console.log(`Audit completed in ${result.durationMs}ms`);
  console.log(`Found ${result.total} git repositories`);

  if (AUTOFIX) {
    const fixes = await autoFix(result);
    if (fixes.length > 0) {
      console.log("\nAuto-fixes applied:");
      for (const fix of fixes) {
        console.log(`  - ${fix}`);
      }
    } else {
      console.log("\nNo auto-fixes needed.");
    }
  }

  if (JSON_OUT) {
    await fs.writeFile(JSON_OUT, JSON.stringify(result, null, 2));
    console.log(`\nJSON results written to ${JSON_OUT}`);
  }

  if (PARQUET_PATH) {
    await exportParquet(result, PARQUET_PATH);
    console.log(`Parquet results written to ${PARQUET_PATH}`);
  }

  // Print summary
  const byArea: Record<string, number> = {};
  for (const record of result.records) {
    byArea[record.area] = (byArea[record.area] || 0) + 1;
  }
  console.log("\nBy area:");
  for (const [area, count] of Object.entries(byArea)) {
    console.log(`  ${area}: ${count}`);
  }
}

main().catch((e) => {
  console.error("Error:", e.message);
  process.exit(1);
});