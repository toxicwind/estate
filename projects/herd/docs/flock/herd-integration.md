# flock × herd integration

## Who dials flock

| Caller | How |
|---|---|
| sovereign-router-ts `nvidia` provider | `http://127.0.0.1:8000` (OpenAI-compatible) |
| AstMatrix (Go) | provider definition points at upstream `integrate.api.nvidia.com/v1`; flock is the optional local enforcement layer |

## Ownership

- **AstMatrix owns provider definitions.** Model lists, base URLs, and strategy
  live in `projects/herd/internal/astmatrix/`.
- **flock owns local enforcement.** Rate limiting, history, dashboard, key
  handling for the NIM surface. It does not define herd's provider catalog.

## Naming

Renamed in full 2026-09-17: `nim-proxy` → `flock` (crate, strings, icons,
daemon, docs). Upstream provenance (miztertea/nim-proxy, MIT) is preserved in
`proxy/Cargo.toml` and the OpenAPI contact block.
