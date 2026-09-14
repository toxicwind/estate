# pi.dev Conversion Kit (from grok-build)

Migration kit that converted the grok-build agent stack to **pi.dev** — the
open-source agent framework with fully transparent request/response (no blinded
payloads, no opaque retry loops). Generated July 2026 from the live
grok-build `config.toml`, pi-mono source, and mcpproxy-go source.

> **Status: historical.** The conversion is done; this directory is kept as a
> reference for the config mapping and the model table below.

## File map

```text
pi-conversion/
├── models.json              →  ~/.pi/agent/models.json
├── settings.json            →  ~/.pi/agent/settings.json
├── project-settings.json    →  /home/toxic/.pi/settings.json
├── mcpproxy-config.json     →  ~/.mcpproxy/mcp_config.json
├── install.sh               →  One-shot installer
└── README.md                →  This file
```

## Quick start

```bash
# 1. Install pi
curl -fsSL https://pi.dev/install.sh | sh

# 2. Install MCPProxy (Linux)
curl -fsSL https://apt.mcpproxy.app/install.sh | sudo bash

# 3. Copy configs
mkdir -p ~/.pi/agent ~/.mcpproxy /home/toxic/.pi
cp models.json ~/.pi/agent/models.json
cp settings.json ~/.pi/agent/settings.json
cp project-settings.json /home/toxic/.pi/settings.json
cp mcpproxy-config.json ~/.mcpproxy/mcp_config.json

# 4. Export keys (or use /login in pi)
export NVIDIA_API_KEY=<redacted> GROQ_API_KEY=<redacted> OPENROUTER_API_KEY=<redacted>

# 5. Start MCPProxy (one terminal), then pi (another)
mcpproxy
cd /home/toxic && pi
```

## What it fixed

| grok-build problem | pi.dev fix |
| ------------------ | ---------- |
| Blinded payloads — raw JSON swallowed by the Rust wrapper | Full HTTP request/response visible in TUI and logs |
| `reasoning_effort="high"` → NIM expects float 0.2–0.99 → serde null error | `thinkingLevelMap` maps pi levels to exact provider values |
| 3x opaque retry loop, generic error at "column 592" | Immediate raw error dump with full response body |
| No NIM day-0 parser support | `compat.thinkingFormat: "openrouter"` + custom `thinkingLevelMap` |
| MCP servers hardcoded in TOML, no dynamic management | MCPProxy federation with quarantine, health checks, BM25 discovery |
| `permission_mode = "always-approve"` buried in TOML | `defaultProjectTrust: "always"` in settings + `/trust` command |

## NIM `reasoning_effort` (historical)

grok-build sent `reasoning_effort` as a serde-typed value; NIM expects a float
string in `0.2`–`0.99`, so high-effort calls died with a generic serialization
error after 3 blind retries. pi.dev solves it with an explicit map:

```json
"thinkingLevelMap": {
  "off": null, "minimal": "0.2", "low": "0.4", "medium": "0.6",
  "high": "0.8", "xhigh": "0.9", "max": "0.99"
}
```

> Note 2026-09-03: `thinkingmachines/inkling` (NVIDIA NIM Inkling) was
> discontinued and removed. Kept here as the plumbing reference pattern.

## Model conversion reference

| grok-build model | pi.dev provider | pi.dev model ID | Context | Max tokens |
| ---------------- | --------------- | --------------- | ------- | ---------- |
| `groq-compound` | `groq` | `groq/compound` | 131K | 16K |
| `groq-120b` | `groq` | `openai/gpt-oss-120b` | 131K | 16K |
| `groq-20b` | `groq` | `openai/gpt-oss-20b` | 131K | 16K |
| `groq-qwen` | `groq` | `qwen/qwen3.6-27b` | 131K | 16K |
| `groq-allam` | `groq` | `allam-2-7b` | 4K | 4K |
| `openrouter-nemotron-ultra` | `openrouter` | `nvidia/nemotron-3-ultra-550b-a55b:free` | 1M | 65K |
| `openrouter-nemotron-super` | `openrouter` | `nvidia/nemotron-3-super-120b-a12b:free` | 1M | 32K |
| `openrouter-nemotron-nano` | `openrouter` | `nvidia/nemotron-3-nano-30b-a3b:free` | 256K | 32K |
| `openrouter-nemotron-nano-omni` | `openrouter` | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 256K | 32K |
| `openrouter-laguna-m1` | `openrouter` | `poolside/laguna-m.1:free` | 262K | 32K |
| `openrouter-laguna-xs` | `openrouter` | `poolside/laguna-xs-2.1:free` | 262K | 32K |
| `openrouter-north-mini` | `openrouter` | `cohere/north-mini-code:free` | 256K | 32K |
| `openrouter-qwen-coder` | `openrouter` | `qwen/qwen3-coder:free` | 1M | 32K |
| `openrouter-hy3` | `openrouter` | `tencent/hy3:free` | 262K | 32K |
| `openrouter-gemma-31b` | `openrouter` | `google/gemma-4-31b-it:free` | 262K | 32K |
| `openrouter-gemma-26b` | `openrouter` | `google/gemma-4-26b-a4b-it:free` | 262K | 32K |
| `openrouter-llama-33-70b` | `openrouter` | `meta-llama/llama-3.3-70b-instruct:free` | 131K | 32K |
| `openrouter-gpt-oss-120b` | `openrouter` | `openai/gpt-oss-120b:free` | 131K | 32K |
| `openrouter-hermes-405b` | `openrouter` | `nousresearch/hermes-3-llama-3.1-405b:free` | 131K | 32K |
| `openrouter-dolphin-24b` | `openrouter` | `cognitivecomputations/dolphin-mistral-24b-venice-edition:free` | 32K | 16K |
| `mistral` | `mistral` | `mistral-large-latest` | 131K | 16K |
| `glm-flash` | `glm` | `glm-4.7-flash` | 200K | 16K |
| `cerebras` | `cerebras` | `gpt-oss-120b` | 128K | 16K |
| `google-gemini` | `google` | `gemini-2.5-flash` | 1M | 8K |
| `fireworks` | `fireworks` | `accounts/fireworks/models/llama-v3p3-70b-instruct` | 131K | 16K |
| `huggingface` | `huggingface` | `meta-llama/Llama-3.3-70B-Instruct` | 131K | 4K |
| `sov-25100` / `local-llama` | `sov-25100` | `beellama/qwen-flash-64k` | 64K | 16K |
| `groq-scout` | `groq` | `openai/gpt-oss-20b` | 131K | 16K |
| `groq-70b` | `groq` | `openai/gpt-oss-120b` | 131K | 16K |

## MCPProxy integration

pi.dev connects to MCPProxy (the federated, secured, observable MCP gateway) at
the same endpoint grok-build used:

- **Quarantine** — new servers are quarantined until manually approved (blocks tool-poisoning attacks)
- **BM25 tool discovery** — agents load one `retrieve_tools` function instead of hundreds of schemas
- **Health checks** — automatic liveness probes
- **Crosses the 128-function OpenAI limit** — federates hundreds of MCP servers

In interactive pi, `/mcp` shows all federated tools.

## Key differences: grok-build → pi.dev

| Feature | grok-build | pi.dev |
| ------- | ---------- | ------ |
| Config format | TOML | JSON (`models.json`, `settings.json`) |
| Config locations | `~/.grok/config.toml` | `~/.pi/agent/models.json`, `~/.pi/agent/settings.json`, `.pi/settings.json` (project) |
| API key storage | Inline `env_key` | `auth.json` (encrypted), env vars, or `/login` |
| MCP servers | TOML `mcp_servers` block | External MCPProxy or `mcp-remote` via extension |
| Permission mode | `permission_mode = "always-approve"` | `defaultProjectTrust: "always"` |
| Raw visibility | None — blinded | Full — every request/response in TUI |
| Error handling | 3x retry, generic serde error | Immediate raw dump, configurable retry |
| Thinking levels | Not supported | `/thinking off/minimal/low/medium/high/xhigh/max` |

## License

All configs here are derived from the grok-build `config.toml` and mapped to
pi.dev's documented schema. MIT (same as pi.dev and MCPProxy).
