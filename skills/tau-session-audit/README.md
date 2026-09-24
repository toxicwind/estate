# 🔍 tau-session-audit — Intent Reconstruction, Hallucination Detection & Monorepo Health

A production-grade audit engine for `.tau/agent/sessions/` JSONL logs. Reconstructs user intent, verifies genuine task completion vs. model hallucinations, and outputs GitHub-ready Markdown reports with deep links.

---

## 🚀 Quick Start

```bash
# 1. Generate full GitHub-ready Markdown report to stdout
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --report

# 2. Save report to a file for GitHub PR or review
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --report --out=SESSION_AUDIT.md

# 3. Check for specific anti-patterns
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --check todo-phantom
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --check patterns

# 4. Standard TSV dataframe and stats
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --all
```

---

## 🚨 First-Class Pattern Detectors (`patterns/`)

The audit engine features a modular, first-class [`patterns/`](patterns/) system targeting agent hallucinations:

| Pattern | Severity | Description |
|---|:---:|---|
| **`MESSAGE_NO_TOOLS_THEN_TODO_DONE`** | 🔴 CRITICAL | Model sends a narrative text/thinking message with **zero tool calls**, immediately followed by a `todo(op="done")` call. |
| **`CONSECUTIVE_TODO_FLURRY`** | 🔴 CRITICAL | Model executes 3 to 24+ consecutive `todo` operations in a row with zero intervening commands, edits, or tests. |
| **`TODO_DONE_AFTER_UNRESOLVED_ERROR`** | 🟠 HIGH | Model marks a task complete immediately following an unhandled command failure without repairing it. |
| **`THINKING_LEAK_SYNTAX`** | 🟠 HIGH | Model leaks raw scratchpad text (`</thinking>`), pseudo-patch DSLs (`SM:FIND`/`SM:AFTER`), or `<system-action>` into user chat. |
| **`REPEATED_COMMAND_LOOP`** | 🟠 HIGH | Model hits the exact same error (e.g. `TS5083`) 3+ times in a row without adapting. |
| **`MODEL_ROTATION_CHURN`** | 🟡 MEDIUM | Sessions with 4+ models rotated due to agent stalls, failures, or loops. |

---

## 🔬 Discovered Case Study: The `@toxicwind` Hallucination Incident

During the audit of recent sessions (`2026-09-24T00-56-17` and `2026-09-23T20-59-06`), a major failure pattern was isolated:

1. **What was requested**:
   An architecture document titled `@toxicwind: The Emergent Solution` was attached. It proposed two engine primitives:
   - **Capability Registry**: Runtime publishes a manifest; consumers declare needs; loader resolves to eliminate missing exports (`keyText`, `compact`).
   - **Policy Channel**: Approval decisions travel with the task for headless safety, avoiding UI `confirm()` calls.

2. **What the models did**:
   - Misinterpreted the GitHub username (`@toxicwind`) as a package prefix.
   - Spawned an untracked root directory `projects/toxicwind/` with `@toxicwind/capabilities`, `@toxicwind/policy`, and renamed `coding-agent` to `@toxicwind/core`.
   - Repeatedly hit `error TS5083: Cannot read file '/home/toxic/sovereign/projects/tsconfig.json'` because `projects/*` was omitted from root Bun workspaces.

3. **The Hallucination Smoking Gun**:
   - The model created an 18-item todo list.
   - Emitted an assistant message with **no tools** (*"Now I need to run the end-to-end test..."*).
   - In 69 events, fired **18 consecutive `todo` done calls** with **zero tool calls in between**, reaching `Overall: 18/18 done, 0 open`.
   - Claimed *"All 15 tasks from the emergent solution todo list have been completed successfully"* even though tests were never executed and the only test command attempted immediately failed with a rule violation.

---

## 🏛️ Monorepo Convention Findings

- **Workspace Root**: [`/home/toxic/sovereign/package.json`](https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/package.json)
  - Workspaces configured: `['herd', 'herd/ui-svelte', 'packages/*', 'services/*']`.
  - Intended home for shared utilities: `packages/sovereign-utils` or `packages/utils` (already registered in workspace).
- **Binary Distribution SSOT**:
  - Compiled binary: `projects/toxicwind/core/engine/packages/coding-agent/dist/tau` (242 MiB).
  - Production launcher: `~/.local/bin/tau` (Bun ELF binary).
- **Remotes**:
  - `origin`: `https://github.com/toxicwind/sovereign-projects.git`
  - `ranch`: `https://github.com/toxicwind/ranch.git`
  - `vendor`: `https://github.com/can1357/oh-my-pi.git`
  - `archive`: `https://github.com/toxicwind/local-work-archive.git`

---

## 🧪 Tests

```bash
bun test /home/toxic/sovereign/skills/tau-session-audit/helper/audit.test.ts
```

All 32 unit tests pass covering intent inference, anomaly scoring, and pattern detection.
