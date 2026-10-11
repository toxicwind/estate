---
name: flicker
description: >
  mbx (mise remote task cache, :25148) is the default build dispatch. Run `mise run <task>` or `mise exec -- <cmd>`; mbx-cache restores eligible task artifacts. The old flicker job daemon is RETIRED. Triggers on: "flicker", "build daemon", "job submit", "mbx", "build dispatch".
---

# mbx — Default Build Dispatch (flicker retired)

**Default: build through `mise`; `mbx-cache` is the remote task cache.**
`flicker` (the old HTTP job daemon at :25148) is retired — its `/api/jobs` endpoint,
the `brand/queue` JSON queue, and the flicker-agent are gone. Do not reintroduce a
queue shim: cache and execution are separate responsibilities (KB §7).

## The one line

```bash
mise run <task>        # cacheable task with declared sources/outputs (default)
mise exec -- <cmd>     # ad-hoc command; mise toolchain resolves
```

## How it works

- `mbx-cache` is the estate's mise remote task cache: a direct Rust binary built from
  pinned `vendored/mr-boxington-cache` (upstream v0.1.1). No Docker, no worker, no queue.
- Supervised by pitchfork as `estate/mbx-cache`; listens loopback-only on
  `127.0.0.1:25148` (`MBX_CACHE_PORT` in `config/ports.env`).
  Launcher: `ops/mbx-cache/run.sh`; data: `var/runtime/mbx-cache`.
 - Client config: `mise/conf.d/15-remote-cache.toml` —
   `task.cache.remote_url = "http://127.0.0.1:25148"`, namespace `"estate"`,
   mode `"read-write"`. This tells mise WHERE the cache is; it does NOT enable
   caching for any task by itself.
 - **Opt-in is per-project (mise 2026.10.0):** the global `[task_config.cache]
   enabled = true` in `mise/conf.d/` does NOT cascade to project tasks — verified
   2026-10-03. Every project that wants caching MUST set it in its own `mise.toml`,
   either per-task (`cache = { enabled = true }` alongside declared `sources` and
   `outputs`) or project-wide (`[task_config.cache] enabled = true` in the
   project's own `mise.toml`). Without this, `mise run` executes every time and
   never consults the cache — the global config alone is silently ignored.
 - Caught 2026-10-03: `ranch/squawk/mise.toml` claimed "mbx-cache enabled" but the
   setting was missing; tasks never hit the cache. Fixed in toxicwind/estate
   commit `5d78f1e` (added `[task_config.cache] enabled = true` to the project's
   own mise.toml). Proven: `mise run probe` cold 3.06s → warm 0.058s (restored
   from mbx-cache).
 - The first run is a cache miss and executes; deleting the outputs and re-running
   reports `restored outputs from cache <digest>` instead of re-executing.
- **Fallback is built in:** if mbx-cache is unreachable, mise treats it as a normal
  cache miss and executes locally. There is no separate fallback path to maintain.

## Health check

```bash
curl -fsS http://127.0.0.1:25148/v1/status   # {"protocol":1,"status":"ok"}
ss -ltn | grep 25148                          # mise-cache on 127.0.0.1:25148
```

## Retired flicker surface (do not use)

- HTTP API `POST /api/jobs`, `GET /api/jobs/:id`, `GET /api/jobs/:id/logs` — gone.
  :25148 now serves mbx-cache (`/v1/status`).
- `flicker` CLI (`~/.local/bin/flicker`) — replaced with a redirect shim that prints
  this pointer and exits 1.
- `helpers/push-build.sh` no longer writes `$HOME/brand/queue` JSON; it runs
  `mise exec -- bun install && mise exec -- bun run build` directly.
- `ranch/flicker/` source tree is retired (kept for reference).
