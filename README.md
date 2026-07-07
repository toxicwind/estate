# sovereign

Private local agent stack: Grok Build, OpenFang, llama-swap on a single workstation (RTX 3090 / sm_86).

**Orchestration:** mise + modular process-compose + **pacman system packages**.  
**Not used:** nix, devbox, devenv, vLLM, docker (core stack).

## Quick start

```bash
# one-time (Arch/CachyOS)
sudo pacman -S --needed process-compose-git caddy prometheus curl

cd ~/sovereign
mise run up-core        # llama-swap, openfang, prometheus, caddy
mise run health
```

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
| `full` | core + landing, watchdog, hf-downloader, yote |

```bash
./stack/up.sh -D core
./stack/build-compose.sh      # flatten → process-compose.yaml
```

## Ports (`stack/ports.env`)

| Port | Service |
|------|---------|
| 25000 | Caddy |
| 25004 | OpenFang |
| 25021 | llama-swap |
| 25030 | Prometheus |

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