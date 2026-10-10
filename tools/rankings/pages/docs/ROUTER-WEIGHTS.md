# Router weights — roundup → sovereign router

The estate sweep's output feeds the sovereign router as routing-weight
input. Two shapes exist; the router's `schema_version: 2` is the contract.

## The two shapes

| File | Schema | Written by | Who reads it |
|---|---|---|---|
| `results/estate/<date>/results.jsonl` | `roundup-bench/1` | `sweeps/roundup-estate-sweep.ts` | humans, audits |
| `results/estate/<date>/weights.json` | `roundup-weights/1` | `sweeps/roundup-estate-sweep.ts` | archives |
| `results/estate/<date>/router-weights.json` | **router `schema_version: 2`** | `sweeps/emit-router-weights.ts --in results.jsonl` | the sovereign router |

## Router contract (`schema_version: 2`)

```json
{
  "schema_version": 2,
  "generated_ts": "...",
  "run_id": "2026-10-02",
  "provider_priors": {
    "herd": { "elo": 1064, "quality_mean": 1.8, "latency_p50_ms": 310,
                    "healthy_frac": 1.0, "basis": "roundup 2026-10-02" }
  },
  "model_priors": [
    { "provider": "openrouter", "model": "inclusionai/ling-3.0-flash-fin:free",
      "quality_mean": 1.9, "latency_p50_ms": 1575, "healthy_frac": 1.0,
      "n": 6, "basis": "roundup 2026-10-02" }
  ]
}
```

`quality_mean` is on the router's 0–2 deterministic instruction-following
scale (exact=2 / contains=1 / empty=0) — the fork's scorer is natively 0–2,
so the sweep's `quality` passes through unscaled.
Provider elo follows the estate rule `1000 + (q-1)*80`. The router applies
`(quality_mean-1)*10` clamped `[-10,+10]` as per-candidate score bonus and
`-5` when `healthy_frac < 0.5`.

## Provider mapping (sweep label → router key)

| Sweep label | Router key | Why |
|---|---|---|
| `herd` | `herd` | the local herd lane in the router's provider table |
| `flock` | `openrouter` | flock-served OpenRouter free-tier models |
| `sov` | `sov` | benchmarked through the router itself; the router lane remaps |

## Wiring a fresh run

```bash
# 1. benchmark (bounded example; drop --limit for the full estate)
bun sweeps/roundup-estate-sweep.ts --providers herd,flock,sov \
    --limit 4 --requests 5 --out results/estate/2026-10-02

# 2. emit the router's weight file
bun sweeps/emit-router-weights.ts \
    --in results/estate/2026-10-02/results.jsonl \
    --out results/estate/2026-10-02/router-weights.json

# 3. land it where the router reads it and flag the router lane in fleet
cp results/estate/2026-10-02/router-weights.json \
   /home/toxic/estate/tools/sovereign-router/sovereign-router-ts/roundup-weights.json
```

The router's `bench-priors.ts` loader reads both the legacy
`bench-priors.json` and this file; it hot-reloads weights on
`/admin/reload` and SIGHUP. `roundup-weights.json` is additive —
`gen-bench-priors.py`'s wholesale-write guard is unaffected.

Rank rule everywhere: **quality desc, then p50 latency asc**.
