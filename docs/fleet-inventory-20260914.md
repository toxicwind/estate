# Sovereign fleet inventory + completion reconciliation — 2026-09-14 ~18:20 MDT

Author: LANE-5 worker (inventory/recon), via bridge to awrawr-pc.
Every claim below was verified live on awrawr-pc through
`python3 ~/workspace/skills/awrawr-mcp/bin/exec.py` unless marked otherwise.
The stale 15:10 "STOP all new work" channel entry was treated as dead data per Chris's ~18:05 order.

## 1. Live status (verified)

| Daemon | Port | Verdict | Evidence |
|---|---|---|---|
| squawk-ws (pitchfork `sovereign/squawk-ws`) | 127.0.0.1:25147 | **UP** | `ss -tlnp` shows `python3` pid 2248059; WS handshake local -> `101 Switching Protocols` (valid bearer), `401` (bad bearer); public `wss://github-mcp-host.tailc9ac71.ts.net/squawk-ws` handshake -> `101` |
| squawk_feed.py (pitchfork `sovereign/squawk-feed`) | 127.0.0.1:25135 | **UP (recovered 18:08)** | `GET /squawk-feed/seq` -> `200 {"seq": 10002}` both locally and via funnel (0.32s). Note: the documented `/seq` path is actually `/squawk-feed/seq` (bare `/seq` -> 404) |
| awrawr-mcp (HTTPS) | :8377 | UP | pid 282976, uptime 15h |
| awrawr-ws-exec (bridge WS) | :8379 | UP | pid 2315871 |
| llama-swap / herd | :25100 | UP | pid 2113115 |
| coyote | :25143 (0.0.0.0) | UP | pid 2094471 |
| buildsrv | :25148 | UP | pid 2625628 |
| shep, herd, nim-proxy, kimi-auto-resolver, sovereign-router | — | UP per `pitchfork status` | 9 daemons in `pitchfork list` |

### Incident found and resolved during this recon (18:07–18:08 MDT)
`squawk_feed.py` died silently ~18:07 (3rd silent death today; `ss` showed it LISTEN at 18:06, `ECONNREFUSED` at ~18:07:30, process gone). My manual `setsid run-feed.sh` restart FAILED with `OSError: [Errno 98] Address already in use` (dying socket not yet released). **pitchfork's own retry loop then started it successfully at 18:08:08** ("serving #fleet ... Bearer <redacted>"), verified 200. No verified reason to redeploy anything.

## 2. Divergences — reconciled or marked

- **Two `squawk_ws_server.py` copies**: CONFIRMED DIFFERENT (md5 7fb4b9c5… vs 022c1e32…, 501 vs 503 lines). LIVE = `/home/toxic/squawk-ws/squawk_ws_server.py`. The `relay/` draft was NEVER deployed; SUPERSEDED marking in `relay/TRANSPORT_STATUS.md` is accurate — and it exists on origin/main (commit 2ddb32e, also 4909c38, cfb4de2). Local main was 3 commits BEHIND origin/main; a concurrent worker had already merged + pushed (`fdcd648 merge: fold origin/main (maximal, local wins)`). I committed the previously-untracked `relay/squawk_ws_server.py` draft (48d8d85, marked SUPERSEDED in message) and pushed: `toxicwind/squawk` main = **48d8d85**. origin/backup/main-20260914 = fdcd648 (pre-push snapshot; original backup from earlier today preserved in history).
- **`/home/toxic/squawk-relay-5f9a2c/`** (also `squawk-relay-baseline`, `squawk-relay-baseline2`, `squawk-host-pUnfHR`): worker scratch dirs. `squawk-relay-5f9a2c/squawk_feed.py` is a DIFFERENT draft copy — relay worker's lane. Left untouched (not my lane; deleting worker scratch is off-limits).
- `pitchfork daemons` (CLI) reports "No daemons configured" while `pitchfork list` shows 9 running and toml defines 37 `[daemons.*]` sections — known CLI/supervisor mismatch; the supervisor-side state is authoritative.

## 3. Silent-death root-cause update (new evidence)

The 18:04 squawk-ws restart sequence is the first WITH a log trail:
`18:04:11 [squawk-ws] state loaded` -> `OSError: [Errno 98] error while attempting to bind on address ('127.0.0.1', 25147)` — TWICE (18:04:11, 18:04:14) — then `18:04:31 listening on 127.0.0.1:25147` (success).

**Finding**: restarts race the dying old instance: the new process starts while the old one still holds the port, bind-crash-loops until the old socket releases. squawk-ws uses `asyncio.start_server` WITHOUT `reuse_address=True`; squawk_feed.py sets `allow_reuse_address=True` but that did not save my manual restart either (socket still bound by the dying process, not TIME_WAIT). The kill itself remains unexplained — no OOM (46G avail, dmesg clean), no traceback in app logs. What IS explained is the crash-loop-on-restart pattern. Also: **pitchfork retry DOES restart squawk-ws and squawk-feed** (observed 18:04 and 18:08), contradicting the 16:25 claim that "pitchfork retry did not restart them" — the earlier claim appears to have been premature (retry needed time / the bind race).

## 4. Watchdog gaps

- **Nothing watches squawk-ws server liveness on awrawr-pc.** Cell cron `squawk-ws-client-watchdog` (1m) only keeps the *cell-side client* alive. The server's deaths were found by humans/manual checks.
- **Nothing watches squawk_feed.py liveness.** Its 18:07 death was found by this recon, not by automation. pitchfork retry eventually recovered it, but with a bind-race delay.
- `service-restart-watchdog` (cell, 1m) watches CELL restarts + pressure — does not probe awrawr-pc services.
- awrawr-pc has no crontab; only systemd user timers (`awrawr-mcp-audit-export`, `gemini-sdk-refresh`) — neither is a service watchdog.
- **Recommendation**: a single liveness prober on awrawr-pc (socket check 25147/25135 -> restart via pitchfork if dead), or fix the restart path to not bind-race (SO_REUSEADDR / systemd `ExecStop` handoff). Filed as open; not implemented in this lane.

## 5. Secrets hygiene flag

`/home/toxic/.shingle/squawk-relay/run-feed.sh` exports `SQUAWK_FEED_TOKEN` as a **plaintext token in a shell script** on disk (not in a repo). Working, but worth moving to a 0600 env file or pitchfork env block at some point. Value NOT recorded here.

## 6. Still open

1. Root cause of the silent kills (3x squawk-ws ~15:11, ~16:20, ~18:02; 3x squawk-feed ~14:10, ~15:14, ~18:07). No OOM, no traceback, no evidence of who/what. Hypothesis space: external kills (OOM-killer ruled out), worker duplicate-restart accidents, pitchfork supervisor bugs.
2. Restart bind-race: new instance crashes on EADDRINUSE while the old instance's socket drains (observed for both daemons today).
3. Watchdog gap for awrawr-pc service liveness (see §4).
4. 37 daemon definitions in pitchfork.toml vs 9 running — intended set for [groups.all] members (mesh-hub, dnsmasq, kafka, yote, etc.) is unclear; they're defined but not started. Probably deliberate, but unconfirmed.

## Command evidence index (all run ~18:06–18:21 MDT via bridge)

- `ss -tlnp | rg "25147|25135|25130|25100|8377|8379"` — ports live
- `curl http://127.0.0.1:25135/squawk-feed/seq` -> `{"seq": 10002}` HTTP 200
- `curl https://github-mcp-host.tailc9ac71.ts.net/squawk-feed/seq` -> same, 0.32s
- stdlib WS handshake (local + public, good/bad bearer) -> 101 / 401
- `pitchfork list` / `pitchfork status sovereign/<id>` — 9 running
- `pitchfork logs sovereign/squawk-ws` — 18:04 bind-crash sequence
- `md5sum` both `squawk_ws_server.py` — different
- `git log/merge-base` on toxicwind/squawk — divergence reconciled, pushed 48d8d85
