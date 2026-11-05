/**
 * coverage-gate.ts — REAL coverage enforcement for @geode/eternal-scraper.
 * Mirrors kairos coverage-gate.ts (AGENTS.md §1.9): runs the suite with lcov,
 * filters to this package's OWN src/, gates line+function at 90%, and runs the
 * .live.ts twin (real router round-trip). Bun's [coverage] thresholds are
 * decorative — this is the gate.
 *
 * Usage: bun scripts/coverage-gate.ts  (from scraper-lib)
 */
import { spawnSync } from "node:child_process"
import { readFileSync, existsSync } from "node:fs"
import { join } from "node:path"

const TARGET_LINES = 90
const TARGET_FUNCS = 90
const LCOV = join(process.cwd(), "coverage", "lcov.info")

const run = spawnSync("bun", ["test", "--coverage", "--coverage-reporter=lcov", "src/"], {
  cwd: process.cwd(), stdio: ["inherit", "inherit", "inherit"],
})
if (run.status !== 0) {
  console.error(`[scraper-lib coverage] test suite FAILED (exit ${run.status})`)
  process.exit(run.status ?? 1)
}

const live = spawnSync("bun", ["run", "src/llm.live.ts"], {
  cwd: process.cwd(), stdio: ["inherit", "inherit", "inherit"],
})
if (live.status !== 0) {
  console.error(`[scraper-lib coverage] live twin FAILED (exit ${live.status})`)
  process.exit(live.status ?? 1)
}

if (!existsSync(LCOV)) {
  console.error(`[scraper-lib coverage] no ${LCOV} produced — cannot gate`)
  process.exit(1)
}

interface FileCov { lf: number; lh: number; fnf: number; fnh: number }
const files = new Map<string, FileCov>()
let cur: string | null = null
for (const line of readFileSync(LCOV, "utf8").split("\n")) {
  if (line.startsWith("SF:")) { cur = line.slice(3).trim(); files.set(cur, { lf: 0, lh: 0, fnf: 0, fnh: 0 }) }
  else if (line.startsWith("LF:")) { if (cur) files.get(cur)!.lf = Number(line.slice(3)) }
  else if (line.startsWith("LH:")) { if (cur) files.get(cur)!.lh = Number(line.slice(3)) }
  else if (line.startsWith("FNF:")) { if (cur) files.get(cur)!.fnf = Number(line.slice(4)) }
  else if (line.startsWith("FNH:")) { if (cur) files.get(cur)!.fnh = Number(line.slice(4)) }
}
const isOwn = (p: string) => p.endsWith("/src/llm.ts") || p === "src/llm.ts" || p.includes("/src/llm.ts")
const src = [...files.entries()].filter(([p]) => isOwn(p))
const tot = src.reduce((a, [, c]) => ({ lf: a.lf + c.lf, lh: a.lh + c.lh, fnf: a.fnf + c.fnf, fnh: a.fnh + c.fnh }), { lf: 0, lh: 0, fnf: 0, fnh: 0 })
const linePct = tot.lf ? (tot.lh / tot.lf) * 100 : 100
const funcPct = tot.fnf ? (tot.fnh / tot.fnf) * 100 : 100
console.log(`\n[scraper-lib coverage] src/ lines ${linePct.toFixed(1)}% (${tot.lh}/${tot.lf})  funcs ${funcPct.toFixed(1)}% (${tot.fnh}/${tot.fnf})  target ${TARGET_LINES}%/${TARGET_FUNCS}%`)
let fail = false
if (linePct < TARGET_LINES) { console.error(`  FAIL: line coverage ${linePct.toFixed(1)}% < ${TARGET_LINES}%`); fail = true }
if (funcPct < TARGET_FUNCS) { console.error(`  FAIL: function coverage ${funcPct.toFixed(1)}% < ${TARGET_FUNCS}%`); fail = true }
if (fail) { console.error(`[scraper-lib coverage] gate NOT met — add tests before this passes.`); process.exit(1) }
console.log(`[scraper-lib coverage] gate met ✓`)
process.exit(0)