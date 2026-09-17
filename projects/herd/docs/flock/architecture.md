# flock architecture

```
                ┌─────────────────────────────────────────┐
                │  flock proxy (Rust)  127.0.0.1:8000      │
                │  rate limiting · history store ·        │
                │  dashboard · OpenAI-compatible API      │
                └───────────────┬─────────────────────────┘
                                │ upstream
                                ▼
                  integrate.api.nvidia.com/v1
```

| Component | Path in `/home/toxic/projects/flock/` | Role |
|---|---|---|
| `proxy/` | Rust service | Local enforcement point: rate limits, request history, operator dashboard, OpenAI-compatible front |
| `client/` | TS + Python clients | Programmatic access to NIM |
| `dashboard/` | Bun dashboard | Benchmark visualization |
| `tools/` | `nvt.py`, `nvidia_nim_inference.py` | CLI toolkit, free-tier inference |
| `research/` | Go research | Inkling API research |
| `benchmarks/` | moonbox trees | Benchmark snapshots + live runs |

flock never serves local models. Local inference is herd/llama-swap's job.
flock is the API-side counterpart to AstMatrix: AstMatrix **owns the canonical
provider definitions** (see `internal/astmatrix/providers.go` — nvidia →
`https://integrate.api.nvidia.com/v1`); flock is the local enforcement point
the routers actually dial.
