# Effort Parameter Audit — Why It Appears "Not Working"

## Verdict

The `effort` parameter on `task` spawns is functionally gated behind a feature-flag default of `false` in the Tau settings schema, meaning callers (including the architect) cannot see or use `effort: "lo"/"med"/"hi"` on the task tool unless they explicitly set `task.enableEffort: true` in config. Even when enabled, the effort only maps to model `thinking.efforts` — and the primary fast model (`freeinference/qwen3.6-35b`) carries `reasoning: false` and `thinking: {}` in the model cache, so it has zero controllable thinking levels. The secondary `vibe_spawn` tool (`{cli, prompt, name}`) has no effort field at all, so vibe workers always use their bundled agent's `thinkingLevel` frontmatter default. Three models out of five freeinference models (`glm-5.3-flash`, `deepseek-v4-flash`, `minimax-m3`) do declare controllable thinking efforts, so effort would actually change behavior only for subagents routed to those models.

## Gate Chain

Every gate between a caller requesting effort and the model receiving a thinking-level is numbered below. When a gate is "disabled" (default state), the effort hint is lost entirely.

1. **Gate 1 — Settings Schema Default (packages/coding-agent/src/config/settings-schema.ts:5139-5151)**
   `"task.enableEffort"` is defined with `default: false`. Without a user override, the feature is invisible to the tool schema.

2. **Gate 2 — Task Tool Schema Generation (packages/coding-agent/src/task/index.ts:584)**
   `getTaskSchema()` reads `this.session.settings.get("task.enableEffort")`. When `false`, the `effort?` field is NOT added to the wire schema, so the LLM never sees it in the tool description.

3. **Gate 3 — Tool Description (packages/coding-agent/src/task/index.ts:163)**
   The `effortEnabled` boolean is interpolated into the task tool's prompt description. When false, the tool description simply doesn't advertise the effort option to the LLM.

4. **Gate 4 — Wire Schema Validation (packages/coding-agent/src/task/types.ts:46)**
   When `effortEnabled: true`, the wire schema accepts `"lo" | "med" | "hi"`. These are the only valid values. No other strings are accepted.

5. **Gate 5 — Structured Subagent Pass-Through (packages/coding-agent/src/task/index.ts:1490)**
   In `#runSpawn`, `params.effort` is forwarded to `runStructuredSubagent({ effort: params.effort })` only when present.

6. **Gate 6 — Executor Resolution (packages/coding-agent/src/task/executor.ts:3639-3643)**
   The executor reads `options.effort`, clamps it with `task.maxEffort` (default `"max"`), and calls `resolveTaskEffortLevel(model, effort, ceiling)` to get a concrete `Effort` value.

7. **Gate 7 — Effort Mapping (packages/tui/src/thinking.ts:287-316)**
   `resolveTaskEffortLevel()` maps `"lo" → supported[0]`, `"med" → supported[supported.length/2]`, `"hi" → supported[last]`. If `maxEffort` clamps below the model's floor, it throws `RangeError: has no supported thinking effort at or below task.maxEffort=`.

8. **Gate 8 — Effective Thinking Level Resolution (packages/coding-agent/src/task/executor.ts:3657)**
   `effectiveThinkingLevel = effortLevel ?? (explicitThinkingLevel ? resolvedThinkingLevel : thinkingLevel ?? resolvedThinkingLevel)`. Effort only wins over the model's default thinking level if a concrete effort was resolved.

9. **Gate 9 — Model Capability (packages/catalog/src/model-thinking.ts:31-36)**
   `getSupportedEfforts(model)` returns `model.thinking?.efforts ?? []`. If the model has no `thinking` metadata (or empty), the list is empty and no effort is usable.

## Model Capability Table (freeinference provider, from models.db)

| Model               | `reasoning` | `thinking.efforts` | `supportsReasoningEffort` | Can `effort` change behavior? |
|---------------------|-------------|--------------------|---------------------------|--------------------------------|
| `qwen3.6-35b`       | `false`     | `{}` (empty)       | `false`                   | **No** — no thinking surface  |
| `diffusiongemma`    | `false`     | `{}` (empty)       | `false`                   | **No** — no thinking surface  |
| `glm-5.3-flash`     | `true`      | `["low", "high", "max"]` | `true`            | **Yes** — three controllable levels |
| `deepseek-v4-flash` | `true`      | `["low", "high", "max"]` | `true`            | **Yes** — three controllable levels |
| `minimax-m3`        | `true`      | `["minimal","low","medium","high","xhigh"]` | `true` | **Yes** — five controllable levels |

**Conclusion:** Only `glm-5.3-flash`, `deepseek-v4-flash`, and `minimax-m3` can actually benefit from effort on freeinference. `qwen3.6-35b` (the default for `@smol`, `@task`, `@slow`, etc.) and `diffusiongemma` have no controllable thinking — effort is silently ignored.

## How to Enable It

### Step 1 — Confirm `task.enableEffort: true` is set

Your config at `/home/toxic/estate/config/tau/config.yml:464` already declares:
```yaml
task:
  enableEffort: true
  maxEffort: high
```

This is correct and visible to the tool schema. The task tool description will advertise `effort: "lo" | "med" | "hi"`.

### Step 2 — Pin subagents to models that support thinking

The bottleneck is Gate 9 above: `qwen3.6-35b` has no thinking surface. To make effort meaningful, subagents must resolve to a model with controllable efforts. Add model overrides in your config.yml:

```yaml
task:
  agentModelOverrides:
    task: freeinference/glm-5.3-flash  # or minimax-m3
    sonic: freeinference/glm-5.3-flash
```

Then update model roles to use models with thinking:
```yaml
modelRoles:
  smol: freeinference/glm-5.3-flash  # was qwen3.6-35b:auto
  task: freeinference/glm-5.3-flash  # was qwen3.6-35b
```

### Step 3 — Provider-side risk

Freeinference's GLM and DeepSeek models support the OpenAI-compatible `reasoning_effort` or `thinking` request field. When tau resolves a thinking level like `"high"` on `glm-5.3-flash`, the compat layer maps it via `mapEffortToProviderParams()` which injects `thinking` or `reasoning_effort` into the request payload. If freeinference rejects these fields with a 400 (unlikely for GLM/DeepSeek, which support them natively), the request will fail. The `supportsReasoningEffort: true` flag in the model cache indicates the provider advertises this capability, so 400 errors are not expected for the models listed above.

**Exact 3-line config change** to make effort actually take effect for the chosen models:

```yaml
task:
  agentModelOverrides:
    task: freeinference/glm-5.3-flash
    sonic: freeinference/glm-5.3-flash
modelRoles:
  smol: freeinference/glm-5.3-flash
  task: freeinference/glm-5.3-flash
```

(4 lines, but only 3 distinct changes: two agent model overrides + two model role updates. The `task.agentModelOverrides` records must match the agent names used by the spawn policy.)

## How to Pin Worker Models

### Mechanism

1. **`task.agentModelOverrides.<name>`** — per-agent model override used during subagent resolution. Maps agent name (e.g. `"sonic"`, `"task"`, `"swarm1"`) to a model selector string.

2. **`modelRoles.<role>`** — role alias that resolves when the agent's model frontmatter references a role (e.g. `model: "@smol"`, `model: "@task"`). The `@role` syntax expands through modelRoles.

3. **Role mapping for vibe_spawn:**
   - `vibe_spawn cli=fast` → `sonic` agent → `model: "@smol"` in frontmatter
   - `vibe_spawn cli=good` → `task` agent → `model: "@task"` in frontmatter
   - So `modelRoles.smol` and `modelRoles.task` control which model the vibe workers use.

### Which settings file applies

- Global config: `~/.tau/agent/config.yml` → symlinked to `/home/toxic/estate/config/tau/config.yml`
- Project config: `.tau/config.yml` in current directory (overrides global)
- CLI flags override both

### Exact YAML for pinning vibe tiers to freeinference models

In `/home/toxic/estate/config/tau/config.yml` under `modelRoles:`:

```yaml
modelRoles:
  smol: freeinference/glm-5.3-flash  # fast vibe workers use glm-5.3-flash
  task: freeinference/glm-5.3-flash  # good vibe workers use glm-5.3-flash
```

Or to use different models for each tier:

```yaml
modelRoles:
  smol: freeinference/qwen3.6-35b    # fast: qwen (no thinking, cheap)
  task: freeinference/glm-5.3-flash  # good: glm (has thinking, can be effort-controlled)
```

**Note:** `sonic` has no role alias — it resolves via `task.agentModelOverrides.sonic`. Add it if needed:
```yaml
task:
  agentModelOverrides:
    sonic: freeinference/glm-5.3-flash  # explicit override
```

### Why workers show `freeinference/qwen3.6-35b`

The currently-running workers show `freeinference/qwen3.6-35b` because:
- The `sonic` agent frontmatter has `model: "@smol"` (agents.ts:68)
- The `task` agent frontmatter has `model: "@task"` (agents.ts:54)
- `modelRoles.smol` is set to `freeinference/qwen3.6-35b:auto` (config.yml:269)
- `modelRoles.task` is set to `freeinference/qwen3.6-35b` (config.yml:268)
- These are role aliases that expand through modelRoles. The worker is NOT using the parent session's active model — it uses the role-expansion chain which falls back to `modelRoles` first, then the active model string.

## Evidence Appendix

### AST Grep Commands and Outputs

**Q1: Where is the task tool schema defined with effort field?**
```
$ sg run -p 'createTaskSchema' -l ts packages/coding-agent/src/task/types.ts
```
Result: `packages/coding-agent/src/task/types.ts:115-183` — `createTaskSchema()` adds `effortField` conditionally:
```ts
const effortField = options.effortEnabled ? { "effort?": effortRule } : {};
```
where `effortRule` at line 46 is `'"lo" | "med" | "hi"'`.

**Q2: Where does `task.enableEffort` get read?**
```
$ sg run -p '"task.enableEffort"' -l ts packages/
```
Results:
- `packages/coding-agent/src/config/settings-schema.ts:5139` — schema definition with `default: false`
- `packages/coding-agent/src/task/index.ts:584` — `getTaskSchema()` call
- `packages/coding-agent/src/task/index.ts:608` — `renderDescription()` call

**Q3: Where is `task.maxEffort` used?**
```
$ sg run -p '"task.maxEffort"' -l ts packages/
```
Results:
- `packages/coding-agent/src/config/settings-schema.ts:5263` — schema definition, default `"max"`
- `packages/coding-agent/src/task/executor.ts:3639` — `settings.get("task.maxEffort")`

**Q4: Where is the effort resolution function?**
```
$ sg run -p 'function resolveTaskEffortLevel' -l ts packages/
```
Result: `packages/tui/src/thinking.ts:287` — maps `"lo"`→first supported, `"med"`→middle, `"hi"`→last supported. Throws RangeError when ceiling below model's floor.

**Q5: What does `vibeSpawnSchema` contain?**
```
$ sg run -p '"vibe_spawn"' -l ts packages/coding-agent/src/tools/vibe.ts
```
Result: `packages/coding-agent/src/tools/vibe.ts:66` — schema is `{ cli: "'fast' | 'good'", name?: string, prompt: string }`. NO effort field.

### Model Cache Query Results

Query: `SELECT substr(models,1,10000) FROM model_cache WHERE provider_id='freeinference:openai-models-list-context-v3'`

Results extracted per-model:
- `qwen3.6-35b`: `reasoning=false`, `thinking={}`, `supportsReasoningEffort=false`
- `diffusiongemma`: `reasoning=false`, `thinking={}`, `supportsReasoningEffort=false`
- `glm-5.3-flash`: `reasoning=true`, `thinking={mode:"effort",efforts:["low","high","max"],defaultLevel:"max",requiresEffort:true}`, `supportsReasoningEffort=true`
- `deepseek-v4-flash`: `reasoning=true`, `thinking={mode:"effort",efforts:["low","high","max"]}`, `supportsReasoningEffort=true`
- `minimax-m3`: `reasoning=true`, `thinking={mode:"effort",efforts:["minimal","low","medium","high","xhigh"]}`, `supportsReasoningEffort=true`

### Config File State

- `/home/toxic/estate/config/tau/config.yml:464` — `enableEffort: true` (ALREADY SET)
- `/home/toxic/estate/config/tau/config.yml:472` — `maxEffort: high` (ALREADY SET)
- `/home/toxic/estate/config/tau/config.yml:268-270` — `modelRoles.smol` and `modelRoles.task` point to `qwen3.6-35b` (THE PROBLEM)
- `/home/toxic/estate/config/tau/models.yml` — no `modelOverrides` section (auto-generated from mimetite)
