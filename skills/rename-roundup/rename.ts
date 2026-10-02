#!/usr/bin/env bun
/**
 * Fork Renaming and Rebranding Engine — Fast Bun Native Implementation.
 * 
 * Order matters: URL anchors are rewritten first so fork-hosted links win, then
 * bare tokens are replaced across all case variants.
 */

import { existsSync } from "node:fs";
import { resolve, relative, extname, basename } from "node:path";
import { parseArgs } from "node:util";

const DEFAULT_REPO = "/home/toxic/workspace/untracked/roundup";

const SKIP_SUFFIX = new Set([
  ".png", ".gif", ".jpg", ".jpeg", ".webp", ".ico", ".svg",
  ".whl", ".so", ".pyc", ".bin", ".node", ".wasm", ".pdf",
  ".lockb", ".lock", ".tar", ".gz", ".zip", ".parquet", ".db"
]);

const SKIP_NAMES = new Set([
  "uv.lock", "bun.lock", "package-lock.json", "Cargo.lock", "yarn.lock"
]);

const SKIP_DIRS = new Set([
  ".git", "build", "dist", "node_modules", ".venv", "venv", "__pycache__", "target"
]);

function buildRules(oldToken: string, newToken: string, oldOrg: string, newOrg: string) {
  const urlRules: Array<[string, string]> = [
    [`github.com/${oldOrg}/${oldToken}`, `github.com/${newOrg}/${newToken}`],
    [`${oldOrg}.github.io/${oldToken}`, `${newOrg}.github.io/${newToken}`],
    [`pypi.org/project/${oldToken}`, `pypi.org/project/${newToken}`],
    [`crates.io/crates/${oldToken}`, `crates.io/crates/${newToken}`],
    [`npmjs.com/package/${oldToken}`, `npmjs.com/package/${newToken}`],
  ];

  const capitalize = (s: string) => s.length > 0 ? s[0].toUpperCase() + s.slice(1) : s;

  const rawTokenRules: Array<[string, string]> = [
    [oldToken.toUpperCase(), newToken.toUpperCase()],
    [capitalize(oldToken), capitalize(newToken)],
    [oldToken.toLowerCase(), newToken.toLowerCase()],
  ];

  // Deduplicate while preserving order
  const seen = new Set<string>();
  const tokenRules: Array<[string, string]> = [];
  for (const [o, n] of rawTokenRules) {
    const key = `${o}\0${n}`;
    if (!seen.has(key)) {
      seen.add(key);
      tokenRules.push([o, n]);
    }
  }

  return { urlRules, tokenRules };
}

async function getTrackedFiles(repoPath: string): Promise<string[]> {
  const proc = Bun.spawn(["git", "ls-files", "-z"], {
    cwd: repoPath,
    stdout: "pipe",
    stderr: "pipe",
  });

  const [stdout, exitCode] = await Promise.all([
    new Response(proc.stdout).text(),
    proc.exited,
  ]);

  if (exitCode !== 0) {
    throw new Error(`git ls-files failed in ${repoPath} (code ${exitCode})`);
  }

  return stdout.split("\0").filter(Boolean).map(p => resolve(repoPath, p));
}

async function processFile(
  fullPath: string,
  repoRoot: string,
  urlRules: Array<[string, string]>,
  tokenRules: Array<[string, string]>,
  dryRun: boolean
): Promise<string | null> {
  const rel = relative(repoRoot, fullPath);
  const parts = rel.split("/");

  // Skip directories & ignored names
  for (const part of parts) {
    if (SKIP_DIRS.has(part) || part.endsWith(".egg-info")) return null;
  }

  const name = basename(fullPath);
  if (SKIP_NAMES.has(name)) return null;

  const ext = extname(fullPath).toLowerCase();
  if (SKIP_SUFFIX.has(ext)) return null;

  try {
    const file = Bun.file(fullPath);
    const original = await file.text();

    let text = original;
    for (const [oldUrl, newUrl] of urlRules) {
      if (text.includes(oldUrl)) {
        text = text.replaceAll(oldUrl, newUrl);
      }
    }

    for (const [oldToken, newToken] of tokenRules) {
      if (text.includes(oldToken)) {
        text = text.replaceAll(oldToken, newToken);
      }
    }

    if (text !== original) {
      if (!dryRun) {
        await Bun.write(fullPath, text);
      }
      return rel;
    }
  } catch {
    // Binary or unreadable text, skip safely
    return null;
  }

  return null;
}

async function main() {
  const { values } = parseArgs({
    args: Bun.argv.slice(2),
    options: {
      repo: { type: "string", default: DEFAULT_REPO },
      old: { type: "string", default: "guidellm" },
      new: { type: "string", default: "roundup" },
      "old-org": { type: "string", default: "vllm-project" },
      "new-org": { type: "string", default: "toxicwind" },
      "dry-run": { type: "boolean", default: false },
      concurrency: { type: "string", default: "64" },
      help: { type: "boolean", short: "h" },
    },
    allowPositionals: true,
  });

  if (values.help) {
    console.log(`
Usage: bun run rename.ts [options]

Options:
  --repo <path>       Target git repository root (default: ${DEFAULT_REPO})
  --old <token>       Old name/token to replace (default: guidellm)
  --new <token>       New name/token (default: roundup)
  --old-org <org>     Old organization (default: vllm-project)
  --new-org <org>     New organization (default: toxicwind)
  --concurrency <n>   Parallel worker pool size (default: 64)
  --dry-run           Preview affected files without writing
  -h, --help          Show help
`);
    return 0;
  }

  const repo = resolve(values.repo ?? DEFAULT_REPO);
  if (!existsSync(repo)) {
    console.error(`Error: Repository path does not exist: ${repo}`);
    return 1;
  }

  const { urlRules, tokenRules } = buildRules(
    values.old ?? "guidellm",
    values.new ?? "roundup",
    values["old-org"] ?? "vllm-project",
    values["new-org"] ?? "toxicwind"
  );

  const files = await getTrackedFiles(repo);
  const concurrency = parseInt(values.concurrency ?? "64", 10) || 64;
  const changed: string[] = [];

  // Parallel pool processing
  let idx = 0;
  async function worker() {
    while (idx < files.length) {
      const file = files[idx++];
      const result = await processFile(file, repo, urlRules, tokenRules, values["dry-run"] ?? false);
      if (result) changed.push(result);
    }
  }

  const workers = Array.from({ length: Math.min(concurrency, files.length) }, () => worker());
  await Promise.all(workers);

  const action = values["dry-run"] ? "would rewrite" : "rewrote";
  console.log(`${action} ${changed.length} files in ${repo}`);
  changed.sort().forEach(f => console.log(`  ${f}`));

  return 0;
}

if (import.meta.main) {
  process.exit(await main());
}
