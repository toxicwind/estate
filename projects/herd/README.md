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
# NOTE (2026-09-19): this vendored tree is missing internal/config and does NOT
# build standalone (`go build` fails: no required module provides
# github.com/mostlygeek/llama-swap/internal/config). The supervised service
# builds from sovereign-projects/sovereign-swap
# (binary: ~/projects/sovereign-projects/sovereign-swap/build/llama-swap).
# Do not run `go build` here until internal/config is restored to this tree.
```

## Related

- Router module docs: `herd/README_FLOCK_V2.md`
- Stack rules: `AGENTS.md` (repo root)
- Ops dashboard: `http://127.0.0.1:25101/` (RUST_WEB_PORT per `config/ports.env`) — APIs under `/ops/api/*`. NOTE 2026-09-19: nothing is listening on :25101; the dashboard service is down.
