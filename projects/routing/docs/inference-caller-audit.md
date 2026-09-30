# Inference Caller Audit — estate-wide (read-only)

**Date:** 2026-09-21
**Crew:** `wiring-audit` (Ember's crew)
**Status:** READ-ONLY. No caller wiring was changed. No rewiring happens before the Sovereign-vs-TAU bake-off verdict.

## What this is

A complete map of every canonical inference caller on the estate: what route/model string each one uses **today**, whether the choice is config-driven or hardcoded, and who owns it — so the post-bake-off rewiring crew has a single execution surface. Every caller listed was read from live disk on yote 2026-09-21. Generated data, chat seeds, vendored deps, benchmarks output, docs prose, and `.git` history were excluded; only live code/config callers remain.

Canonical ports: herd `:25100` · keypool `:25109` · sovereign router `:25104` · kimi-code `:25126` · kimi-auto-shim `:25153` · toolcall-llm `:25152` · nim-kimi sidecar `:25163` · oracle daemon `:25151` · flock proxy `:25193`.

## Summary counts

| Family | Callers / selection points | Hardcoded | On `sovereign/free` |
|---|---|---|---|
| Oracle-market (bidders, workers, judges, debate) | 9 | 1 partial-live (route-name priority list in code) + 1 bench-only | 0 |
| Kimi + tooling + squawk + cockpit | 8 | 1 (`nim-kimi-sidecar.py` MODEL_ID) | 1 (kimi-code default) |
| Super-ralph (CLI, shim, bidder env) | 13 live (+1 stale dup) | 4 clear + shim fallbacks | 0 |
| Debate-oracle + misc daemons/scripts | 5 | 4 (+1 direct-upstream bypass) | 1 (debate-run default router `:25104`; lane models hardcoded) |
| Research/checker scripts (enumerated, not wired) | 3 | 2 hardcoded model lists (research-only) | 0 |
| TAU (engine + extensions + configs) | 23 | 8 hardcoded — **all latent** (upstream oh-my-pi) | 7 (default/task/smol/advisor/subagent-default/router-quality/router-reasoning) |
| **Verified non-callers** | 6 | — | — |
| **TOTAL live callers** | **59** | **21 (10 live-affecting, 11 latent/bench/research-only)** | **9** |

**Rewire action needed (before verdict: map only, no changes):** 10 live callers hardcode model selection in code (concrete IDs or in-code priority lists), 1 direct upstream bypass (`api.groq.com` from Kodi addons), 1 staleness trap (`kimi-code-setup` would clobber the live `sovereign/free` default on re-run), and 8 latent hardcoded fallbacks in the TAU engine (upstream oh-my-pi, only reachable for unconfigured roles — `slow` is in `cycleOrder`). The rest are config-driven and rewire by editing router config alone.

## Oracle-market callers

All paths POST to `$HERD_URL` (default `http://127.0.0.1:25100`) `/v1/chat/completions`. The string `sovereign/free` and port `:25104` appear nowhere in this tree.

| caller | current route | config or hardcoded | owner | rewire action needed |
|---|---|---|---|---|
| `agents/oracle-market/bin/oracle_ask.py` — `run_ask()` judge panel | Aliases `oracle-judge-a/b/c`, fallback `oracle-judge-local`; env `ORACLE_JUDGES` override; **fail-closes**: rejects any concrete ID (with `/`, `:`, or family names) | config (aliases; concrete IDs owned by `config/herd.yaml`) | sovereign / oracle-market crew | none — clean alias surface |
| `oracle_ask.py` → `escalation.debate_tier()` advocates | Reuses the same alias list; round-robin over aliases | config (inherits panel) | sovereign / oracle-market crew | none |
| `agents/oracle-market/bin/escalation.py` `debate_tier` | No route of its own — takes `judges` list + injected `chat_fn` | N/A (transport-injected) | sovereign / oracle-market crew | none |
| `agents/oracle-market/bin/bidder.py` `_resolve_ralph_model()` | Candidates `[RALPH_MODEL env, "kimi-k3-nim", "gemini-3-flash-preview"]`; live-probes each against herd `:25100/v1`, first 200-with-choices wins, 300s cache | **partial-hardcoded**: priority list in code, but all entries are herd route names, not upstream IDs | sovereign / oracle-market crew | **map only** — priority list arguably belongs in router config |
| `agents/oracle-market/bin/oracle_daemon.py` POST `/ask` (`:25151`) | Pass-through to `run_ask`; no defaulting | config | sovereign / oracle-market crew | none |
| `config/herd.yaml` `oracle-judge-a` | `--target openrouter-free/nex-agi/nex-n2.5-mini:free --standby openrouter-free/nex-agi/nex-n2.5-pro:free` | config (the canonical selection surface) | sovereign / herd config | none — this is where selection belongs |
| `config/herd.yaml` `oracle-judge-b` | `--target openrouter-free/nex-agi/nex-n2.5-pro:free --standby openrouter-free/poolside/laguna-s-2.1:free` | config | sovereign / herd config | none |
| `config/herd.yaml` `oracle-judge-c` | `--target openrouter-free/poolside/laguna-s-2.1:free --standby openrouter-free/nex-agi/nex-n2.5-mini:free` | config | sovereign / herd config | none |
| `config/herd.yaml` `oracle-judge-local` | Native llama-swap alias `beellama/gemma-96k` (shim entry removed — re-entrant deadlock fix) | config | sovereign / herd config | none |
| `agents/oracle-market/bench/judge_return.py` `--mode old` | Hardcoded `["openrouter-free/nex-agi/nex-n2.5-mini:free", "…pro:free", "…laguna-s-2.1:free"]` | **hardcoded (bench-only, intentional baseline)** | sovereign / oracle-market crew | none — bench, not live |

Also verified: `bin/keypool.py` is key management only (no model selection); `bin/test_oracle_repair.py` is a test asserting `model=kimi-k3-nim` on `:25100/v1`; paper-search (`skills/paper-search/bin/paper-search` → `race_papers.py`) makes **zero inference calls** (arXiv + alphaXiv HTTP only) — not a caller.

## Kimi + tooling + squawk + cockpit callers

| caller | current route | config or hardcoded | owner | rewire action needed |
|---|---|---|---|---|
| kimi-code CLI/web (`~/.kimi-code/config.toml`) | `default_model = "sovereign/free"` → provider `sovereign` → `http://127.0.0.1:25104/v1` | config (TOML) | sovereign / ember-kimi-route crew | none — already on sovereign/free |
| `sovereign/bin/kimi-code-setup` | Writes `default_model = "herd/qwen-flash"` (stale) + herd fallback table | config-writer (bash) | sovereign/bin | **staleness trap** — re-running clobbers the live `sovereign/free` default; script needs updating before verdict execution |
| kimi-auto-shim (`:25153`, pitchfork run line) | `--target openrouter-free/moonshotai/kimi-k3:free --standby openrouter-free/moonshotai/kimi-k2.6:free --standby openrouter-free/moonshotai/kimi-k2.5:free --standby openrouter-free/moonshotai/kimi-k2.7-code:free --standby hf-free/moonshotai/Kimi-K3 --standby nim-kimi/moonshotai/kimi-k3` | config (pitchfork TOML, mirrors `herd.d/kimi-auto.yaml` byte-identical) | sovereign/pitchfork.toml + kimi-auto | none |
| toolcall-llm (`:25152`, pitchfork run line) | `llama-server -m /home/toxic/models/qwen3.5-9b-dflash-Q5_K_M.gguf --alias qwen3.5-9b-tool` | config (pitchfork TOML) | sovereign/pitchfork.toml | none — local GGUF, no provider selection |
| nim-kimi sidecar (`:25163`, `sovereign/bin/nim-kimi-sidecar.py`) | `MODEL_ID = "moonshotai/kimi-k3"` → `https://integrate.api.nvidia.com/v1/chat/completions` | **hardcoded (Python const)** | sovereign/bin | **map only** — model-family-named code hardcodes that family's ID; route `nim-kimi/moonshotai/kimi-k3` is in herd.yaml config |
| herd router (`:25100`, `config/herd.yaml` + `herd.d/`) | pools `openrouter-free`→keypool `:25109`, `hf-free`→`router.huggingface.co/v1`, `nim-kimi`→`:25163`, `beellama` local; modelMap `kimi-k2`, `kimi-k3-nim` honest (a49f7bf0 intact) | config (YAML) | sovereign/config / herd-deployer | none — the sanctioned pattern |
| sovereign router (`:25104`, `tools/sovereign-router/sovereign-router-ts/router.ts`) | `sovereign/free` = provider `sovereign` + id `free` → free-routing across ranked providers | router behavior (TS) | sovereign-router-ts | none — routing strategy, not ID selection |
| kimi-code `[models]` fallback table (config.toml) | `herd/qwen-flash`, `herd/kimi-k2.7-code`, `herd/kimi-k2.6`, `herd/gemini-flash`, `moonshot/kimi-k2.7-code` — user-selectable, not default | config (TOML) | kimi-code-setup writer | none |

Verified non-callers: cockpit (`:25212` stock Linux admin console, zero LLM refs); all squawk tooling (ws `:25147`, feed `:25135`, magic-link `ui.html`, relay sink/forward) — zero LLM call sites.

## Super-ralph callers

Bidder daemon env today (forge/scout): inherited `NIM_MODEL=moonshotai/kimi-k3` is **ignored** by the ralph-pathfinder resolver — effective spawn env is `NIM_PROXY_BYPASS=1`, `NIM_BASE_URL=http://127.0.0.1:25100/v1`, `NIM_MODEL=<probed winner ∈ kimi-k3-nim, gemini-3-flash-preview>`. The string `sovereign/free` appears nowhere in this tree; `:25104` and `:25109` are unreferenced.

| caller | current route | config or hardcoded | owner | rewire action needed |
|---|---|---|---|---|
| `bidder.py` `_run_super_ralph` env injection (bidder.py:535–545) | `NIM_PROXY_BYPASS=1`, `NIM_BASE_URL=http://127.0.0.1:25100/v1`, `NIM_MODEL=<probed winner>` | config | sovereign / oracle-market crew | none |
| super-ralph CLI `resolveProxyConfig` (`src/nimProxy.ts:79–86`) | Non-bypass: `model="free"`, `baseUrl=http://127.0.0.1:25193` | config (env) w/ hardcoded defaults | super-ralph | none — proxy alias, no provider ID |
| super-ralph CLI `proxyEnvOverrides` (`src/nimProxy.ts:96–109`) | Injects `NIM_BASE_URL=http://127.0.0.1:25193/v1`, `NIM_MODEL="free"`, `ANTHROPIC_BASE_URL=http://127.0.0.1:25193` | config | super-ralph | none |
| generated workflow `createClaude` (template `src/cli/index.ts:386`) | `new ClaudeCodeAgent({model: "claude-sonnet-4-6"})` | **hardcoded** | super-ralph | **map only** — wire-dead under the shim (ignores `--model`, sends `NIM_MODEL`); live today only via the shim |
| generated workflow `createCodex` | `new CodexAgent({model: "gpt-5.3-codex"})` | **hardcoded** | super-ralph | **map only** — dead path (`HAS_CODEX=false`) |
| CLI question-gen, bypass branch (`src/cli/index.ts:567–575`) | `model = ANTHROPIC_DEFAULT_OPUS_MODEL \|\| "claude-opus-4-6"` → `$ANTHROPIC_BASE_URL/v1/chat/completions` | config w/ **hardcoded fallback** | super-ralph | **map only** — hardcoded `"claude-opus-4-6"` fallback; live path overrides via env |
| CLI direct-Anthropic last resort (`src/cli/index.ts:~604`) | `model: "claude-opus-4-6"` → `https://api.anthropic.com/v1/messages` | **hardcoded** | super-ralph | **map only** — fires only with no baseUrl + API key |
| claude NIM shim (`claude.nim-shim-real`) | `MODEL = process.env.NIM_MODEL \|\| "openai/gpt-oss-20b"` → `${BASE}/chat/completions` | config w/ hardcoded fallbacks | bridge infra (shim) | none today (NIM_MODEL always set) |
| claude shim wrapper (`/home/toxic/.local/bin/claude`) | sources `/home/toxic/.secrets`; default `NIM_BASE_URL=http://127.0.0.1:25193/v1` | config | bridge infra | none |

Also observed (config, flag for hygiene): `/home/toxic/.secrets` model values are all upstream provider IDs (`NIM_MODEL=moonshotai/kimi-k3`, `ANTHROPIC_DEFAULT_*=nvidia/nemotron-3-*` — documented dead since 09-14) — not herd routes. The bidder resolver already refuses to inherit them.

## Debate-oracle + misc daemon/script callers

| caller | current route | config or hardcoded | owner | rewire action needed |
|---|---|---|---|---|
| `killer-features/debate-oracle/bin/debate-run` | Default router `http://127.0.0.1:25104/v1`, lanes `[(:25100, "beellama/qwen-flash-64k"), (:25100, "beellama/qwen-flash-256k"), (router, "code")]` | **hardcoded** lane list | sovereign / debate-oracle crew | **map only** — lane models hardcoded in the tool; `--lanes` override exists |
| `killer-features/debate-oracle/bin/oracle.py` | Staggered judge race `[("kimi-k3-nim", :25100), ("kimi-k2", :25100)]` | **hardcoded** (route names) | sovereign / debate-oracle crew | **map only** — judge list in code |
| `killer-features/debate-oracle/e2e/llm.py` | `ROUTER=http://127.0.0.1:25104/v1/chat/completions`, `DIRECT=http://127.0.0.1:25100/v1/chat/completions`; `DIRECT_MODEL={"mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m": "toolcall-local/qwen3.5-9b-tool"}` | **hardcoded** | sovereign / debate-oracle crew | none — e2e harness only, not live traffic |
| `ops/openfang-health/provider-race.py` | Candidates `[{:25100, "qwen3.5-9b-tool"}, {:25100, "kimi-auto"}, {:25100, "beellama/exaone-4-0-1-2b-iq4xs"}]` | **hardcoded** candidate list | sovereign/ops | **map only** — selection in code; route names only, no upstream IDs |
| `projects/kodi-fleet/addons/lasso/.../groq_api.py` + `manifold-upstream/.../groq_api.py` | `https://api.groq.com/openai/v1/chat/completions` with caller-supplied `model_id` | **hardcoded direct upstream bypass** (external API, Groq key) | kodi-fleet | **map only** — bypasses all routers; only canonical caller hitting a provider directly |

Research/checker scripts (not live wiring, enumerated for completeness): `projects/model-max/sweep.py` (enumerates herd `/models`, probes liveness — no hardcoded models, clean), `projects/range/ranch/research/check_providers.py` (hardcoded provider/model test lists — research-only), `killer-features/code-racer/strategies/lib/cr.py` (env-configurable URLs, but **no importers anywhere on the estate** — dead lib, excluded).

## TAU callers (engine + extensions + configs)

Config surface — clean, resolving today:

| caller | current route | config or hardcoded | owner | rewire action needed |
|---|---|---|---|---|
| `projects/tau/config/agent-config.yml` — `modelRoles.default/task/smol/advisor` | `sovereign/free` → `http://127.0.0.1:25104/v1`, model id `free` (deployed byte-identical to `~/.tau/agent/config.yml` apart from comment header) | config (YAML) | tau-config crew | none — already on sovereign/free |
| same — `modelRoles.tiny` | `herd/beellama/exaone-4-0-1-2b-iq4xs` → `:25100/v1` local llama-swap | config (YAML) | tau-config crew | none |
| same — `subagents.defaultModel` | `sovereign/free` | config (YAML) | tau-config crew | none |
| `~/.tau/agent/models.yml` sovereign provider | `baseUrl: http://127.0.0.1:25104/v1`, `api: openai-completions`, static models `free`, `ling` | config (YAML) | tau-config crew | none |
| same — herd provider | `baseUrl: http://127.0.0.1:25100/v1`, `api: openai-completions`, `openai-models-list` discovery | config (YAML) | tau-config crew | none |
| `agent-config.yml` `providers.openai-compatible.baseUrl` | `http://127.0.0.1:25100/v1` | config | tau-config crew | none |
| `~/.tau/model-router.json` profiles | quality/reasoning: `sovereign/free`; cheap: `herd/beellama/exaone-4-0-1-2b-iq4xs`; fast: `herd/beellama/qwen-flash-64k`; balanced: `herd/qwen-flash-da-128k`; backup: `herd/gemma-4-12b-unified` | config (JSON; **no engine consumer** — engine resolves via agent config) | tau-config crew | none |
| remote compaction (`agent/src/compaction/openai.ts`) | inherits session model/endpoint | inherits session route | upstream oh-my-pi | none |
| web-search grounding (`web/search/index.ts`, providers/gemini.ts, openrouter.ts) | uses `candidate.model` = session model | inherits session route | upstream oh-my-pi | none |
| provider transports (`ai/src/providers/kimi.ts`, `openai-completions.ts`, `openai-shared.ts`) | baseUrl from config model object; **no sovereign/herd URL hardcoded in engine code** | config-driven | upstream oh-my-pi | none — routers≠model-code respected; `kimi.ts` is a generic adapter |
| flock extension (`extensions/flock/src/flock.ts`) | `DEFAULT_BASE_URL=http://127.0.0.1:8000`, `FLOCK_BASE_URL` override; model = user `--model` passthrough, no default | config w/ hardcoded URL | extensions/flock (sovereign) | none |
| kimi extension (`extensions/kimi/src/kimi.ts`) | shells out to `kimi -p`; default = kimi CLI's own `auto`; `--model <alias>` passthrough | external binary's selection | extensions/kimi (sovereign) | flagged, by design — deliberate Moonshot-CLI wrapper |

Latent hardcoded fallbacks (all upstream oh-my-pi; cannot fire a live call today — only `herd`+`sovereign` providers configured):

| caller | current route | config or hardcoded | owner | rewire action needed |
|---|---|---|---|---|
| `model-resolver.ts` fallback → `engine/packages/coding-agent/src/priority.json` | unconfigured roles pin `openai-codex/gpt-5.6-sol`, `kimi-code/k3`, `anthropic/claude-opus-5`, `gemini-3.8-flash`, `gpt-5.3-codex-spark`, `claude-haiku-4-5`, `typesafe/jev-latest`, … | **hardcoded in code** | upstream oh-my-pi (forked) | **map only** — latent; live roles all configured, providers missing → falls to `availableModels[0]` |
| model cycling (`cycleOrder: smol, default, slow`) | `slow` role NOT configured → `findSlowModel` → priority.json slow list | config 2/3, **hardcoded fallback** for slow | upstream + tau-config | **map only** — least-latent of the batch; `slow` is in cycleOrder |
| image-gen tool (`tools/image-gen.ts:141`) | `HOSTED_CHAT_MODEL_PRIORITY = ["gpt-5.5","gpt-5.4","gpt-5.1","gpt-5","gpt-5-codex"]` | **hardcoded** | upstream oh-my-pi | **map only** — scoped to openai/openai-codex, not live |
| Anthropic server-side fallback (`session/settings-stream-fn.ts:54`) | injects `fallbacks: [{ model: "claude-opus-4-8" }]` when `providers.anthropic.serverSideFallback` = true | **hardcoded**, enabled by config flag | upstream oh-my-pi | **map only** — anthropic provider not configured |
| Perplexity web-search (`web/search/providers/perplexity.ts`) | `PI_PERPLEXITY_API_MODEL` → `sonar-pro`; subscription `PI_PERPLEXITY_MODEL` → `experimental`; anon `turbo` | **hardcoded**, env-overridable | upstream oh-my-pi | **map only** — search tool backend, not agent inference |
| TTS/STT legacy migration (`config/settings.ts`) | `deepinfra/hexgrad/Kokoro-82M`, `local/whisper-*`, `typesafe/jev-latest` | **hardcoded** (migration path only) | upstream oh-my-pi | **map only** — fires only on legacy-setting migration |
| pi-catalog `DEFAULT_MODEL_PER_PROVIDER` (`provider-models/descriptors.ts`) | per-upstream-provider defaults (anthropic, google, groq, …) | **hardcoded** catalog data | upstream oh-my-pi catalog | **map only** — only if those providers were configured (they aren't) |
| `scripts/bench-router-models.ts:32` | `ROUTER_URL = process.env.ROUTER_URL ?? "http://127.0.0.1:25104"` | env w/ hardcoded default | engine repo | none — dev script, not production inference |

TAU hygiene flags (read-only observations, not wiring): (1) `model-router.json` backup is now `herd/gemma-4-12b-unified`, not `herd/pollinations-free/openai`; (2) tree `launcher/profiles/default.yml` says `model: ling` while deployed `~/.tau/profiles/default.yml` says `model: sovereign/free` — tree stale; harmless (engine has zero `TAU_LLM_*` consumers) but the canonical-source header is broken for this file; (3) nothing in the live engine routes via `:25109` (keypool); no `NIM_MODEL` consumers in engine code.

Net TAU verdict: **23 selection points — 15 config-driven and clean** (7 on `sovereign/free`, 5 on `herd/*` local, 3 inheritance paths), **8 hardcoded latent** upstream fallbacks. TAU is clean where it's configured; its doctrine risk lives in `priority.json` + `cycleOrder`'s `slow` role.

## Bake-off verdict gate

**No rewiring happens before the Sovereign-vs-TAU bake-off verdict.** This document is the execution map. The post-verdict execution checklist:

1. `sovereign/bin/kimi-code-setup` — refresh the stale `herd/qwen-flash` default before anyone re-runs it.
2. Super-ralph hardcoded fallbacks (`claude-sonnet-4-6`, `gpt-5.3-codex`, `claude-opus-4-6` ×2, shim `openai/gpt-oss-20b`) — wire the workflow template and bypass branches to a config/env route.
3. `bidder.py` `_resolve_ralph_model` priority list, `debate-run` lanes, `oracle.py` judge race, `provider-race.py` candidates — move selection into router config (aliases).
4. TAU `priority.json` hardcoded lists + `cycleOrder`'s unconfigured `slow` role — configure `slow` explicitly and neutralize the upstream fallbacks (upstream oh-my-pi code; coordinate with the TAU fork).
5. `nim-kimi-sidecar.py` `MODEL_ID` — move into herd config; keep the sidecar a dumb adapter.
6. Kodi `groq_api.py` ×2 — decide whether media-metadata inference stays on a direct Groq bypass or routes through herd.
7. `bench/judge_return.py --mode old` — leave alone (intentional historical baseline).
8. `/home/toxic/.secrets` upstream-ID model values (`nvidia/nemotron-3-*` dead IDs) — hygiene, not wiring.

## Method note

Five parallel read-only sweeps (TAU engine+extensions+configs, super-ralph CLI+shim+bidder env, oracle-market+bidders+judges+debate, kimi+tooling+squawk+cockpit, general scripts/daemons/misc callers) plus a manual backfill of the general slice where the worker's report was thin (debate-oracle, code-racer, openfang-health, Kodi addons). Every finding read from live disk on yote 2026-09-21; nothing was edited, committed, restarted, or rewired as part of this audit. KB §2 row: `wiring-audit` (Ember's crew), DONE with the commit SHA below.
