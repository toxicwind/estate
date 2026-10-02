# Recon & Technical Specification: `stealth/space-bunny-alpha` & OpenRouter Zero-Cost Model Architecture

## Executive Summary & Breakthrough Findings
On 2026-10-02, an estate-wide scan of all 464 models on OpenRouter identified **4 models** configured with zero-cost pricing (`prompt: "0"`, `completion: "0"`). Among these, **`stealth/space-bunny-alpha`** is a singular anomaly: it operates completely unmetered, bypassing OpenRouter's 1,000/day free-tier rate limit (`free_model_daily_requests: 0 remaining`), with **no moderation**, **1M context window**, **512K max completion**, and **native multimodal (text, image, video)** support.

Telemetry confirms an expiration timestamp of **`2026-10-05`**, indicating an unannounced 5-day evaluation window by an upstream foundation lab testing a frontier model.

---

## Detailed Model Specification (`stealth/space-bunny-alpha`)

Extract from live `/api/v1/models` telemetry:
- **Model ID**: `stealth/space-bunny-alpha` (Canonical: `stealth/space-bunny-alpha`)
- **Active Window**: Created `1790174884`, **Expires**: `2026-10-05`
- **Context Length**: **1,000,000 tokens** (1M)
- **Max Output**: **524,288 tokens** (512K max completion)
- **Input Modalities**: Text, Image, Video (`text+image+video->text`)
- **Output Modalities**: Text
- **Moderation**: **`is_moderated: false`** (Raw uncensored evaluation path)
- **Per-Request Limits**: `null` (No token throttling or concurrency clamps)
- **Pricing**: `$0.00 / M prompt`, `$0.00 / M completion`
- **Tool Capabilities**: Native `tools` and `tool_choice` parameter support
- **Reasoning Engine**:
  - `mandatory: true`
  - `default_effort: "max"`
  - `supported_efforts: ["low", "medium", "high", "xhigh", "max"]`

---

## Comparative Taxonomy: What Use Do These Zero-Cost Models Have?

Out of 464 models on OpenRouter, zero-cost models fall into three distinct operational categories:

| Model ID | Context | Real Cost | Rate Limits / Auth Gate | Architecture & Operational Utility |
| :--- | :--- | :--- | :--- | :--- |
| **`stealth/space-bunny-alpha`** | **1,000,000** | **$0.00** | **None** (Bypasses daily free cap) | **Frontier Agent Workhorse**: Full repo refactoring, complex ReAct loops, video/visual log debugging, large-scale multi-file code synthesis without burning API budget. |
| **`google/lyria-3-pro-preview`** | 1,048,576 | $0.00 | HTTP 402 Gate (Requires balance > $0) | **Multimodal Audio/Music Reasoning**: DeepMind's Lyria 3 architecture. Zero token cost, but account must hold positive balance to pass admission check. |
| **`google/lyria-3-clip-preview`** | 1,048,576 | $0.00 | HTTP 402 Gate (Requires balance > $0) | **Audio/Video Clip Generation**: Lightweight counterpart to Pro preview for high-speed multimodal generation. |
| **`openrouter/free`** | 200,000 | $0.00 | Hard Cap: 1,000 req/day per key | **Fallback Meta-Router**: Auto-balances across public `:free` models (Llama 3.3, Qwen, Nemotron). Useful for simple heartbeats/health probes; unsuitable for heavy agent tasks due to 429 lockout. |

---

## Operational Utilization Plan for the Estate

1. **Autonomous Coding & Subagent Swarms**:
   - Until `2026-10-05`, route all high-throughput agent tasks (`subagents`, `corral`, `super-ralph`) through `stealth/space-bunny-alpha`.
   - Take advantage of the 1M context to feed complete estate repos (`/home/toxic/estate`) without chunking or compaction loss.

2. **ReAct & Tool Calling (Corral / Claude Code Shim)**:
   - Configure `reasoning_effort: "medium"` or `"low"` when low latency is required for quick tool execution.
   - Use `tools` natively instead of parsing raw `<tool_call>` strings where supported.

3. **Multimodal Analysis**:
   - Feed terminal HUD snapshots, UI bug screenshots, or visual telemetry directly to `space-bunny-alpha` for automated visual triage.

4. **Expiration Hardening (Oct 5 Milestone)**:
   - Because `space-bunny-alpha` expires on October 5, 2026, fallback chains must automatically fail over to `google-antigravity/gemini-3.8-flash` and local GGUFs (`gemma-4-12b` via herd) once the stealth endpoint terminates.
