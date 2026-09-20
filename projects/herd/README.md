# herd — Inference Front Door

`herd/` is the **toxicwind fork of llama-swap** (Go, module `github.com/mostlygeek/llama-swap`). It serves the stack's single OpenAI-compatible endpoint. Cloud-provider routing is delegated to the **flock** daemon on `127.0.0.1:8000` via the `flock:` config key — the in-process `internal/flock` Go router was retired 2026-09-17 and the shipped binary ignores the `astMatrix:` config key with a warning (see `README_FLOCK_V2.md`).

- **Upstream:** <https://github.com/mostlygeek/llama-swap>
- **Fork:** <https://github.com/toxicwind/llama-swap>
- **Live service:** pitchfork `herd` → `http://127.0.0.1:25100` (`/v1`, `/ui`, `/health`), launched by `stack/services/herd.sh` with `config/herd.yaml`

## What's in here

| Path | Role |
| ---- | ---- |
| `llama-swap.go`, `internal/` | Fork source (upstream + our additions) |
| `internal/flock/` | flock Go router — RETIRED from the shipped binary 2026-09-17 (tree-only; live cloud routing is the `:8000` flock daemon via the `flock:` key). Kept: 8 strategies, 13 cloud providers, SQLite health DB (see `README_FLOCK_V2.md`) |
| `config.yaml` | Symlink -> ../../config/herd.yaml (canonical; was a stale autoscan copy) |
| `MODEL_INVENTORY.md` | Local GGUF / model-id audit for this host |
| `TUNING.md` | Performance tuning notes |
| `model-profiles.json` | Model profiles |

The supervised service builds from `sovereign-projects/sovereign-swap`; this tree is the vendored fork source. Don't treat this README as upstream docs — upstream usage lives in the fork repo.

## Why a fork

Sovereign clients (Zed's llama.cpp provider, OpenFang, IDE copilots) need:

1. Stable **OpenAI-compatible streaming** across differing backends → `normalize_sse`
2. **Model discovery events** for Zed → `GET /models/sse`
3. Port reclaim when an orphan `llama-server` holds a slot → pre-spawn `fuser -k`
4. **IPv4 loopback** defaults (`127.0.0.1`) so dual-stack `localhost` doesn't break dials

## Backends

`config/herd.yaml` maps model aliases to three llama.cpp engine builds on `:25001–:25099`: beellama.cpp, llama-cpp-turboquant, and ik_llama.cpp. (The vendored `herd/config.yaml` also defines a fourth, ik_llama.cpp's turboquant build, but the live `config/herd.yaml` does not use it.)

## Operate

```bash
curl -sS http://127.0.0.1:25100/health          # → OK
curl -sS http://127.0.0.1:25100/v1/models | python3 -c "import sys,json;print([m['id'] for m in json.load(sys.stdin)['data'] if m['id'].startswith('flock:')][:5])"  # cloud models via flock daemon
pitchfork restart herd                           # restart the service
```

Rebuild the fork binary:

```bash
# This tree builds standalone: `go build` succeeds here (internal/config is
# present; verified 2026-09-20). The supervised production service builds
# from sovereign-projects/sovereign-swap
# (binary: ~/projects/sovereign-projects/sovereign-swap/build/llama-swap).
```

## Self-healing peers (2026-09-20)

Every `peers:` entry carries an event-driven health state machine
(`internal/router/peer_health.go`, knobs in `internal/config/health.go`):

- **States:** `healthy` -> `degraded` (advisory; still serves) ->
  `circuit-open` (ejected from rotation; requests fail fast with
  structured 503 `peer_circuit_open`) -> `half-open` -> `healthy`.
- **No polling.** The half-open probe is the next *real* request after
  `cool_off_seconds`, admitted single-flight. No timers, sleeps, or
  background health checks anywhere in the path.
- **Clean slate on recovery.** A successful probe readmits the peer with the
  failure score reset to zero: re-ejection needs the full configured
  threshold of *fresh* evidence. A recovered peer is never one failure away
  from the circuit reopening. (The rolling error window is telemetry, not
  score: a just-recovered peer may briefly read as `degraded` while the
  window still holds the earlier failures — it stays in rotation.)
- **Taxonomy:** every outcome is classified per the reliability taxonomy --
  `402-not-entitled`, `404-dead-id`, `429-throttled`, `200-empty`,
  `403-refused`, `5xx`, `transport`, `success` (aligned with
  `projects/openrouter-probe/probe_reliability.py`). Each failure adds
  its class weight to a score; each success subtracts `recovery_credit`.
  Score >= `failure_threshold` opens the circuit.
- **Scoring:** EWMA latency plus a rolling 32-outcome error window drive
  the `degraded` signal; every state change emits a structured transition
  log (peer id, states, class, score -- never URLs, headers, bodies,
  or secrets).
- **Config:** optional `health:` block per peer in `config/herd.yaml`
  (see `config.example.yaml` and `config-schema.json`); enabled with
  conservative defaults when absent. `enabled: false` opts a peer out.
  Model selection stays in router config -- no model IDs are hardcoded.
- **Observe:** `GET /peer-health` returns per-peer state, EWMA latency,
  error rate, failure score, and retry-after.
- **Prove it:** `scripts/probe-peer-health.sh` drives the full
  failure -> ejection -> recovery -> readmission cycle against a scripted
  backend and asserts every step. The driver is fully event-driven: process
  readiness is signaled over named pipes, ports are allocated collision-free,
  and the cool-off is never slept through — instead the herd runs twice
  (long cool-off proves fail-fast 503; 5ms cool-off makes the first real
  request after recovery the half-open probe). No sleeps, no polling loops,
  no timer delays.

Borrowed discipline: sony/gobreaker closed/half-open/open two-step
admit/report with a generation guard; EWMA + rolling-window signals per
current routing literature (HACO 2607.19215, SkyWalker 2505.24095, vLLM
Semantic Router 2603.04444).

Hot-path overhead (AMD Ryzen 7 8700F, `go test -bench`):
`BenchmarkAdmit` 9.6 ns/op, `BenchmarkClassifyOutcome` 261 ns/op,
`BenchmarkReportSuccess` 747 ns/op — about 1 microsecond per proxied
request, dominated by proxy latency by three orders of magnitude.

## Related

- Router module docs: `README_FLOCK_V2.md`
- Stack rules: `AGENTS.md` (repo root)
- Ops dashboard backend: `http://127.0.0.1:25201/` (`RUST_WEB_BACKEND_PORT` per `config/ports.env`). NOTE: `RUST_WEB_PORT=25101` in ports.env is stale — :25101 is model-guard per `pitchfork.toml` (flagged for the fleet; ports.env not yet updated).

---
*Up: [master README](../../README.md) · [projects/](../README.md) · [fleet knowledgebase](../../docs/fleet-knowledgebase.md)*
