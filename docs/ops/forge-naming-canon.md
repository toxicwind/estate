# Build daemon naming canon: forge = the name; flicker = the fork; mbx = the client

Why the ecosystem had three names, and the canonical resolution (2026-10-19).

## Roles

| Name | What it is | Status |
|---|---|---|
| **forge** | The ranch build daemon on `:25148` — the name that faces outward (pitchfork daemon `estate/forge`, ports SSOT `MBX_CACHE_PORT=25148`, repo `ranch/forge`) | **canonical** |
| **flicker** | The underlying ENGINE: a stripped Woodpecker-v3 Go fork ("flicker-server") that runs jobs through shell login sessions and returns `CACHED` for identical job specs. Lives at `ranch/forge/flicker/` | internal engine |
| **mbx** | The CLIENT nickname for the same system ("mise + flicker = mbx-cache"). `MBX_CACHE_PORT=25148` in ports.env is the forge daemon's port, not a separate service | client alias |

They are **one system**, not three: mbx-cache talks to flicker-server, which
lives under the forge repo. `ranch/forge/README.md` documents the full stack
(REAPI NativeLink :25155, forge daemon :25148, woodpecker CI fork).

## The naming problem (2026-10-19)

- The pitchfork daemons pointed at `var/reconciliation/flicker/bin/` — a
  **stale runtime copy** (var/ is runtime state, and the real source is
  `ranch/forge/flicker`). Every boot tried to exec a binary that was gone.
- Worse: `estate/forge` was disabled briefly during archaeology — WRONG; forge
  is the live build daemon and was re-enabled, rebuilt, and rejoined.
- `flicker` appeared in ~4 different path/name surfaces ("flicker makes no
  sense", the user said — correct: it's just the engine name of the forge daemon).

## Canonical names (single source of truth)

```
binary:   ranch/forge/flicker/bin/forge-server     (fresh build 2026-10-19,
          dist/woodpecker-server copied + aliased; symlinks flicker-server,
          woodpecker-server -> forge-server for compat)
agent:    ranch/forge/flicker/bin/forge-agent      (symlink flicker-agent)
daemon:   estate/forge       -> forge-server   :25148  (pitchfork.toml + .d)
          estate/forge-agent -> forge-agent   (worker)
config:   FLICKER_ROOT = ranch/forge/flicker (env in daemon block; name kept for code compat)
repo:     ranch/forge (umbrella: gateway/router/woodpecker/nativelink docs)
engine:   flicker (the Go fork name inside the repo; not user-facing)
client:   mbx (mise task-cache client; `mise run` reaches it)
```

## Build (fresh, verified 2026-10-19)

```bash
cd /home/toxic/estate/ranch/forge/flicker
corepack enable --install-directory /home/toxic/.local/bin   # pnpm for web/
make build-server   # -> dist/woodpecker-server
make build-agent    # -> dist/woodpecker-agent
cp dist/woodpecker-server bin/forge-server && ln -sf forge-server bin/flicker-server
cp dist/woodpecker-agent  bin/forge-agent  && ln -sf forge-agent  bin/flicker-agent
```

## Health

```bash
curl -fsS http://127.0.0.1:25148/api/health   # {"cache":{"entries":N},"ok":true,"running":0,"service":"flicker",...}
pitchfork status estate/forge estate/forge-agent
```