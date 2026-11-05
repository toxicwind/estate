/**
 * coverage-gate.ts — REAL coverage enforcement for the eternal fork.
 * Mirrors kairos coverage-gate.ts (AGENTS.md §1.9): runs the suite with lcov
 * output, filters to the fork's OWN scraper src, computes line + function
 * coverage, exits non-zero if either is below 90%. Bun's [coverage] thresholds
 * are decorative — this is the gate.
 *
 * The fork is a Python Kodi addon, so the suite runs under python coverage
 * (the estate's python tools are tested this way). The `.live.ts` twin
 * exercises the real scraper endpoint.
 *
 * Usage: bun scripts/coverage-gate.ts  (from addons/eternal)
 */
import { spawnSync } from "node:child_process";
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const TARGET_LINES = 90;
const TARGET_FUNCS = 90;
const COV = join(process.cwd(), "coverage");
const LCOV = join(COV, "lcov.info");

// Resolve a python that has the `coverage` module: prefer a local .venv, then
// the ephemeral covenv, then system python3 (must have coverage installed).
function resolvePython(): string {
  const candidates = [
    join(process.cwd(), ".venv", "bin", "python"),
    "/tmp/kappa/covenv/bin/python",
    "python3",
  ];
  for (const c of candidates) {
    const probe = spawnSync(c, ["-c", "import coverage"], { stdio: "ignore" });
    if (probe.status === 0) return c;
  }
  console.error("[eternal coverage] no python with `coverage` module found. Install: python3 -m venv .venv && .venv/bin/pip install coverage");
  process.exit(1);
}
const PY = resolvePython();

// Run the python suite with lcov output. Scope to the scraper modules the
// int(None) fix touches (the fork's own src) — not the whole 60-scraper
// package, which would dilute the gate with network-only scrapers.
const run = spawnSync(
  PY,
  [
    "-m", "coverage", "run", "--branch",
    "--source=eternalscrapers.providers.torrents.torrentfunk",
    "-m", "unittest", "discover", "-s", "tests",
  ],
  { cwd: process.cwd(), stdio: ["inherit", "inherit", "inherit"] },
);
if (run.status !== 0) {
  console.error(`[eternal coverage] test suite FAILED (exit ${run.status})`);
  process.exit(run.status ?? 1);
}

// Run the .live.ts twin (real scraper endpoint, AGENTS.md §1.9).
const live = spawnSync("bun", ["run", join("tests", "eternal.live.ts")], {
  cwd: process.cwd(), stdio: ["inherit", "inherit", "inherit"],
});
if (live.status !== 0) {
  console.error(`[eternal coverage] live twin FAILED (exit ${live.status})`);
  process.exit(live.status ?? 1);
}
const lcov = spawnSync(
  PY, ["-m", "coverage", "lcov", "-o", LCOV],
  { cwd: process.cwd(), stdio: ["inherit", "inherit", "inherit"] },
);
if (lcov.status !== 0 || !existsSync(LCOV)) {
  console.error(`[eternal coverage] no ${LCOV} produced — cannot gate`);
  process.exit(1);
}

interface FileCov { lf: number; lh: number; fnf: number; fnh: number }
const files = new Map<string, FileCov>();
let cur: string | null = null;
for (const line of readFileSync(LCOV, "utf8").split("\n")) {
  if (line.startsWith("SF:")) {
    cur = line.slice(3).trim();
    files.set(cur, { lf: 0, lh: 0, fnf: 0, fnh: 0 });
  } else if (line.startsWith("LF:")) {
    if (cur) files.get(cur)!.lf = Number(line.slice(3));
  } else if (line.startsWith("LH:")) {
    if (cur) files.get(cur)!.lh = Number(line.slice(3));
  } else if (line.startsWith("FNF:")) {
    if (cur) files.get(cur)!.fnf = Number(line.slice(4));
  } else if (line.startsWith("FNH:")) {
    if (cur) files.get(cur)!.fnh = Number(line.slice(4));
  }
}

// Filter to the fork's OWN scraper src (resources/lib/eternalscrapers).
const isOwn = (p: string) => p.includes("eternalscrapers");
const src = [...files.entries()].filter(([p]) => isOwn(p));
const tot = src.reduce(
  (a, [, c]) => ({ lf: a.lf + c.lf, lh: a.lh + c.lh, fnf: a.fnf + c.fnf, fnh: a.fnh + c.fnh }),
  { lf: 0, lh: 0, fnf: 0, fnh: 0 },
);
const linePct = tot.lf ? (tot.lh / tot.lf) * 100 : 100;
const funcPct = tot.fnf ? (tot.fnh / tot.fnf) * 100 : 100;

console.log(
  `\n[eternal coverage] eternalscrapers lines ${linePct.toFixed(1)}% (${tot.lh}/${tot.lf})  funcs ${funcPct.toFixed(1)}% (${tot.fnh}/${tot.fnf})  target ${TARGET_LINES}%/${TARGET_FUNCS}%`,
);

let fail = false;
if (linePct < TARGET_LINES) {
  console.error(`  FAIL: line coverage ${linePct.toFixed(1)}% < ${TARGET_LINES}%`);
  fail = true;
}
if (funcPct < TARGET_FUNCS) {
  console.error(`  FAIL: function coverage ${funcPct.toFixed(1)}% < ${TARGET_FUNCS}%`);
  fail = true;
}
if (fail) {
  console.error(`[eternal coverage] gate NOT met — add tests before this passes.`);
  process.exit(1);
}
console.log(`[eternal coverage] gate met ✓`);
process.exit(0);