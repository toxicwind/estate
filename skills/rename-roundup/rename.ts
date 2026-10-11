#!/usr/bin/env bun
/**
 * rename-roundup — full-blown fork renaming and rebranding engine (Bun-native).
 *
 * Rewrites a repository checkout from one brand to another across file
 * CONTENTS and file NAMES, driven by an explicit pairs file. Built for the
 * case a naive search-replace would destroy: short tokens like `omp` that
 * appear inside `complete`, `prompt`, `component`.
 *
 * Pairs file format (one rule per line, `#` comments, blank lines ignored):
 *   substr:  OLD => NEW     plain substring replace (distinctive tokens:
 *                           `oh-my-pi`, `@oh-my-pi`, full URLs)
 *   word:    OLD => NEW     whole-word replace via \bOLD\b (short tokens:
 *                           `omp`, `OMP`, `Omp` — never touches `complete`)
 *   prefix:  OLD => NEW     word-prefix replace via \bOLD (`pi-` -> `tau-`)
 *   exclude: TOKEN           never rewritten (e.g. OMP_NUM_THREADS, the real
 *                           OpenMP variable inside vendored uutils code)
 *
 * Every substr/word/prefix rule auto-expands to UPPER and Capitalized
 * variants (omp => tau also yields OMP => TAU, Omp => Tau). Rules apply in
 * file order. Exclusions are placeholder-swapped before any rule runs.
 *
 * Safety invariants:
 * - Operates only on `git ls-files` tracked files (never untracked scratch).
 * - Skips binaries by extension, lockfiles, build outputs, .git.
 * - Filenames are renamed with `git mv` (history preserved), deepest first.
 * - `--dry-run` previews everything. `--commit` wraps the run in one git
 *   commit so rollback is `git reset --hard HEAD~1` (or `git revert`).
 *   Without --commit, rollback of an uncommitted run is `git checkout -- .`
 *   plus `git status` to catch the renames.
 *
 * Idempotent: a second run changes nothing (no old tokens remain).
 */

import { existsSync, readFileSync } from "node:fs";
import { resolve, relative, extname, basename, dirname } from "node:path";
import { parseArgs } from "node:util";

type Mode = "substr" | "word" | "prefix";
interface Rule { mode: Mode; old: string; new: string; re: RegExp }

const SKIP_SUFFIX = new Set([
  ".png", ".gif", ".jpg", ".jpeg", ".webp", ".ico", ".svg",
  ".whl", ".so", ".pyc", ".bin", ".node", ".wasm", ".pdf",
  ".lockb", ".lock", ".tar", ".gz", ".zip", ".parquet", ".db",
]);

const SKIP_NAMES = new Set([
  "uv.lock", "bun.lock", "package-lock.json", "Cargo.lock", "yarn.lock",
]);

const SKIP_DIRS = new Set([
  ".git", "build", "dist", "node_modules", ".venv", "venv",
  "__pycache__", "target", ".moon", ".cache",
]);

const capitalize = (s: string) => (s.length > 0 ? s[0].toUpperCase() + s.slice(1) : s);
const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function buildRule(mode: Mode, old: string, fresh: string): Rule[] {
  // Auto-expand case variants: lower (as given), UPPER, Capitalized.
  const variants: Array<[string, string]> = [
    [old, fresh],
    [old.toUpperCase(), fresh.toUpperCase()],
    [capitalize(old), capitalize(fresh)],
  ];
  const seen = new Set<string>();
  const rules: Rule[] = [];
  for (const [o, n] of variants) {
    if (!o || o === n) continue;
    const key = `${mode}\0${o}\0${n}`;
    if (seen.has(key)) continue;
    seen.add(key);
    let re: RegExp;
    if (mode === "substr") re = new RegExp(escapeRe(o), "g");
    else if (mode === "word") re = new RegExp(`\\b${escapeRe(o)}\\b`, "g");
    else re = new RegExp(`\\b${escapeRe(o)}`, "g");
    rules.push({ mode, old: o, new: n, re });
  }
  return rules;
}

function parsePairsFile(path: string): { rules: Rule[]; excludes: string[] } {
  const rules: Rule[] = [];
  const excludes: string[] = [];
  const lines = readFileSync(path, "utf8").split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line || line.startsWith("#")) continue;
    const m = line.match(/^(substr|word|prefix|exclude)\s*:\s*(.+)$/);
    if (!m) throw new Error(`pairs file ${path}:${i + 1}: bad line: ${line}`);
    if (m[1] === "exclude") {
      excludes.push(m[2].trim());
      continue;
    }
    const parts = m[2].split("=>");
    if (parts.length !== 2) throw new Error(`pairs file ${path}:${i + 1}: want OLD => NEW: ${line}`);
    rules.push(...buildRule(m[1] as Mode, parts[0].trim(), parts[1].trim()));
  }
  return { rules, excludes };
}

/** Legacy simple mode: --old/--new/--old-org/--new-org (substring semantics). */
function legacyRules(oldToken: string, newToken: string, oldOrg: string, newOrg: string): { rules: Rule[]; excludes: string[] } {
  const rules: Rule[] = [];
  const push = (mode: Mode, o: string, n: string) => rules.push(...buildRule(mode, o, n));
  push("substr", `github.com/${oldOrg}/${oldToken}`, `github.com/${newOrg}/${newToken}`);
  push("substr", `${oldOrg}.github.io/${oldToken}`, `${newOrg}.github.io/${newToken}`);
  push("substr", `pypi.org/project/${oldToken}`, `pypi.org/project/${newToken}`);
  push("substr", `crates.io/crates/${oldToken}`, `crates.io/crates/${newToken}`);
  push("substr", `npmjs.com/package/${oldToken}`, `npmjs.com/package/${newToken}`);
  push("substr", oldToken, newToken);
  return { rules, excludes: [] };
}

async function getTrackedFiles(repoPath: string): Promise<string[]> {
  const proc = Bun.spawn(["git", "ls-files", "-z"], {
    cwd: repoPath, stdout: "pipe", stderr: "pipe",
  });
  const [stdout, exitCode] = await Promise.all([new Response(proc.stdout).text(), proc.exited]);
  if (exitCode !== 0) throw new Error(`git ls-files failed in ${repoPath} (code ${exitCode})`);
  return stdout.split("\0").filter(Boolean).map((p) => resolve(repoPath, p));
}

function shouldSkip(fullPath: string, repoRoot: string): boolean {
  const rel = relative(repoRoot, fullPath);
  for (const part of rel.split("/")) {
    if (SKIP_DIRS.has(part) || part.endsWith(".egg-info")) return true;
  }
  if (SKIP_NAMES.has(basename(fullPath))) return true;
  if (SKIP_SUFFIX.has(extname(fullPath).toLowerCase())) return true;
  return false;
}

/** Placeholder armor for exclusions: NUL-wrapped so no rule can match them. */
function armor(text: string, excludes: string[]): { text: string; table: string[] } {
  const table: string[] = [];
  for (const ex of excludes) {
    if (!ex || !text.includes(ex)) continue;
    const ph = `\0EXCL${table.length}\0`;
    table.push(ex);
    text = text.split(ex).join(ph);
  }
  return { text, table };
}
function unarmor(text: string, table: string[]): string {
  for (let i = 0; i < table.length; i++) text = text.split(`\0EXCL${i}\0`).join(table[i]);
  return text;
}

function applyRules(text: string, rules: Rule[], excludes: string[]): string {
  const a = armor(text, excludes);
  let t = a.text;
  for (const r of rules) t = t.replace(r.re, r.new);
  return unarmor(t, a.table);
}

async function main(): Promise<number> {
  const { values } = parseArgs({
    args: Bun.argv.slice(2),
    options: {
      repo: { type: "string" },
      pairs: { type: "string" },
      old: { type: "string" },
      new: { type: "string" },
      "old-org": { type: "string" },
      "new-org": { type: "string" },
      "dry-run": { type: "boolean", default: false },
      commit: { type: "string" },
      concurrency: { type: "string", default: "64" },
      help: { type: "boolean", short: "h" },
    },
    allowPositionals: true,
  });

  if (values.help) {
    console.log(`
rename-roundup — fork renaming and rebranding engine (Bun-native).

Usage:
  bun run rename.ts --repo <path> --pairs <file> [--dry-run] [--commit "msg"]
  bun run rename.ts --repo <path> --old <t> --new <t> [--old-org o] [--new-org n]

Pairs file rules (one per line):
  substr:  OLD => NEW    substring (distinctive tokens: oh-my-pi, @scope, URLs)
  word:    OLD => NEW    whole word \\\\bOLD\\\\b (short tokens: omp — skips "complete")
  prefix:  OLD => NEW     word prefix \\\\bOLD (pi- -> tau-)
  exclude: TOKEN         never rewritten (OMP_NUM_THREADS)

Options:
  --repo <path>       target git repo root (default: cwd)
  --pairs <file>      rule file (preferred)
  --dry-run           preview only: lists content changes + renames
  --commit "<msg>"    git add -A && git commit -m "<msg>" after the run
  --concurrency <n>   worker pool size (default: 64)
  -h, --help

Rollback: with --commit: git reset --hard HEAD~1. Without: git checkout -- .
Idempotent: re-running changes nothing.
`);
    return 0;
  }

  const repo = resolve(values.repo ?? process.cwd());
  if (!existsSync(resolve(repo, ".git"))) {
    console.error(`Error: not a git repo root: ${repo}`);
    return 1;
  }

  let rules: Rule[];
  let excludes: string[];
  if (values.pairs) {
    ({ rules, excludes } = parsePairsFile(resolve(values.pairs)));
  } else if (values.old && values.new) {
    ({ rules, excludes } = legacyRules(values.old, values.new, values["old-org"] ?? "", values["new-org"] ?? ""));
  } else {
    console.error("Error: need --pairs <file> or --old/--new");
    return 1;
  }
  const dryRun = values["dry-run"] ?? false;

  const files = (await getTrackedFiles(repo)).filter((f) => !shouldSkip(f, repo));
  const concurrency = parseInt(values.concurrency ?? "64", 10) || 64;
  const changed: string[] = [];
  let idx = 0;

  async function worker() {
    while (idx < files.length) {
      const file = files[idx++];
      try {
        const original = await Bun.file(file).text();
        const updated = applyRules(original, rules, excludes);
        if (updated !== original) {
          if (!dryRun) await Bun.write(file, updated);
          changed.push(relative(repo, file));
        }
      } catch { /* binary/unreadable — skip */ }
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, files.length) }, () => worker()));

  // Filename pass: apply the same rules to tracked paths, git mv deepest-first.
  const renames: Array<[string, string]> = [];
  const collisions: string[] = [];
  const pathRules = rules; // word/prefix regexes work on paths too (/ and - are boundaries)
  const sorted = [...files].sort((a, b) => b.length - a.length);
  for (const file of sorted) {
    const rel = relative(repo, file);
    const newRel = applyRules(rel, pathRules, excludes);
    if (newRel !== rel) {
      if (existsSync(resolve(repo, newRel))) collisions.push(`${rel} -> ${newRel} (target exists)`);
      else renames.push([rel, newRel]);
    }
  }
  // Apply dir renames via files: git mv each file; git handles dir renames.
  // Deeper paths first so a parent dir rename never strands a child.
  renames.sort((a, b) => b[0].length - a[0].length);
  let renamed = 0;
  if (!dryRun) {
    const { mkdirSync } = await import("node:fs");
    for (const [o, n] of renames) {
      mkdirSync(dirname(resolve(repo, n)), { recursive: true });
      const p = Bun.spawn(["git", "mv", o, n], { cwd: repo, stdout: "pipe", stderr: "pipe" });
      const code = await p.exited;
      if (code === 0) renamed++;
      else {
        const err = await new Response(p.stderr).text();
        collisions.push(`${o} -> ${n} (git mv failed: ${err.trim().split("\n")[0]})`);
      }
    }
  }

  const action = dryRun ? "would rewrite" : "rewrote";
  console.log(`${action} ${changed.length} files in ${repo}`);
  for (const f of changed.sort()) console.log(`  M ${f}`);
  console.log(`${dryRun ? "would rename" : "renamed"} ${dryRun ? renames.length : renamed} paths`);
  for (const [o, n] of renames) console.log(`  R ${o} -> ${n}`);
  for (const c of collisions) console.log(`  ! COLLISION ${c}`);

  if (!dryRun && values.commit) {
    const add = Bun.spawn(["git", "add", "-A"], { cwd: repo, stdout: "pipe", stderr: "pipe" });
    if ((await add.exited) !== 0) { console.error("git add -A failed"); return 1; }
    const cm = Bun.spawn(["git", "commit", "-m", values.commit], { cwd: repo, stdout: "pipe", stderr: "pipe" });
    const out = await new Response(cm.stdout).text();
    if ((await cm.exited) !== 0) { console.error(`git commit failed: ${out}`); return 1; }
    console.log(`committed: ${out.trim().split("\n")[0]}`);
    console.log("rollback: git reset --hard HEAD~1");
  } else if (!dryRun) {
    console.log("rollback (uncommitted): git checkout -- . && git status  # then revert renames per R lines above");
  }
  return collisions.length > 0 ? 2 : 0;
}

if (import.meta.main) process.exit(await main());
