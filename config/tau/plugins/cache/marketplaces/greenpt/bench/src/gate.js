#!/usr/bin/env node
"use strict";
// Regression gate: compare a candidate result stamp against a reference stamp and
// exit non-zero if any shared variant regressed. Makes "SKILL.md changed" mean
// "the numbers were re-verified", instead of hoping someone eyeballs report.md.
//
//   node src/gate.js <candidate-stamp> <reference-stamp>
//
// Thresholds (env):
//   GATE_TESTS   max allowed test-pass drop, fraction        (default 0.02)
//   GATE_JUDGE   max allowed judge-median drop, points       (default 5)
//   GATE_OUTPUT  max allowed shrink of a variant's output-vs-baseline
//                reduction, fraction points                  (default 0.10)
//   GATE_TURNS   max allowed growth in paired median agent turns, fraction
//                (default 0.10; only checked on stamps that record `iterations`)
//
// The output rule compares the PAIRED per-task median reduction, not a ratio of arm
// totals — one long task must not be able to mask a regression on the other twenty.
//
// Only variants present in BOTH stamps are compared; judge/output rules need a
// baseline in both. Mock stamps gate against mock, live against live — mixing
// the two is meaningless and rejected.

const fs = require("fs");
const path = require("path");
const { aggregate } = require("./report");
const { pairedDelta } = require("./paired");

const GATE_TESTS = Number(process.env.GATE_TESTS ?? 0.02);
const GATE_JUDGE = Number(process.env.GATE_JUDGE ?? 5);
const GATE_OUTPUT = Number(process.env.GATE_OUTPUT ?? 0.1);
const GATE_TURNS = Number(process.env.GATE_TURNS ?? 0.1);

const [cand, ref] = process.argv.slice(2);
if (!cand || !ref) {
  console.error("usage: node src/gate.js <candidate-stamp> <reference-stamp>");
  process.exit(2);
}

function load(stamp) {
  const file = path.join(__dirname, "..", "results", stamp, "results.json");
  const { meta, records } = JSON.parse(fs.readFileSync(file, "utf8"));
  const variants = [...new Set(records.map((r) => r.variant))];
  return { meta, records, rows: aggregate(records, variants, meta.model), variants };
}

const c = load(cand);
const r = load(ref);
if (Boolean(c.meta.mock) !== Boolean(r.meta.mock)) {
  console.error(`refusing to gate mock against live (${cand} mock=${!!c.meta.mock}, ${ref} mock=${!!r.meta.mock})`);
  process.exit(2);
}

// Control arm: `baseline` in the single-call bench, `off` in the Cline harness bench.
const controlOf = (variants) => (variants.includes("baseline") ? "baseline" : variants.includes("off") ? "off" : null);

// Paired per-task output reduction, e.g. honey at -29% -> 0.29; null without a control.
function reduction(s, v) {
  const base = controlOf(s.variants);
  if (!base || v === base) return null;
  const d = pairedDelta(s.records, { variant: v, baseline: base, metric: (x) => x.usage.output || 0 });
  return d.medianRel == null ? null : -d.medianRel;
}

// Paired per-task growth in agent turns. Only the harness bench records `iterations`.
function turns(s, v) {
  const base = controlOf(s.variants);
  if (!base || v === base) return null;
  const d = pairedDelta(s.records, { variant: v, baseline: base, metric: (x) => x.iterations });
  return d.n ? d.medianRel : null;
}

const shared = c.variants.filter((v) => r.variants.includes(v));
const failures = [];
const lines = [
  `gate: ${cand} vs ${ref} (model ${c.meta.model} vs ${r.meta.model})`,
  `| Variant | Tests Δ | Judge Δ | Paired out-vs-base Δ | Turns Δ |`,
  `|---------|--------:|--------:|---------------------:|--------:|`,
];

for (const v of shared) {
  const cv = c.rows[v];
  const rv = r.rows[v];
  const testsD = cv.passRate - rv.passRate;
  const judgeD = cv.judge - rv.judge;
  const cRed = reduction(c, v);
  const rRed = reduction(r, v);
  const redD = cRed != null && rRed != null ? cRed - rRed : null;
  const cTurns = turns(c, v);
  const rTurns = turns(r, v);
  const turnsD = cTurns != null && rTurns != null ? cTurns - rTurns : null;

  if (testsD < -GATE_TESTS) failures.push(`${v}: tests ${(rv.passRate * 100).toFixed(0)}% -> ${(cv.passRate * 100).toFixed(0)}%`);
  if (judgeD < -GATE_JUDGE) failures.push(`${v}: judge ${rv.judge.toFixed(0)} -> ${cv.judge.toFixed(0)}`);
  if (redD != null && redD < -GATE_OUTPUT)
    failures.push(`${v}: paired output reduction ${(rRed * 100).toFixed(0)}% -> ${(cRed * 100).toFixed(0)}%`);
  if (turnsD != null && turnsD > GATE_TURNS)
    failures.push(`${v}: agent turns ${signed(rTurns)} -> ${signed(cTurns)} vs control (retry tax)`);

  lines.push(
    `| ${v} | ${(testsD * 100).toFixed(0)}pt | ${judgeD.toFixed(1)} | ${redD == null ? "—" : `${(redD * 100).toFixed(0)}pt`} | ${turnsD == null ? "—" : `${(turnsD * 100).toFixed(0)}pt`} |`
  );
}

function signed(x) {
  return `${x >= 0 ? "+" : ""}${(x * 100).toFixed(0)}%`;
}

console.log(lines.join("\n"));
if (failures.length) {
  console.error(`\nREGRESSION (thresholds: tests ${GATE_TESTS}, judge ${GATE_JUDGE}, output ${GATE_OUTPUT}, turns ${GATE_TURNS}):`);
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}
console.log(`\nOK — no regression in ${shared.length} shared variants`);
