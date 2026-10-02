# Squawk HFT: Microsecond Audit (2026-09-14)

## Theoretical Minimums (measured)

### awrawr-pc local path — ALREADY MICROSECOND

| Operation | Min | Median | Max |
|-----------|-----|--------|-----|
| File write + fsync + read | 14.4µs | 16.0µs | 54.2µs |
| inotify create → event | 5.7µs | 6.6µs | 29.1µs |
| JSON parse (typical msg) | 1.46µs | 1.89µs | 144µs |

**Verdict**: The awrawr-pc side is already at the microsecond floor.
Python overhead (GIL, JSON) is ~2µs — irrelevant. No further optimization
meaningful here.

### Network path (cell → awrawr-pc) — MILLISECOND floor

| Operation | Min | Median | Max |
|-----------|-----|--------|-----|
| Raw TCP connect (funnel) | 1.3ms | 4.1ms | 16.7ms |
| TLS + WS handshake (persistent, amortized) | — | ~670ms | 8.4s |
| Bridge WS exec (measured) | — | ~250ms | — |

**Theoretical floor**: ~4ms RTT (speed of light + Tailscale).
**Current**: ~250ms for bridge exec. **Gap: ~240ms unexplained.**

## Where Microseconds Are Lost (ranked by impact)

### 1. The 240ms gap (HIGHEST IMPACT)
Bridge WS takes 250ms but raw TCP is 4ms. The 240ms is in:
- Egress proxy CONNECT (~?ms)
- TLS handshake on reconnect (~?ms, should be amortized)
- Python WS daemon multiplexing (~?ms)
- Application processing (~?ms)

**Action**: Instrument the bridge WS daemon with per-hop timing.
Likely culprits: proxy CONNECT per request (not reusing), or the
multiplexing layer adding queue delay.

### 2. Cell-side: spool → worker (MEDIUM)
The hook worker spawn time is unmeasured. If the worker takes 200ms
to start, that's 200ms of the 500ms end-to-end.

**Action**: Log worker spawn → first output time.

### 3. Push daemon stability (MEDIUM)
The push daemon died (17:49) and wasn't restarted until manual
intervention. The hook's health-check only runs when the hook fires.
If the hook system stalls, push stays dead.

**Action**: The 1s poll hook IS the watchdog. Verify the hook is
actually firing every 1s. If not, the push architecture is fragile.

### 4. Python startup (LOW)
Each hook invocation spawns Python (~50ms). For the 1s poll, this
is 5% overhead. Acceptable.

**Action**: None. Not worth optimizing.

### 5. JSON serialization (NEGLIGIBLE)
1.9µs. Don't touch.

## What "Microsecond Proof" Actually Means

True microsecond end-to-end is **impossible** for cell→awrawr-pc
(physics: 4ms RTT floor). "Microsecond proof" means:
1. The local path IS microsecond (proven: 6-16µs).
2. The network path is at the theoretical floor (4ms).
   We're at 250ms — 60x over the floor. That's the target.
3. Every hop is measured with µs precision (we have ns timers).

**Realistic target**: 10-20ms end-to-end (not 500ms, not 1µs).
That requires killing the 240ms gap.

## Bench Repo Audit

### How they prove latency claims

| Repo | Metrics | Statistical Rigor |
|------|---------|-------------------|
| **NVIDIA NIM** (our bench_max_*.json) | TTFT (ms), total_ms, status | Single-run (weak) |
| **llama-bench** (llama.cpp) | PP/TG tok/s, repetitions=5 | 5 reps, CSV/JSON/SQL |
| **open-llm-benchmarks** | TTFT p95, E2E p95, tok/s | Concurrency sweeps, p95 |
| **Fireworks benchmark** | TTFT, ITL, QPS, 50 runs | P50/P95/P99, 50 iterations |
| **vlm-llm-benchmark** | 6 dims (acc/TTFT/tput/conc/stab) | 30-min stability, drift check |
| **evaluating-llms-harness** | MMLU/HumanEval/GSM8K | Quality only, NOT latency |

### What we should borrow

1. **P50/P95/P99** (not just median). Our race log only has mean.
2. **Warm-up iterations**. First connection is slow (670ms); steady-state is faster.
3. **Concurrency sweeps**. What happens under load? (Not tested.)
4. **Methodology doc**. Write down exactly what's measured, like open-llm-benchmarks/METHODOLOGY.md.
5. **Repetitions**. llama-bench uses 5; Fireworks uses 50. We use 1.

### What we have on /home/toxic (don't reinvent)

- `/home/toxic/ik_llama.cpp/examples/llama-bench/` — gold standard for local inference bench
- `/home/toxic/bench-wt-tau/herd/internal/bench/` — Go bench (orchestrator, probe, state)
- `/home/toxic/gear-push-zv/evaluating-llms-harness/` — quality eval (not latency)
- `~/workspace/skills/nvidia-nim-loader/` — NIM TTFT/total_ms measurements

## Streaming Tools (favor these)

- **Persistent WS** (done): streaming, not polling.
- **Server-Sent Events**: alternative to WS, simpler, auto-reconnect. Not needed (WS works).
- **Tailscale**: already the transport. No faster option for cell→pc.

## Changes Made

None to existing files (all <2000 lines, no rewrites needed).
This is a findings doc only. The 240ms gap investigation is next.

## Next Steps (for parent)

1. Instrument bridge WS daemon: per-hop timing (proxy, TLS, multiplex, app).
2. Verify hook fires every 1s (if not, push is fragile).
3. Add P95 to race log (currently only mean).
4. Write METHODOLOGY.md for Squawk latency (borrow from open-llm-benchmarks).
