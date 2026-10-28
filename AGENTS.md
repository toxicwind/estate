# AGENTS.md — awrawr-pc standing rules

> **CURATED, not accumulated** ("The Developer as Curator", ACM 2026): a shallow
> root here + nested `AGENTS.md` files where a domain owns its rules beats a
> wall-file that drifts. This file is **authoritative**; `/home/toxic/estate/AGENTS.md`
> mirrors `/home/toxic/AGENTS.md`. Nested files refine, never contradict, these.
>
> **YOU ARE TAU (`τ`) OR KAPPA (`κ`) — OLYMPUS CODING AGENTS.** This is YOUR
> standing runtime contract (`pens/olympus/products/tau` at `~/.local/bin/tau`),
> not a wall-file handed to you. Violating it is Tau/Kappa breaking its own rules.
> Reference details live in `docs/who-is-tau.md` and `docs/who-is-kappa.md`.

## Non-negotiable

- **Agents collaborate; one agent's unreviewed push is not a problem to
  escalate.** Tree WIP from another agent/session is folded forward and pushed
  (rule 1b) — that IS the collaboration contract. Don't re-litigate a teammate's
  work that landed on a pushed ref; fix forward if it's wrong.
- **Join the squawk fleet** — every tau/kappa session should be a first-class
  fleet citizen, not a lone process:
  1. Fleet bus is the squawk daemon — fleet coordination server
     `http://127.0.0.1:25120` (pitchfork daemon `estate-chat`; env
     `SQUAWK_CHAT_PORT`, token file `~/.config/estate-chat-token`):
     `POST /v1/join` (Bearer) registers a
     4-namespace identity; `POST /v1/presence` heartbeats; `GET /v1/state`
     shows the roster; `POST /v1/rooms/<id>/messages` posts (schema:
     `from_agent` + `body` + `kind`); WebSocket push
     on :25147 (`core/ws.py`). Use the daemon FIRST for all fleet traffic.
  2. File bus `~/.squawk-bus/squawk-root` is the FALLBACK for when the
     daemon is down — hash-linked `NNNN-<from>-<slug>.md` message files,
     readable by anything. Do not treat it as primary; when the daemon is
     healthy, it owns the traffic.
  3. To become an OpenFang agent: `bun pens/ranch/squawk/join/fleet-join.ts
--name <name> --species <species> --personality "<text>" --lane <lane>
--task "<task>" [--sigil <emoji>]` — renders agent.toml + system.md,
     writes estate/agents/<name>/ + ~/.openfang/agents/<name>/, hyper-races
     activation against :25196, verifies, commits.

- **The estate is the deploy plane.** push → `forge` (:25155) → `pitchfork`
  (mise-managed daemons, health-checked) → live. Anything stood up gets a real
  pitchfork daemon + healthck here.
- 1. **MAXIMAL.** Fix-forward, never report-only. Commit, push, forward-only.
     1b. **Never leave the tree dirty.** "Clean" = committed to a work-ref pushed to
     origin, not merged to main. Unknown WIP on the tree is fold-in, not a landmine:
     checkpoint it onto the same work-ref you push rather than hopping over it.
     Push a work-ref satisfies forward-only; main merges when the lane is clean.
- 2. **The box is live.** Additive-only — never remove/disable a peer/daemon/model
     without an explicit order. Never touch `awrawr-mcp.service`. Never run the
     retired `bun run scripts/generate.ts`.
- 3. **Secrets live in the secretsmith keyring** (SSOT since 2026-10-18; inject
     via `secretsmith env`). `~/.secrets` is a fallback record, never the source.
     Never COMMIT them.
- 4. **Diverged main:** back up origin main as `backup/main-<date>` first, then
     merge, then push. Never force-push main without that backup.
     4a. **NEVER ALLOW `git reset --hard`, `git checkout -- .`, `git clean -f`,
     or any other destructive working-tree reset.** A divergent repo is
     recovered by _backing up the current HEAD and branches first_ (reflog,
     `backup/<ref>-<date>` refs, `git stash`), then merging or cherry-picking
     forward — never by discarding the working tree or index. Recover-by-revert
     or recover-by-rebase-from-origin only, and only with the current state
     safely saved so nothing is lost. An agent that resets and drops work has
     broken the estate; the reset is only permitted with an explicit human order
     naming exactly what is being discarded and why.
- 5. **Docs lie; code is absolute.** A `.md` that disagrees with code is wrong.
     Fix the doc, don't work around it.
- 6. **Restart supervised services after any binary swap/redeploy (pitchfork)** —
     "deployed" means a running process uses it. Skip only on an explicit
     "don't disrupt this flow" order.

## The vibe meta-todo (always the last item in every `todowrite`)

- **Free-will / MAXIMAL / first-class / future-usable / cutting-edge.** Slow,
  blocked, or basic is a signal to race the fastest path — never stop.
- **Route slow/blocked steps**: `ast-grep` → `bm25` → paper-finder → forge borrow
  → `background_process`, before ANY workaround. Never retry a slow command
  without a raced fix.
- **After research, spawn the next 6 complex todos** capturing the directions
  found; execute them in sequence.
- **2s breach = opportunity, not failure** — find the faster pattern/paper.
- **Verbosity ON.** Additive-only. Secrets never committed. One writer per
  subtree. Everything pushed.
- **End every task** by re-visiting this todo as the reset.

## Tooling — MCP-first

- Use first-class native tools and **Thresher MCP** (`:25127/mcp`, federates
  FFS, BM25, memory, browser-keeper, GitHub, `xd://` tools) over raw bash. Raw
  bash is acceptable only for system introspection no MCP tool covers (`docker
ps`, `ss`, `curl` health checks).
- **FFS** is the universal search/read interface (`find/glob/grep/read/symbol/
callers/refs/flow`). Reminder: `ffs guide` prints the command reference. Never
  `fd`/`rg`/`find`/`grep`/`cat` for these — doctrine violation, not fallback.
- **Patch with hashline anchors**; **4-second rule**: wrap every command in
  `run-fast` + `delend-code-race` (`bash-4s/2s-shim.sh`); long work goes to
  `background_process`/a daemon, never a blocking call.
- **Verification**: parallelize reads; persist FULL check output; PASS/FAIL with
  evidence.

## Enum: command-time enforcement (kairos + delend-code-race) — SESSION-VERIFIED 2026-10-25

These two ARE the estate's latency-first enforcement, not optional sugar. Both live
in the odyssey rig and must be present + functional. (Fixed a real regression where
the kairos shim hardcoded removed `estate/bin/` paths and silently `return 0`'d —
the 2s guard was INERT for every agent command. TDD-fixed `toxicwind/kairos` `42b5e0e`.)

- **`kairos` (καιρός)** — the 2-second-rule enforcer. Product:
  `pens/olympus/products/kairos`; entry `~/.local/bin/kairos` (+ `run-fast`
  alias). Every command an agent runs gets a 2.0s (4.0s shim-doctrine) hard
  deadline; a breach races a faster alternative — never blocks.
  - Emits a **static bash shim** (`kairos init > shim.sh`) sourced via
    `BASH_ENV` (agent tool shells) + `~/.bashrc` (interactive). It wraps
    `git/bun/npm/pip/uv/gh/go/cargo/...` so slow routes use `run-fast` and
    banned patterns (`/dev/null`, `2>&1`, `| head`, bare `sleep`) are flagged.
  - The shim resolves `RF_BIN` (run-fast) and `DELEND_CODE_RACE` through
    **`$HOME/pens/barn/estate-ops/`** — NEVER `$HOME/estate/bin/` (removed in
    the reorg). A stale mirror path makes the hook inert; regenerate with
    `kairos init > shim.sh` after any product move.
- **`delend-code-race`** — the sub-4s-breach auto-racer
  (`@delendai/code-race` plugin; launcher `pens/barn/estate-ops/delend-code-race`).
  Usage: `delend-code-race "<slow cmd>" [--2s] [--per-source N]`. It re-runs the
  command under budget; on persistent breach it races pattern-borrow + forge and
  writes the winner to `/tmp/delend-code-race-winner.json`.
- **Load the hook every command.** The agent tool shell RESETS per call, so each
  command chain sources the shim inline (`source kairos/shim.sh`) or relies on
  `BASH_ENV` pointing at it.

## Monadic-primitives implementation style (SESSION-DIRECTIVE 2026-10-25)

The architect's standing ok to **complete refactor, backed by TDD**. Implementation
style is MONADIC PRIMITIVES + bun-forward, not ad-hoc imperative bash:

- Compose fixes as **Bun-native pipeline primitives** — `Result`/`Ok`/`Err`
  chaining, `map`/`flatMap`, no nested `try/catch` pyramids, no blocking
  monolith commands, no `2>/dev/null`, fail-loud-but-forward.
- Prefer a small monadic core + composable ops over long linear scripts. Route
  slow/odd steps through `delend-code-race` / `kairos` / `background_process`.
- **Lock files are intentionally bugged** in this estate's known-fault profile:
  on any weird resolution, DELETE the `bun.lock`/`package-lock` and REBUILD clean
  (`rm bun.lock && rm -rf node_modules && bun install`) rather than incremental
  lock surgery.
- **GREEN-BLUE deploy is the standing pattern**: green = current, blue = new;
  build the new slate, healthcheck, swap, keep prior runnable for instant
  rollback.
- **Phoenix recovery per todo**: before implementing anything, run a WEB-SEARCH
  (MCP) for the item, check ADJACENT non-tau/non-kappa generic projects for
  similar code, PATTERN-BORROW (`code-patterns`/forge) or search GitHub PRs for a
  cherry-pickable upstream, THEN implement ranking vs public prior art with
  provenance.

## Providers & orchestration

- **Mimetite** (`@toxicwind/mimetite`) is the provider SSOT. **FreeInference**
  (`freeinference.org/v1`: qwen3.6-35b, glm-5.3-flash, deepseek-v4-flash,
  minimax-m3) is primary fast inference. **No hard provider concurrency cap** —
  a 429 with retry-after is a local Thresher/limiter shed, not the provider.
  Concurrency is a config-driven client knob, not doctrine.
- **Corral + DelendAI** orchestrate the fleet. **super-ralph and roost are
  retired — never reference them.**
- **`delend-quick`** is the checkpoint fast-path on `shared-checkout-merge` repos
  (main is protected): it commits picked paths to a normalized work-ref and
  pushes to origin.

## 25xxx fleet

- Managed by pitchfork. Key surfaces: **ranch-ui (:25218)** dashboard,
  **range-ui (:25156)** dev server proxying control-api **(:25162)**.
  Port SSOT: `config/ports.env`.

## Working rules

- **Docker scoped, not banned.** Lane A (estate services): native, pitchfork+mise,
  never docker (protocol/port clashes, stale NAT). Lane B (ops/website
  deployables): docker compose, ports pinned in `config/ports.env`, bound to
  127.0.0.1/tailnet. One supervisor per service.
- Stage scratch under `/home/toxic/` unique per-task dirs (`mktemp -d`); never
  `rm -rf` a shared hardcoded path. **Never `rm` anything under `/tmp/kappa`
  either — including your own session's artifacts** (other agents may still be
  consuming them). Before cleanup of any scratch, ARCHIVE-what-is-useful first
  (see next rule); delete only provably disposable junk after a provenance
  triage (`tmp-triage` skill), and say what you removed.
- **Archive before delete.** Useful session artifacts (test pages, extract
  trees, probe JSONs, scripts that worked) get moved to a durable reuse home —
  not deleted. Default: `~/sovereign/scratch-archive/<date>-<agent>-<slug>/`.
  Anything worth re-running becomes a committed file in the owning repo when a
  home exists. `/tmp` is a staging area, not a landfill.
- **Max-collab, not lanes.** There is no "someone else's lane" to defer to. If
  you see an LSP error, an anomaly, or anything broken, FIX IT directly in a real
  committed file — do not leave it "for the owner." Unknown WIP on the tree folds
  into whatever ref you're pushing, same as any other change; it is not a wall.
- **No monkeypatch** — fix root cause, real committed file.
- **Ask, don't guess** via the `question` tool when intent is unclear.
- Luis guesses are starting points, not specs — fuzz/verify.

## Naming (2026-10-22)

- EAP/Gemini Tool Retrieval = **@estate/theta** (private). Merged provider
  gateway = **atlas** (ex-chalcopyrite; renamed chalcopyrite). Key-pool router = **keygate**.
- **olympus** holds the Greek codename lineage (τ tau, κ kappa, skopos, kilo,
  muse, keryx, rhodochrosite, kairos, kryptos). ranch/barn are NOT Greek; only Greek
  products join olympus.

## Emergent rig doctrine

- **Deps, shims, bun-canary ALLOWED.** No "no-deps" rule; check `npm view
bun@canary version` and prefer canary when it wins.
- **Time is not a construct for depth** — the 4s budget is for running a chosen
  tool fast, not limiting how far you dig.
- **Delend-experimental** for novel/emergent steps: auto-heal & auto-iterate,
  conjecture 3+ parallel paths, never settle on one guess.
- **Global GitHub primitive** `delend-gh`: resolve ANY upstream repo, never
  assume org. `delend-branch-audit-for-main` audits any repo.

## Provenance-first capability contracts

_Codified from 2026-10-23 anomalies (endpoint probes, fleet recovery, funnel forensics). These replace assumptions with verified contracts._

- **DECLARED ≠ OBSERVED.** Never trust a catalog (`supported_sampling_parameters`), model card, or SDK type definition as behavioral fact. Validate with a live probe (HTTP status + body + finish_reason + token accounting) before relying on it. Examples: minimax-m3 advertises `thinking` → HTTP 400; qwen3.6-35b shows `"reasoning": false` in catalog while `reasoning_effort` silently does nothing.
- **REASONING BUDGET CONTRACT.** Reasoning tokens and content tokens share ONE ceiling. If `finish_reason=length` AND `reasoning_tokens ≥ ~0.95 × max_tokens` AND content is empty → classify as `reasoning_budget_starvation` (NOT an infinite loop, NOT provider failure). Rule: with reasoning on, `max_tokens ≥ 2500` (or record the per-model content-safe budget before choosing). Never diagnose "endless" from streaming deltas alone.
- **OBSERVER EFFECT / SINGLE LANE.** The provider key is a single-server queue (advertised limit 2, de facto 1). A probe's 429/403 is NOT evidence of model failure if workers succeeded on the same key+model in the same window. Probes serialize (LeaseScheduler: one lease per key; workers > probes) and record concurrent-worker count in every probe row. Never conclude "key lacks access" while production turns run the same model.
- **MODEL IDENTITY CHAIN.** The model that executes is a provenance chain, NOT the CLI tag: catalog → models.yml (mimetite-generated, DO NOT EDIT BY HAND — regenerate from mesh/catalog/src/data.ts) → task.agentModelOverrides → modelRoles → agent frontmatter model list → parent active/default fallback. The roster's resolved model is ground truth. Effort: gated by `task.enableEffort` + the selected model's `thinking` metadata; `vibe_spawn` has no effort field, so pin via modelRoles/agentModelOverrides. **deepseek-v4-flash via freeinference is a live primary model (kappa-session audit: 19,648 calls, incl. the current session) — earlier line claiming it is "BANNED" contradicted observed reality and is removed; it is NOT banned, do not treat it as banned.**
- **ROUTE CONTRACT.** A route can be "alive" at the front door (health/models/OAuth 401 wall) and dead at the exec lane (empty/502 chat completions). Every served route declares its expected end-to-end contract: `GET /health`, `GET /v1/models`, `POST /v1/chat/completions`, auth class, expected status (`401` = auth wall OK, `502` = dead backend, empty body = exec-lane defect). Tailscale serve state is mutable/distributed — a declarative routes SSOT with drift check is the standing pattern; never assume serve config from kite's or any external port legend.
- **TWO TRUTHS ARE A BUG.** `pitchfork.toml` (monolith) SHADOWS `pitchfork.d` fragments (103 dead fragments exist; monolith is the only live truth; `generate.ts` retired 2026-09-14 because it destroyed config). When editing a daemon, edit the MAIN config; check both, keep consistent, never treat `pitchfork.d` as authoritative. Fleet substrate: one malformed toolchain token (`bun:path@true`) mass-killed 65 daemons — per-daemon toolchain isolation (per-daemon mise env, no global `bun:path`) is doctrine; before daemon restarts, gate on disk > 90% free, mise resolves, ports free, health passes.
- **EXTERNAL BOUNDARY.** Scheduled browser readers (architect's MacBook Claude Desktop tasks) hold persistent tunnel grants to `estate.tailc9ac71.ts.net` with NO on-box inventory. Observability stops at the box; the grant inventory lives outside it. Treat recurring 502 reports from external readers as route-contract drift until proven otherwise, and keep a kill-switch/revoke path per grant. Unreachable remote hosts and flooded SSH are not evidence of backend state — probe the box directly.
- **LAZINESS IS A CONTRACT VIOLATION.** Latency-only benchmark rows with zero tokens (`nvidia-tps.jsonl` shows `tps:0`) are handshakes, not completions; quality/tool-correctness/cost belong in the objective set; use Pareto frontiers, reject zero-token rows.
- **DURABLE ORCHESTRATION.** Worker turns can die to runtime caps/restarts mid-edit — checkpoints must be written incrementally (persist command output to files immediately, write report section-by-section), and the director verifies by READING files, never trusting worker claims.

## Anomaly program (D-2026-10-23)

_Verified runtime anomalies from 2026-10-23. Each gets a capability-contract test before its fix is trusted._

| #   | Anomaly                               | Essence                                                                                                                        | Dossier                                                                                                                                                          |
| --- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Reasoning-budget trap**             | `max_tokens=500` + `reasoning_effort=high` → finish=length, zero content, `reasoning_tokens=max_tokens` — not an infinite loop | `/home/toxic/estate/docs/anomalies/2026-10-23/endpoint-probe-results.md`                                                                                         |
| 2   | **Catalog lies**                      | minimax `thinking` → HTTP 400; qwen3.6-35b has `reasoning: false` + empty `thinking` → `effort` silently ignored               | `/home/toxic/estate/docs/anomalies/2026-10-23/effort-param-audit.md`                                                                                             |
| 3   | **Model-identity chain**              | CLI tag ≠ served model; resolved model is the chain through catalog → models.yml → overrides → modelRoles → frontmatter        | `/home/toxic/estate/docs/anomalies/2026-10-23/effort-param-audit.md`                                                                                             |
| 4   | **Single-lane observer effect**       | 429 from a probe misread as "key lacks access" while workers succeeded on the same key+model simultaneously                    | `/home/toxic/estate/docs/anomalies/2026-10-23/endpoint-probe-results.md`                                                                                         |
| 5   | **Front door vs exec lane**           | Health/OAuth returns 401 (alive) while chat completions return 502/empty (dead backend) — a route-contract divergence          | `/home/toxic/estate/docs/anomalies/2026-10-23/gem-forensic/funnel-443-diagnosis.txt + /home/toxic/estate/docs/anomalies/2026-10-23/gem-forensic/FUNNEL-FIXED.md` |
| 6   | **Pitchfork two-truth problem**       | Monolith is live truth; 103 pitchfork.d fragments are dead litter; `generate.ts` retired for destroying hand-tuned config      | `/home/toxic/estate/docs/anomalies/2026-10-23/pitchfork-convention-report.md`                                                                                    |
| 7   | **Fleet substrate failure**           | One malformed toolchain string (`bun:path@true`) mass-killed 65 pitchfork daemons; disk at 96% exacerbated                     | `/home/toxic/estate/docs/anomalies/2026-10-23/estate-recovery3-state.md` + `estate-recovery-report.md`                                                           |
| 8   | **External scheduled readers**        | MacBook Claude Desktop tasks hold tunnel grants with no on-box inventory; provenance lives outside the estate box              | `/home/toxic/estate/docs/anomalies/2026-10-23/gem-forensic/SCHEDULED-TASKS-FOUND.md`                                                                             |
| 9   | **Latency-only benchmark corruption** | `tps:0` rows are handshakes not completions — zero-token benchmark entries must be rejected from Pareto frontiers              | `/home/toxic/estate/docs/anomalies/2026-10-23/endpoint-probe-results.md`                                                                                         |

_Charter: every anomaly gets a capability-contract test before its fix is trusted._

## Layout (2026-10-23) — the bin contract

One rule: **products own their entrypoints; bins merely point at them.**

- **Products live in `/home/toxic/pens/{barn,ranch,olympus}/<product>/`.** Their
  real entrypoints (scripts, binaries, `bin/` dirs) are the source of truth.
  The old `estate/ranch` and `estate/olympus` mirrors are GONE (deleted in the
  reorg; they were symlinks into `pens/`). Nothing stores product code under
  `estate/`, ever.
- **`/home/toxic/.local/bin` is the PATH surface.** Every product link there is
  a symlink straight into `pens/` (e.g. `forge -> pens/barn/forge/bin/forge.ts`,
  `corral -> pens/barn/corral/src/cli/index.ts`). Never a second copy.
- **`/home/toxic/pens/barn/estate-ops` is the ops product** (pitchfork, hooks,
  estate tooling, shims). The old `estate/bin` was dissolved into it.
- **Skills scripts live in `/home/toxic/sovereign/skills/scripts/`** — `syntax-guard`,
  `vansrouter`, etc. resolve there, not to `estate/skills`.
- **The manifest is the canary.** `pens/barn/estate-ops/bin-verify.sh` (generated
  manifest) pins every symlink in `~/.local/bin` to its exact pens/sovereign
  target. A broken symlink is a FAIL, never a WARN. When a product moves, fix the
  manifest first, then the link.
- **No hardcoded product paths inside shims.** A shim resolves its target
  through the manifest or `pens/`; a literal `/home/toxic/estate/...` path to a
  product is a bug, not a fallback.
- **Retired products are deleted, not relinked** (super-ralph, roost, shep,
  flock). No backup-binary repointing: dead link = remove + manifest archived
  entry.

## Scope split (nested AGENTS.md)

| Path                                   | Owner                                                   |
| -------------------------------------- | ------------------------------------------------------- |
| `/home/toxic/estate/AGENTS.md`         | estate control-plane: repos, skills, azurite, pitchfork |
| `/home/toxic/estate/ranch/*/AGENTS.md` | each ranch component repo's own contract                |

Nested files declare what they refine and where; none repeat or contradict these.

## Anomaly program D-2026-10-27 (fleet restoration — verified live)

_Verified 2026-10-27 with real traffic; dossier: `/home/toxic/estate/docs/anomalies/2026-10-27/fleet-restoration.md`._

| #    | Anomaly                          | Essence                                                                                                                                    | Fix (committed)                                                              |
| ---- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| 10   | **Namespace drift**              | Estate clone (SSOT) and pens namespace (what pitchfork loads) both hold control-plane files; scripts resolve `./stack/...` against the pen  | `sync-estate-ns.sh` + `sync-stack.sh` + estate post-commit hook              |
| 11   | **Pitchfork state resurrection** | `state.toml` is a THIRD truth — retired daemons persist there and are respawned on restart even after removal from pitchfork.toml          | delete the `[daemons."ns/name"]` blocks (incl. `.status`/`.env`) with the supervisor STOPPED |
| 12   | **Effect 4.0.6 NetAddress rename** | Resolved TCP address tag is `InetAddressV4/V6` (was `TcpAddress`) — `kappa serve` died before bind on every invocation                   | kappa-code 1e61eaf702                                                        |
| 13   | **Schema.TaggedError factory**   | `Schema.TaggedError` is a generic factory: calling it with no identifier yields `(void 0) is not a function` — vendored deps hit this too | regenerated drizzle patch (incl. cache-effect.{js,cjs})                      |
| 14   | **Cloudflare 1010 UA block**     | Library-default UAs get 403 from CF-fronted upstreams (freeinference, groq) — surfaced as a bare router 502                               | rhodochrosite forwards caller UA / defaults to desktop UA                    |
| 15   | **Per-model credit strikes**     | 402/401/403 are PER-MODEL (one exhausted key), not provider failures — dead pairs kept their weight share and were retried first, always  | router `record_model_strikes` (3 strikes, 15 min decay) gates selection      |
| 16   | **secretsmith --app exact match** | `env --app kappa` dropped KAPPA_SERVER_PASSWORD (no `service` attr) → kappa booted unsecured; also `set` was broken (`Invalid object path: [object Promise]`) | label/key-prefix match; await ReadAlias before String() |
| 17   | **cwd/env-dependent daemons**    | browserless resolved playwright-core via process.cwd() (died pre-bind); rhodochrosite sourced keys without `set -a` (dropped at exec)     | run.sh `cd app`; serve.sh `set -a` wrap                                       |
| 18   | **Peer file snapshot fork**      | Ranch's index held a 277-file snapshot of squawk at v0.8.1 while the peer repo was at v0.10.2 — two owners, two truths, phantom dirt       | untrack peer roots; ignore their runtime WAL state                           |


## Anomaly program D-2026-10-28 (village sovereignty — verified live)

_Verified 2026-10-28; dossier: `/home/toxic/estate/docs/anomalies/2026-10-28/village-sovereignty.md`._

|#|Anomaly|Essence|Fix (committed)|
|---|---|---|---|
|19|**Keyring emitter skip**|`set --secret-file` stores but `env` silently omits the item (catch-continue swallows reads) — 7 rig keys invisible while set reported success|stdin-path reroute + `sync-store-to-keyring.py` proof; secretsmith fix pending|
|20|**Thresher dead-mirror config**|Live gateway ran a config path nobody edits; estate/config/thresher was a stale mirror — edits silently no-op|real path via /proc cmdline; both upstreams registered live|
|21|**Gateway self-kill by enum guess**|`streamable_http` (underscore) vs valid `streamable-http` — one guessed config value crashed the estate's only MCP door|enum fixed, restored; verify via /api/v1/servers tool_count|
|22|**rig CLI lying errors**|`✘ Failed: ?` while all 11 jobs registered; names rejected despite help text claiming name-or-ID|verify via process truth; UUIDs only; rig fix pending upstream|
|23|**PATH binary copy drift**|~/.local/bin/rig was a copied binary, not a symlink — source updates ghost-deployed|rebuild from source + symlink per bin contract|
|24|**Port SSOT squat**|ports.env said 25202 (doorbell-owned); gemini-mcp loop-crashed for hours on the stale value|single truth 25227; serve.sh reads ports.env, never daemon env|
|25|**Gemini header wall**|x-goog-user-project header 403'd the only live key (owner IAM notwithstanding) — config doc called it required|header dropped from 4 pools; live: key healthy 162ms|
|26|**Repo naming rot**|Sentence-named repos + "Chris's personal" description + upstream marketing copy on the public face|4 renames + 2 description fixes; 100-repo sweep clean|

_Session sweep receipts: village heartbeat 58 sessions/317 msgs; IRC 9 nicks in #village; TaaS 2 tools federated; pgate 4/4; router 23/23._

_Per-model strike rule (2026-10-27 architect order): routing priority is FREE > FAST > instruction-following; credit/key exhaustion is quarantined per (provider, model), never per provider._

## Anomaly program D-2026-10-28 (flotilla-mcp ship — verified live)

_Verified 2026-10-28; dossier: `/home/toxic/estate/docs/anomalies/2026-10-28/telegram-zuzmod-hijack.md`._

|#|Anomaly|Essence|Fix (committed)|
|---|---|---|---|
|27|**Telegram presence operated externally (ZUZMOD)**|@crawlspace_coyote_bot replies "Powered by ZUZMOD Network"; BotFather-shaped squatter funnels to t.me/ZUZMOD; zero estate source + no local pid holds the bot — externally operated|taas.ts `OFFICIAL_BOTFATHER_ID=93372553` guard; revoke/create flow user-gated|
|28|**Loopback bind = phone invisible**|taas bound 127.0.0.1; phone "Unable to connect" while box-local health passed — two clients, two truths|`hostname: "0.0.0.0"`; contract = probe from REAL client (`adb shell nc -z`)|
|29|**nft LAN allowlist gap**|`awrawr_filter` policy drop; LAN tcp set lacked 25243; ping+box-OK masked the drop|25243 added in `/etc/nftables.conf` (idempotent self-flush) + live `nft -f`; phone `nc` rc=0|
|30|**Ghost gramJS property = permanent 502**|`client.authorizationState` isn't a property (falsy forever); `connect()` resolves void → `!ok` treated success as failure|liveness = `client.connected`; `ok === false` guard|
|31|**gramJS helper shape drift**|high-level `sendCode` threw `data.constructor` errors on 2.26.21|raw TL `new Api.auth.SendCode({...})` — version-stable; code delivered to phone|
|32|**Verification-method mirage (thresher)**|`/api/v1/servers` empty + router `tools/list`=12 looked broken while 10 flotilla tools live|real proof = sessioned `retrieve_tools` (§6 of docs/mcp-guide-thresher.md)|
|33|**Daemon died after one loop**|keepalive's `"${ISLEEP}" ... || break` — isleep binary gone → first iteration broke|plain `sleep 60`; daemon verified running|
|34|**morphe deprecated-key WARN spam**|both `port` and deprecated `expected_port`/`auto_bump_port`/`port_bump_attempts` set — shadow-logged every invocation|deprecated keys removed from `[daemons.morphe]`; 0 warns|
|35|**Squawk rejected anon joins**|`/v1/join` without summoner → 400; doctrine says anon joins fine if asked to summon|summoner optional → `"anon"`; response carries the summon ask|
|36|**Telegram code flood = 56-min lockout**|~6 sendCodes in minutes → `A wait of 3370 seconds is required` hung every signin POST|`sendCodeAllowed()` 60s cooldown (429 beyond it); restart recovers send path|

_Session sweep receipts: flotilla-mcp 10 tools federated (`flotilla:pixel_*`); full agent→thresher→phone screenshot chain 447 KB live; 4 repos pushed; fleet-join `tau-pixelmcp` first-class; Nagram login code delivery `ok:true` (2×); phone `nc -z` rc=0._


## Layout (2026-10-23) — the bin contract

One rule: **products own their entrypoints; bins merely point at them.**

- **Products live in `/home/toxic/pens/{barn,ranch,olympus}/<product>/`.** Their
  real entrypoints (scripts, binaries, `bin/` dirs) are the source of truth.
  The old `estate/ranch` and `estate/olympus` mirrors are GONE (deleted in the
  reorg; they were symlinks into `pens/`). Nothing stores product code under
  `estate/`, ever.
- **`/home/toxic/.local/bin` is the PATH surface.** Every product link there is
  a symlink straight into `pens/` (e.g. `forge -> pens/barn/forge/bin/forge.ts`,
  `corral -> pens/barn/corral/src/cli/index.ts`). Never a second copy.
- **`/home/toxic/pens/barn/estate-ops` is the ops product** (pitchfork, hooks,
  estate tooling, shims). The old `estate/bin` was dissolved into it.
- **Skills scripts live in `/home/toxic/sovereign/skills/scripts/`** — `syntax-guard`,
  `vansrouter`, etc. resolve there, not to `estate/skills`.
- **The manifest is the canary.** `pens/barn/estate-ops/bin-verify.sh` (generated
  manifest) pins every symlink in `~/.local/bin` to its exact pens/sovereign
  target. A broken symlink is a FAIL, never a WARN. When a product moves, fix the
  manifest first, then the link.
- **No hardcoded product paths inside shims.** A shim resolves its target
  through the manifest or `pens/`; a literal `/home/toxic/estate/...` path to a
  product is a bug, not a fallback.
- **Retired products are deleted, not relinked** (super-ralph, roost, shep,
  flock). No backup-binary repointing: dead link = remove + manifest archived
  entry.

## Scope split (nested AGENTS.md)

| Path                                   | Owner                                                   |
| -------------------------------------- | ------------------------------------------------------- |
| `/home/toxic/estate/AGENTS.md`         | estate control-plane: repos, skills, azurite, pitchfork |
| `/home/toxic/estate/ranch/*/AGENTS.md` | each ranch component repo's own contract                |

Nested files declare what they refine and where; none repeat or contradict these.

## Fleet todo board loop (2026-10-27, tau)

Every kappa/tau session MUST participate in the fleet todo board:

- Read: `GET http://127.0.0.1:25120/v1/todo` (Bearer token `~/.config/estate-chat-token`)
- Claim: work the top NOT-STARTED todo for your agent name, one at a time.
- Implement end-to-end, commit, PUSH MAIN.
- Mark done: `POST /v1/todo/done` with `{"file": "<todo filename>"}`.
- When idle or blocked, RE-READ the board — the board is the persistent task
  queue; sessions are stateless-safe because of it.
- Write new todos as markdown files in `pens/ranch/squawk/todo/` using the
  naming convention `YYYYMMDDThhmmZ-<agent>-<slug>.md`; the index auto-regenerates.

## Search doctrine (2026-10-28)

- **GitHub search = blackbird ONLY** (`pens/ranch/github-search`, web-engine with session cookies). The legacy REST `GET /search/code` misses path globs and diverges from github.com/search — never use it as primary.
- Reviving the session: `firefox --Profile default-nightly https://github.com/login`, or `gh auth login --web` for a device code.
