# Estate Polling Audit — 2026-09-21

**Auditor:** Shrew 🐭 (Ember's crew) — hatch side; Mole 🦔 (Ember's crew) — yote daemon side
**Directive:** Chris — "I think you should audit polling for example scheduler"
**Doctrine:** event-driven, never timers. No artificial sleeps, no timeouts-as-delays,
no daemon that wakes on a timer to recompute the world.
**Method:** read every line of every suspect file; verified timers fire via code-path
reads + `ps`/`ss`. Nothing was committed or restarted during the audit (read-only).

## Summary counts

| Bucket | Hatch | Yote | Total |
|---|---|---|---|
| CONVERT (event alternative exists) | 2 | 5 | **7** |
| LEGIT (timer genuinely needed) | 9 | 8 | **17** |
| Already event-driven (no action) | 1 | 9 | **10** |
| Dormant / disabled | 3 | 0 | **3** |
| Ambiguous (needs tiebreaker) | 0 | 2 | **2** |

No runaway poll loop was found. Every suspect idled at 0.0% CPU — nothing was
burning, so no emergency fleet alert was raised. The payoffs here are latency
(paper-poller), idle-box quiet (stash-guard), and doctrine (the rest).

---

## HATCH — crons (the scheduler Chris named)

All six cron definitions live under `~/workspace/goals/*/crons/minutely/`.

### 🔴 CONVERT

1. **squawk-monitor — every 5m — ENABLED**
   (`goals/awawr-pc-connector-setup/crons/minutely/squawk-monitor__interval@5m.md`)
   Polls the fleet channel via `~/workspace/bin/squawk read fleet --n 5`, which
   shells out to `ls` the message files on yote through the bridge, then diffs
   against `/home/hatch/.cache/squawk-last-seen`.
   **Replacement:** the feed already supports `/subscribe` and the WS lane
   pushes — subscribe once, wake on message arrival instead of waking every 5m
   to ask "anything new?". This is the single biggest scheduler violation on hatch.

2. **`squawk ask` answer wait — `~/workspace/bin/squawk`, `cmd_ask` (~L463–476)**
   Posts the question, then `while time.time() < deadline and len(answers) < want:`
   re-reads the channel and `time.sleep(2)` — up to 600s of 2s polling.
   **Replacement:** the feed's recursive `/wait?since=<seq>` long-polling
   (the transport the UI itself uses). Already a known remaining item from the
   request/response lane; the code comment above it claims "no poll loops in
   caller code" while the implementation polls — comment and code disagree.

### 🟢 LEGIT

3. **swarm-watchdog — every 5m — ENABLED** — crash-prevention interlock
   (hatch load1 > 10 → swarm-pause, yote load1 > 40 → eject runaways).
   Circuit breaker, explicitly carved out of the no-polling rule by doctrine.
   Docstring says "every 2 min via cron" but the real schedule is 5m — stale doc.
4. **bridge-watchdog — every 5m — ENABLED** — one authenticated probe of the
   Hatch↔Yote bridge per run; silence on success, sentinel + quiet-complete on
   known 401 drift. Safety heartbeat; no push alternative exists for "is the
   far end still answering".
5. **agent-reaper — every 30m — ENABLED** — pure `muse.db` census queries
   (phantoms / stalled / errored). No internal sleep or poll loop; the 30m
   cadence is the only timer. A DB LISTEN/NOTIFY conversion is theoretically
   possible but the query pack is cheap and the cadence is coarse — legit.
6. **exec.py `--poll` / `--watch` flags** (`~/workspace/awrawr-bridge/exec.py`
   L766 `_sysinfo_loop`, L907 `_watch_loop`) — opt-in human CLI monitoring
   modes, not background timers. Legit.
7. **race.py hedge sleep** (`~/workspace/skills/race/bin/race.py:210`,
   `await asyncio.sleep(hedge_ms / 1000)`) — bounded one-shot HFT hedge delay,
   part of the race itself. Legit.
8. **ws_daemon.py pinger** (`~/workspace/awrawr-bridge/ws_daemon.py:246`,
   `await asyncio.sleep(PING_INTERVAL)`) — WS protocol keepalive; keepalive
   *is* the event mechanism for half-open TCP. Legit. (Note: the cron docs
   claim "the legacy ws_daemon.py is deleted" — a ws_daemon.py IS running as
   PID 1839; it is the current persistent WS daemon, the doc refers to the old
   build. Doc should be corrected.)
9. **exec.py startup waits** (L289: 12s socket wait with 0.25s sleep;
   L698: one 2s re-probe on fresh-daemon race) — bounded one-shot startup
   settling with fail-fast breaks. Legit.
10. **progress-watchdog startup sleep** (`~/workspace/bin/progress-watchdog:296`,
    `time.sleep(4)` after supervisor launch, then health check) — one-shot. Legit.
11. **race-optimizer.py inotify fallback** (`~/workspace/bin/race-optimizer.py:234`,
    `LogWatcher.wait`) — inotify primary, `time.sleep(min(timeout,1.0))`
    fallback only when inotify is unavailable. Defensive; and the script is
    currently dormant (see below).

### Already event-driven

12. **`squawk race-poll` drain loop** (`~/workspace/bin/squawk:383`, `while True`)
    — drains pending race requests, exits when none remain. No sleep, no timer.
    A work loop, not a poll loop.

### Dormant / disabled (no action)

13. `race-optimizer.py` — not scheduled, not running (the 37%-CPU timer hog from
    2026-09-20 is already dead; a `.bak` copy sits next to it).
14. `yote-connector-watch` cron — `enabled: false`.
15. `audit-bridge-watch` cron — `enabled: false`.
16. No systemd user timers exist on hatch.

---

## YOTE — pitchfork daemons (dug by Mole 🦔, all 76 `[daemons.*]` reviewed,
timer suspects read line-by-line, live PIDs + CPU verified)

### 🔴 CONVERT (ranked by payoff)

1. **paper-poller — every 30s** — `/home/toxic/paper-poller/bin/poller.py`
   L269–274: `while True: poll_once(); time.sleep(INTERVAL)`, INTERVAL=30s
   (L42, env `PAPER_POLLER_INTERVAL`). `poll_once()` (L203–228) reads
   `CHANNEL = "/home/toxic/.shingle/directives.md"` (L43) — **a local file** —
   scanning for PAPER-TASK entries. Live PID 190380, 18h uptime, firing every
   30s. **Replacement:** inotify watch on directives.md (or parent dir, re-armed
   like bidder.py's self-healing watches) → `poll_once()` on modify/close_write;
   keep startup poll + `/health` server. Zero external APIs — the canonical
   violation. Payoff is latency, not CPU: PAPER-TASK pickup goes 30s → instant,
   compounding with the lane's HFT race rules.
2. **stash-guard fast path — every 90s** —
   `/home/toxic/sovereign/tools/stash-guard/stash-guard.py` L599–609:
   `while True: once(); time.sleep(args.interval)`, interval=90s (L48, daemon
   runs `--deep --interval 90`, live PID 190776). `once()` full-scans
   `/home/toxic/sovereign` + all worktrees for dirty state every 90s — the most
   expensive periodic job in the fleet. **Replacement:** recursive inotify on the
   watched dirs with ~60s debounce → run `once()` only when files changed; keep
   the hourly `--deep` scan as the LEGIT backstop. Snapshots become
   change-driven (better semantics for a flight recorder); the idle box goes
   truly quiet.
3. **squawk-relay forward.py — 30s full-sweep backstop** —
   `/home/toxic/.shingle/squawk-relay/forward.py` L41 (`SWEEP_INTERVAL = 30.0`),
   L267–281: inotify primary + full sweep every 30s as backstop.
   **Replacement:** trust inotify (local ext4, reliable) or raise backstop to 10m.
4. **squawk-relay sink.py — 60s full-sweep backstop** —
   `/home/toxic/.shingle/squawk-relay/sink.py` L29 (`FULL_SWEEP_INTERVAL = 60.0`),
   L202–216: same pattern (the 5s `ino.wait(5.0)` wake does no work unless
   events fired). **Replacement:** same as forward.py; convert the pair together.
5. **bench-radar — 10s stat poll fallback** —
   `/home/toxic/sovereign/tools/bench-radar/server.ts` L529–557:
   `fs.watch` (inotify-backed) is primary, but `setInterval(..., POLL_MS)`
   with POLL_MS=10000 (L29) stat-checks the log every 10s.
   **Replacement:** drop the setInterval; keep fs.watch + initial `scan(true)`.
   Pure doctrine payoff (one statSync per 10s is ~nothing in CPU).

### 🟢 LEGIT

6. **buildsrv-watchdog — every 20s** —
   `tools/buildsrv/buildsrv-watchdog.py` L201–213 (`while not stop` + 20×1s
   sleeps). Polls buildsrv `/health`, restarts after 3 consecutive fails.
   Circuit breaker for the wedged-but-alive case (documented 2026-09-14 lock
   deadlock) that pitchfork `retry=true` cannot see — a deadlocked process
   emits no events.
7. **paper-poller-watchdog — every 30s** — `/home/toxic/paper-poller/bin/watchdog.py`
   L139–154. GETs poller `/health` + stale-`last_poll` check; SIGKILLs wedged
   poller. Same circuit-breaker rationale. (Caveat: if paper-poller converts to
   inotify, this watchdog's staleness check must be reworked — see Ambiguous.)
8. **sovereign-router warm standby — every 30s** —
   `tools/sovereign-router/sovereign-router-ts/router.ts` L608–633:
   `setInterval(..., 30000)` pings `/models` on 3 **local-only** providers
   (llama-swap, kimi-auto, nim-local), feeding circuit-strike records + warm TCP.
   Circuit-breaker input; zero cloud spend.
9. **sovereign-router live discovery — every 30m** —
   `tools/sovereign-router/sovereign-router-ts/router_live_models.ts` L158–167
   (`REFRESH_MS = 30*60*1000`, L29). External provider APIs offer no push;
   30min cadence is cheap.
10. **squawk-ws ping keepalive — every 30s** —
    `projects/range/ranch/squawk-ws/squawk_ws_server.py` L423–427:
    `await asyncio.sleep(30)` → WS ping frames. Keepalive *is* the event
    mechanism for half-open TCP; no alternative exists.
11. **squawk-feed poll fallback — 2s, defensive only** —
    `projects/range/ranch/squawk/squawk_feed.py` L250–278: inotify primary with 55s
    long-poll; the 2s fallback (L257) fires only if inotify is unavailable —
    never on Linux yote.
12. **stash-guard hourly deep scan** — `stash-guard.py:49`
    (`DEFAULT_DEEP_EVERY=3600`) stays as the safety backstop after the fast
    path converts.
13. Minor legit sleeps: estate-reconcile 1s debounce, squawk-ws 0.3s burst
    coalesce, nats-tail / nim-kimi-sidecar reconnect backoffs.

### Already event-driven (no action — the pack already converted these)

14. **openfang-health** (`ops/openfang-health/loop.sh`) — blocks in `inotifywait`;
    daily digest via the inotifywait 86400s timeout. NOTE: pitchfork.toml comment
    still says "5-min OpenFang/coyote health loop" — **stale comment**, code was
    converted 2026-09-21.
15. **refusal-watchdog / sorry-watchdog** — blocking inotifywait, zero timers
    (live PIDs 314022, 328394).
16. **estate-reconcile-watch** (`bin/estate-reconcile` L261–277) — inotify loop,
    1s debounce only.
17. **oracle-market fleet** (`oracle_loop.py`, `bidder.py`, `market_watchdog.py`,
    `oracle_chat.py`, `oracle_daemon.py`) — inotify (ctypes) + select();
    deadline wakeups via select() timeouts are legit timers, not polls.
18. **kimiclaw bridge.ts** — zero setInterval/setTimeout/sleep.
19. **squawk-ws-client** — push client, no sleeps; exits on failure for pitchfork retry.
20. **nats-tail** (`projects/range/ranch/squawk/nats/squawk_nats_tail.py`) — NATS
    subscribe; single `asyncio.sleep(backoff)` (L265) is reconnect backoff.
21. **herd-keypool.py** `time.sleep(0.01/0.4)` hits (L1127–1188) — inside **test
    scaffolding** (FakeResp race test), not production.
22. **nim-kimi-sidecar.py:211** — reconnect backoff delay, not a poll loop.

### 🟡 Ambiguous (needs a tiebreaker before converting)

A1. **paper-poller-watchdog staleness check vs. an inotify paper-poller:** if
    paper-poller converts, `last_poll` stops advancing on cadence — the
    watchdog's "stale last_poll" kill criterion (`watchdog.py` L54–62) must
    change to an event-heartbeat (touch a heartbeat file on every inotify wake).
    Resolve by converting both together.
A2. **sink.py/forward.py backstop value:** belt-and-braces against missed
    inotify events. Check relay logs for sweep-found-missed entries; on local
    ext4 with the seq-allocator race fixed, expected value is near zero.

### Drive-by note (out of lane, recorded not actioned)

pitchfork.toml's own `health_http`/`health_port` probes (30s cadence on ~20
daemons) are a supervisor-owned poll tax — one GET per 30s per daemon. Not
daemon-code timers, so out of this audit's lane, but it is the largest remaining
fixed-cadence wake source on the box.

---

## Environment notes found during the audit (not timer issues)

- **Stuck interactive rebase in the shared worktree** (observed 2026-09-21
  ~16:25 MDT): an interactive rebase of `main` onto `dcfdc651cb` (commit
  `612463113d` "herd: rip UI out to ranch", author Ember, 16:21 MDT) is stopped
  with conflicts (`UU docs/fleet-knowledgebase.md` et al). As a side effect,
  `projects/range/ranch/squawk/seq_alloc.py` is absent from the worktree (present on
  `origin/main`), which breaks the `~/workspace/bin/squawk send` CLI path
  (it hardcodes that path on yote). Left untouched — owner's lane.
- Stale comments found: `swarm-watchdog` docstring ("every 2 min" vs real 5m
  cron); pitchfork.toml openfang-health comment ("5-min loop" vs converted
  inotify loop); `bin/squawk` ask comment ("no poll loops in caller code").

## Top 3 CONVERT candidates to fix first

1. **paper-poller 30s → inotify on directives.md** — one-file, local-only;
   task-pickup latency 30s → instant.
2. **stash-guard 90s fast path → debounced recursive inotify** (keep hourly
   deep scan) — kills the fleet's most expensive periodic job.
3. **squawk-monitor 5m cron → /subscribe or WS push** — the scheduler Chris
   named; removes the flagship "wake up and ask if anything happened" loop.
   (`squawk ask`'s sleep(2) poll converts with it via `/wait?since=`.)

Nothing in this audit was converted — audit only, per the brief.
