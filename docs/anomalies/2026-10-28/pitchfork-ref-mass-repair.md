# D-2026-10-28: pitchfork moved-folder mass ref repair + yote TaaS bring-up (tau)

All items verified with live probes / real traffic this session.
Charter: every anomaly gets a capability-contract test before its fix is trusted.

Trigger: goal item 11.1.2 (verify yote bot joins estate chat + handles inbound
commands autonomously). `pitchfork status` showed `estate/yote available`
(registered, never startable) — pulling that thread exposed that the
estate→pens clean-arch reorg never swept the pitchfork monolith's `dir`/`run`
refs. A full sweep found **9 more daemons with dead refs** (6 moved, 3 corpses).
Architect order: mass-fix the bad folder names at the ref — **no symlink
restoration**. Commit: estate `5e90a7eeee` (branch `wip/kappa/estate-cutover-20261027`).

| # | Anomaly | Symptom (exact strings) | Root cause | Fix | Contract test (live) |
|---|---|---|---|---|---|
| 41 | **yote daemon dir stale after reorg** | `pitchfork start estate/yote` → `✗ failed: unexpected response from supervisor: expected DaemonStart or DaemonReady, got Error("No such file or directory (os error 2)")`; `estate/ranch/yote` contained only a `.git` remnant | Clean-arch reorg deleted `estate/ranch/*` mirrors; monolith kept `dir = "ranch/yote"` which resolves relative to the estate clone → pre-spawn ENOENT on every start | `dir = "/home/toxic/pens/ranch/yote"` (estate `5e90a7eeee`) | start exit 0; `GET :25102/health` → 200 `{"ok":true,...pollCursor, dlqDepth:0}` |
| 42 | **estate SSOT edit invisible to running supervisor** | After editing `/home/toxic/estate/pitchfork.toml`, start STILL failed; supervisor log: `spawning daemon estate/yote with mise ["x","--","sh","-c","exec bun run src/yote.ts"]` — the OLD command | Supervisor loads `pens/estate/pitchfork.toml` (`namespaces.estate dir=/home/toxic/pens/estate` in `~/.config/pitchfork/config.toml`), a SECOND truth; clone edits propagate only via `sync-estate-ns.sh` (anomaly #10 mechanism regressed on this commit path) | Ran `pens/barn/estate-ops/bin/sync-estate-ns.sh` (exit 0: pitchfork.toml + stack/ + ports.env + thresher) | Supervisor log shows new spawn (absolute bun, no mise); `pitchfork status` → `estate/yote running` |
| 43 | **`mise = true` pre-spawn kill on non-activated dir** | `cd pens/ranch/yote && mise which bun` → `mise ERROR bun is a mise bin however it is not currently active. Use 'mise use' to activate it in this directory.`; with `mise = true` pitchfork wraps `mise x -- sh -c …` → exit 2 pre-spawn, surfacing as the same ENOENT | `mise = true` assumes the daemon dir activates its toolchain; yote's bun comes from `~/.bun`, dir has no mise activation | Dropped `mise = true` from `[daemons.yote]`; run made absolute: `exec /home/toxic/.bun/bin/bun run src/yote.ts` | Manual spawn reached yote's own port-ownership guard (proof the binary runs); then pitchfork-managed start healthy |
| 44 | **Stale Telegram webhook permanently blocks poll loop** | Every 3.6s since 10-27: `poll tg: Conflict: can't use getUpdates method while webhook is active; use deleteWebhook to delete the webhook first` | An earlier experiment set a webhook on the yote bot token; Bot API forbids `getUpdates` while a webhook exists, and it survives restarts | `POST /bot<token>/deleteWebhook` → 200 `Webhook was deleted`; `getWebhookInfo` → url "(none)", pending 0 | Conflict lines ceased; `POST :25102/test/e2e` → 200 `{"ok":true,"sent":"…","chatId":716302190,"agent":"coyote","via":"openfang-http"}` — full inbound-command round-trip |
| 45 | **Monolith mass stale refs (9 daemons)** | Sweep flagged MISSING targets: bedrock-ui, boundless, delendai-web, kimi-audit-dash, kimi-code, market-loop, forever-loop, refusal-watchdog, sorry-watchdog | estate→pens reorg + archive moves never swept `[daemons.*] dir/run/ready_cmd`; 6 pointed at moved homes, 3 at products deleted outright (corpses) | 6 re-pointed to verified live homes (Boundless repo, estate-projects weaver, archive/detached-2026 kimi-token-audit, src/local/kimi-code + estate-ops claim-port, archive/home-dirs-2026 refusal-hunt ×2); 3 corpses parked `auto=[]`/`boot_start=false` with CORPSE provenance comments (no target exists anywhere on disk — ffs-swept) | `pitchfork list` parses clean post-edit; every new target verified on disk (ls/ffs) BEFORE the edit landed; estate commit pushed `5e90a7eeee` |
| 46 | **Self-inflicted evidence laundering: swallowed stderr → false "no hits"** | Two consecutive `ffs find` sweeps printed `(no hits)` for EVERY needle — including a sanity needle (`yote`) that must match | Invalid CLI flags (`--max-results` instead of `--limit`, then `-i`/`--mode` where unsupported) + stderr discarded + output sliced: tool errors were laundered into a "no hits" conclusion (twice) | Protocol change: persist RAW combined output to a file and read it back verbatim before concluding (`/tmp/ffs-raw-sweep.txt`, 11,538 bytes) | Raw re-run produced real hit lists; every moved-product home located and disk-verified from that raw evidence |
| 47 | **Fleet todo done-endpoint doc lies** | `POST /v1/todo/done` `{"file": …}` → 404 `{"ok":false,"error":"not found"}` — endpoint shape as documented in AGENTS.md fleet-todo-loop | Daemon implements `POST /v1/todo/<file>/done` (path param, no body); doc drifted from code | Used path-param endpoint → 200; fixed the AGENTS.md doc line (rule 5: docs lie, code is absolute) | Board re-read shows yote todo `status: DONE` |

**Known gap (honest):** `kimi-code` ref now points at the right monorepo
(`/home/toxic/src/local/kimi-code`) but `apps/kimi-code/dist/main.mjs` was
never built there — first `pitchfork start estate/kimi-code` needs the
monorepo build (kicked off at retrospective time, pid 819944).

**New capability, not an anomaly:** yote + coyote joined the squawk fleet as
first-class citizens (`POST /v1/join` receipts 200, presence heartbeats live);
taas MCP surface (`telegram_newbot`, `telegram_status`) verified on :25243.
