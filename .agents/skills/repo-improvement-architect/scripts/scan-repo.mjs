#!/usr/bin/env node
// Fast repo inventory for the Repo Improvement Architect skill.
// Usage: node scan-repo.mjs [repoRoot]
// Prints manifests, package scripts, CI workflow files, and a file-type tally.
// Read-only. No network. No mutation.
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, extname } from "node:path";

const root = process.argv[2] ?? process.cwd();
const SKIP = new Set([".git", "node_modules", "dist", "build", "coverage", ".next", "vendor"]);

const MANIFESTS = [
  "package.json",
  "pnpm-lock.yaml",
  "yarn.lock",
  "package-lock.json",
  "bun.lockb",
  "pyproject.toml",
  "requirements.txt",
  "go.mod",
  "Cargo.toml",
  "Makefile"
];

function detectPackageManager() {
  if (existsSync(join(root, "pnpm-lock.yaml"))) return "pnpm";
  if (existsSync(join(root, "yarn.lock"))) return "yarn";
  if (existsSync(join(root, "bun.lockb"))) return "bun";
  if (existsSync(join(root, "package-lock.json"))) return "npm";
  return "unknown";
}

function walk(dir, depth, tally, files) {
  if (depth > 6) return;
  for (const entry of readdirSync(dir)) {
    if (SKIP.has(entry)) continue;
    const full = join(dir, entry);
    let s;
    try {
      s = statSync(full);
    } catch {
      continue;
    }
    if (s.isDirectory()) {
      walk(full, depth + 1, tally, files);
    } else {
      files.count++;
      const ext = extname(entry) || "(none)";
      tally[ext] = (tally[ext] ?? 0) + 1;
    }
  }
}

console.log(`# Repo inventory: ${root}\n`);

console.log("## Manifests");
for (const m of MANIFESTS) {
  if (existsSync(join(root, m))) console.log(`- ${m}`);
}
console.log(`\nDetected package manager: ${detectPackageManager()}\n`);

const pkgPath = join(root, "package.json");
if (existsSync(pkgPath)) {
  try {
    const pkg = JSON.parse(readFileSync(pkgPath, "utf8"));
    console.log("## package.json scripts");
    for (const [k, v] of Object.entries(pkg.scripts ?? {})) {
      console.log(`- ${k}: ${v}`);
    }
    console.log("");
  } catch (err) {
    console.log(`(could not parse package.json: ${err.message})\n`);
  }
}

const wfDir = join(root, ".github", "workflows");
if (existsSync(wfDir)) {
  console.log("## CI workflows");
  for (const f of readdirSync(wfDir)) console.log(`- .github/workflows/${f}`);
  console.log("");
}

const tally = {};
const files = { count: 0 };
walk(root, 0, tally, files);
console.log(`## File types (${files.count} files)`);
for (const [ext, n] of Object.entries(tally).sort((a, b) => b[1] - a[1]).slice(0, 15)) {
  console.log(`- ${ext}: ${n}`);
}
