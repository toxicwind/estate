# sovereign

Private local agent stack: Grok Build, OpenFang, llama-swap on a single workstation (RTX 3090 / sm_86).

**Orchestration:** mise + modular process-compose + **pacman system packages**.  
**Not used:** nix, devbox, devenv, vLLM, docker (core stack).

## Quick start

```bash
# one-time (Arch/CachyOS)
sudo pacman -S --needed process-compose-git caddy prometheus curl

cd ~/sovereign
mise run up             # sovereign: core + yote + rust-dash
mise run health
```

Profiles:

| Command | What |
|---------|------|
| `mise run up` | **sovereign** — llama-swap, openfang, prometheus, caddy, **yote**, **rust-dash** |
| `mise run up-core` | core only (no yote/rust) |
| `mise run up-full` | sovereign + landing, watchdog, hf-downloader |

Stop: `mise run down`

## LLM routing

| Endpoint | Role |
|----------|------|
| `:25021` | **Ingress** — llama-swap (all clients) |
| `:25001` | Upstream — spawned on demand per model |
| `:25004` | OpenFang |

Default model: `beellama/qwen-flash` (9B IQ4_XS). Legacy swap id `llama` maps to the same.

```bash
curl -s http://127.0.0.1:25021/v1/models | jq '.data[].id'
```

Config: `tools/llama-swap/config.yaml`  
Builds: beellama, turboquant, ik_llama, ik_turboquant under `~/projects/`.

## Stack layout

```
sovereign/
├── mise.toml                 # task aliases
├── stack/
│   ├── ports.env             # port SSoT
│   ├── profiles.sh           # core | full
│   ├── modules/*.yaml        # one process per file
│   ├── services/             # service entrypoints
│   └── up.sh / down.sh / health.sh
├── bin/                      # thin wrappers
├── tools/llama-swap/
├── src/                      # openfang, watchdog, landing, …
└── process-compose.yaml      # generated compat (stack/modules is canonical)
```

| Profile | Processes |
|---------|-----------|
| `core` | llama-herder, openfang, prometheus, caddy |
| `sovereign` | core + **yote** (:25042), **rust-dash** (:25005) |
| `full` | sovereign + landing, watchdog, hf-downloader |

```bash
./stack/up.sh -D sovereign
./stack/build-compose.sh
```

## Ports (`stack/ports.env`)

| Port | Service |
|------|---------|
| 25000 | Caddy (routes `/rank*`, `/yote*` → backends) |
| 25004 | OpenFang |
| 25005 | **rust-dash** — DevOps advisor + ranking UI |
| 25021 | llama-swap |
| 25030 | Prometheus |
| 25042 | **yote** — Telegram bot orchestrator |

## Client config

```toml
# ~/.grok/config.toml
[model.llama]
model = "beellama/qwen-flash"
base_url = "http://localhost:25021/v1"
```

GGUF models live in `~/projects/models/` (not in this repo).

## Repo

Private: [github.com/toxicwind/sovereign](https://github.com/toxicwind/sovereign)