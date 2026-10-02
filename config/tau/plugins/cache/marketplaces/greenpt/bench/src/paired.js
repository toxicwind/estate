"use strict";
// Paired per-task statistics.
//
// Arm totals are outlier-dominated: one long web task can drive a whole-suite
// ratio, so `sum(honey)/sum(baseline)` is not the number an independent paired
// benchmark would reproduce. Everything here is computed per task, paired against
// the baseline, then reduced with a median plus a significance test.
//
// Runs collapse by median (not mean) so a single bad sample doesn't move a cell.
// A task missing from either arm is excluded from BOTH.

const median = (xs) => {
  if (!xs.length) return NaN;
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};

// {task: median-across-runs} for one variant
function perTask(records, variant, metric) {
  const acc = {};
  for (const r of records) {
    if (r.variant !== variant) continue;
    const v = metric(r);
    if (v == null || !Number.isFinite(v)) continue;
    (acc[r.task] ||= []).push(v);
  }
  return Object.fromEntries(Object.entries(acc).map(([t, xs]) => [t, median(xs)]));
}

function pairs(records, variant, baseline, metric) {
  const a = perTask(records, variant, metric);
  const b = perTask(records, baseline, metric);
  return Object.keys(a)
    .filter((t) => t in b)
    .sort()
    .map((t) => ({ task: t, a: a[t], b: b[t] }));
}

// Φ(z) via the A&S 7.1.26 erf approximation (|error| < 1.5e-7) — ample for a p-value.
function phi(z) {
  const s = z < 0 ? -1 : 1;
  const x = Math.abs(z) / Math.SQRT2;
  const t = 1 / (1 + 0.3275911 * x);
  const y =
    1 -
    ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) *
      t *
      Math.exp(-x * x);
  return 0.5 * (1 + s * y);
}

// Wilcoxon signed-rank, two-sided, normal approximation with tie + continuity
// correction. Returns null below n=6: the exact two-sided p can't reach 0.05 there,
// so a number would be theatre.
function wilcoxon(diffs) {
  const d = diffs.filter((x) => x !== 0);
  const n = d.length;
  if (n < 6) return null;

  // average ranks over ties in |d|
  const idx = d.map((x, i) => i).sort((i, j) => Math.abs(d[i]) - Math.abs(d[j]));
  const rank = new Array(n);
  const tieGroups = [];
  for (let i = 0; i < n; ) {
    let j = i;
    while (j + 1 < n && Math.abs(d[idx[j + 1]]) === Math.abs(d[idx[i]])) j++;
    const avg = (i + j) / 2 + 1;
    for (let k = i; k <= j; k++) rank[idx[k]] = avg;
    if (j > i) tieGroups.push(j - i + 1);
    i = j + 1;
  }

  const wPlus = d.reduce((a, x, i) => a + (x > 0 ? rank[i] : 0), 0);
  const mu = (n * (n + 1)) / 4;
  const tieAdj = tieGroups.reduce((a, t) => a + (t ** 3 - t), 0) / 48;
  const sigma = Math.sqrt((n * (n + 1) * (2 * n + 1)) / 24 - tieAdj);
  if (!sigma) return 1;

  const z = (Math.abs(wPlus - mu) - 0.5) / sigma; // continuity correction toward mu
  return Math.min(1, 2 * (1 - phi(Math.max(z, 0))));
}

const choose = (n, k) => {
  let c = 1;
  for (let i = 0; i < k; i++) c = (c * (n - i)) / (i + 1);
  return c;
};

// Exact two-sided binomial sign test at p=0.5 over the non-ties.
function signTest(lower, higher) {
  const n = lower + higher;
  if (!n) return null;
  const m = Math.min(lower, higher);
  let tail = 0;
  for (let i = 0; i <= m; i++) tail += choose(n, i);
  return Math.min(1, (2 * tail) / 2 ** n);
}

// metric: (record) => number. Direction is left to the caller — `lower`/`higher`
// count how many tasks the variant came in under/over baseline, whatever that means
// for the metric.
//
//   medianRel  median of per-task (variant/baseline - 1); the headline "+7.6%" shape
//   medianAbs  median of per-task (variant - baseline), in the metric's own units
//   p          Wilcoxon signed-rank on the absolute differences (null when n < 6)
//   pSign      exact sign test over non-ties — the right test for ordinal judge scores
function pairedDelta(records, { variant, baseline, metric }) {
  const ps = pairs(records, variant, baseline, metric);
  const diffs = ps.map((p) => p.a - p.b);
  const rels = ps.filter((p) => p.b !== 0).map((p) => p.a / p.b - 1);
  const lower = diffs.filter((d) => d < 0).length;
  const higher = diffs.filter((d) => d > 0).length;

  return {
    n: ps.length,
    medianRel: rels.length ? median(rels) : null,
    medianAbs: ps.length ? median(diffs) : null,
    p: wilcoxon(diffs),
    pSign: signTest(lower, higher),
    lower,
    higher,
    ties: diffs.length - lower - higher,
    tasks: ps.map((p) => p.task),
  };
}

module.exports = { pairedDelta, perTask, median, wilcoxon, signTest, phi };
