# 🔍 Tau Session Audit & Monorepo Health Report

> **Audit Run:** `2026-10-15T05:21:21.992Z` | **Total Sessions Audited:** `296` | **Total Events:** `88,364`

## 🎯 Executive Summary

- **Discovered Primary Anti-Pattern**: Multiple models hallucinating completion by outputting natural-language messages with zero tool calls, followed immediately by firing `todo(op="done")` flurries (up to 24 consecutive calls).
- **Phantom Todo Completion Rate**: `35/296` sessions (11.8%) exhibited unearned or flurried todo completions.
- **Critical Anomalies Detected**: `97` sessions had critical severity pattern violations.
- **Monorepo Structure**: clean at report time (no misnamed `projects/toxicwind/` root observed).

---

## 🚨 Discovered Patterns & Hallucination Taxonomy

| Pattern Name | Severity | Detections | Description |
|---|:---:|:---:|---|
| **Rapid Consecutive Todo Done Flurry Without Intervening Work** | 🔴 CRITICAL | `67` | Documented in [`patterns/`](https://github.com/toxicwind/estate/blob/main/skills/tau-session-audit/patterns/) |
| **Repeated Tool Failure Loop** | 🟠 HIGH | `111` | Documented in [`patterns/`](https://github.com/toxicwind/estate/blob/main/skills/tau-session-audit/patterns/) |
| **High Model Churn Session** | 🟠 HIGH | `62` | Documented in [`patterns/`](https://github.com/toxicwind/estate/blob/main/skills/tau-session-audit/patterns/) |
| **Todo Marked Done Immediately After Tool Failure** | 🟠 HIGH | `17` | Documented in [`patterns/`](https://github.com/toxicwind/estate/blob/main/skills/tau-session-audit/patterns/) |
| **Unexecuted Scratchpad or Pseudo-Tool Syntax in Chat** | 🟠 HIGH | `4` | Documented in [`patterns/`](https://github.com/toxicwind/estate/blob/main/skills/tau-session-audit/patterns/) |
| **Message with No Execution Tools Followed by Todo Done** | 🔴 CRITICAL | `1` | Documented in [`patterns/`](https://github.com/toxicwind/estate/blob/main/skills/tau-session-audit/patterns/) |

### 1. The Phantom Todo Completion (Primary Smoking Gun)

Models repeatedly demonstrated the following failure mode:
1. Initialized an 10–18 item plan in `todo`.
2. Emitted an assistant message with narrative text / thinking (e.g. *"Now I will run end-to-end tests..."*) with **zero tool calls**.
3. Fired consecutive `todo(op="done")` tool executions back-to-back without running tests, edits, or commands.

#### Top Sessions with Phantom Todo Flurries:

| Session File | Model | Max Consecutive Todos | Total Tools | Details |
|---|---|:---:|:---:|---|
| [`-tmp/2026-10-11T21-55-16-455Z_01a12cf6-8767-735c-82dd-7668788e3520.jsonl`](https://github.com/toxicwind/estate/blob/main/config/tau/agent/sessions/-tmp/2026-10-11T21-55-16-455Z_01a12cf6-8767-735c-82dd-7668788e3520.jsonl) | `cohere/command-a-plus-05-2026` | **33** | 1979 | Intent: *General agent work* |
| [`-tmp/2026-10-12T18-26-28-597Z_01a1315d-ba75-7440-a3e7-279c47f61fbe.jsonl`](https://github.com/toxicwind/estate/blob/main/config/tau/agent/sessions/-tmp/2026-10-12T18-26-28-597Z_01a1315d-ba75-7440-a3e7-279c47f61fbe.jsonl) | `omni/oc/longcat-2.5-preview-free` | **18** | 1356 | Intent: *General agent work* |
| [`-tmp/2026-10-14T21-23-50-703Z_01a13c4c-d52f-72d3-bdf1-8ff0ed355e55.jsonl`](https://github.com/toxicwind/estate/blob/main/config/tau/agent/sessions/-tmp/2026-10-14T21-23-50-703Z_01a13c4c-d52f-72d3-bdf1-8ff0ed355e55.jsonl) | `nvidia/minimaxai/minimax-m3` | **18** | 413 | Intent: *NVIDIA config / model setup* |
| [`-tmp/2026-10-14T06-00-54-104Z_01a138ff-da58-7746-9c03-165eeda99720.jsonl`](https://github.com/toxicwind/estate/blob/main/config/tau/agent/sessions/-tmp/2026-10-14T06-00-54-104Z_01a138ff-da58-7746-9c03-165eeda99720.jsonl) | `nvidia/mistralai/mistral-7b-instruct-v03` | **17** | 1506 | Intent: *NVIDIA config / model setup* |
| [`-tmp/2026-10-14T20-56-04-696Z_01a13c33-6958-7264-8d8a-4e015fdaac0b.jsonl`](https://github.com/toxicwind/estate/blob/main/config/tau/agent/sessions/-tmp/2026-10-14T20-56-04-696Z_01a13c33-6958-7264-8d8a-4e015fdaac0b.jsonl) | `flock/z-ai/glm-5.3-flash` | **15** | 1637 | Intent: *General agent work* |
| [`-tmp/2026-10-03T03-43-46-193Z_01a0ffdc-5a11-7799-9388-3bd28faf68ad.jsonl`](https://github.com/toxicwind/estate/blob/main/config/tau/agent/sessions/-tmp/2026-10-03T03-43-46-193Z_01a0ffdc-5a11-7799-9388-3bd28faf68ad.jsonl) | `github-copilot/gpt-5.1-codex` | **14** | 5742 | Intent: *General agent work* |
| [`-Downloads/2026-10-05T20-26-22-371Z_01a10dbe-fb23-77a9-9e8f-fbe36d87ea4c.jsonl`](https://github.com/toxicwind/estate/blob/main/config/tau/agent/sessions/-Downloads/2026-10-05T20-26-22-371Z_01a10dbe-fb23-77a9-9e8f-fbe36d87ea4c.jsonl) | `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` | **14** | 1437 | Intent: *NVIDIA config / model setup* |
| [`-tmp/2026-10-11T11-12-08-484Z_01a12aa9-b924-72e1-b303-20076b66d14e.jsonl`](https://github.com/toxicwind/estate/blob/main/config/tau/agent/sessions/-tmp/2026-10-11T11-12-08-484Z_01a12aa9-b924-72e1-b303-20076b66d14e.jsonl) | `openrouter/stealth/space-bunny-alpha` | **14** | 442 | Intent: *General agent work* |
| [`-tmp/2026-10-14T05-13-31-334Z_01a138d4-79c6-73db-b5ff-022c21753d81.jsonl`](https://github.com/toxicwind/estate/blob/main/config/tau/agent/sessions/-tmp/2026-10-14T05-13-31-334Z_01a138d4-79c6-73db-b5ff-022c21753d81.jsonl) | `vercel-ai-gateway/inclusionai/ling-3.1-flash` | **13** | 1730 | Intent: *Estate project work* |
| [`-tmp/2026-10-09T08-57-21-430Z_01a11fe1-9b16-7679-8d27-708e0091b919.jsonl`](https://github.com/toxicwind/estate/blob/main/config/tau/agent/sessions/-tmp/2026-10-09T08-57-21-430Z_01a11fe1-9b16-7679-8d27-708e0091b919.jsonl) | `cerebras/zai-glm-4.6` | **12** | 1110 | Intent: *General agent work* |

---

## 🤖 Model Hallucination & Churn Matrix

Which models were most prone to phantom completions and syntax leaks:

| Model Identifier | Sessions Used | Phantom Todo Incidents | Syntax / Thinking Leaks | Health Verdict |
|---|:---:|:---:|:---:|:---:|
| `openrouter/nvidia/nemotron-3.5-lightning:free` | 30 | **5** | 0 | 🟡 Moderate Risk |
| `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` | 2 | **5** | 0 | 🟡 Moderate Risk |
| `omni/oc/longcat-2.5-preview-free` | 5 | **5** | 0 | 🟡 Moderate Risk |
| `nvidia/mistralai/mistral-7b-instruct-v03` | 3 | **4** | 0 | 🟡 Moderate Risk |
| `github-copilot/gpt-5.1-codex` | 3 | **3** | 0 | 🟡 Moderate Risk |
| `vercel-ai-gateway/inclusionai/ling-3.1-flash` | 14 | **3** | 1 | 🟡 Moderate Risk |
| `openrouter/stealth/space-bunny-alpha` | 27 | **3** | 3 | 🔴 High Hallucination Risk |
| `google-antigravity/gemini-3.5-flash-lite` | 8 | **3** | 0 | 🟡 Moderate Risk |
| `cerebras/zai-glm-4.6` | 5 | **3** | 0 | 🟡 Moderate Risk |
| `flock/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | 26 | **3** | 0 | 🟡 Moderate Risk |
| `vercel-ai-gateway/moonshotai/kimi-k3` | 5 | **2** | 0 | 🟡 Moderate Risk |
| `unknown` | 55 | **2** | 0 | 🟡 Moderate Risk |
| `vercel-ai-gateway/poolside/laguna-s-2.1-free` | 11 | **2** | 0 | 🟡 Moderate Risk |
| `abliteration/abliterated-model` | 2 | **1** | 0 | 🟡 Moderate Risk |
| `moonshot/moonshot-v1-auto` | 2 | **1** | 0 | 🟡 Moderate Risk |
| `vercel-ai-gateway/inclusionai/ling-3.1-flash-free` | 6 | **1** | 0 | 🟡 Moderate Risk |
| `google-antigravity/gemini-3.8-flash` | 3 | **1** | 0 | 🟡 Moderate Risk |
| `anthropic/claude-opus-5-5` | 12 | **1** | 0 | 🟡 Moderate Risk |
| `openrouter/dots-studio/dots-3-note-preview:free` | 7 | **1** | 0 | 🟡 Moderate Risk |
| `nvidia/minimaxai/minimax-m3` | 4 | **1** | 0 | 🟡 Moderate Risk |
| `vercel-ai-gateway/minimax/minimax-m3-free` | 4 | **0** | 0 | 🟢 Reliable |
| `nvidia/nvidia/nemotron-3-ultra-550b-a55b` | 2 | **0** | 0 | 🟢 Reliable |
| `zen/space-bunny-free` | 2 | **0** | 0 | 🟢 Reliable |
| `nvidia/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | 4 | **0** | 0 | 🟢 Reliable |
| `openrouter/liquid/lfm-2.5-2.6b:free` | 6 | **0** | 0 | 🟢 Reliable |
| `vercel-ai-gateway/spacexai/grok-4.1-fast-reasoning` | 2 | **0** | 0 | 🟢 Reliable |
| `vercel-ai-gateway/inclusionai/ling-3.0-flash-sante-free` | 3 | **0** | 0 | 🟢 Reliable |
| `zenmux/z-ai/glm-5.3-free` | 2 | **0** | 0 | 🟢 Reliable |
| `flock/stealth/space-bunny-alpha` | 2 | **0** | 0 | 🟢 Reliable |
| `nvidia/nvidia/nemotron-3-super-120b-a12b` | 7 | **0** | 0 | 🟢 Reliable |
| `nvidia/nvidia/nemotron-3.5-lightning-30b-a3b` | 6 | **0** | 0 | 🟢 Reliable |
| `nvidia/nvidia/nemotron-parse-2.0` | 4 | **0** | 0 | 🟢 Reliable |
| `nvidia/z-ai/glm-5.3-flash` | 6 | **0** | 0 | 🟢 Reliable |
| `flock/~z-ai/glm-latest` | 2 | **0** | 0 | 🟢 Reliable |
| `anthropic/claude-opus-4-8` | 2 | **0** | 0 | 🟢 Reliable |

---

---

## 🏛️ Monorepo Convention & Workspace Architecture Audit

> Live-computed at report time — only emitted when observed on disk.

- Binary SSOT: `/home/toxic/.local/bin/tau` resolves to `/home/toxic/.local/bin/tau` (229 MiB).

### Next Steps

1. Relocate misnamed modules into the registered workspace.
2. Enforce verification gate: `tau-session-audit --check patterns` in agent handoffs to catch unearned todo completions before completing turns.
