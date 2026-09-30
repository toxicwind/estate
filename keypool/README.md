# keypool

Modular API-key rotation proxy for LLM providers, living under
`~/sovereign/keypool/` and served by `~/sovereign/bin/herd-keypool.py`.

Listens on `127.0.0.1:25109`. Path-routed: `/<pool>/<rest>` forwards to
the pool's `upstream + <rest>` with a health-checked key chosen per
request. Key values never appear in logs, `/status`, or the audit file —
only names, sha256 prefixes, states, and latencies.

## Why

One address in front of N keys per provider, so callers change a base
URL instead of their auth. Handles the Gemini Interactions EAP wire
protocol (`/v1beta/interactions`, `tool_search`, `defer_loading`,
`mcp_server`) by translating OpenAI-shaped bodies in and Interactions-
shaped bodies out.

## Patterns

Each lives in its own file and is imported where used.

| # | Pattern                 | File             | What it does                                                           |
|---|-------------------------|------------------|------------------------------------------------------------------------|
| 9 | Monotonic clock         | `clock.py`       | All intervals on `time.monotonic()`; NTP steps can't invert cooldowns  |
| 6 | Error taxonomy          | `errors.py`      | SWITCH / SURFACE / SOFT; only SWITCH parks a key                       |
| 1 | Proactive rate guard    | `ratelimit.py`   | Parse `x-ratelimit-*`; skip a key before it 429s                       |
| 7 | Retry-After parsing     | `ratelimit.py`   | 3 header formats + Go-duration                                         |
| 2 | Circuit breaker         | `circuit.py`     | CLOSED → OPEN → HALF_OPEN per pool; fail fast during provider outage   |
| 3 | Adaptive scoring        | `scoring.py`     | Weighted score + weighted-random pick over top-N                       |
| 4 | Capacity phases         | `capacity.py`    | Inflight counter; spread-then-stack concurrency                        |
| 5 | Prompt-cache affinity   | `affinity.py`    | Session → key binding; keeps provider prompt cache warm                |
| 8 | Abort-aware backoff     | `backoff.py`     | ±25% jitter + interruptible wait                                       |
|10 | Atomic persistence      | `persist.py`     | Write-temp + `os.replace` for health state                             |
|11 | Session GC              | `affinity.py`    | TTL sweep on bound sessions; no unbounded growth                       |
|12 | Cross-provider cascade  | `pool.py`        | Config `cascade:` lists a fallback chain on total pool failure         |
|13 | Non-blocking alerts     | `alerts.py`      | Bounded queue + daemon worker; rotation never waits on a webhook       |

## Layout

    ~/sovereign/keypool/
    ├── README.md         this file
    ├── __init__.py       version + docstring
    ├── __main__.py       entry point (`python3 -m keypool`)
    ├── clock.py          pattern 9
    ├── errors.py         pattern 6
    ├── ratelimit.py      patterns 1, 7
    ├── circuit.py        pattern 2
    ├── scoring.py        pattern 3
    ├── capacity.py       pattern 4
    ├── affinity.py       patterns 5, 11
    ├── backoff.py        pattern 8
    ├── persist.py        pattern 10
    ├── alerts.py         pattern 13
    ├── secrets.py        file/dir secrets loader
    ├── yamlparse.py      PyYAML with a tiny fallback
    ├── translate.py      OpenAI ↔ Interactions wire
    ├── state.py          KeyState
    ├── pool.py           Pool (wires the patterns)
    ├── proxy.py          HTTP handler + pattern 12
    └── selftest.py       pattern assertions, no network

`~/sovereign/bin/herd-keypool.py` is a 5-line shim that calls
`keypool.__main__.main()`. Pitchfork and mise both point at that shim,
so the interface to the supervisor never changed.

## Operations

Managed by pitchfork (`~/sovereign/pitchfork.toml`, daemon `keypool`):

    mise run restart-keypool
    mise run health-keypool
    mise run keypool-selftest        # added
    mise run keypool-status          # added

Or directly:

    pitchfork restart keypool
    pitchfork logs keypool -n 100
    curl -s http://127.0.0.1:25109/health | jq
    curl -s http://127.0.0.1:25109/status | jq

Reload after editing `keypools.yaml` (no restart, no dropped requests):

    kill -HUP "$(pgrep -f herd-keypool.py)"

## Config

`~/sovereign/config/keypools.yaml`:

    pools:
      <pool>:
        upstream: https://...
        protocol: gemini-interactions      # optional; enables wire translation
        interactions_path: /v1beta/interactions
        health:  {method: GET, path: /x, ok: [200]}
        fail_status: [400, 401, 402, 403, 404, 429]
        cooldown: {401: 300, 429: 60, default: 120}
        keys:    [K1, {name: K2, free_only: true}]
        capacity: {optimal: 2, max: 8}     # pattern 4
        circuit:  {failure_threshold: 5, recovery_timeout: 120}  # pattern 2
        affinity: {ttl: 3600}              # pattern 5
        cascade:  [other-pool, ...]        # pattern 12

Key **values** live only in `~/.secrets`. The config references them by
name. Adding a key is a one-line append to `.secrets` plus a name in the
`keys:` list; `kill -HUP` picks it up.

## Calling

OpenAI shape:

    curl -s http://127.0.0.1:25109/gemini-eap-openai/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -d '{"model":"gemini-2.5-flash","messages":[{"role":"user","content":"hi"}]}'

Gemini Interactions EAP (tool retrieval):

    curl -s http://127.0.0.1:25109/gemini-eap-interactions/v1beta/interactions \
      -H 'Content-Type: application/json' \
      -d '{"model":"gemini-flash-tool-retrieval","input":"say ok",
           "tools":[{"type":"tool_search"}]}'

Session stickiness is opt-in via `X-Session-Id: <opaque>`. Same session
→ same key until failure. Useful when the provider caches the prompt.

## Testing

    python3 -m keypool --selftest
    mise run keypool-selftest

Asserts each pattern in isolation against a mock; no network access,
no credentials touched. Exit 0 = pass.

## Adding a pattern

1. Add `<pattern>.py` with one clear responsibility.
2. Import it where it's needed (`pool.py` for selection-adjacent, `proxy.py`
   for request-path-adjacent).
3. Add an assertion to `selftest.py`.
4. Add a row to the pattern table above.

## What this replaced

`~/sovereign/bin/herd-keypool.py` was a 38 KB monolith. The new entry
shim keeps the same filename so pitchfork and mise config are unchanged.
The old file was backed up next to it as
`herd-keypool.py.pre-modular.<timestamp>`.
