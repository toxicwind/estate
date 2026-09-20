# Herd — Inference Front Door (llama-swap fork)

**herd/** is the **toxicwind llama-swap fork** (Go): the OpenAI-compatible
inference front door for the whole Sovereign stack.

- **Upstream:** [mostlygeek/llama-swap](https://github.com/mostlygeek/llama-swap)
- **Port:** `:25100` (`LLAMA_SWAP_PORT` / `HERD_PORT` — SSOT in `config/ports.env`)
- **Backends:** llama-server slots on `:25001–25099`

## Why a fork

Sovereign clients (Zed llama.cpp provider, OpenFang `provider = "llama"`, Grok,
IDE copilots) need:

1. Stable **OpenAI-compatible streaming** even when backends differ → `normalize_sse`
2. **Model discovery events** for Zed → `GET /models/sse`
3. Reliable restarts when an orphan `llama-server` holds ports → pre-spawn port reclaim
4. **IPv4 loopback** defaults (`127.0.0.1`) so dual-stack `localhost` does not break dial
5. Native multi-provider routing → AST Matrix Go port (`internal/astmatrix/`)

## Layout

| Path                                      | Role                                                                          |
| ----------------------------------------- | ----------------------------------------------------------------------------- |
| `llama-swap.go`, `internal/`, `go.mod`    | Fork source (Go)                                                              |
| `internal/astmatrix/`                     | AST Matrix router: 6 strategies, ELO scoring, circuit breakers, SQLite WAL health DB |
| `config.yaml`                             | Live config (RTX 3090 / sm_86, routing matrix, macros for llama.cpp forks)   |
| `config.example.yaml`, `config.local.yaml`| Config templates                                                              |
| `MODEL_INVENTORY.md`, `model-profiles.json`| Local GGUF / model-id audit for this host                                    |
| `ui-svelte/`                              | Router/swap dashboard UI                                                      |
| `mesh/`                                   | Mesh-side integration                                                         |
| `scripts/`, `patches/`                    | Build scripts and patch sets                                                  |
| `docs/`, `TUNING.md`, `model-profiles.md` | Docs and tuning notes                                                         |

## Operate

```bash
# via sovereign stack
cd /home/toxic/sovereign && mise run up     # includes llama-swap module
mise run restart-llama
mise run health

# build + run the fork binary directly
cd herd && go build -o llama-swap .
./llama-swap -config config.yaml -listen 127.0.0.1:25100
```

Health: `curl -sS http://127.0.0.1:25100/health` → `OK`

## Ports (SSOT: `config/ports.env`)

| Env                                 | Port        | Surface               |
| ----------------------------------- | ----------- | --------------------- |
| `LLAMA_SWAP_PORT` / `HERD_PORT`     | **25100**   | Proxy + `/ui` + `/v1` |
| `LLAMA_START_PORT`–`LLAMA_END_PORT` | 25001–25099 | Backend slots owned by swap |

## Related

- Stack rules: `/home/toxic/sovereign/AGENTS.md` — **no vLLM**
- Ops dashboard (rust-web): `http://127.0.0.1:25101/` — APIs under `/ops/api/*`
- AST Matrix details: `README_ASTMATRIX_V2.md` (in this directory)
