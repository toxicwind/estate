# Router Proof: sovereign-router vs dumb direct (2026-09-21)

Head-to-head benchmark. Question: is the sovereign router measurably better than
a dumb direct route, or is the "intelligence" narration? Measured, no cheerleading.

## Method

- **Contender A (intelligent):** `POST 127.0.0.1:25104/v1/chat/completions`
  `{"model":"sovereign/free"}` — sovereign-router v3.2 (Bun/TS; hybrid strategy:
  sticky_affinity → ast_race → circuit_chain; SQLite HealthDB with Elo, latency
  EMA, circuit breakers, flap tracker).
- **Contender B (dumb direct):** `POST 127.0.0.1:25100/v1/chat/completions`
  `{"model":"openrouter-free/cohere/north-mini-code:free"}` — herd llama-swap,
  one pinned model through the keypool sidecar (`:25109`). No failover.
- 30 trials × 3 prompt types per contender, strictly sequential (no parallelism),
  contender A fully, then contender B. Same 30 random `BENCH-<token>` strings for
  both (apples-to-apples). `max_tokens=512` every request (reasoning models need
  headroom; tiny budgets fake-fail them). 120 s timeout per request. 429s and
  errors are DATA: recorded, never retried, never re-spun.
- Types:
  - **EXACT** — "Output exactly: BENCH-\<token\>. No other text." → success =
    `body.strip() == token`.
  - **QUALITY** — "Explain recursion in exactly three sentences for a smart
    12-year-old, with one concrete real-world example." → fixed judge
    (`:25100` `openrouter-free/nex-agi/nex-n2.5-pro:free`, the 10/10 census
    judge): "Score 0-10: exactly-three-sentences (0-3), correctness (0-3),
    concrete example (0-2), age-fit (0-2). Reply with just the number."
    Success = score ≥ 6.
  - **CODE** — "Write a Python function fib(n) returning the nth Fibonacci
    number. Code only." → success = `"def fib" in body`.
  - Empty/whitespace-only body = failure for ALL types (substance guard).
- Raw data: `router-proof-20260921.json` (same dir, gitignored scratch).
  Bench script: `router-proof-bench.py` (same dir). Ran 2026-09-21 ~12:40–12:47 UTC.

## Results

| Contender | Type | n | Transport OK | Success | Mean score | p50 lat | p95 lat | Wins served by |
|---|---|---|---|---|---|---|---|---|
| A intelligent | EXACT | 30 | 66.7% | **56.7%** | 0.567 | 297.5 ms | 1153.2 ms | EXAONE-4.0-1.2B-IQ4_XS (local) ×17 |
| A intelligent | QUALITY | 30 | 66.7% | **30.0%** | 7.70 (n=10 scored) | 275.6 ms | 5739.8 ms | EXAONE 1.2B ×8, nemotron-3-super-120b ×1 |
| A intelligent | CODE | 30 | 63.3% | **63.3%** | 0.633 | 498.4 ms | 9120.6 ms | EXAONE 1.2B ×19 |
| B dumb direct | EXACT | 30 | 16.7% | **16.7%** | 0.167 | 43.7 ms¹ | 755.8 ms | north-mini-code:free ×5 |
| B dumb direct | QUALITY | 30 | 16.7% | **10.0%** | 9.33 (n=3 scored) | 44.2 ms¹ | 4869.2 ms | north-mini-code:free ×3 |
| B dumb direct | CODE | 30 | 16.7% | **0.0%** | 0.000 | 44.0 ms¹ | 4818.1 ms | — (5 answered, none contained `def fib`) |

¹ B's p50 is dominated by fast 502 failures (~44 ms) — that is not a speed win,
it is the median of mostly-errors. Compare success-conditional latency instead.

Error ledger: A → `http_503 {"error":"connect_timeout"}` ×31 (router's own cloud
fallbacks timing out). B → `http_502 {"error":"keypool 'openrouter-free': no
healthy key", "tried":["OPENROUTER_API_KEY_1"]}` ×75 — the OpenRouter free
keypool was unhealthy for nearly the entire run.

## Verdict (plain)

**Yes, the intelligent router is measurably better — on availability, decisively.**
It delivered 3.4×–6.3× the task success of the dumb direct route (EXACT 56.7%
vs 16.7%, QUALITY 30% vs 10%, CODE 63.3% vs 0%). The mechanism is visible in the
data: when the OpenRouter free keypool went unhealthy, the router failed over to
a local EXAONE-4.0 1.2B (and once to nemotron-3-super-120b) and kept serving,
while the dumb route had exactly one model and died with the keypool.

**On per-answer quality, the dumb route wins — on a tiny sample.** When
north-mini-code:free actually answered, it scored 9.33/10 vs the router's 7.7
(n=3 vs n=10). The honest reading of the "intelligence" on display: it was
failover breadth, not model-selection brilliance. Nearly all of A's wins came
from a 1.2B local model — fast (p50 ~300–500 ms) but mediocre (17/20 transported
EXACT, quality mean 7.7). And A still failed ~1/3 of its requests with 503
connect_timeouts on its own cloud fallbacks.

**What this proves and what it doesn't:** it proves resilience under failure —
one route, one keypool, one bad hour, and the dumb setup goes to zero while the
router keeps working. It does NOT prove universal superiority: on a day the free
keypool is healthy, B's numbers would look much better and the gap would narrow.
A re-run on a healthy keypool day is the obvious follow-up before claiming more.

## Caveats

- Point-in-time outage: keypool `openrouter-free` reported "no healthy key" for
  ~the whole run. This benchmark measures router behavior under failure.
- The fixed judge rode the same dead keypool (`nex-n2.5-pro:free` via `:25100`),
  returning empty 10× — so A/QUALITY scored n=10 of 20 transported answers.
- Sequential single run; no confidence intervals; time-of-day effects not
  controlled (A ran 12:40–12:44, B 12:44–12:47 UTC).
