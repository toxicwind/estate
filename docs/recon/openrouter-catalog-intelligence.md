# OpenRouter Full-Catalog Intelligence & Architectural Recon

**Audit Date:** 2026-10-02  
**Target Surface:** OpenRouter Public & Stealth API (`https://openrouter.ai/api/v1`)  
**Scope:** 464 models indexed and evaluated against live telemetry, account gating, and runtime constraints.

---

## 1. Executive Summary & Catalog Topology

A full census of OpenRouter's 464-model catalog on 2026-10-02 reveals distinct architectural, pricing, and routing tiers. While standard marketing categorizes models into "free" and "paid", the actual operational surface divides across:

1. **Unmetered Zero-Cost Anomalies**: Exactly **1 model** (`stealth/space-bunny-alpha`) executes at `$0.00` cost with **no daily rate limit** and **no credit admission check**.
2. **Preview Zero-Cost Models**: Models listed at `$0.00` prompt/completion (e.g. `google/lyria-3-pro-preview`) but gated by HTTP 402 balance checks.
3. **Public `:free` Pool**: 17 models subject to a shared **1,000 requests/day per key** cap (`free_model_daily_requests`).
4. **Dynamic Meta-Routers**: 6 endpoints with `-1` pricing that route dynamically across upstream pools.
5. **Ultra-Context Frontier**: 14 models offering **1M to 2M tokens** context window.
6. **Sub-$0.05/M Hyper-Budget Tier**: High-efficiency production models costing fraction-of-a-cent per million tokens.
7. **Unmoderated Models**: 328 out of 464 models (70.7%) configured with `is_moderated: false`.

---

## 2. The Zero-Cost & Unmetered Anomaly: `stealth/space-bunny-alpha`

### Profile
- **Canonical ID**: `stealth/space-bunny-alpha` (Do NOT prefix with `openrouter/` when querying the API; that causes HTTP 400).
- **Context Length**: **1,000,000 tokens** (1M)
- **Max Output**: **524,288 tokens** (512K completion)
- **Modalities**: `text+image+video->text` (Native multimodal input)
- **Moderation**: `is_moderated: false`
- **Cost**: `$0.00` prompt, `$0.00` completion
- **Hard Expiration Date**: **`2026-10-05`**

### Operational Value
Unlike `openrouter/free` or `:free` models, `stealth/space-bunny-alpha` does not draw down or check `free_model_daily_requests`. Live testing confirmed full HTTP 200 execution when the key had `0 remaining` free requests (`used: 1016/1000`). It is currently the highest-throughput, zero-cost reasoning asset available for agent swarms and deep ReAct loops until October 5, 2026.

---

## 3. Dynamic Meta-Routers (`-1` Pricing Tier)

Six endpoints advertise `-1` pricing, indicating algorithmic multi-model routing, prompt-based dispatch, or dynamic arbitration:

| Endpoint | Context | Description & Target Workload |
| :--- | :--- | :--- |
| **`openrouter/auto-beta`** | **2,000,000** | Experimental Auto Router testing routing algorithms with 2M context ceiling. |
| **`openrouter/pareto-code`** | **2,000,000** | Code-specialized router balancing cost vs pass@1 benchmark efficiency. |
| **`openrouter/bodybuilder`** | 128,000 | Dynamic agentic task router designed for multi-step workflow execution. |
| **`openrouter/fusion`** | 1,000,000 | Multi-model speculative / consensus routing combining answers from varied families. |
| **`typesafe/jev-router`** | 1,000,000 | TypeSafe decision router based on Jev decision-scoring architectures. |
| **`openrouter/auto`** | **2,000,000** | Production auto-router directing requests based on prompt complexity and latency. |

*Note: All meta-routers require non-zero balance to route, returning HTTP 402 when balance is zero.*

---

## 4. The 2-Million Token Frontier

OpenRouter now hosts multiple models with 2,000,000 context windows, unlocking full-repository indexing in single prompts:

1. **`x-ai/grok-4.20-multi-agent`** (2,000,000 tokens) — `$1.25 / M` prompt, `$2.50 / M` completion. Designed specifically for multi-agent swarm state representation.
2. **`x-ai/grok-4.20`** (2,000,000 tokens) — `$1.25 / M` prompt, `$2.50 / M` completion. Base 2M long-context release.
3. **`openrouter/auto-beta`** & **`openrouter/pareto-code`** (2,000,000 tokens).

---

## 5. Sub-$0.05/M Hyper-Budget Tier (High-Throughput Production)

For background batch processing, continuous auditing, and high-frequency tool loops where zero balance is not available:

| Model ID | Prompt Cost / M | Compl Cost / M | Context | Key Strength |
| :--- | :--- | :--- | :--- | :--- |
| **`~deepseek/deepseek-v4-flash-latest`** | **$0.0058** | $1.60 | 1,048,576 | Lowest cost per prompt token on the entire platform. |
| **`deepseek/deepseek-v4-flash-0731`** | **$0.0077** | $1.28 | 1,048,576 | Pinned snapshot of DeepSeek v4 Flash. |
| **`~deepseek/deepseek-flash-latest`** | **$0.0150** | $1.20 | 1,048,576 | Standard DeepSeek Flash floating alias. |
| **`ibm-granite/granite-4.0-h-micro`** | **$0.0170** | $0.11 | 131,000 | Balanced input/output ratio for ultra-cheap micro-tasks. |
| **`openai/gpt-oss-20b`** | **$0.0180** | $0.09 | 131,072 | Open-weight small model hosted on high-throughput infra. |
| **`mistralai/mistral-nemo`** | **$0.0190** | $0.03 | 131,072 | Lowest output token cost ($0.03/M) for text-heavy generation. |
| **`inclusionai/ling-3.0-flash-vl`** | **$0.0210** | $0.06 | 262,144 | Multimodal vision-language at sub-cent scale. |

---

## 6. Native Multimodal Support (Audio & Video Ingestion)

93 models in the catalog support input modalities beyond text and images:

- **Full Media Stack (`file, image, text, audio, video`)**:
  - `google/gemini-2.5-flash` (1,048,576 ctx)
  - `google/gemini-2.5-flash-lite` (1,048,576 ctx)
  - `amazon/nova-2-lite-v1` (1,000,000 ctx) — supports video and file ingestion at $0.30/M prompt.
- **Video + Text/Image Stack**:
  - Bytedance Seed 2.0 series (`seed-2.0-code`, `seed-2-1-turbo`, `seed-1.6-flash`).
  - Google Gemini 3 series (`gemini-3.8-flash`, `gemini-3.7-flash`).

---

## 7. Authentication & Rate-Limit Mechanics

Telemetry from account status probes revealed three distinct error codes and their architectural roots:

1. **HTTP 401 `"User not found."`**:
   - Distinct from `Invalid API key`.
   - Occurs when the API key hash exists in OpenRouter's edge auth cache, but the foreign key reference to the account/workspace record in the central DB has been deleted, purged, or orphaned.
   - Solution: Rotate key to an active provisioned workspace key in `/home/toxic/.secrets`.

2. **HTTP 402 `"Insufficient credits"`**:
   - Triggered on preview models and all non-`:free` models when account balance is $0.00.
   - Does **not** apply to `stealth/space-bunny-alpha`.

3. **HTTP 429 `"Rate limit exceeded: free-models-per-day-high-balance"`**:
   - Enforces a 1,000 requests/day per key quota across all `:free` models collectively.
   - Lockout duration is ~12-24h (`retry-after-ms=43159806`).
   - Bypassed entirely by `stealth/space-bunny-alpha`.

---

## 8. Sovereign Estate Integration Recommendations

1. **Subagents (`.tau/agent/config.yml`)**: Keep primary task and plan roles mapped to `openrouter/stealth/space-bunny-alpha` to sustain high-velocity autonomous execution without quota exhaustion.
2. **Oracle Market (`ranch/oracle/agent.toml`)**: Configured to `stealth/space-bunny-alpha` via OpenRouter to ensure sealed-bid clearing and task assignment never stall on local GGUF swapping.
3. **Corral & Claude Shim (`ranch/corral`)**: Route away from local `:25100` (which was causing EXAONE 1.2B crash loops) and target `stealth/space-bunny-alpha` through OpenRouter directly or via Sovereign Router (`:25104`).
4. **October 5 Milestone**: On 2026-10-05 when `space-bunny-alpha` expires, immediately swap default agent routing to `google-antigravity/gemini-3.8-flash` or the sub-$0.05/M DeepSeek Flash tier.
