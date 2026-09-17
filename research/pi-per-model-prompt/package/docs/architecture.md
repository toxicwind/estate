# Architecture

## Goal

`pi-per-model-prompt` packages one Pi extension that appends a small, auditable harness core for every model and then applies narrower prompt deltas for specific model identities.

The extension exists to correct observed model behavior under Pi's coding harness while keeping a single shared append layer for cross-model coding discipline. It is not a generic prompt registry and it should not duplicate large baseline policy that already belongs in Pi itself.

## Why this shape

The package follows Pi's extension and package guidance:

- expose one extension entry through `package.json -> pi.extensions`
- keep the runtime as raw TypeScript so Pi can load it through its normal extension loader
- avoid a build pipeline unless packaging requirements actually demand one
- keep correction logic in plain data modules so resolution is easy to test

This keeps the package cheap to audit, easy to publish, and easy to evolve with new model deltas.

## Runtime flow

1. Pi loads `index.ts` from the package manifest.
2. `src/index.ts` registers a `before_agent_start` hook and a `before_provider_request` hook.
3. On each prompt, the start hook inspects `ctx.model.id`.
4. `src/resolve.ts` composes matching layers in deterministic order.
5. `src/prompt.ts` appends each layer once by marker (line-start matching to avoid false positives).
6. For the exact selected model `gpt-5.4`, the provider-request hook patches outgoing Responses-style payloads to set `text.verbosity = "low"`, including Azure deployment-alias payloads.
7. If nothing changes, the hooks return `undefined` and leave the prompt or payload untouched.

## Composition model

Resolution is additive rather than branch-based.

### Design principle: strong base, narrow deltas

The harness core carries **all cross-model coding contracts** — scope discipline, output efficiency, context-before-edit, grounded implementation, tool discipline, diagnostic discipline, verification and faithful reporting, collaborator mindset, code security, actions-with-care, git safety, and user update discipline. Many of these rules are adapted from battle-tested Claude Code harness rules and apply equally to all model families. Family and model layers carry **only model-specific corrections** that the base cannot cover. Runtime request overrides stay separate and narrowly scoped to provider payload details such as model-specific verbosity hints.

### Prompt cache constraint

Layers are always **appended** to the system prompt, never prepended or injected mid-stream. This preserves any upstream prompt caching (e.g., Pi's own system prompt prefix) since the cache-keyed prefix remains unchanged.

### Shared harness core

Every model receives the same first layer:

1. shared harness-core append layer (`HARNESS_CORE_LAYER`)

This layer carries the cross-model coding contracts that should hold even when no family-specific delta matches:

- `output_contract` — deliverable completeness and format discipline
- `output_efficiency` — go straight to the point, no filler, expand only when warranted
- `scope_discipline` — minimal change, no over-engineering, no speculative extras, no backwards-compat hacks
- `context_before_edit` — read before edit, resolve dependencies, check cross-module contracts
- `grounded_implementation` — ground claims in observed evidence, never fabricate, no unnecessary file creation
- `tool_discipline` — prefer dedicated tools, sequential dependency resolution, parallelize safely
- `diagnostic_discipline` — diagnose before switching tactics, don't retry blindly
- `verification_and_reporting` — run checks, report faithfully, don't hedge confirmed results or claim unverified success
- `collaborator_mindset` — flag misconceptions and adjacent bugs
- `code_security` — no injection vulnerabilities, fix insecure code immediately
- `actions_with_care` — reversible actions proceed, irreversible actions need confirmation, investigate before deleting unexpected state
- `git_safety` — no force-push/skip-hooks/amend-after-failure, stage by name, commit/push only when asked
- `user_updates_spec` — concise updates at phase transitions only

### OpenAI GPT-5

Current order:

1. shared harness core (`HARNESS_CORE_LAYER`)
2. family layer (`GPT5_FAMILY_LAYER`) — output structure, follow-through policy, no meta-commentary openers
3. model-line layer (`GPT5_CODEX_LAYER`, if `codex` tag present) — scope reinforcement
4. version or exact-model layer (`GPT54_LAYER` or `GPT53_CODEX_LAYER`) — official-style answer shape and model-specific corrections

Examples:

- `gpt-5.4` → `HARNESS_CORE` + `GPT5_FAMILY` + `GPT54`, plus runtime `text.verbosity = "low"` on Responses-style requests
- `gpt-5.4-codex` → `HARNESS_CORE` + `GPT5_FAMILY` + `GPT5_CODEX` + `GPT54`
- `gpt-5.3-codex` → `HARNESS_CORE` + `GPT5_FAMILY` + `GPT5_CODEX` + `GPT53_CODEX`

### Anthropic Claude

All Claude models receive a fixed three-layer stack regardless of series:

1. shared harness core (`HARNESS_CORE_LAYER`)
2. family layer (`CLAUDE_FAMILY_LAYER`) — XML preference, thinking discipline, long-context attention
3. coding-agent layer (`CLAUDE_CODING_AGENT_LAYER`) — comment discipline, implementation reporting

Detection is based on the presence of `opus`, `sonnet`, or `haiku` in the model ID.

Most Claude Code harness rules (output efficiency, actions-with-care, git safety, faithful reporting, collaborator mindset) have been promoted to the shared harness core since they apply equally to all model families. The Claude-specific layers now only carry rules for Claude's unique tendencies: over-commenting, reasoning exposition, XML structure preference, and long-context positional bias.

This order matters because the broader baseline should land before narrower corrections.

## Source layout

```
index.ts                               # package entry (re-exports src/index.ts)
src/index.ts                           # Pi extension entry; registers before_agent_start + before_provider_request hooks
src/model-identity.ts                  # parser for gpt-5*, claude-*; produces ModelIdentity
src/resolve.ts                         # deterministic layer resolution by family/version/tags
src/prompt.ts                          # PromptLayer types, section/prose builders, appendOnce, hasMarker
src/layers/base.ts                     # shared harness-core append layer (strong baseline for all models)
src/layers/openai/gpt5/family.ts       # GPT-5 family baseline (output contract, follow-through policy, no meta-commentary openers)
src/layers/openai/gpt5/codex.ts        # GPT-5 Codex line (scope reinforcement)
src/layers/openai/gpt5/gpt-5.4.ts     # GPT-5.4 delta (autonomy, no-fluff interaction style, official-style answer shape)
src/layers/openai/gpt5/gpt-5.3-codex.ts # GPT-5.3-Codex delta (official-style compact answer shape, ambiguity handling)
src/layers/anthropic/claude/family.ts  # Claude family baseline (XML, thinking discipline, long-context attention)
src/layers/anthropic/claude/coding-agent.ts # Claude coding-agent delta (comment discipline, implementation reporting)
test/model-identity.test.ts            # parser coverage for supported and unsupported ids
test/prompt.test.ts                    # helper behavior and append idempotence
test/resolve.test.ts                   # exact layer ordering and model matching
test/extension.test.ts                 # end-to-end hook behavior for before_agent_start
```

## Model parsing

`inspectModelIdentity` returns a `ModelIdentity` with:

- `family`: `"gpt-5"` | `"claude"` | `undefined`
- `version`: `{ major, minor? }` for GPT models
- `series`: `"opus"` | `"sonnet"` | `"haiku"` for Claude models
- `tags`: `Set<"codex">` for GPT models with a `-codex` suffix

Unknown model IDs return `{ rawId, tags: new Set() }` with no family; `resolveLayers` still returns the shared harness-core layer for these.

## Rules for adding a new layer

Add a new layer only if all of the following are true:

1. There is a measured shared or model-specific failure mode.
2. The issue is not already corrected by an existing broader layer.
3. The new behavior can be described as a stable shared contract or a narrow correction, not a new policy center.
4. The layer can be identified by a unique marker.
5. The expected resolution order is deterministic.

When adding a layer:

1. create a file under the relevant family directory (`src/layers/<provider>/<family>/`)
2. give it a unique `marker`
3. include concise `meta` with target, fixes, and non-goals
4. update `src/resolve.ts`
5. add or extend tests for model parsing and composition order
6. update `README.md` if externally visible behavior changed

## Test strategy

The package tests four paths:

- `model-identity`: parser coverage for supported and unsupported ids
- `prompt`: helper behavior and append idempotence
- `resolve`: exact layer ordering and model matching
- `extension`: end-to-end hook behavior for `before_agent_start`

The tests intentionally avoid depending on a running Pi process; they validate the extension as a pure TypeScript module with mocked hook registration.
