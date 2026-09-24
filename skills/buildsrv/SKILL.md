---
name: buildsrv
description: Pitchfork build daemon interface (port 25148) for accelerated, forward-only Rust, Go, Bun, and Python builds and tests with sccache/ccache and log streaming.
---

# buildsrv — Accelerated Build Daemon

`buildsrv` is the project-scoped, pitchfork-supervised build daemon listening on `127.0.0.1:25148`. It offloads compile, test, and typecheck workloads away from interactive agent loops into an NVMe-cached execution runner.

## Why buildsrv Matters

1. **NVMe sccache / ccache Acceleration**:
   - Compiles leverage persistent NVMe-backed compiler caches (`sccache` for Rust/C/C++, `ccache` for C/C++, hot cache directories for Go and Bun).
   - Eliminates redundant recompilations across agent turns and parallel subagents.
2. **Forward-Only Build Semantics**:
   - Enforces forward-only build invariants (no rolling back to older, incompatible compiler caches or artifacts).
   - Prevents stale artifact cross-contamination between parallel workers.
3. **Structured Log Streaming**:
   - Stdout and stderr are captured and streamed asynchronously with line markers.
   - Eliminates terminal lockup and buffer truncation during long compilation pipelines.

## When to Use

Use `buildsrv` whenever executing non-trivial build or verification operations:
- **Rust / Cargo**: `cargo build`, `cargo check`, `cargo test`, `cargo clippy`.
- **Go**: `go build ./...`, `go test ./...`, `go vet ./...`.
- **Bun**: `bun build`, `bun test`, `bun run tsc --noEmit`.
- **Python**: `pytest`, `mypy`, `ruff check`.

Do **not** use `buildsrv` for trivial fact-finding commands (e.g. `which`, `ls`, small regex searches) or pure file edits.

## Health Check & Status

The daemon exposes an HTTP status endpoint on port 25148:

```bash
# Basic health check via HTTP
curl -fsS http://127.0.0.1:25148/health

# Or via CLI
buildsrv health

# Response format:
# {"ok": true, "uptime_s": ..., "queue_depth": 0, "running": [], "workers": 2, "active_threads": 0, "counters": {"failed": ..., "succeeded": ...}}
```

## CLI Usage

### 1. Submit a Build Job (`buildsrv submit`)

Submits a command to be executed in the target workspace under daemon supervision:

```bash
# Submit a Rust release build
buildsrv submit --name "sovereign-cargo-build" --repo /home/toxic/sovereign --toolchain cargo --cmd "cargo build --release"

# Submit a Bun test suite
buildsrv submit --name "sovereign-bun-test" --repo /home/toxic/sovereign --toolchain bun --cmd "bun test"

# Submit a Python test suite
buildsrv submit --name "sovereign-pytest" --repo /home/toxic/sovereign --toolchain python --cmd "pytest"

# Submit a Go check
buildsrv submit --name "sovereign-go-build" --repo /home/toxic/sovereign --toolchain go --cmd "go build ./..."
```

### 2. Inspect Job Status (`buildsrv status` / `buildsrv list`)

Check the lifecycle state of a queued or running build, or list recent jobs:

```bash
# Check status of a specific job
buildsrv status <job-id>

# Check status of recent jobs
buildsrv status -n 10

# List recent jobs
buildsrv list
```

### 3. Stream or Inspect Logs (`buildsrv logs`)

Inspect build output or follow live progress:

```bash
# Follow live compilation logs
buildsrv logs -f <job-id>

# Fetch the last 100 lines of captured logs
buildsrv logs -n 100 <job-id>
```

### 4. Wait / Completion Protocol

To wait on a running job:
```bash
# Using CLI status polling
while true; do
  STATUS=$(buildsrv status <job-id> | jq -r .status)
  if [ "$STATUS" = "succeeded" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 1
done
```

## Fallback & Error Protocol

If `buildsrv` is unreachable or down:
1. Verify pitchfork process status:
   ```bash
   pitchfork status buildsrv
   ```
2. If restarting through pitchfork is permitted, restart the service:
   ```bash
   pitchfork restart buildsrv
   ```
3. If the daemon remains unavailable, fall back to direct scoped CLI execution, noting the lack of NVMe cache acceleration.
