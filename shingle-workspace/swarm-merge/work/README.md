# NvidiaLensSwarm

NVIDIA NIM + OpenAI-Swarm-style multi-agent orchestration, with lens profiles
and async DAG execution. **Maximal-merge branch**: a coherent consolidation of
the repo's swarm runtime, two Drive research monoliths, and the live NIM API
layer (fail-fast model audit, 2026-09-14).

## What this is

- **`nim/`** — the shared NIM API layer. Every model call routes through it.
  OpenAI-compatible `POST /v1/chat/completions` against
  `https://integrate.api.nvidia.com/v1`, 5s fail-fast timeouts, model-aware
  cold-start handling, typed errors (auth / 404-gated / 410-EOL / deprecated /
  timeout / stream-stall). Auth: Secure Vault surrogate → `NVIDIA_API_KEY` →
  clean error. Never silently mocks.
- **`swarm/`** — async DAG execution engine (`nvidia_swarm_core.py`:
  layered topological execution, per-node latency/TTFT/TPS), model-neutral
  agents (`nvidia_swarm_agent.py`, JSON or `<tool_call>` tag grammars),
  transport (`nvidia_swarm_transport.py`, fail-fast aiohttp), ArchiveFS
  (chunked binary archives, ported from the Drive monolith and hardened),
  transport tuning presets (`transport_profiles.py`).
- **`lens/`** — five canonical lens profiles (research, code, analysis,
  orchestrator, proof) with live-model defaults and `build_swarm_from_lens()`.
- **`swarm_maximal.py`** — one-command maximal runner (preset + lens DAG).
- **`launcher.py`** — full CLI with opt-in subsystems (ZMQ, proxy, MCP, git,
  unshare, envd). Refuses to silently fall back to mock.

## Quick start

```bash
pip install aiohttp python-dotenv        # tiktoken optional
export NVIDIA_API_KEY=nvapi-...          # or Secure Vault custom.nvidia (sandbox)

python swarm_maximal.py --ping                              # NIM reachability
python swarm_maximal.py --task "summarize this repo" \
    --lenses research,code --profile architectural
python launcher.py --task "..." --lenses research,code,proof # full CLI
python launcher.py --mock --task "..."                       # explicit test double
```

Model defaults come from the **2026-09-14 live 82-model audit**
(`toxicwind/nvidia-nim-model-probe`): `openai/gpt-oss-20b` (default),
`z-ai/glm-5.3-flash` (alternate). The catalog is nondeterministic and
mutates — re-verify before scripting new ids.

## Layout

| Path | Role |
|---|---|
| `nim/` | Unified NIM API layer (client, model table, README) |
| `swarm/` | DAG engine, agents, transport, ArchiveFS, presets |
| `lens/` | Lens profiles + registry (`profiles.py`) |
| `swarm_maximal.py` | Maximal one-command runner |
| `launcher.py` | Full CLI, opt-in subsystems |
| `MERGE.md` | Merge decision record (sources, overlap map) |
| `SOVEREIGN.md` | Sovereign topology seam (herd-adjacent) |

## Known constraints (honest)

- The NIM catalog is an **unreliable narrator**: models delist silently
  (deepseek-v4-pro vanished mid-audit), 404-gating is per-account, and
  availability flips between runs. Only live probes tell the truth.
- Cold-start models (kimi-k3 ~43s TTFT, ultra-550b) need explicit
  `allow_cold_start=True`; they violate the 5s production ceiling otherwise.
- `nvidia/nemotron-3-super-120b-a12b` is deprecated 2026-10-03 (503s).
- Triton/gRPC paths are experimental/opt-in — hosted NIM is the supported route.
- Subsystems (ZMQ/proxy/MCP/git/unshare/envd) are legacy integrations kept
  opt-in; the core path is `nim/` → `swarm/` → `lens/`.

## Sources merged

See **MERGE.md** for the full decision record: `toxicwind/nvidia-swarm-lens`
(main, read-only), Drive `nvidia_lens_swarm_maximal.py` +
`nvidia_swarm_standalone.py`, the `toxicwind/nvidia-nim` spec fork (reference
only), and the local `nvidia-nim-loader` / `model-ranking` skills.
