# pi.dev Full Conversion from grok-build
## /home/toxic — July 2026 Cutting Edge

This package converts your entire grok-build stack to **pi.dev** (the dominant open-source agent framework as of July 2026: 182K+ stars, MIT license, fully transparent request/response). No more blinded payloads, no more `Retry failed: serialization error: invalid type: null, expected u32`.

---

## What You're Leaving Behind

| grok-build Problem | pi.dev Fix |
|---|---|
| Blinded payloads — raw JSON swallowed by 844K LOC Rust wrapper | Full HTTP request/response visible in TUI and logs |
| `reasoning_effort="high"` → NIM expects float 0.2-0.99 → serde null error | `thinkingLevelMap` maps pi levels to exact provider values |
| 3x opaque retry loop, generic error at "column 592" | Immediate raw error dump with full response body |
| No Inkling day-0 parser support (Issue #31359) | `compat.thinkingFormat: "openrouter"` + custom `thinkingLevelMap` |
| MCP servers hardcoded in TOML, no dynamic management | MCPProxy federation with quarantine, health checks, BM25 discovery |
| `permission_mode = "always-approve"` buried in TOML | `defaultProjectTrust: "always"` in settings + `/trust` command |

---

## File Map

```
pi-conversion/
├── models.json              →  ~/.pi/agent/models.json
├── settings.json            →  ~/.pi/agent/settings.json
├── project-settings.json    →  /home/toxic/.pi/settings.json
├── mcpproxy-config.json     →  ~/.mcpproxy/mcp_config.json
├── install.sh               →  One-shot installer
└── README.md                →  This file
```

---

## Quick Start

```bash
# 1. Install pi
curl -fsSL https://pi.dev/install.sh | sh

# 2. Install MCPProxy
# macOS:
brew install --cask smart-mcp-proxy/mcpproxy/mcpproxy
# Linux:
curl -fsSL https://apt.mcpproxy.app/install.sh | sudo bash

# 3. Copy configs
mkdir -p ~/.pi/agent ~/.mcpproxy /home/toxic/.pi
cp models.json ~/.pi/agent/models.json
cp settings.json ~/.pi/agent/settings.json
cp project-settings.json /home/toxic/.pi/settings.json
cp mcpproxy-config.json ~/.mcpproxy/mcp_config.json

# 4. Export your keys (or use /login in pi)
export NVIDIA_API_KEY=nvapi-...
export GROQ_API_KEY=gsk_...
export OPENROUTER_API_KEY=sk-or-...
export MISTRAL_API_KEY=...
export GLM_API_KEY=...
export CEREBRAS_API_KEY=...
export GOOGLE_API_KEY=...
export FIREWORKS_API_KEY=...
export HF_TOKEN=hf_...

# 5. Start MCPProxy (in one terminal)
mcpproxy

# 6. Start pi (in another terminal)
cd /home/toxic && pi

# 7. Select your model
/model              # shows ALL your converted models
/model nim-inkling  # select Inkling
/model groq         # select Groq Compound
```

---

## The Critical Fix: NIM Inkling `reasoning_effort`

Your grok-build config had:
```toml
[model.nim-inkling.extra_body]
reasoning_effort = 0.8   # grok-build sent this as string or null
```

NIM expects `reasoning_effort` as a **float string** in the range `0.2` to `0.99`. grok-build's serde layer was blinding the actual payload, retrying 3x, then throwing the generic column-592 error.

In pi.dev, this is solved via `thinkingLevelMap`:

```json
"thinkingLevelMap": {
  "off": null,           // Inkling doesn't support off
  "minimal": "0.2",
  "low": "0.4",
  "medium": "0.6",
  "high": "0.8",         // maps to your 0.8
  "xhigh": "0.9",
  "max": "0.99"
}
```

When you set `/thinking high` in pi, it sends `reasoning_effort: "0.8"` to NIM. If NIM rejects it, you see the **full raw HTTP response** immediately — no retries, no blinding.

Also set:
```json
"compat": {
  "supportsDeveloperRole": false,      // NIM doesn't understand "developer" role
  "supportsReasoningEffort": true,     // NIM DOES support reasoning_effort
  "maxTokensField": "max_completion_tokens",
  "thinkingFormat": "openrouter"       // sends reasoning_effort as top-level field
}
```

---

## Model Conversion Reference

| grok-build Model | pi.dev Provider | pi.dev Model ID | Context | Max Tokens |
|---|---|---|---|---|
| `nim-inkling` | `nim-inkling` | `thinkingmachines/inkling` | 128K | 16K |
| `groq-compound` | `groq` | `groq/compound` | 131K | 16K |
| `groq-compound-mini` | `groq` | `groq/compound-mini` | 131K | 16K |
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
| `sov-25100` | `sov-25100` | `beellama/qwen-flash-64k` | 64K | 16K |
| `local-llama` | `sov-25100` | `beellama/qwen-flash-64k` | 64K | 16K |
| `llm7` | `llm7` | `gpt-4o-mini` | 1M | 16K |
| `linuxdo` | `linuxdo` | `gpt-3.5-turbo` | 16K | 4K |
| `keylessai` | `keylessai` | `gpt-3.5-turbo` | 8K | 4K |
| `groq-scout` | `groq` | `openai/gpt-oss-20b` | 131K | 16K |
| `groq-70b` | `groq` | `openai/gpt-oss-120b` | 131K | 16K |

---

## MCPProxy Integration

Your grok-build had:
```toml
[mcp_servers.mcpproxy]
command = "npx"
args = ["-y", "mcp-remote", "http://127.0.0.1:25109/mcp", ...]
```

MCPProxy replaces this with a **federated, secured, observable** MCP gateway:

```bash
# Start MCPProxy (listens on :25109, same port)
mcpproxy

# Add your MCP servers through MCPProxy instead of grok-build
mcpproxy upstream add my-mcp-server \
  --url https://my-mcp-server.com/mcp \
  --header "Authorization: Bearer token"

# Or add stdio servers
mcpproxy upstream add filesystem \
  --command npx \
  --args "-y,@modelcontextprotocol/server-filesystem,/home/toxic"

# Check health
mcpproxy doctor
mcpproxy upstream list

# pi.dev connects to MCPProxy via the SAME endpoint
# In interactive pi: /mcp shows all federated tools
```

MCPProxy benefits over raw `mcp-remote`:
- **Quarantine** — new servers are quarantined until manually approved (blocks Tool Poisoning Attacks)
- **BM25 tool discovery** — agents load one `retrieve_tools` function instead of hundreds of schemas (~99% token reduction)
- **Health checks** — automatic ping/liveness probes every 30s
- **Security scanners** — Snyk, Semgrep, Trivy against quarantined servers before approval
- **Crosses the 128-function OpenAI limit** — federates hundreds of MCP servers

---

## Subagent / Persona Migration

Your grok-build personas:
```toml
[subagents.personas.principal-confident]
model = "nim-inkling"
instructions = "You are a principal engineer..."

[subagents.personas.sovereign-local]
model = "sov-25100"
instructions = "You run on local llama-swap only..."
```

In pi.dev, personas are handled via **extensions** or **steering messages**. The simplest migration:

```bash
# Create project-level extensions in /home/toxic/.pi/extensions/
# Or use /steering to inject system prompts per-session

# For now, use model selection + custom instructions:
/model nim-inkling
# Then paste your principal-confident instructions as the first user message
# or use /steering to set persistent context
```

Advanced: write a custom extension that registers subagent personas as pi.dev commands. See `packages/coding-agent/examples/extensions/subagent/` in the pi-mono repo.

---

## Key Differences: grok-build → pi.dev

| Feature | grok-build | pi.dev |
|---|---|---|
| **Config format** | TOML | JSON (`models.json`, `settings.json`) |
| **Config locations** | `~/.grok/config.toml` | `~/.pi/agent/models.json`, `~/.pi/agent/settings.json`, `.pi/settings.json` (project) |
| **Model registry** | Inline in TOML | `models.json` with provider blocks |
| **API key storage** | Inline `env_key` | `auth.json` (encrypted), env vars, or `/login` |
| **MCP servers** | TOML `mcp_servers` block | External MCPProxy or `mcp-remote` via extension |
| **Tool timeout** | `tool_timeout_sec = 300` | `retry.provider.timeoutMs` + bash timeout |
| **Bash timeout** | `timeout_secs = 600` | Same — pi.dev respects shell timeout |
| **Output limit** | `output_byte_limit = 5000000` | No hard limit; uses streaming |
| **Permission mode** | `permission_mode = "always-approve"` | `defaultProjectTrust: "always"` |
| **YOLO mode** | `yolo = true` | Implicit in `always` trust + no confirmation prompts |
| **Auto-update** | `auto_update = true` | `pi update` or package manager |
| **Plugins** | `enabled = ["neon"]` | Extensions via `-e` flag or `.pi/extensions/` |
| **Subagents** | TOML personas | Extensions or steering messages |
| **Raw visibility** | NONE — blinded | FULL — every request/response in TUI |
| **Error handling** | 3x retry, generic serde error | Immediate raw dump, configurable retry |
| **Thinking levels** | Not supported | `/thinking off/minimal/low/medium/high/xhigh/max` |
| **Compact mode** | `compact_mode = true` | Built-in TUI layout |
| **Max thoughts width** | `max_thoughts_width = 120` | Automatic TUI wrapping |

---

## Debugging NIM Inkling

If NIM still throws errors:

```bash
# 1. Test the endpoint directly
curl -s https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "thinkingmachines/inkling",
    "messages": [{"role":"user","content":"hello"}],
    "max_completion_tokens": 1024,
    "reasoning_effort": "0.8"
  }' | jq .

# 2. Run pi with raw logging
PI_LOG_LEVEL=debug pi --model nim-inkling/thinkingmachines/inkling

# 3. Check what pi actually sends
# In the TUI, press Ctrl+L to open the log panel — full request/response visible
```

---

## Why pi.dev Over OpenCode?

Both are valid. Here's the decision matrix:

| Concern | Choose pi.dev | Choose OpenCode |
|---|---|---|
| **Minimal attack surface** | ✅ ~few thousand LOC, zero SaaS | Larger codebase, more features |
| **Auditability** | ✅ Plain-text JSON logs of every step | Full request/response visible |
| **Active maintenance** | ✅ July 2026 dominant framework (182K stars) | Also actively maintained |
| **MCP support** | ✅ Via MCPProxy federation | Native MCP support |
| **Provider count** | 30+ built-in + custom | 75+ built-in |
| **TUI quality** | ✅ Best-in-class terminal UI | Functional TUI |
| **Extensions ecosystem** | ✅ Rich extension API | Plugin marketplace |
| **Headless/CI** | ✅ `pi -p`, `--mode json`, `--mode rpc` | `opencode run`, `opencode serve` |
| **Self-hosted models** | ✅ First-class (Ollama, vLLM, llama.cpp) | Supported |

For your stack — NIM, Groq, OpenRouter free tier, local llama-swap, MCPProxy — **pi.dev is the tighter fit**. You get transparency without bloat.

---

## License

All configs in this package are derived from your grok-build `config.toml` and mapped to pi.dev's documented schema. MIT (same as pi.dev and MCPProxy).

---

*Generated July 26, 2026 from grok-build config.toml + pi-mono source analysis + mcpproxy-go source analysis.*
