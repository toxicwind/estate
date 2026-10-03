---
name: mbx-cache
description: Direct local mise remote task cache. Use for build-cache health, cache debugging, and rebuilding the pinned mbx-cache binary.
---

# mbx-cache

`mbx-cache` is the estate's local remote cache for mise task artifacts and
mr-boxington build outputs. It replaces flicker/woodpecker; it is **not** a job
queue or a container runner.

## Ownership

| Fact | Owner |
|---|---|
| daemon lifecycle | `pitchfork.toml` `[daemons.mbx-cache]` |
| port | `config/ports.env` `MBX_CACHE_PORT=25148` |
| launcher | `ops/mbx-cache/run.sh` |
| upstream source | `vendored/mr-boxington-cache` pinned at v0.1.1 |
| runtime data | `var/runtime/mbx-cache` |
| client configuration | `mise/conf.d/15-remote-cache.toml` |

The server is a direct Rust binary built with mise. No Docker, Podman, agent,
job API, or copied credential exists in this path. It binds loopback and allows
anonymous access only because nothing outside the host can reach it.

## Health

```bash
curl -fsS http://127.0.0.1:25148/v1/status
curl -fsS http://127.0.0.1:25148/v1/capabilities
```

Expected capability contract: protocol major 1, `task` action kind, BLAKE3 and
SHA-256, immutable action results and manifests.

## Rebuild

```bash
cd /home/toxic/estate/vendored/mr-boxington-cache
mise exec -- cargo build --release
```

The estate Cargo workspace explicitly excludes this vendored crate. That
boundary is required: otherwise Cargo captures it into the estate workspace and
fails on estate-only Rust members before the upstream build begins.

## Verify cache restore

A cache-enabled mise task needs declared `sources` and `outputs`. First run is
a miss; after deleting the declared output, the second run must say:

```text
restored outputs from cache <digest>
```

A remote cache stores successful task artifacts. It does not schedule builds;
run the build with `mise run <task>` and use the cache for reuse.