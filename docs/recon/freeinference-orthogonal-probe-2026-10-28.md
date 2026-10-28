# FreeInference orthogonal probe — 2026-10-28

Ground truth from live probes (real-browser UA on every request, per skill
`freeinference-orthogonal-probe`). Date: 2026-10-28. Probe ran from
`awrawr-pc` tau session; key from secretsmith (`hyi-` key, never logged).

## Context / why this probe

`pens/ranch/geode-rig/swarm-10.json` (refresh 2026-10-28T03:55Z) claimed:

> "freeinference upstream fully dead + 96% of :25193 catalog has dead upstream
> mappings (instant-502)" … "nemotron_ultra is the ONLY confirmed-working lane".

Today's live probes **contradict that finding** — freeinference is alive and
serving real completions on two lanes. The swarm-10 conclusion is STALE and
effectively REVERSED. This document is the correction.

## Endpoint map (all probed 2026-10-28 ~09:00Z)

| Endpoint | Auth | Status | Notes |
|---|---|---|---|
| `GET https://freeinference.org/health` | none | 200 | `{status:healthy, routes_configured:33, instance:fec71a0b9673815d, database_connected:true}` |
| `GET https://freeinference.org/v1/models` | hyi- key | 200 | Catalog now advertises **only 2 models**: `glm-5.3-flash`, `deepseek-v4-flash` |
| `GET https://freeinference.org/public-stats` | none | 200 | 90-day traffic superset: 4 models seen |
| `GET https://openinfra.freeinference.org/api/dashboard` | none | 200 | Fleet telemetry: healthy |

## Catalog (`/v1/models`, 2026-10-28)

Only two models advertised now (was 6 on 2026-10-19: glm-5.3-flash, minimax-m3,
qwen3.6-35b, diffusiongemma, deepseek-v4-flash, bge-m3).

| id | ctx | max out | input $/1M | output $/1M | cache-read $ | on_demand |
|---|---|---|---|---|---|---|
| glm-5.3-flash | 1.0M | 131K | 0.30 | 1.00 | 0.06 | false |
| deepseek-v4-flash | 1.0M | 393K | 0.44 | 1.32 | 0.014 | false |

## Live chat-completions probes (the truth test)

| model | HTTP | wall ms | content | finish_reason |
|---|---|---|---|---|
| **deepseek-v4-flash** | 200 | **571** | `OK` | stop |
| **qwen3.6-35b** | 200 | **447** | `OK` | stop |
| glm-5.3-flash | 200 | **30,256** (30s!) | *(empty)* | — |
| minimax-m3 | 404 | 391 | — | — |
| minimax-m3.1-flash | 404 | — | — | — |
| diffusiongemma | 404 | — | — | — |

Sentinel probe: "Reply with exactly: OK", max_tokens=16, stream off.

### Interpretation

- **deepseek-v4-flash and qwen3.6-35b are the only live, fast, content-producing
  lanes.** ~0.4–0.6 s round trips, finish=stop, exact sentinel. Confirms the
  architect's operational report ("only deepseek and qwen are working").
- **glm-5.3-flash responds 200 but stalls ~30s with no content** at this
  moment — same contention signature as 2026-10-27 re-audit (glm was the
  contended lane then too). Not dead; effectively unusable for latency-bound work.
- **minimax / diffusiongemma 404** — retired from the chat lane (unlisted in
  catalog, consistent with the "retired IDs → 404" rule).
- **bge-m3** exists only in traffic superset (embeddings lane, not chat).

## public-stats superset (90-day window, generated_at 2026-10-28T09:00Z)

Totals: **1,181,780,179,383 tokens**, 12,055,322 requests, 366 accounts,
cached-input share 93.4%.

| model | tokens | requests |
|---|---|---|
| deepseek-v4-flash | 628,906,381,300 | 5,993,947 |
| glm-5.3-flash | 366,452,342,884 | 2,536,866 |
| qwen3.6-35b | 42,899,049,570 | 1,804,126 |
| bge-m3 | 1,257,566,129 | 340,827 |

Agents by kind: coding 60.6% of tokens, general 16.3%, direct 15.4%, custom
7.5%, chat 0.1%.

## openinfra dashboard fleet telemetry (generated_at 1793187522400 ≈ 09:38Z)

- Fleet status: **healthy**; 4 nodes, 3 online; **11 GPUs, 7 online**;
  avg GPU util 27.4%; avg temp 53°C; ~628 GB / 1.35 TB HBM used.
- GPU inventory includes **NVIDIA H200** pairs (h200a region) + rtx6000b
  (bge-m3 embeddings, vllm).
- Hourly served: ~5,044 reqs; daily ~132,905 reqs (cache_tokens 15.9B).
- Served servers include `h200a-glm53-flash` (glm-5.3-flash) and
  `h200a-replica-a` (deepseek-v4-flash, seen in requests telemetry,
  decode ~841 TPS, ttft ~8s on a 114K-token prefill — huge-context loads are
  slow; small probes are fast as measured above).

## Verdict

1. **swarm-10.json's 2026-10-28T03:55Z finding is STALE and WRONG-REVERSED.**
   It claims freeinference "fully dead" and nemotron-ultra as the only live
   lane; in fact freeinference's deepseek/qwen returned 200+content in <600ms
   at 09:00Z while the nvidia nemotron-3-super lane 404s
   (`Function ac74040f not found for account`) in the current tau runtime.
2. **Live freeinference lanes today: deepseek-v4-flash (571ms) and
   qwen3.6-35b (447ms).** These are the fastest measured working models on the
   estate right now.
3. glm-5.3-flash is a 30s-stall; treat as quarantined for latency-bound work
   (probe again before trusting).
4. The catalog shrink (6 → 2 advertised) matches the traffic superset: the two
   fast lanes are the product's own winners.

## Decisions (for the estate)

- **Keep/re-route freeinference lanes for deepseek-v4-flash + qwen3.6-35b** —
  they are live, fast, and correct. The prior "freeinference = dead" note in
  swarm-10 must be corrected (see follow-up task).
- **Do not route vibe/spark workers through nvidia nemotron-3-super `:medium`**
  (404 ac74040f) — that lane is dead on this account right now. Reference the
  measured-fastest live lanes instead.
- **Quarantine glm-5.3-flash for latency-bound subagent work** until a repeat
  probe shows sub-5s.
- Do not add minimax-m3 / minimax-m3.1-flash / diffusiongemma — 404 on chat.

## Provenance

- Probes: curl with real-browser UA
  `Mozilla/5.0 (X11; Linux x86_64) … Chrome/141.0.0.0 Safari/537.36`
  (UA-ban doctrine), hyi- API key via `secretsmith env FREEINFERENCE_API_KEY`.
- Raw response bodies persisted: `/tmp/models.json`, `/tmp/public-stats.json`,
  `/tmp/dashboard.json`, `/tmp/fi-health.json` (session-bound working copies).
- Prior baseline: `estate/docs/freeinference-provider.md` (2026-10-19) +
  2026-10-27 re-audit notes; skill `freeinference-orthogonal-probe`.

## Rerunnable probe

Canonical script archived at
`estate/docs/anomalies/2026-10-26/freeinference-orthogonal-probe.sh`;
the 2026-10-28 run was executed inline from the tau session (curl one-liners),
results summarized above.