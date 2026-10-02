# Honey benchmark results

model: `claude-opus-4-8` · judge: `claude-opus-4-8+claude-sonnet-4-6+claude-haiku-4-5-20251001+gpt-5.5` · tasks: 23 · runs: 3

| Variant | Tests pass | Judge ±sd | Judge vs base | Output tok | Output vs base | $ (cached) | $ (cold) | CO₂ (g) |
|---------|-----------:|----------:|--------------:|-----------:|---------------:|-----------:|---------:|--------:|
| baseline | 97% | 94 ±7 | 100% | 90,795 | +0% | $7.015 | $7.015 | 1996.0 |
| caveman | 94% | 94 ±4 | 100% | 71,183 | -22% | $5.720 | $7.319 | 1564.8 |
| ponytail | 90% | 92 ±5 | 98% | 70,644 | -22% | $6.138 | $6.138 | 1553.0 |
| honey | 100% | 93 ±6 | 99% | 77,098 | -15% | $6.253 | $8.658 | 1694.9 |
| honey-design | 100% | 95 ±5 | 101% | 80,169 | -12% | $6.353 | $7.585 | 1762.4 |

- **Tests pass** — objective: extracted code run against unit tests.
- **Judge ±sd** — LLM-as-judge (0-100, panel median) with per-record stdev. A judge gap
  inside ±sd is noise, not a quality win. Rubric: `plain`.
- **Output tok / Output vs base** — the headline lever: tokens each skill directly
  controls. Caching-independent.
- **$ (cached)** — steady state: skill prompt prompt-cached (≈10% input cost on repeat
  tasks). **$ (cold)** — first-turn worst case: skill prompt billed as fresh input. Real
  cost sits between, nearer cached as a session lengthens. Rates in `bench/pricing.json`.
- **CO₂** via EcoLogits port (`hooks/eco.js`), from output tokens.
