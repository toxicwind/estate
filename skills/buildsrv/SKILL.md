---
name: buildsrv
description: NativeLink build server.
---

# NativeLink & Build Infrastructure

NativeLink is the primary build server across the estate.
It provides REAPI caching and execution for Bazel, Cargo, and Bun.
It replaces the legacy buildsrv daemon.
Pitchfork supervises the service.

## Architecture

NativeLink runs on two ports:
- Frontend endpoint: `127.0.0.1:25155`.
- Worker endpoint: `127.0.0.1:25157`.
- Pitchfork daemon: `nativelink`.
- CAS storage path: `var/runtime/nativelink/`.

The mbx-cache service handles tasks:
- HTTP endpoint: `127.0.0.1:25148`.
- Pitchfork daemon: `mbx-cache`.
- Serves as the mise remote task cache.

Shared compiler caches include `sccache` and `ccache`.
Python wheels use `uv`.

## Bazel Remote Cache

In `estate/ranch/tau/.bazelrc`:
```ini
build --remote_cache=grpc://127.0.0.1:25155
build --remote_upload_local_results=true
build --remote_local_fallback
```

## Health Checks

```bash
ss -tulpn | grep -E "25155|25157"
pitchfork status nativelink
pitchfork status mbx-cache
```
