#!/usr/bin/env node
// Paired per-task statistics (bench/src/paired.js). The Wilcoxon anchors are exact
// two-sided p-values from full 2^n sign enumeration under H0 — computed independently,
// not read back from this implementation. The normal approximation is allowed to sit
// slightly ABOVE the exact value (conservative) but not below it by more than the
// stated tolerance.

const test = require('node:test');
const assert = require('node:assert/strict');
const { pairedDelta, perTask, median, wilcoxon, signTest, phi } = require('../bench/src/paired');

test('median: odd, even, single, empty', () => {
  assert.equal(median([3, 1, 2]), 2);
  assert.equal(median([4, 1, 3, 2]), 2.5);
  assert.equal(median([7]), 7);
  assert.ok(Number.isNaN(median([])));
});

test('phi: known normal CDF values', () => {
  assert.ok(Math.abs(phi(0) - 0.5) < 1e-9);
  assert.ok(Math.abs(phi(1.96) - 0.975) < 1e-4);
  assert.ok(Math.abs(phi(-1.645) - 0.05) < 1e-4);
});

test('wilcoxon: matches exact enumeration on a no-tie sample (exact p = 0.7695)', () => {
  const p = wilcoxon([-5, 3, -8, 12, -1, 7, -14, 2, -9, 4]);
  assert.ok(Math.abs(p - 0.76953125) < 0.02, `got ${p}`);
});

test('wilcoxon: strongly one-sided sample is significant (exact p = 0.00098)', () => {
  const p = wilcoxon([-40, -32, -55, -8, -61, -27, -44, 3, -19, -50, -36, -12]);
  assert.ok(p < 0.01, `got ${p}`);
  assert.ok(p >= 0.00098, 'approximation must not undercut the exact p');
});

test('wilcoxon: tie correction on repeated |d| (exact p = 0.5625)', () => {
  const p = wilcoxon([-2, -2, -2, 2, -2, -2, -2, 3]);
  assert.ok(p > 0.35 && p < 0.75, `got ${p}`);
});

test('wilcoxon: zeros are dropped, and n<6 non-ties yields null (no fake power)', () => {
  assert.equal(wilcoxon([1, -1, 2, -2, 3]), null);
  assert.equal(wilcoxon([1, -1, 2, -2, 3, 0, 0, 0]), null); // zeros don't buy n
  assert.equal(wilcoxon([]), null);
  assert.equal(wilcoxon([0, 0, 0, 0, 0, 0, 0, 0]), null);
});

test('wilcoxon: all differences equal and same sign -> smallest attainable p', () => {
  const p = wilcoxon([-3, -3, -3, -3, -3, -3, -3, -3]);
  assert.ok(p < 0.05, `got ${p}`);
});

test('signTest: exact two-sided binomial', () => {
  assert.equal(signTest(5, 0), 2 / 32);
  assert.equal(signTest(0, 10), 2 / 1024);
  assert.equal(signTest(5, 5), 1);
  assert.equal(signTest(0, 0), null); // all ties -> no test
});

const rec = (variant, task, run, output) => ({ variant, task, run, usage: { output } });

test('perTask: collapses runs by median, not mean', () => {
  const records = [rec('honey', 't', 0, 10), rec('honey', 't', 1, 12), rec('honey', 't', 2, 900)];
  assert.deepEqual(perTask(records, 'honey', (r) => r.usage.output), { t: 12 });
});

test('pairedDelta: per-task relative median, not a ratio of arm totals', () => {
  // t3 is a huge task where honey saves little; arm totals would be dominated by it.
  const records = [
    rec('baseline', 't1', 0, 100), rec('honey', 't1', 0, 50),
    rec('baseline', 't2', 0, 100), rec('honey', 't2', 0, 50),
    rec('baseline', 't3', 0, 10000), rec('honey', 't3', 0, 9900),
  ];
  const d = pairedDelta(records, { variant: 'honey', baseline: 'baseline', metric: (r) => r.usage.output });

  assert.equal(d.n, 3);
  assert.equal(d.medianRel, -0.5); // paired: honey halves the typical task
  assert.equal(d.lower, 3);
  assert.equal(d.higher, 0);

  const armRatio = (50 + 50 + 9900) / (100 + 100 + 10000) - 1;
  assert.ok(armRatio > -0.03, 'arm-total ratio is dominated by t3 — that is the bug being fixed');
});

test('pairedDelta: a task missing from either arm is excluded from both', () => {
  const records = [
    rec('baseline', 't1', 0, 100), rec('honey', 't1', 0, 50),
    rec('baseline', 't2', 0, 100), // honey never ran t2
    rec('honey', 't3', 0, 10), // baseline never ran t3
  ];
  const d = pairedDelta(records, { variant: 'honey', baseline: 'baseline', metric: (r) => r.usage.output });
  assert.deepEqual(d.tasks, ['t1']);
  assert.equal(d.n, 1);
  assert.equal(d.p, null); // n=1: no significance claim
});

test('pairedDelta: null/NaN metric values are skipped, not counted as zero', () => {
  const records = [
    { variant: 'baseline', task: 't1', run: 0, judge: 90 },
    { variant: 'honey', task: 't1', run: 0, judge: null },
    { variant: 'honey', task: 't1', run: 1, judge: 80 },
  ];
  const d = pairedDelta(records, { variant: 'honey', baseline: 'baseline', metric: (r) => r.judge });
  assert.equal(d.medianAbs, -10); // 80 vs 90, the null run ignored
});

test('pairedDelta: identical arms report all ties and no significance', () => {
  const records = [];
  for (let i = 0; i < 8; i++) {
    records.push(rec('baseline', `t${i}`, 0, 100), rec('honey', `t${i}`, 0, 100));
  }
  const d = pairedDelta(records, { variant: 'honey', baseline: 'baseline', metric: (r) => r.usage.output });
  assert.equal(d.ties, 8);
  assert.equal(d.medianRel, 0);
  assert.equal(d.p, null);
  assert.equal(d.pSign, null);
});
