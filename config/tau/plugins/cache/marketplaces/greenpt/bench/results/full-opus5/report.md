# Honey benchmark results

model: `claude-opus-5` · judge: `claude-opus-5+claude-sonnet-5+claude-haiku-4-5-20251001+gpt-5.5` · tasks: 23 · runs: 3

## Paired (headline)

| Variant | n | Δ output | p | Δ LOC | p | Δ new-input | p | Δ cost | p | Judge W/L/T | sign p |
|---------|--:|---------:|--:|------:|--:|------------:|--:|-------:|--:|------------:|-------:|
| caveman | 23 | -44% | <0.001 | -39% | 0.009 | -1% | <0.001 | -39% | <0.001 | 8/10/3 | 0.815 |
| ponytail | 23 | -16% | 0.002 | -42% | <0.001 | -1% | <0.001 | -13% | 0.002 | 8/13/0 | 0.383 |
| honey | 23 | -43% | <0.001 | -69% | <0.001 | -1% | <0.001 | -33% | <0.001 | 7/12/2 | 0.359 |

Every Δ is a **per-task** delta vs `baseline`: runs collapse by median, tasks pair up,
and the column is the median of those paired deltas. `p` is a two-sided Wilcoxon
signed-rank test (`—` when fewer than 6 non-tied tasks — no significance is claimed there).
`(ns)` marks a delta that misses p<0.05: a tie, not a win. **Judge W/L/T** counts tasks
where the variant scored above / below / level with baseline, tested with an exact sign
test — the right test for ordinal, noisy judge scores, and one a mean-of-means can hide.

- **Δ output** — the headline lever: volume each skill directly controls, caching-independent.
- **Δ new-input** — fresh + cache-creation tokens, the class where a skill prompt *costs*.
  Cache reads are excluded: they bill at a tenth and dominate a long session regardless.
- **Δ cost** — all four token classes at `bench/pricing.json` rates.

## Arm totals

| Variant | Tests pass | Judge ±sd | Judge vs base | Output tok | Output vs base | New input tok | $ (cached) | $ (cold) | CO₂ (g) |
|---------|-----------:|----------:|--------------:|-----------:|---------------:|--------------:|-----------:|---------:|--------:|
| baseline | 83% | 91 ±11 | 100% | 204,104 | +0% | 13,683 | $5.171 | $5.171 | 4486.9 |
| caveman | 96% | 93 ±2 | 102% | 129,270 | -37% | 17,197 | $3.383 | $3.929 | 2841.8 |
| ponytail | 93% | 92 ±7 | 101% | 120,148 | -41% | 15,307 | $3.112 | $3.375 | 2641.3 |
| honey | 96% | 90 ±13 | 99% | 145,056 | -29% | 18,622 | $3.898 | $5.446 | 3188.8 |

Volumes and absolute costs. The *vs base* column here is a ratio of sums and is
outlier-sensitive — one long task can drive it; prefer the paired table above.

- **Tests pass** — objective: extracted code run against unit tests.
- **Judge ±sd** — LLM-as-judge (0-100, panel median) with per-record stdev. A judge gap
  inside ±sd is noise, not a quality win. Rubric: `plain`.
- **$ (cached)** — steady state: cache reads at ≈10% of input, cache *creation* charged.
  **$ (cold)** — first-turn worst case: every input token billed fresh. Real cost sits
  between, nearer cached as a session lengthens. Rates in `bench/pricing.json`.
- **CO₂** via EcoLogits port (`hooks/eco.js`), from output tokens.
