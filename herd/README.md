# herd — Inference Front Door

`herd/` is the **toxicwind fork of llama-swap** (Go, module `github.com/mostlygeek/llama-swap`) with the **AST Matrix** cloud-provider router compiled in. It serves the stack's single OpenAI-compatible endpoint.

- **Upstream:** <https://github.com/mostlygeek/llama-swap>
- **Fork:** <https://github.com/toxicwind/llama-swap>
- **Live service:** pitchfork `herd` → `http://127.0.0.1:25100` (`/v1`, `/ui`, `/health`), launched by `stack/services/herd.sh` with `config/herd.yaml`

## What's in here

| Path | Role |
| ---- | ---- |
| `llama-swap.go`, `internal/` | Fork source (upstream + our additions) |
| `internal/astmatrix/` | AST Matrix Go router — 8 strategies, 13 cloud providers, SQLite health DB (see `README_ASTMATRIX_V2.md`) |
| `config.yaml` | Vendored routing matrix + backend config reference |
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

`config/herd.yaml` maps model aliases to four llama.cpp engine builds on `:25001–:25099`: beellama.cpp, llama-cpp-turboquant, ik_llama.cpp, and ik_llama.cpp's turboquant build.

## Operate

```bash
curl -sS http://127.0.0.1:25100/health          # → OK
curl -sS http://127.0.0.1:25100/astmatrix/status # router status
pitchfork restart herd                           # restart the service
```

Rebuild the fork binary:

```bash
cd /home/toxic/sovereign/herd
go build -o llama-swap .
```

## Related

- Router module docs: `herd/README_ASTMATRIX_V2.md`
- Stack rules: `AGENTS.md` (repo root)
- Ops dashboard: `http://127.0.0.1:25101/` — APIs under `/ops/api/*`
