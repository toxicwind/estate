# completion-audit

A **checkable** completions auditor: wraps any completion call (model
inference CLI, code-race run, transport attempt) and emits one JSONL row per
call with **nanosecond-captured** timestamps (start, first-byte, end),
content hashes, ceiling enforcement, and winner/loser attribution. Then
`verify` replays the ledger and **recomputes every claim** — artifacts, not
vibes.

Built for the HFT-latency program (Chris's doctrine: latency is a correctness
criterion; race redundant approaches; measure everything; keep the fast path
hot). It is the missing piece under the `hft-latency` skill: that skill owns
`bin/race.py` (the racer) and `bin/measure.py` (μs timing helper) — this
harness is what makes a *completion* auditable and its numbers checkable.

## What it measures

Per call, captured at `time.perf_counter_ns()` (monotonic, ns resolution;
reported at μs):

- `t_ns.start` — just before spawn
- `t_ns.first_byte` — first non-empty stdout chunk (TTFB; null if no output)
- `t_ns.end` — after process reaped (or after kill on ceiling breach)
- `elapsed_us`, `ttfb_us` — derived, recomputed by verify
- `sha256(stdout)`, `sha256(stderr)`, `sha256(prompt)` — content hashes
- `exit_code`, `valid` (exit 0 AND optional `--match` regex on stdout)
- `ceiling_breached` — the attempt exceeded `--ceiling` seconds and was killed
- `winner` — null at write; **attribution is a claim**: `report`/`verify`
  recompute winner per `--race-id` (min `elapsed_us` among valid) and `verify`
  FAILS if a stored winner flag disagrees

Resolution proof: every `report` includes a `clock_probe` —
`min_nonzero_delta_ns` of `perf_counter_ns` over 200k samples (151ns measured
2026-09-14). Claims are μs; the source is ns.

## Ledger format

JSONL, one row per call. Default ledger `~/.cache/shingle/completion_audit.jsonl`
(cell and awrawr-pc both). Schema `v:1`:

```json
{"v":1,"ts":"2026-09-14T18:20:00Z","tag":"nim-gpt-oss-20b","race_id":"r1",
 "strategy":"nim.py chat","cmd":[...],"cmd_sha256":"...","prompt_len":42,
 "prompt_sha256":"...","match":null,"ceiling_s":60.0,
 "t_ns":{"start":123456789,"first_byte":123458000,"end":125000000},
 "elapsed_us":1543211,"elapsed_ms":1543.211,"ttfb_us":700123,"ttfb_ms":700.123,
 "exit_code":0,"valid":true,"ceiling_breached":false,
 "stdout_len":312,"stderr_len":0,
 "stdout":{"full":true,"len":312,"sha256":"...","b64":"..."},
 "stderr":{"full":true,"len":0,"sha256":"...","b64":""},
 "winner":null}
```

Outputs over 1 MiB store head/tail (8 KiB each) + hashes instead of full
bytes; `verify` checks the stored parts and flags anything it cannot
recompute. stderr truncates at 64 KiB.

Schema deliberately mirrors the live HFT workstream ledger
`~/.cache/shingle/latency_race_winners.jsonl`
(`timestamp, race, strategy, latency_ms, valid, winner, http_status, ttfb_ms`)
so rows are comparable; fields added here are the checkable ones (ns
timestamps, hashes, ceilings).

## How to audit a completion

```bash
# one NIM completion, 60s ceiling, must contain "answer" in stdout
audit.py audit --tag nim-gpt-oss-20b --ceiling 60 --match answer \
    --prompt prompt.txt --ledger ~/.cache/shingle/completion_audit.jsonl \
    -- nim.py chat --model openai/gpt-oss-20b "$(cat prompt.txt)"

# a two-strategy race: same tag + race_id, winner recomputed at report time
audit.py audit --tag model-race --race-id r1 --strategy gpt-oss-20b --ceiling 60 -- \
    nim.py chat --model openai/gpt-oss-20b "2+2=?"
audit.py audit --tag model-race --race-id r1 --strategy kimi-k3 --ceiling 60 -- \
    nim.py chat --model kimi-k3 "2+2=?"

# a code-race run (audits the whole race as one completion)
audit.py audit --tag code-race --ceiling 120 -- \
    race.py --ident RelayManager --lang python
```

Exit code: 0 iff valid and not ceiling-breached. A one-line `audited` NDJSON
event goes to stderr (borrowed from `hft-latency` `measure.py`); the wrapped
command's stdout is captured into the row, not passed through.

## How to verify

```bash
audit.py verify ~/.cache/shingle/completion_audit.jsonl            # all rows
audit.py report ~/.cache/shingle/completion_audit.jsonl --out rep.json
audit.py verify ~/.cache/shingle/completion_audit.jsonl --report rep.json
```

`verify` recomputes: timestamp ordering, `elapsed_us`, `ttfb_us`, `cmd_sha256`,
stdout/stderr hashes (full) or head/tail hashes (truncated), `valid`,
`ceiling_breached`, winner attribution per race_id — and with `--report`,
every percentile the report wrote. Exit 0 = every claim checks out; any
tampering (e.g. edited `elapsed_us`, swapped hash) fails with the row named.

`report` prints percentiles only (p50/p95/p99 — never averages alone) per
tag, plus the clock-resolution probe.

## Borrowed, not invented

- ns timing + NDJSON-on-stderr + per-attempt ceilings: `hft-latency/bin/measure.py`
- race-first-wins + winners-log shape: `hft-latency/bin/race.py` (itself
  borrowed from `code-race/bin/race.py`)
- row schema fields: live `~/.cache/shingle/latency_race_winners.jsonl`
  (HFT workstream races: `race_a_bridge_transport`, `race_b_herd_free_routes`)
- per-run JSONL ledger + aggregate audit command: `emergent-enrich/papers.py --audit`
- content-hash dedup for attribution: squawk-feed transport `race-borrow`
- bench-pattern context: `hft-latency/patterns/bench-borrowing.md` (stub,
  dedicated worker filling it from nimstats/NVIDIA/llm-bench-rig)
