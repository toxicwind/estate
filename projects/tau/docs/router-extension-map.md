# TAU/oh-my-pi routing-extension map

Recon of TAU's real canonical routing extension: what it is, where the one true
copy lives, which copies are dead, exactly how it picks models, and the exact
invocation a benchmark harness should use for a head-to-head vs Sovereign Router
(`:25104`, model `sovereign/free`).

All paths below are on yote (the bridge box). Commit provenance checked 2026-09-21.

## 1. Canonical path

**`/home/toxic/sovereign/tau-extensions/omp-model-router`**
— package `@cakriwut/omp-model-router`, version 0.8.9.

Upstream origin: `github.com/cakriwut/omp-model-router` (README.md:34–50 installs via
`omp plugin install @cakriwut/omp-model-router`; package.json:3 name).

This is a **vendorized fork snapshot with local additions** (calibration harness,
auto-upgrade, embargo, RTK hooks, extra commands) — not a byte-identical copy of
upstream. Treat it as "our" router extension, derived from upstream.

Key files and sizes:

| File | Lines | Role |
|---|---|---|
| `src/index.ts` | 483 | extension factory, session/turn hooks, `/router` commands |
| `src/provider.ts` | 1147 | registers the `router` provider; calls `resolveRouting` at stream time |
| `src/routing/compose.ts` | 551 | `resolveRouting`: composes heuristic + context-capacity + classifier + image |
| `src/routing/heuristic.ts` | 580 | `decideRouting`: keyword/phase heuristic |
| `src/routing/index.ts` | 197 | `runClassifier` (sync LLM classifier), `parseClassifierOutput` |
| `src/routing/pin.ts` | 220 | scoped pins + pressure/lapse logic |
| `src/routing/text.ts` | 62 | prompt text extraction helpers |
| `src/config.ts` | 520 | `FALLBACK_CONFIG`, profiles, `parseCanonicalModelRef` |
| `src/types.ts` | ~230 | `RouterTier`, `RouterPhase`, `RoutingDecision`, `TaskType` |
| `src/calibration/*` | — | session calibration, confusion matrix, trace JSONL, `omp-router` CLI lab |
| `src/commands/*` | — | `/router` subcommands: help,status,enable,disable,pin,profile,set,thinking,usage,log,embargo,reload,update,fix,debug,widget |
| `src/cli/index.ts` | 49 | `omp-router` bin — **calibration lab only** (see §5) |

## 2. Stale / dead duplicates — full inventory

`/home/toxic` holds **two distinct trees** for this extension, duplicated across
many worktrees (~446 ffs hits). They are NOT identical (0.8.9 on both, but real
content drift).

| Path | State | Diff vs canonical |
|---|---|---|
| `sovereign/tau-extensions/omp-model-router` | **CANONICAL** (top-level, full tree) | — |
| `sovereign/scratch/tau-ext-forks/packages/omp-model-router` | STALE snapshot (reduced tree) | Lacks `src/calibration/hooks.ts`, `calibration/index.ts`, `calibration/pitfalls.ts`, `calibration/session.ts`, `calibration/trace.ts`, full CLI calibrate impl, extra commands/routing code |
| `<worktree>/tau-extensions/omp-model-router` (e.g. `dash-main`, `edge-work`, `herd-healer`, `oracle-hardening-wt`, `sovereign-clean`, `sovereign-wt-auto1m`) | STALE — branch/worktree snapshots of older main | track active crews' WIP; read-only for recon |
| `<worktree>/scratch/tau-ext-forks/packages/omp-model-router` | DEAD — fork snapshots mirroring the stale reduced tree | do not use |

Both top-level trees entered sovereign-projects history in the visible log at
`f9095c2665`; `diff -rq` shows changed shared files plus many files present only
in the top-level tree. Verdict: **only
`sovereign/tau-extensions/omp-model-router` is live**; `scratch/tau-ext-forks/…`
is a dead snapshot. The per-worktree copies are branch-local history, not
sources of truth.

## 3. Runtime wiring — is it loaded by tau right now?

**No. The extension is dormant code; it is NOT installed in the running tau.**

Evidence (all checked 2026-09-21 on yote):

1. `/home/toxic/.tau/agent/extensions/` — **empty** (the only user-level extension
   discovery dir). The running tau (PID 1694582, started 12:06,
   `engine/packages/coding-agent/dist/omp`) loads extensions from
   `<cwd>/.tau/extensions`, `~/.tau/agent/extensions`, `settings.json#extensions`,
   and installed plugin manifests (`engine/docs/extension-loading.md`) — the
   router extension is in none of them.
2. `strings dist/omp | grep omp-model-router` — **no matches** (1 file searched).
3. `/home/toxic/.omp/agent/model-router/` — **absent** (no config, no
   `traces/*.jsonl`). If the extension had ever run a session here, the trace dir
   would exist.
4. `/home/toxic/.tau/model-router.json` exists but only holds profile→model
   selectors (cheap→local EXAONE, quality/reasoning→`sovereign/free`, etc.) —
   it is tau-config wiring, **not** proof the extension is loaded.

So: TAU's session model today comes from `agent/models.yml` modelRoles
(`default→sovereign/free`) and the herd router — not from this extension.
**Do not claim a benchmark "beat TAU's router" unless the harness first installs
the extension** (see §5).

## 4. Model-selection logic — exact file/line references

### 4.1 Types

`src/types.ts`:

- **L4** `export type RouterTier = "high" | "medium" | "low";`
- **L41** `export type RouterPhase = "planning" | "implementation" | "lightweight";`
- `RouterPin = RouterTier | "auto"`; `ScopedPinSource = "user"|"heuristic"|"classifier"|"rule"|"auto-upgrade"`

### 4.2 Default config (tier → model mapping)

`src/config.ts`:

- **L18** `export const ROUTER_TIERS = ["high","medium","low"] as const;`
- **L22–50** `FALLBACK_CONFIG` — default profile `auto`:
  - high → `anthropic/claude-sonnet-4-5`, thinking `high`
  - medium → `anthropic/claude-sonnet-4-5`, thinking `medium`
  - low → `anthropic/claude-haiku-4-5`, thinking `low`
- **L131** `parseCanonicalModelRef` — splits `"provider/modelId"` refs.
- **L465** `resolveProfileName` — profile alias resolution.

User config lives at `~/.omp/agent/model-router/` (config.json + traces/);
profiles in README: Auto, Deep, Cheap, Hybrid, OSS.

### 4.3 Heuristic (step 1)

`src/routing/heuristic.ts`:

- **L376–380** `phaseForTier`: high→planning, medium→implementation, low→lightweight.
- **L382–415** `buildRoutingDecision(profileName, profile, tier, phase, reasoning, …)`:
  reads `profile[tier]`, parses `routed.model` → `{targetProvider, targetModelId, targetLabel}`,
  resolves thinking level (tier default or override).
- **L417–580** `decideRouting(context, profileName, profile, previousDecision, pinnedTier,
  thinkingOverrides, phaseBias, rules, isBudgetExceeded, floor)` — decision cascade:
  1. pinned tier (scoped pin) wins outright — skips everything else.
  2. custom `rules` keyword matches (word-boundary, `buildKeywordMatcher` L167).
  3. HIGH/LOW hint matchers, SUMMARY/GIT matchers → fixed tiers.
  4. STRONG/WEAK planning matchers (WEAK needs corroboration: wordCount≥12,
     `why ` prefix, prior planning phase, or ≥2 matches).
  5. wordCount ≥ highThreshold (120, planning-biased) → high; LOOKUP + short +
     no tool results → low; planning-phase stickiness; tool-result history →
     medium; wordCount ≤ lowThreshold (12, phase-biased) → low.
  6. Budget: `isBudgetExceeded && tier==="high"` → downgrade to medium (`isBudgetForced`).

### 4.4 Composition (the orchestrator)

`src/routing/compose.ts`:

- **L29–30** `TIER_ORDER = ["low","medium","high"]`, `RESPONSE_HEADROOM_TOKENS = 8192`.
- **L43–62** `tierUsableCapacity(tier, profile, registry)`:
  `model.contextWindow − max(model.maxTokens, 8192)`; undefined if unresolvable.
- **L65–100** `promoteForContextCapacity` — cheapest tier whose usable capacity fits
  current context tokens; if none fit, best-effort highest-capacity tier.
- **L158–550** `resolveRouting(input, config)` — full pipeline, in order:
  1. **L164–175** heuristic via `decideRouting`.
  2. **L178–226** pin-pressure lapse (heuristic-only sessions): shadow-routes with
     no pin; `incrementPinPressure` (src/routing/pin.ts, threshold
     `DEFAULT_PIN_PRESSURE_THRESHOLD = 3`, pin.ts:20); on lapse, pin busts,
     classifier cache busts, shadow decision takes over.
  3. **L229–238** Rule-J / rule-match sticky pins: heuristic/rule decisions set
     scoped pins via `setScopedPin(…, "heuristic"|"rule")`.
  4. **L240–290** context-capacity promotion: if live context tokens exceed the
     decided tier's usable capacity → promote to cheapest fitting tier
     (`isContextTriggered = true`); cache bust.
  5. **L292–448** classifier override — **skipped** when: no `classifierModel`
     configured, sub-agent session (`parentSessionId` set), context-triggered, or
     rule-matched. Prompt-equality cache (signature
     `lastUserText|userMsgIndex|toolBucket`, TTL 20 turns) gates fresh calls.
     Verdict handling:
     - `calibration.mode === "telemetry"` (default, config.ts L40): classifier
       runs **for data collection only** — heuristic decision stands.
     - `"adaptive"`: verdict overrides; with active pin, verdict only feeds
       pin-pressure (stronger signal than heuristic); on lapse applies classifier tier.
     - classifier failed → heuristic fallback, `isHeuristic = true`.
  6. **L450–510** image upgrade: if context has image attachment and decided tier's
     models lack image input → lowest tier that supports images (budget-respecting).
  7. **L540–548** floor (`defaultPin`): only a baseline default replacing hardcoded
     "medium" — NOT a minimum clamp.

### 4.5 LLM classifier (step inside step 5)

`src/routing/index.ts`:

- **L15–18** `SYNC_CLASSIFIER_TIMEOUT_MS = 10_000`, `SYNC_CLASSIFIER_MAX_BUFFER = 512`.
- **L25–42** `resolveClassifierContextWindow(refs, registry)` — first resolvable
  classifier model's `contextWindow`; fallback 128_000.
- **L44–190** `runClassifier(classifierModelRefs, modelRegistry, context, phase,
  debug, toolCounts, pitfalls, contextWindow)`:
  - accepts one model or a **fallback chain**; resolves each via
    `modelRegistry.find`; requires API key via `modelRegistry.getApiKey`;
  - `streamSimple` with `maxTokens: 200`, hard 10 s abort, ≤512 chars buffered;
  - `parseClassifierOutput` — first parseable verdict wins, returned immediately;
  - **all classifiers fail → returns `undefined`** → heuristic stands.

### 4.6 Calibration (telemetry + learning)

`src/calibration/session.ts`:

- per-session confusion matrix `matrix[heuristic][llm]` (3×3, low=0/medium=1/high=2);
- `initSessionCalibration` (global prior weighted 0.1 by default);
- `updateCalibrationMatrix` — records every heuristic-vs-classifier comparison.
- `src/calibration/hooks.ts` — `calibrationSessionStart`, `calibrationTurnStart/End`
  (async classifier polling), wired into session lifecycle.
- `src/calibration/trace.ts` — appends per-turn records incl. prompt logs to
  `classifierPrompt.jsonl` under the session artifacts dir (enabled by
  `calibration.traceEnabled`).

### 4.7 Extension entry (how it hijacks the session model)

`src/index.ts`:

- **L26** `const routerExtension = (pi: ExtensionAPI) => { … }`; **L483** `export default`.
- registers a **`router` provider** (`registerRouterProvider`, src/provider.ts);
  profiles become selectable as `router/<profileName>` via `modelRegistry.find`.
- `pi.on("session_start", …)` — reloads config, activates session scope, re-registers
  provider, switches session model to `router/<selectedProfile>`.
- **L323** `pi.on("turn_start", …)` — scope re-activation, user opt-out detection
  (manual `/model` switch disables router), classifier polling via calibration hooks.
- `pi.on("turn_end", …)` — restores `router/…` model, writes trace, releases context.
- `pi.on("tool_execution_end", …)` — **auto-upgrade**: ≥2 consecutive failures of
  the same tool (threshold, config `autoUpgrade.threshold`) → scoped pin to next
  higher tier (`"auto-upgrade"` source).
- `/router` slash commands registered via `registerCommands` (src/commands/index.ts:76).

`src/provider.ts` **L554** — the `router` provider's stream path calls
`resolveRouting({context, previousDecision, pinnedTier: scopedPin, floor,
isBudgetExceeded, modelRegistry, lastExtensionContext, calibration, scope}, …)`
on every turn, then delegates `streamSimple` to the decided
`targetProvider/targetModelId` (L725, L834, L1031 delegation points).

### 4.8 What this router is / is NOT

- It is a **complexity-tier classifier** (heuristic + optional LLM) mapping
  prompts to high/medium/low → profile-configured models. Cost/complexity routing.
- It has **no Elo, no latency racing, no provider failover** — nothing like
  Sovereign Router's ranking machinery. `sovereign/free` appears in its world only
  as a tier-mapped model ref, not as a routing signal.
- Telemetry mode is default: the LLM classifier mostly **observes** unless
  `calibration.mode: "adaptive"` is set.

## 5. Exact benchmark invocation (head-to-head vs Sovereign Router)

### 5.1 What `omp-router` CLI is — and is NOT

`bun run src/cli/index.ts` (`bin.omp-router`) is a **calibration lab harness only**:
`calibrate analyze|simulate|export|import|reset` and `prompt-log` over
`~/.omp/agent/model-router/traces/*.jsonl`. **It cannot route a prompt.**
There is no standalone "ask the router which model" CLI. Routing happens
**in-session**, inside an oh-my-pi/tau turn, via the `router` provider.

### 5.2 Benchmark route A — the real route (in-session, recommended)

Install the extension into a tau profile, then drive prompts through `tau -p`:

```bash
# 1. install (one-time) — source path since we benchmark OUR fork:
cd /home/toxic/sovereign/tau-extensions/omp-model-router
bun install
# place the extension where the engine discovers it, e.g.:
mkdir -p ~/.tau/agent/extensions
ln -s /home/toxic/sovereign/tau-extensions/omp-model-router ~/.tau/agent/extensions/omp-model-router
# (or: omp plugin install @cakriwut/omp-model-router  for the upstream build)

# 2. enable inside one tau session, pick profile, verify:
tau -p '/router enable auto'        # routerEnabled=true, defaultProfile=auto persisted
tau -p '/router status'             # confirm provider=router, profile, tiers->models

# 3. run the benchmark prompt set (each turn routes, then streams the tier model):
for p in "${prompts[@]}"; do
  tau -p "$p"
done

# 4. read per-turn decisions from the trace log:
ls ~/.omp/agent/model-router/traces/*.jsonl
# each record: heuristic tier, classifier verdict, final tier, target model, latency
```

Optional flags: `/router pin high` (force tier), `/router set calibration.mode adaptive`
(LLM classifier actually overrides), `/router debug` (per-turn reasoning).

For a scripted harness, drive `tau -p` per prompt and parse the trace JSONL +
`/router log` output; the tier→model mapping comes from the active profile
(`~/.omp/agent/model-router/config.json`, defaults in src/config.ts L22–50).

### 5.3 Benchmark route B — library-level (routing function only)

Test `resolveRouting` in isolation with a stubbed `ExtensionContext`/`modelRegistry`:

```ts
import { resolveRouting } from "…/tau-extensions/omp-model-router/src/routing/compose.ts";
import { FALLBACK_CONFIG } from "…/tau-extensions/omp-model-router/src/config.ts";

const decision = await resolveRouting(
  { context, previousDecision: undefined, modelRegistry: stubRegistry,
    isBudgetExceeded: false },
  { profileName: "auto", profile: FALLBACK_CONFIG.profiles.auto,
    phaseBias: 0.5, classifierModel: "anthropic/claude-haiku-4-5",
    calibrationConfig: { enabled: true, mode: "telemetry" } },
);
// decision.tier / decision.targetProvider / decision.targetModelId / decision.reasoning
```

This benchmarks the **classifier+heuristic**, not end-to-end inference — fair only
for the "which tier would it pick" question.

### 5.4 Sovereign side (the other half of the head-to-head)

Sovereign Router `:25104` (OpenAI-compatible) with model `sovereign/free`:

```bash
curl -s http://127.0.0.1:25104/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"sovereign/free","messages":[{"role":"user","content":"<PROMPT>"}]}'
```

### 5.5 Fairness notes for Tally's harness

1. The tau side must record **which model actually served** (`targetProvider/targetModelId`
   from the trace) — "the router" is not a model; compare outcomes per tier model,
   not vs the word "router".
2. Default profile maps high AND medium to `anthropic/claude-sonnet-4-5` — two
   tiers, one model. A harness that only varies prompts may see no model change;
   use a profile with distinct tier models (Cheap/Hybrid) for a real A/B.
3. Telemetry mode ≠ adaptive: with default config the LLM classifier never changes
   the model — set `calibration.mode: adaptive` for the classifier to matter.
4. The classifier is skipped in sub-agent sessions and on context-trigger/rule-match
   turns — harness prompts must run as the main session user turn.
5. Cost dimension: router tiers trade quality for cost; a fair scorecard reports
   quality/latency/cost per prompt, not a single winner.

## 6. Bottom line

- Canonical: `sovereign/tau-extensions/omp-model-router` (`@cakriwut/omp-model-router`
  0.8.9, our fork+extensions of upstream).
- Stale: `sovereign/scratch/tau-ext-forks/packages/omp-model-router` (dead reduced
  snapshot). Worktree copies are branch-local history.
- **Not loaded by the running tau** (empty `~/.tau/agent/extensions/`, no strings
  in `dist/omp`, no `~/.omp/agent/model-router/`).
- Selection logic: heuristic → pin-pressure → context-capacity promotion →
  LLM classifier (adaptive overrides / telemetry observes) → image upgrade → floor;
  tier → `profile[tier].model` via `buildRoutingDecision`.
- Benchmark: there is no route-a-prompt CLI; the real harness installs the extension
  and drives `tau -p` per prompt, reading `~/.omp/agent/model-router/traces/*.jsonl`;
  compare against `curl :25104/v1/chat/completions` with `sovereign/free`.
