#!/usr/bin/env node
"use strict";
// Aggregate per-(variant,task,run) records into the headline tables + a markdown report.
//
// Two views, and the order matters:
//   pairedTable() — the headline. Per-task paired deltas vs baseline, reduced with a
//                   median + Wilcoxon / sign test. This is what an independent paired
//                   benchmark reproduces.
//   table()       — arm totals. Kept for continuity and absolute volumes, but a ratio
//                   of sums is outlier-dominated, so it is no longer the claim.

const fs = require("fs");
const path = require("path");
const { pairedDelta } = require("./paired");

const pricing = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "pricing.json"), "utf8"));

function rateFor(model) {
  const hit = pricing.rates.find((r) => model.toLowerCase().includes(r.match));
  return hit || pricing._default;
}

// Cost by token class. Cache CREATION is a real charge (Anthropic bills it at 1.25x
// input) — dropping it made the skill prompt look free on the turn that installs it.
function dollars(model, { input = 0, cache_write = 0, cache_read = 0, output = 0 }) {
  const r = rateFor(model);
  const cw = r.cache_write ?? pricing._default.cache_write;
  const cr = r.cache_read ?? pricing._default.cache_read;
  return (input * r.in + cache_write * r.in * cw + cache_read * r.in * cr + output * r.out) / 1e6;
}

// Every input token billed at full freight — the first turn of a session, or any run
// where the skill prompt never gets a cache hit.
function dollarsCold(model, u) {
  return dollars(model, {
    input: (u.input || 0) + (u.cache_write || 0) + (u.cache_read || 0),
    output: u.output || 0,
  });
}

// "New input" = fresh + cache-creation. The only input class a prompt-level skill can
// move, and the class where its own system prompt COSTS. Cache reads are excluded:
// they bill at a tenth and dominate a long session regardless of what the skill does.
const newInput = (u) => (u.input || 0) + (u.cache_write || 0);

const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
const stdev = (xs) => {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  return Math.sqrt(mean(xs.map((x) => (x - m) ** 2)));
};
const pct = (x) => `${(x * 100).toFixed(0)}%`;
const signedPct = (x) => `${x >= 0 ? "+" : ""}${(x * 100).toFixed(0)}%`;

// A cell the model REFUSED (stop_reason "refusal" — seen on Fable 5 with bare task
// prompts) measures the safety layer, not the skill. Refused records are excluded from
// every statistic; a task whose arm loses all its runs then drops from pairing on the
// existing missing-arm rule. Never silent: callers print refusalSummary().
const dropRefusals = (records) => records.filter((r) => r.stop_reason !== "refusal");
function refusalSummary(records) {
  const ref = records.filter((r) => r.stop_reason === "refusal");
  if (!ref.length) return null;
  const by = {};
  for (const r of ref) (by[`${r.variant}/${r.task}`] ||= 0), (by[`${r.variant}/${r.task}`] += 1);
  return `${ref.length} refused cell(s) excluded: ${Object.entries(by)
    .map(([k, n]) => `${k}×${n}`)
    .join(", ")}`;
}

// records: [{variant, task, run, usage:{input,output,cache_read,cache_write}, passed, judge, gco2}]
function aggregate(records, order, model) {
  records = dropRefusals(records);
  const byVariant = {};
  for (const r of records) (byVariant[r.variant] ||= []).push(r);

  const rows = {};
  for (const v of order) {
    const rs = byVariant[v] || [];
    const sum = (f) => rs.reduce((a, r) => a + f(r), 0);
    const u = {
      input: sum((r) => r.usage.input || 0),
      cache_write: sum((r) => r.usage.cache_write || 0),
      cache_read: sum((r) => r.usage.cache_read || 0),
      output: sum((r) => r.usage.output || 0),
    };
    const judges = rs.filter((r) => r.judge != null).map((r) => r.judge);
    rows[v] = {
      variant: v,
      n: rs.length,
      passRate: mean(rs.map((r) => (r.passed ? 1 : 0))),
      judge: mean(judges),
      judgeSd: stdev(judges), // per-record spread: a small judge gap inside ±sd is noise, not a win
      input: u.input,
      cacheWrite: u.cache_write,
      cacheIn: u.cache_read,
      newInput: newInput(u),
      output: u.output,
      gco2: sum((r) => r.gco2 || 0),
      usd: dollars(model, u), // cached steady state
      usdCold: dollarsCold(model, u), // cold session: skill prompt billed fresh
    };
  }
  return rows;
}

// ---- headline: paired per-task deltas -------------------------------------------

const METRICS = (model) => ({
  output: (r) => r.usage.output || 0,
  loc: (r) => (r.loc == null ? null : r.loc), // Lever 1 direct; null on relay tasks (no code)
  newInput: (r) => newInput(r.usage),
  cost: (r) => dollars(model, r.usage),
  judge: (r) => (r.judge == null ? null : r.judge),
});

const p = (x) => (x == null ? "—" : x < 0.001 ? "<0.001" : x.toFixed(3));
// A delta whose p misses 0.05 is a tie, and gets said so rather than quoted as a win.
const delta = (d) => (d.medianRel == null ? "—" : `${signedPct(d.medianRel)}${d.p != null && d.p >= 0.05 ? " (ns)" : ""}`);

function paired(records, order, model, baseline = "baseline") {
  records = dropRefusals(records);
  const m = METRICS(model);
  const out = {};
  for (const v of order) {
    if (v === baseline) continue;
    out[v] = {
      output: pairedDelta(records, { variant: v, baseline, metric: m.output }),
      loc: pairedDelta(records, { variant: v, baseline, metric: m.loc }),
      newInput: pairedDelta(records, { variant: v, baseline, metric: m.newInput }),
      cost: pairedDelta(records, { variant: v, baseline, metric: m.cost }),
      judge: pairedDelta(records, { variant: v, baseline, metric: m.judge }),
    };
  }
  return out;
}

function pairedTable(records, order, model, baseline = "baseline") {
  const d = paired(records, order, model, baseline);
  const header =
    "| Variant | n | Δ output | p | Δ LOC | p | Δ new-input | p | Δ cost | p | Judge W/L/T | sign p |\n" +
    "|---------|--:|---------:|--:|------:|--:|------------:|--:|-------:|--:|------------:|-------:|";
  const lines = order
    .filter((v) => d[v] && d[v].output.n)
    .map((v) => {
      const x = d[v];
      const j = x.judge;
      // "wins" = variant scored HIGHER than baseline on that task
      const wlt = `${j.higher}/${j.lower}/${j.ties}`;
      return `| ${v} | ${x.output.n} | ${delta(x.output)} | ${p(x.output.p)} | ${delta(x.loc)} | ${p(x.loc.p)} | ${delta(x.newInput)} | ${p(x.newInput.p)} | ${delta(x.cost)} | ${p(x.cost.p)} | ${wlt} | ${p(j.pSign)} |`;
    });
  return [header, ...lines].join("\n");
}

function table(rows, order) {
  const base = rows.baseline;
  const rel = (x, b) => (b ? x / b - 1 : 0);
  const qVs = (x, b) => (b ? x / b : 0);

  const header =
    "| Variant | Tests pass | Judge ±sd | Judge vs base | Output tok | Output vs base | New input tok | $ (cached) | $ (cold) | CO₂ (g) |\n" +
    "|---------|-----------:|----------:|--------------:|-----------:|---------------:|--------------:|-----------:|---------:|--------:|";
  const lines = order
    .filter((v) => rows[v] && rows[v].n)
    .map((v) => {
      const r = rows[v];
      const q = base && base.judge ? pct(qVs(r.judge, base.judge)) : "—";
      const ov = base ? signedPct(rel(r.output, base.output)) : "—";
      const j = `${r.judge.toFixed(0)} ±${r.judgeSd.toFixed(0)}`;
      return `| ${v} | ${pct(r.passRate)} | ${j} | ${q} | ${r.output.toLocaleString()} | ${ov} | ${r.newInput.toLocaleString()} | $${r.usd.toFixed(3)} | $${r.usdCold.toFixed(3)} | ${r.gco2.toFixed(1)} |`;
    });
  return [header, ...lines].join("\n");
}

module.exports = { aggregate, table, paired, pairedTable, dollars, newInput, refusalSummary };

// ---- CLI: recompute a committed stamp offline, no API spend ----------------------
//
//   node src/report.js --stamp full-opus48            # whole suite
//   node src/report.js --stamp full-opus48 --by-type  # per tier (code / web / relay)
if (require.main === module) {
  const i = process.argv.indexOf("--stamp");
  const stamp = i >= 0 ? process.argv[i + 1] : null;
  if (!stamp) {
    console.error("usage: node src/report.js --stamp <stamp> [--by-type]");
    process.exit(2);
  }
  const file = path.join(__dirname, "..", "results", stamp, "results.json");
  const { meta, records } = JSON.parse(fs.readFileSync(file, "utf8"));
  const variants = [...new Set(records.map((r) => r.variant))];
  console.log(`${stamp} · model ${meta.model} · runs ${meta.runs}${meta.mock ? " · MOCK" : ""}\n`);

  if (process.argv.includes("--by-type")) {
    for (const t of [...new Set(records.map((r) => r.type))]) {
      const rs = records.filter((r) => r.type === t);
      const rows = aggregate(rs, variants, meta.model);
      const tasks = new Set(rs.map((r) => r.task)).size;
      console.log(`### ${t} (${tasks} tasks)\n`);
      console.log(pairedTable(rs, variants, meta.model));
      console.log(`\ntests: ${variants.map((v) => `${v} ${(rows[v].passRate * 100).toFixed(0)}%`).join(" · ")}\n`);
    }
    return;
  }

  const refNote = refusalSummary(records);
  if (refNote) console.log(`⚠ ${refNote}\n`);
  console.log("PAIRED (per-task median vs baseline, Wilcoxon; judge by sign test)\n");
  console.log(pairedTable(records, variants, meta.model) + "\n");
  console.log("ARM TOTALS (volumes; the ratio column is outlier-sensitive)\n");
  console.log(table(aggregate(records, variants, meta.model), variants));
}
