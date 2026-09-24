# 🔍 Tau Session Audit & Monorepo Health Report

> **Audit Run:** `2026-09-24T01:59:30.339Z` | **Total Sessions Audited:** `128` | **Total Events:** `20,912`

## 🎯 Executive Summary

- **Discovered Primary Anti-Pattern**: Multiple models hallucinating completion by outputting natural-language messages with zero tool calls, followed immediately by firing `todo(op="done")` flurries (up to 24 consecutive calls).
- **Phantom Todo Completion Rate**: `12/128` sessions (9.4%) exhibited unearned or flurried todo completions.
- **Critical Anomalies Detected**: `32` sessions had critical severity pattern violations.
- **Monorepo Structural Finding**: `projects/toxicwind/` was created by confused models misinterpreting the username as a package namespace. Intended shared utilities belong under `packages/sovereign-utils` or `packages/utils`.

---

## 🚨 Discovered Patterns & Hallucination Taxonomy

| Pattern Name | Severity | Detections | Description |
|---|:---:|:---:|---|
| **Rapid Consecutive Todo Done Flurry Without Intervening Work** | 🔴 CRITICAL | `22` | Documented in [`patterns/`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/skills/tau-session-audit/patterns/) |
| **Message with No Execution Tools Followed by Todo Done** | 🔴 CRITICAL | `5` | Documented in [`patterns/`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/skills/tau-session-audit/patterns/) |
| **Repeated Tool Failure Loop** | 🟠 HIGH | `44` | Documented in [`patterns/`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/skills/tau-session-audit/patterns/) |
| **High Model Churn Session** | 🟠 HIGH | `22` | Documented in [`patterns/`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/skills/tau-session-audit/patterns/) |
| **Defensive Completion Escape After User Brain-Dump / Clarifications** | 🟠 HIGH | `11` | Documented in [`patterns/`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/skills/tau-session-audit/patterns/) |
| **Unexecuted Scratchpad or Pseudo-Tool Syntax in Chat** | 🟠 HIGH | `6` | Documented in [`patterns/`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/skills/tau-session-audit/patterns/) |

### 1. The Phantom Todo Completion (Primary Smoking Gun)

Models repeatedly demonstrated the following failure mode:
1. Initialized an 10–18 item plan in `todo`.
2. Emitted an assistant message with narrative text / thinking (e.g. *"Now I will run end-to-end tests..."*) with **zero tool calls**.
3. Fired consecutive `todo(op="done")` tool executions back-to-back without running tests, edits, or commands.

#### Top Sessions with Phantom Todo Flurries:

| Session File | Model | Max Consecutive Todos | Total Tools | Details |
|---|---|:---:|:---:|---|
| [`-/2026-09-24T00-56-17-937Z_01a0d0e9-cb11-775d-8e6c-1dcbd77053ba.jsonl`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/.tau/agent/sessions/-/2026-09-24T00-56-17-937Z_01a0d0e9-cb11-775d-8e6c-1dcbd77053ba.jsonl) | `anthropic/claude-opus-4-8` | **24** | 750 | Intent: *General agent work* |
| [`-/2026-09-22T20-06-56-767Z_01a0caba-85ff-7346-a2b0-60399834875d.jsonl`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/.tau/agent/sessions/-/2026-09-22T20-06-56-767Z_01a0caba-85ff-7346-a2b0-60399834875d.jsonl) | `google-antigravity/gemini-3.8-flash` | **23** | 2172 | Intent: *General agent work* |
| [`-/2026-09-22T19-17-14-867Z_01a0ca8d-05f3-75d7-bd19-117c53bf6a8e.jsonl`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/.tau/agent/sessions/-/2026-09-22T19-17-14-867Z_01a0ca8d-05f3-75d7-bd19-117c53bf6a8e.jsonl) | `google-antigravity/gemini-3.8-flash` | **16** | 1160 | Intent: *General agent work* |
| [`-/2026-09-22T18-55-23-027Z_01a0ca79-0193-7476-b998-8ccca2530e8c.jsonl`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/.tau/agent/sessions/-/2026-09-22T18-55-23-027Z_01a0ca79-0193-7476-b998-8ccca2530e8c.jsonl) | `cerebras/zai-glm-4.6` | **13** | 280 | Intent: *General agent work* |
| [`-/2026-09-22T11-24-03-358Z_01a0c8db-cd9e-73d5-8e1c-7de53c93d257.jsonl`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/.tau/agent/sessions/-/2026-09-22T11-24-03-358Z_01a0c8db-cd9e-73d5-8e1c-7de53c93d257.jsonl) | `herd/kimi-k3-nim` | **9** | 1061 | Intent: *General agent work* |
| [`-/2026-09-22T15-43-01-828Z_01a0c9c8-e6c4-77f6-808e-4c200871451a.jsonl`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/.tau/agent/sessions/-/2026-09-22T15-43-01-828Z_01a0c9c8-e6c4-77f6-808e-4c200871451a.jsonl) | `mistral/zai-glm-5-3` | **8** | 1115 | Intent: *Bashrc aliases setup* |
| [`-/2026-09-17T22-56-14-277Z_01a0b195-b7c5-754b-a261-a17285af72e6.jsonl`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/.tau/agent/sessions/-/2026-09-17T22-56-14-277Z_01a0b195-b7c5-754b-a261-a17285af72e6.jsonl) | `nvidia/nvidia/nvidia-nemotron-nano-9b-v2` | **8** | 948 | Intent: *NVIDIA config / model setup* |
| [`-/2026-09-23T20-59-06-472Z_01a0d010-a368-71d4-bca0-c1944ed1cac3.jsonl`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/.tau/agent/sessions/-/2026-09-23T20-59-06-472Z_01a0d010-a368-71d4-bca0-c1944ed1cac3.jsonl) | `cloudflare-ai-gateway/workers-ai/@cf/moonshotai/kimi-k2.6` | **8** | 886 | Intent: *General agent work* |
| [`-/2026-09-15T02-41-01-039Z_01a0a2f0-6e6f-7479-8d13-5ccc98ddbe7e.jsonl`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/.tau/agent/sessions/-/2026-09-15T02-41-01-039Z_01a0a2f0-6e6f-7479-8d13-5ccc98ddbe7e.jsonl) | `openrouter/dots-studio/dots-3-note-preview:free` | **6** | 500 | Intent: *Audit / verification* |
| [`-/2026-09-22T12-53-07-657Z_01a0c92d-59c9-768a-830e-f5b3b03416ac.jsonl`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/.tau/agent/sessions/-/2026-09-22T12-53-07-657Z_01a0c92d-59c9-768a-830e-f5b3b03416ac.jsonl) | `google-antigravity/gemini-3.7-flash` | **4** | 1507 | Intent: *General agent work* |

---

## 🤖 Model Hallucination & Churn Matrix

Which models were most prone to phantom completions and syntax leaks:

| Model Identifier | Sessions Used | Phantom Todo Incidents | Syntax / Thinking Leaks | Health Verdict |
|---|:---:|:---:|:---:|:---:|
| `google-antigravity/gemini-3.8-flash` | 2 | **10** | 0 | 🔴 High Hallucination Risk |
| `herd/kimi-k3-nim` | 3 | **3** | 0 | 🟡 Moderate Risk |
| `cerebras/zai-glm-4.6` | 2 | **3** | 0 | 🟡 Moderate Risk |
| `google-antigravity/gemini-3.7-flash` | 2 | **2** | 1 | 🟡 Moderate Risk |
| `anthropic/claude-opus-4-8` | 4 | **1** | 1 | 🟡 Moderate Risk |
| `sovereign/inclusionai/ling-3.0-flash-fin:free` | 9 | **1** | 0 | 🟡 Moderate Risk |
| `sovereign/free` | 53 | **0** | 0 | 🟢 Reliable |
| `openrouter/thinkingmachines/inkling-small:free` | 8 | **0** | 0 | 🟢 Reliable |
| `herd/qwen-36-27b-mtp-ud` | 4 | **0** | 0 | 🟢 Reliable |
| `herd/beellama/qwen-flash-128k` | 3 | **0** | 0 | 🟢 Reliable |
| `google-antigravity/gemini-3.6-flash` | 3 | **0** | 0 | 🟢 Reliable |
| `anthropic/claude-opus-5` | 3 | **0** | 0 | 🟢 Reliable |
| `cloudflare-ai-gateway/workers-ai/@cf/zai-org/glm-5.2` | 2 | **0** | 0 | 🟢 Reliable |
| `unknown` | 3 | **0** | 0 | 🟢 Reliable |
| `nvidia/openai/gpt-oss-20b` | 2 | **0** | 0 | 🟢 Reliable |
| `groq/moonshotai/kimi-k2-instruct-0905` | 2 | **0** | 0 | 🟢 Reliable |
| `herd/fast` | 3 | **0** | 0 | 🟢 Reliable |
| `herd/beellama/exaone-4-0-1-2b-iq4xs` | 2 | **0** | 3 | 🔴 High Hallucination Risk |
| `herd/qwen-flash-da-128k` | 5 | **0** | 0 | 🟢 Reliable |
| `herd/gemini/gemini-3.5-flash` | 2 | **0** | 0 | 🟢 Reliable |

---

## 🏛️ Monorepo Convention & Workspace Architecture Audit

### 1. Workspace Misalignment
- Root [`package.json`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/package.json) defines: `workspaces: ['herd', 'herd/ui-svelte', 'packages/*', 'services/*']`.
- `projects/*` is **not** included in the root workspace declaration.
- Intermediate `projects/tsconfig.json` was missing, causing child builds in `projects/toxicwind/*` to fail with `error TS5083: Cannot read file '/home/toxic/sovereign/projects/tsconfig.json'`.

### 2. The `projects/toxicwind` Misnaming
- Models misinterpreted the user's GitHub username (`@toxicwind`) as a package prefix and created an untracked root directory `/home/toxic/sovereign/projects/toxicwind/`.
- Modules created inside: `capabilities/` (`@toxicwind/capabilities`), `policy/` (`@toxicwind/policy`), `registry-baseline/`, `repair/`.
- **Resolution**: These utilities belong under the sovereign umbrella as `packages/sovereign-utils` or inside `packages/utils`, which is already registered in Bun workspaces.

### 3. Binary Build SSOT
- The real binary compiled from `packages/coding-agent` is located at:
  - `projects/toxicwind/core/engine/packages/coding-agent/dist/tau` (242 MiB)
- It is installed at `~/.local/bin/tau`.

---

## 🛠️ Actionable Next Steps

1. **Relocate Utilities**: Migrate `@toxicwind/capabilities` and `@toxicwind/policy` from `projects/toxicwind/` into `packages/sovereign-utils/`.
2. **Add Root Workspace**: Include `packages/sovereign-utils` into root `package.json` workspaces.
3. **Enforce Verification Gate**: Use `tau-session-audit --check patterns` in agent handoffs to detect any unearned todo completions before completing turns.
