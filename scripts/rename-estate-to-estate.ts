// Mass rename: Estate -> estate across live estate text files.
// Preserves:
//   * physical dirs whose name contains "Estate" (references to them stay valid)
//   * pitchfork daemon keys Estate-exporter / Estate-stream-broker
// Skips: .git, node_modules, var/, salvage/, archives, scratch, binaries, logs, baks.
import { readdirSync, statSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

function* walk(dir: string): Generator<string> {
  let entries: string[] = [];
  try { entries = readdirSync(dir); } catch { return; }
  for (const e of entries) {
    const p = join(dir, e);
    let st;
    try { st = statSync(p); } catch { continue; }
    if (st.isDirectory()) {
      if (SKIP_DIRS.includes(e)) continue;
      yield* walk(p);
    } else yield p;
  }
}

const ROOT = "/home/toxic/estate";
// live estate surface only — ranch/* are independent subrepos with their own naming
const SUBDIRS = ["docs", "skills", "scripts", "config", "agents", "manor", "services", "stack", "tools", "python", "infra", "profiles", "migration", "crews", ".github", ".code-scalpel", "audit", "brain", "corral", "deploy", "devices", "gear", "keypool", "lib", "nix", "packages", "pdfshield", "research", "src", "standalone", "tests", "trail-runner", "ts", "work", "killer-features", "completion-audit", "bridge", "pi-skills", "six-task-loop", "skills-hub", "mesh", "hatch", "bin", "ast-grep-rules", "hooks", "deploy", "test", "types", "corral", "devices", "gear", "infra"];
const ROOT_FILES = ["pitchfork.toml", "mise.toml", "AGENTS.md", "README.md", "TASKS.md", "SOUL.md", "IDENTITY.md", "projects.toml", "AUDIT.md", "MERGE-DECISIONS.md", ".Estate-integration.ts", ".Estate-integration.json", ".env.example", ".envrc"];
const PRESERVE_TOKENS = [
  "Estate-exporter",
  "Estate-stream-broker",
  "Estate-swap",
  "Estate-router",
];
const SKIP_DIRS = [
  ".git", "node_modules", "var", "salvage", "scratch", "archives",
  "archive", "__pycache__", "vendored", "run", "logs", "log", "sessions",
  "memories", "cache", "plugins", "qdrant_data", "grafana", "prometheus",
  ".prometheus", "state", "engines", "venv",
];
const SKIP_EXT = [".pyc", ".log", ".bak", ".png", ".jpg", ".woff", ".bin", ".sqlite"];
const SKIP_FILES = ["rename-Estate-to-estate.ts"];

function lineRefsExistingEstatePath(line: string): boolean {
  // find path-ish tokens containing "Estate" that exist on disk
  const re = /[\w.$~\/-]*Estate[\w.-]*/gi;
  for (const m of line.matchAll(re)) {
    const tok = m[0];
    const cands = [
      tok.replace(/^~\/?/, "/home/toxic/").replace(/^\$HOME\/?/, "/home/toxic/"),
      tok.replace(/^\.?\/?estate\/?/, "/home/toxic/estate/"),
      `/home/toxic/estate/${tok.replace(/^\.\//, "")}`,
    ];
    for (const c of cands) {
      if (c.includes("Estate") && existsSync(c)) return true;
    }
  }
  return false;
}

let changedFiles = 0, changedLines = 0, preservedLines = 0;
const preserved: string[] = [];

const targets: string[] = ROOT_FILES.map((f) => join(ROOT, f)).filter((p) => existsSync(p));
for (const d of SUBDIRS) {
  const dp = join(ROOT, d);
  if (existsSync(dp)) for (const p of walk(dp)) targets.push(p);
}

for (const p of targets) {
  const extOk = [".md", ".toml", ".sh", ".ts", ".js", ".yml", ".yaml", ".json", ".py", ".env", ".txt"].some((e) => p.endsWith(e));
  if (!extOk) continue;
  if (SKIP_EXT.some((e) => p.endsWith(e))) continue;
  if (SKIP_FILES.some((f) => p.endsWith(f))) continue;
  if (p.includes(".bak")) continue;
  if (p.endsWith(".env") || p.includes(".env") || p.includes(".secrets")) continue;
  let text: string;
  try {
    text = new TextDecoder().decode(readFileSync(p));
  } catch { console.log(`SKIP (read): ${p}`); continue; }
  if (!/Estate/i.test(text)) continue;
  if (text.includes("\0")) continue; // binary guard

  const isPitchfork = p.endsWith("pitchfork.toml");
  const out: string[] = [];
  let fc = 0;
  for (const line of text.split("\n")) {
    if (!/Estate/i.test(line)) { out.push(line); continue; }
    if (PRESERVE_TOKENS.some((t) => line.includes(t)) || lineRefsExistingEstatePath(line)) {
      preservedLines++;
      preserved.push(`${p.replace(ROOT + "/", "")}: ${line.trim().slice(0, 100)}`);
      out.push(line);
      continue;
    }
    const nl = line
      .replace(/ESTATE/g, "ESTATE")
      .replace(/Estate/g, "Estate")
      .replace(/Estate/g, "estate");
    if (isPitchfork && /\[daemons\.estate[\w-]*\]/.test(nl) === false) { /* fine */ }
    if (nl !== line) { fc++; }
    out.push(nl);
  }
  if (fc > 0) {
    try { writeFileSync(p, out.join("\n")); } catch (e) { console.log(`SKIP (write): ${p} ${e}`); continue; }
    changedFiles++; changedLines += fc;
    console.log(`${p.replace(ROOT + "/", "")}  (${fc} lines)`);
  }
}
console.log(`\nDONE: ${changedFiles} files, ${changedLines} lines changed, ${preservedLines} lines preserved`);
if (preserved.length) console.log(`\nPreserved (runtime-sensitive / existing paths):\n${preserved.map((l) => "  " + l).join("\n")}`);
