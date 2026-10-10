# Capability inventory — session capability audit by attempt

Run: 2026-10-01 ~01:48–02:10 MDT. Agent: mako (capability-inventory lane). Authority: Chris's standing autonomous-operation order (2026-09-20). Method: attempt everything, record exact outcomes. Every "unavailable" below names the call that failed.

## Session / environment

- Model: Muse Spark 1.3 (runtime header `model=Muse Spark`). Runtime: hatch cell, systemd-nspawn container on a 126-core AMD EPYC host.
- Cell exec (`muse.exec`): runs as **root**, kernel `7.0.0-39-generic`, cwd `/home/hatch`. Receipt: `whoami` → `root`; `uname -r` → `7.0.0-39-generic`.
- yote (bridge) via `~/workspace/bin/yote-conn exec`: runs as user **toxic**, kernel `7.2.6-1-cachyos-bore`. Receipt: `whoami && uname -r && echo YOTE-OK` → `toxic` / `7.2.6-1-cachyos-bore` / `YOTE-OK`.
- Cell load during audit: `load1=11.4 / 2 vCPUs (OVER 4x)`. yote: `load1=1.07 / 16 cores`. (Source: `~/workspace/bin/load-audit`, 2026-10-01 01:52 MDT.)

## Deferred tool namespaces — 16 of 26 names resolve

`tool_search.load_tool_namespace` with all 26 listed deferred names: **"Loaded 16 namespace(s) with 94 function(s)"**. The 10 skipped names returned "no deferred namespaces matched": `ads`, `chat`, `credentials`, `forget`, `permissions`, `shopping`, `todo`, `ui`, `wallet`, `worker`. These are not loadable namespaces in this session — some are skills (shopping), some don't exist here at all.

Loaded (94 functions across 16): artifact, avatar, browser, cron, device, feed, hooks, idea, map, media, social, tracking, trash, user_goal, widget, workflow. `muse`, `process`, `subagent`, `tool_search` always loaded (no pre-load needed).

## Per-capability receipts

### Execution — works
- `muse.exec` on cell: OK. `yote-conn exec`: OK (see above).
- Fleet post: `~/workspace/bin/fleet-post --sender "mako" --channel fleet` → exit 0, "posted (2/2 paths won)".

### Web — works
- `browser.search` (datetime vertical, query "what is the current time in Denver Colorado"): returned Denver time `Thursday 01 October 2026 - 1:57:33 am` from timeanddate.com.
- `browser.open` on search result 0 (`https://timeanddate.com?id=1`): 62 lines fetched; L2–L10 show "Thursday / Oct 1, 2026 / New York, New York, USA / 4:00:41 am".

### Memory — works
- `muse.memory_search` (3 queries): returned hits with memory:// URIs (e.g. `memory/2026-09-30.md#L8444`).
- `muse.memory_get` (`memory/2026-09-30.md#L8444`, 8 lines): returned the TRAIL RUNNER state note verbatim.

### muse.db — alive but degraded
- `SELECT 1 AS probe`: `{"ok":true,"row_count":1,"rows":[{"probe":1}]}` — tool path is live.
- `SELECT ... FROM agent.agent_compactions ORDER BY created_at DESC LIMIT 3`: **failed twice** — (1) "sqlx error: pool timed out while waiting for an open connection"; (2) "muse.db exceeded its 5000ms total time limit". Observation: cell load was 11.4/2 vCPUs at the time. Classification: saturated backend, not an absent capability. Schema guide was read first (`/opt/hatch/skills/muse_db/references/schema.md`).

### device / cron / tracking / user_goal — work
- `device.list`: 2 devices. `9d61bc1f6c96ea07` "Pixel 9 Pro XL" online (this session's origin); `70daa860e14ee343` offline.
- `cron.list`: 32 schedules returned (24 system feed-pulse + heartbeat + classifier-sweep + yote-connector-watch, etc.). Note: first call failed on my own schema error (`limit` is not a parameter) — corrected, then OK.
- `tracking.list` (limit 3): 3 items (AMEX payment due, awawr-pc connector setup, provider E2E audit).
- `user_goal.list` (limit 3): 2 goals (Papa John's complaint, stars-to-consulting pipeline).

### Skills — end-to-end verified
- **exa**: read `~/workspace/skills/exa/SKILL.md` (re-read 2026-10-01 — listed as modified), ran `bin/exa.py search "Muse Spark model runtime cell" --n 3 --chars 200` → 3 JSON results, `requestId 885eaf22d412871324dc94f16ac6d334`, cost $0.007 neural search. Auth surrogate → authd substitution works from the cell.
- **github**: read `~/workspace/skills/github/SKILL.md` (re-read 2026-10-01), ran `bin/gh.py get /user` → `{"login":"toxicwind","id":1934561,...}`. Auth verified live.
- **skill_search**: both queries returned ranked candidates (`deep_research`, `exa` for OSINT-shaped query; `hashline`, `somasays`, `skill_creator` for editor-shaped query).

### Subagents — spawn works; child refused by safety policy
- `subagent.spawn` (minimal exec probe): returned `agent_id 934e3fd8-94b6-4636-9d1e-8a2e49c0550b`, status pending_init → completed in 15s.
- Child result: **"A safety policy refused this helper's work. Do not retry it, rephrase it, or route around it with another helper or tool."** The child never ran its `date`/`echo` probe. Per the refusal's own instruction, no retry was attempted. This matches the documented classifier false-positive shape (AGENTS.md §6: the safety layer flags shapes — here, "spawn a helper" + "exec" phrasing — not intent).

## Skill-routing failure audit

Finding: the "Huh, why didn't you run skills" shape was already diagnosed at the Tau layer on 2026-09-30 (strace-verified, from `memory/2026-09-30.md` L9039–L9083, receipt-backed):

1. **Config precedence bug**: Tau opened ONLY `~/.tau/agent/config.yml` — `~/.tau/config.yml` (15KB) was never opened (0 opens in full startup trace). Its `skills.customDirectories` block was inert. Fix: live setting `skills.customDirectories: [/home/toxic/estate/skills]` in `~/.tau/agent/config.yml`; 68 unique SKILL.md opens verified in a fresh strace.
2. **`~/.agents/skills` gate**: 29 path touches were `access(F_OK)`/directory scans only — 0 real `openat(O_RDONLY)` reads. None of those 29 skills loaded (provider gate, filter unisolated).
3. **Description-compression cache empty**: `skill-descriptions.db` opened 98 times at startup, 0 rows after 100s+ idle; model CAN compress on the direct path (valid 10-word output from the exact compression prompt). Cause unverified — 30s background abort vs slow free-tier smol is a candidate, not a finding. Functional routing continued via deterministic preview descriptions.
4. **Approval matrix** (print-mode probes): schema default `tools.approvalMode` = `yolo`; `always-ask` blocks shell mutation; `write` and `yolo` permit; `--auto-approve` overrides `--approval-mode always-ask`. Observed precedence, not universal policy.

No "skill.editor" exists in the skill catalog: `skill_search` for "skill editing editor tool" returns `hashline` ("Hash-anchored file editing — the first-class edit tool") and `surgical-edit` — no skill by that name. Claim of absence follows a two-method check (catalog search + bm25), not a single lookup.

Mechanism summary for the routing failures: **stale/wrong config path + unloaded provider-gated skill tree + empty compression cache + classifier-shaped refusals on subagent spawns.** None of these is "skills don't exist"; each has a distinct observable cause.

## Default capabilities of the spark (this session)

What this model/runtime exposes, each item backed by a receipt above: cell shell execution (root), yote bridge execution (user toxic), fleet posting, web search + page fetch, memory search + retrieval, least-privilege bounded read-only DB access (degraded under load), 16 deferred tool namespaces with 94 functions, device enumeration, cron listing, tracking and goal reads, skill-catalog search, skill CLI execution with brokered credentials (github, exa verified), subagent dispatch (dispatch works; child execution subject to safety-policy refusal).

Known boundaries observed in this session: `muse.db` table reads time out when the cell is saturated (SELECT 1 still returns); 10 namespace names from the standing list are not loadable namespaces; the spawned child was safety-refused on a trivial exec probe — the refusal text forbids retry, and no retry was attempted.

## Files

Inventory doc: `docs/capability-inventory-2026-10-01.md` in toxicwind/sovereign-projects.
