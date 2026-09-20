#!/usr/bin/env python3
"""Apply the verified README fixes for toxicwind/openfang. Fails loudly if any
target string is not found exactly once."""
import sys

PATH = "/home/toxic/readme-fix-openfang-20260914/README.md"

with open(PATH, encoding="utf-8") as f:
    text = f.read()

edits = []

def edit(old, new, label):
    edits.append((old, new, label))

# 1. Header: stale LOC / test count / clippy
edit(
    "  Open-source Agent OS built in Rust. 137K LOC. 14 crates. 1,767+ tests. Zero clippy warnings.<br/>",
    "  Open-source Agent OS built in Rust. 160K+ lines of Rust. 14 crates. 2,696+ tests. Zero clippy warnings (CI-enforced).<br/>",
    "header stats",
)

# 2. Hands heading 7 -> 9
edit("### The 7 Bundled Hands", "### The 9 Bundled Hands", "hands heading")

# 3. Hands table: add the two missing hands after the Browser row
old_browser_row = "| **Browser** | Web automation agent. Navigates sites, fills forms, clicks buttons, handles multi-step workflows. Uses Playwright bridge with session persistence. **Mandatory purchase approval gate**: it will never spend your money without explicit confirmation. |"
new_rows = old_browser_row + "\n" + (
    "| **Infisical Sync** | Autonomous secrets synchronisation between a self-hosted Infisical instance and the agent's local credential vault. "
    "Keeps agents in sync with a shared Infisical instance as the single source of truth, and lets agents push new secrets back to Infisical. "
    "Requires `INFISICAL_URL` plus machine-identity credentials. |\n"
    "| **Trader** | Autonomous market intelligence and trading engine. Multi-signal analysis, adversarial bull/bear reasoning, calibrated "
    "confidence scoring, strict risk management, and portfolio-level analytics. Analysis-only, paper trading, or live via Alpaca — "
    "approval gate on by default. |"
)
edit(old_browser_row, new_rows, "hands table rows")

# 4. Binary size claim (unverifiable) -> soften
edit(
    "The entire system compiles to a **single ~32MB binary**. One install, one command, your agents are live.",
    "The entire system compiles to a **single binary**. One install, one command, your agents are live.",
    "binary size line",
)
edit(
    "| **Install Size** | **~32 MB** | ~500 MB | ~8.8 MB | ~100 MB | ~200 MB | ~150 MB |",
    "| **Install Size** | **Single binary** | ~500 MB | ~8.8 MB | ~100 MB | ~200 MB | ~150 MB |",
    "install size table",
)

# 5. Architecture block
edit(
    "14 Rust crates. 137,728 lines of code. Modular kernel design.",
    "14 Rust crates. 160K+ lines of Rust. Modular kernel design.",
    "architecture LOC",
)
edit(
    "openfang-hands       7 autonomous Hands, HAND.toml parser, lifecycle management",
    "openfang-hands       9 autonomous Hands, HAND.toml parser, lifecycle management",
    "architecture hands row",
)

# 6. Dead WhatsApp docs link -> verified live URL
edit(
    "See the [Cloud API configuration docs](https://openfang.sh/docs/channels/whatsapp).",
    "See the [Cloud API configuration docs](https://openfang.sh/docs/channel-adapters#whatsapp).",
    "whatsapp docs link",
)

# 7. Providers section: 27/123+ -> 38/200+, roster from model_catalog.rs
edit(
    """## 27 LLM Providers, 123+ Models

3 native drivers (Anthropic, Gemini, OpenAI-compatible) route to 27 providers:

Anthropic, Gemini, OpenAI, Groq, DeepSeek, OpenRouter, Together, Mistral, Fireworks, Cohere, Perplexity, xAI, AI21, Cerebras, SambaNova, HuggingFace, Replicate, Ollama, vLLM, LM Studio, Qwen, MiniMax, Zhipu, Moonshot, Qianfan, Bedrock, and more.""",
    """## 38 LLM Providers, 200+ Models

Native drivers (Anthropic, Gemini, OpenAI-compatible, Bedrock, Vertex, and more) route to 38 providers with 200+ models in the built-in catalog:

Anthropic, Gemini, OpenAI, Groq, DeepSeek, OpenRouter, Together, Mistral, Fireworks, Cohere, Perplexity, xAI, AI21, Cerebras, SambaNova, HuggingFace, Replicate, Ollama, vLLM, LM Studio, Qwen, Qwen Code, MiniMax, Zhipu, Z.AI, Moonshot, Qianfan, Bedrock, Azure, Venice, NVIDIA, GitHub Copilot, Claude Code, Codex, VolcEngine, Requesty, Chutes, and Lemonade.""",
    "providers section",
)

# 8. Dev test count comment
edit("# Run all tests (1,767+)", "# Run all tests (2,696+)", "dev test count")

# 9. Stability notice version
edit(
    "OpenFang v0.5.10 is pre-1.0.",
    "OpenFang v0.6.9 is pre-1.0.",
    "stability notice version",
)

# 10. Coyote section before Stability Notice
coyote_section = """## Coyote: Sovereign Dynamic Agent

> Downstream addition — ships in this mirror, not in upstream OpenFang.

**Coyote** is a first-class dynamic agent registered in `agents/registry.toml`.
It was renamed from `hal-substrate` so the agent name matches what the rest of
the Sovereign stack already addresses: route chains and bridges request model
`openfang:coyote`, and `resolve_agent()` in `openfang-api` looks agents up by
name — so the manifest now lives at `agents/coyote/agent.toml`, exactly where
the router expects it.

- **Manifest** (`agents/coyote/agent.toml`, v3.1.0) — "autonomous agent
  inference engine" with sigil-driven control, persistent memory, slot-save,
  and metrics capabilities.
- **Model routing** — primary alias `kimi-auto`, fallback chain
  `local-fast` → `free` (zero-cost providers).
- **Service surface** — binds `COYOTE_PORT` (25143) with `/health`, `/task`,
  and `/stop` endpoints; accepts tasks from CLI, WebChat, MQTT, and custom
  channels through the OpenFang router.
- **System prompt** (`agents/coyote/system.md`) — operating rules plus
  control-plane integration: Yote voice layer (:25102), OpenFang mesh hub
  (:25103), MCP proxy (:25109), GHAS GPU telemetry (:25112–25114).

To disable it without deleting anything, set `enabled = false` for coyote in
`agents/registry.toml`.

---

## Stability Notice"""
edit("\n---\n\n## Stability Notice", "\n---\n\n" + coyote_section, "coyote section")

applied = []
for old, new, label in edits:
    n = text.count(old)
    if n != 1:
        print(f"FATAL: '{label}' found {n} times (expected 1). Aborting, no changes written.")
        sys.exit(1)
    text = text.replace(old, new)
    applied.append(label)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(text)

print(f"OK: applied {len(applied)} edits:")
for a in applied:
    print(f"  - {a}")
