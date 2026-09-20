# Bench Borrowing — latency measurement patterns

**Purpose:** How the pros measure inference latency, borrowed (not reinvented) for the `hft-latency` skill.
Researched 2026-09-14 on awrawr-pc (`/home/toxic/...`) + web. Coordinator: 8bdc8e26.

---

## 1. Pattern: streaming TTFB via SSE chunk timing (NIMStats)

**Source:** `/home/toxic/projects/nim-bench-dashboard/data/Clouder1122__NIMStats__test_models.py`
(one fork of ~28 forks of `ahmedhabibo/NIMStats`, consolidated in that repo; also
`scripts/save_all.py` consolidates all forks' `history.db` files into one dashboard)

Stream (`"stream": True`) against any OpenAI-compatible `/chat/completions`, stamp
`time.perf_counter()` at request start, and record the moment the **first non-empty
`delta.content`** arrives. Tokens come from the final `usage` chunk, so `tokens/sec`
is exact, not estimated:

```python
started = time.perf_counter()
time_to_first_token_ms = None
completion_tokens = 0
content_parts = []
for raw_line in response:                      # urllib stream of the SSE body
    line = raw_line.decode("utf-8", errors="replace").strip()
    if not line or not line.startswith("data: "):
        continue
    data_str = line[len("data: "):]
    if data_str == "[DONE]":
        break
    chunk = json.loads(data_str)
    text = (chunk.get("choices") or [{}])[0].get("delta", {}).get("content") or ""
    if text:
        if time_to_first_token_ms is None:
            time_to_first_token_ms = int((time.perf_counter() - started) * 1000)
        content_parts.append(text)
    usage = chunk.get("usage") or {}
    completion_tokens = int(usage.get("completion_tokens") or 0)
response_time = int((time.perf_counter() - started) * 1000)
```

**Borrow:** the per-request record shape — `{model, success, responseTime,
timeToFirstToken, tokensGenerated, totalTokens, error}` — and the append-to-`history.db`
pattern (`db_utils.write_run`), one JSON row per run, timestamped UTC.

**Reusable as-is:** yes — env-configurable (`API_BASE`, `NIM_API_KEY`, `MODEL_GROUP`).
Run one model: `MODEL_GROUP=all NIM_API_KEY=... python3 <user>_NIMStats__test_models.py`.
It benchmarks against any OpenAI-compatible endpoint, not just NVIDIA.

## 2. Pattern: warmup + best-of-N decode-gate (genesis harness)

**Source:** `/home/toxic/projects/genesis-vllm-patches/benchmarks/harness/tgs_decode.py`
with shared helpers in `benchmarks/harness/_common.py` (`post_completion_stream`)

- **Warmup runs are discarded** (`--warmup-runs 1`): cold-start (model load,
  KV-cache cold, GPU clocks) never pollutes the measured numbers.
- **Best-of-N timed runs** (`--timed-runs 3`, best `tgs` kept): damps noise
  without paying for percentile math on small N.
- **Decode t/s isolates post-first-token generation:**
  `decode_sec = total - ttft; decode_toks = total_tokens - 1; tgs = decode_toks / decode_sec`.
  This separates *prefill* (TTFT) from *decode* — the two numbers move independently.
- **Gate semantics:** each harness emits `GateResult{name, value, threshold, passed}`
  and a `HarnessReport`, exits non-zero on gate failure. Benchmarks are go/no-go
  gates, not vibes.
- Shared `_common.py` pieces worth borrowing: `probe_health(endpoint)` (fail-fast on
  `/health` before burning a bench), `default_out_path()` (timestamped JSON reports),
  one-arg-parser factory for consistent CLI across harnesses.

```python
# timed loop shape from tgs_decode.py
samples, best_tgs = [], 0.0
for _ in range(args.timed_runs):
    ttft, total_tokens, total = post_completion_stream(endpoint, key, model, filler,
                                                       max_tokens=args.gen_tokens)
    tgs = max(total_tokens - 1, 0) / max(total - ttft, 1e-9)
    samples.append({"ttft_sec": ttft, "total_sec": total, "tgs": tgs})
    best_tgs = max(best_tgs, tgs)
```

**Reusable as-is:** yes — `python -m benchmarks.harness.tgs_decode --endpoint
http://<host>:8000/v1 --context-tokens 160000 --gen-tokens 256 --threshold 49`.
Built for long-context decode gates; generalises to any vLLM/OpenAI endpoint.

## 3. Pattern: ns timers, KV-cache reset, samples arrays (llama-bench)

**Source:** `/home/toxic/ik_llama.cpp/examples/llama-bench/llama-bench.cpp` (~line 2200)

- Timer granularity is **nanoseconds** (`get_time_ns()`, samples stored in `samples_ns`).
  For HFT-like work: `time.perf_counter_ns()` in Python, `time.Now()` in Go — never
  wall-clock seconds with ms rounding.
- **Warmup run before timed reps:** one tiny prompt (1 token) + one generation run,
  discarded.
- **KV cache cleared between reps** (`llama_kv_cache_clear(ctx)`) so every rep
  measures the same steady state — equivalent for API benches: each timed request
  is independent; never reuse a warm session as your only sample.
- Output is **avg + stddev** over reps (fields `avg_ns`, `stddev_ns`, `avg_ts`,
  `stddev_ts` in its printer), not a single number.

**Borrow:** warmup → N reps → mean/stddev; ns timers; identical starting state per rep.

## 4. Pattern: shuffle candidates, discard run 0 (http-bench-toxicwind)

**Source:** `/home/toxic/projects/http-bench-toxicwind/benchmark.py`

- `random.shuffle(packages)` **before every run** — candidate order is randomised to
  kill ordering bias (TCP warmup, DNS cache, server-side cache priming favouring
  whoever goes first).
- **Run 0 is discarded** (`if run == 0: continue`) — the first run is the warmup.
- Per-package metrics split into **conn time, TLS time, total, req/sec** — transport
  layers measured separately so you know *which* layer is slow.

**Borrow:** when racing routes, shuffle the candidate order each race; always
discard the first round.

## 5. Pattern: free latency histograms from the server itself (NVIDIA NIM `/metrics`)

**Source:** NVIDIA NIM observability docs —
<https://docs.nvidia.com/nim/vision-language-models/1.2.0/observability.html>

Every NIM microservice exposes Prometheus histograms **per model, per request** —
no synthetic probing needed:

| Metric | Meaning |
|---|---|
| `time_to_first_token_seconds` | TTFT histogram |
| `time_per_output_token_seconds` | decode TPOT histogram |
| `e2e_request_latency_seconds` | full request latency histogram |
| `request_prompt_tokens` / `request_generation_tokens` | token count histograms |
| `num_requests_running` / `num_requests_waiting` | live queue pressure |

**Borrow:** if an upstream route is a NIM (or anything exposing these), **scrape
`/metrics` instead of probing** — it's ground truth from the server, zero extra
load, and queue depth (`num_requests_waiting`) tells you *why* TTFT spiked.
Anything we host through herd should expose the same shape so the router can read it.

## 6. Pattern: full percentile report + goodput (NVIDIA AIPerf)

**Source:** <https://github.com/ai-dynamo/aiperf> (successor to GenAI-Perf), plus
NVIDIA's guide <https://developer.nvidia.com/blog/llm-performance-benchmarking-measuring-nvidia-nim-performance-with-genai-perf/>

AIPerf profiles any OpenAI-compatible endpoint and reports per metric
**avg / min / max / p99 / p90 / p50 / std**: TTFT, time-to-second-token, request
latency, inter-token latency (ITL), output tokens/sec/user, input/output sequence
lengths. Key methodology points:

- **Percentiles, not averages.** A single avg hides the tail; p99 TTFT is the
  number that decides whether the router is "fast". NVIDIA explicitly warns that
  different tools define apparently-similar metrics differently — pin the
  definitions (TTFT = request-sent → first content token, see pattern 1).
- **TTFT is not comparable across prompt lengths.** Prefill work scales with input
  tokens; always record `input_tokens` alongside TTFT or the numbers are meaningless
  (NVIDIA benchmark methodology: ISL/OSL fixed per run).
- **`--goodput`**: requests/sec that complete *under your SLO thresholds*
  (e.g. `--goodput "time_to_first_token:370 request_latency:648"`). Throughput
  measures what the hardware did; **goodput measures what users got** — this is the
  number a router should optimise.
- **ITL (inter-token latency) exposes variance** that TPOT averages hide — the
  stutters from other requests' prefill. Track per-chunk arrival times if you want
  this (cheap: timestamp each SSE chunk).

**Reusable as-is — do not rebuild:** this is the pro harness.

```bash
pip install aiperf
aiperf profile \
  --model "<route model id>" \
  --url http://127.0.0.1:25100 \
  --endpoint-type chat \
  --streaming \
  --concurrency 1 \
  --request-count 50 \
  --ui-type none
# quick single-shot sanity instead of a full run:
aiperf chat --model "<id>" --url http://127.0.0.1:25100 --quick "say hello in one short sentence"
# prints: TTFT: 20.06 ms / TPS: 154.11 / ITL: 6.31 ms / Cache: 77.8%
```

Point it at herd (`127.0.0.1:25100`) with `--endpoint-type chat` and it measures the
*routed* path end-to-end — no code to write.

---

## Reuse verdict (don't rebuild what's already built)

| Harness | Invoke | Use for |
|---|---|---|
| **aiperf** | `aiperf profile --model <id> --url <endpoint> --endpoint-type chat --streaming --concurrency 1 --request-count N` | Full percentile methodology, goodput, ITL — the reference bench |
| **NIMStats script** | `API_BASE=... NIM_API_KEY=... python3 <fork>__NIMStats__test_models.py` | Quick per-model TTFB + tok/s sweep across many models, history.db trend |
| **genesis `tgs_decode.py`** | `python -m benchmarks.harness.tgs_decode --endpoint <url>/v1 --context-tokens 160000 --gen-tokens 256 --threshold 49` | Decode-rate gates at long context |
| **llama-bench.cpp** | existing binary in ik_llama.cpp tree | Local GGUF engine speed (pp/tg), not API routing |

---

## 7. Proposal: per-route latency memory for herd

**Status quo:** herd (`127.0.0.1:25100`, `/home/toxic/sovereign/herd/`, llama-swap
lineage) has **no per-route latency memory**. Router lives in
`internal/router/` (`base.go`, `group.go`, `peer.go`, `matrix*.go`, `scheduler/`);
persistence in `internal/store/` (SQLite via goose migrations — `store.go` already
has `TokenMetrics` with `TokensPerSecond`, so a latency table fits the existing
pattern). Prometheus helpers already exist in `internal/perf/prometheus.go`.

### What to track (per completed request, per route = model id + upstream URL)

| Field | How |
|---|---|
| `ttft_ms` | ns timer at proxy start → first non-empty streamed content chunk (pattern 1) |
| `e2e_ms` | ns timer at proxy start → stream close |
| `output_tokens` | from final `usage` chunk (exact, not estimated) |
| `decode_tps` | `(output_tokens - 1) / ((e2e_ms - ttft_ms) / 1000)` (pattern 2) |
| `input_tokens` | from `usage` — TTFT is meaningless without it (pattern 6) |
| `status` | `ok` / `error` + HTTP code; errors count against the route, not just slowness |
| `ts` | UTC; `route` key = `model_id + "|" + upstream_url` |

Optional but cheap: timestamp every SSE chunk → ITL p50/p99 for the route
(pattern 6); scrape upstream `/metrics` when it exposes NIM-style histograms
(pattern 5) and merge as the server-side view.

### Where to log it

- **Hot path:** append-only JSONL, one line per request:
  `/home/toxic/.herd/latency/route_latency.jsonl`
  (JSONL keeps the write path lock-free and crash-safe; matches the NIMStats
  `history.db` / `code_race_winners.jsonl` conventions already in use fleet-wide).
- **Aggregates:** a new goose migration in `internal/store/migrations/`
  (`latency_rollup` table: route, window_start, n, ttft_p50, ttft_p99,
  decode_tps_p50, err_rate) rolled up every 60s by a background goroutine, so the
  router reads one row instead of scanning JSONL. SQLite is already the store —
  no new dependency.

### How the router "leads with the proven winner"

1. **Score per route** (EWMA, refreshed on every completed request):
   `score = w1 * ttft_p50 + w2 * (1000 / decode_tps_p50) + w3 * err_penalty`,
   all in comparable ms-ish units; err_penalty = `err_rate_5m * BIG`.
2. **Route selection:** candidates for a model sorted by score ascending; try in
   order with **fail-fast per-attempt timeouts** (slow is a kind of wrong).
   Shuffle ties (pattern 4).
3. **Leader cache:** keep the current winner per model with a 60s TTL — "keep the
   fast path hot". On TTL expiry or a failure, re-sort from fresh aggregates.
4. **Freshness decay:** EWMA alpha weighted toward recent samples; a route that
   was fast an hour ago but degraded now must lose quickly. Also decay routes with
   **zero recent samples** toward "unknown" so stale winners don't stick.
5. **Active refresh:** when a route has no samples in the last N minutes and it's
   a candidate, send one low-cost probe (`max_tokens: 1`, `stream: true`) through
   it — a 1-token probe gives TTFT for ~zero cost. This is the race-borrow loop:
   *passive* measurement on real traffic + *active* 1-token probes for cold routes.
6. **Goodput as the headline:** the dashboard/leaderboard number per route is
   requests/sec under the fleet SLO (e.g. TTFT ≤ 400ms), not raw throughput —
   optimise what users get (pattern 6).

### Minimal viable implementation (forward-only, additive)

1. Add a proxy-middleware hook in `internal/router/base.go` (or the scheduler)
   that wraps the upstream response stream and emits the JSONL line — additive,
   no changes to routing logic.
2. Add the goose migration + 60s rollup goroutine in `internal/store/`.
3. Add score sort + leader cache in the candidate-selection path; gate behind a
   config flag (`routing.latency_aware: true`) so it ships dark and flips on.

Until that's built, **aiperf pointed at herd is the stand-in**:
`aiperf profile --model <id> --url http://127.0.0.1:25100 --endpoint-type chat
--streaming --concurrency 1 --request-count 50 --goodput "time_to_first_token:400"`.
