# Honey benchmark results

model: `gpt-5.5` · judge: `claude-opus-4-8+claude-sonnet-4-6+claude-haiku-4-5-20251001+gpt-5.5` · tasks: 23 · runs: 3

| Variant | Tests pass | Judge ±sd | Judge vs base | Output tok | Output vs base | $ (cached) | $ (cold) | CO₂ (g) |
|---------|-----------:|----------:|--------------:|-----------:|---------------:|-----------:|---------:|--------:|
| baseline | 100% | 96 ±3 | 100% | 93,506 | +0% | $1.427 | $1.427 | 58.2 |
| caveman | 99% | 96 ±3 | 100% | 77,918 | -17% | $1.375 | $1.378 | 48.5 |
| ponytail | 100% | 93 ±11 | 97% | 94,471 | +1% | $1.509 | $1.509 | 58.8 |
| honey | 99% | 96 ±4 | 100% | 76,145 | -19% | $1.357 | $1.469 | 47.4 |
| honey-design | 97% | 96 ±3 | 100% | 71,231 | -24% | $1.248 | $1.248 | 44.3 |

- **Tests pass** — objective: extracted code run against unit tests.
- **Judge ±sd** — LLM-as-judge (0-100, panel median) with per-record stdev. A judge gap
  inside ±sd is noise, not a quality win. Rubric: `plain`.
- **Output tok / Output vs base** — the headline lever: tokens each skill directly
  controls. Caching-independent.
- **$ (cached)** — steady state: skill prompt prompt-cached (≈10% input cost on repeat
  tasks). **$ (cold)** — first-turn worst case: skill prompt billed as fresh input. Real
  cost sits between, nearer cached as a session lengthens. Rates in `bench/pricing.json`.
- **CO₂** via EcoLogits port (`hooks/eco.js`), from output tokens.
