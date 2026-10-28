# Squawk Consolidation — Full Inventory

Date: 2026-09-17 ~14:00 MDT. Read-only inventory (nothing modified).
Goal per Chris: consolidate all squawk into one actual first-class service ("the next OpenFang").

---

## 1. Live daemons (pitchfork, awrawr-pc)

### 1a. sovereign/squawk-ws — WebSocket push server
- PID: 179162 (running)
- Stanza (`/home/toxic/sovereign/pitchfork.toml:317`):
  - `run = "exec python3 /home/toxic/squawk-ws/squawk_ws_server.py"`
  - `dir = "/home/toxic/squawk-ws"`, `mise = false`, `retry = true`, `boot_start = true`, `auto = ["start"]`
  - `ready_cmd = "ss -ltn 'sport = :25147' | grep -q LISTEN"`
  - `env = { SQUAWK_WS_PORT = "25147", SQUAWK_CHAT_ROOT = "/home/toxic/.shingle/squawk-root" }`
- Source: `/home/toxic/squawk-ws/squawk_ws_server.py` (17,140 bytes, stdlib only: asyncio + inotify via libc ctypes, no deps)
- Port: **127.0.0.1:25147**
- Protocol: WS at `/squawk-ws`; `Authorization: Bearer <token>` on Upgrade, constant-time compare; no header -> 401. After 101, client sends `{"subscribe": ["fleet","leads"]}` (or nothing = all). Server replays last ~20 msgs/channel, then streams `{seq, channel, sender, text, ts, sealed}` JSON frames. Sealed messages broadcast sender + `sealed:true` flag only — never content/ciphertext.
- Sources watched: `/home/toxic/.shingle/squawk-root/<channel>/*.md` + zipfs-vault zip manifest (default `SQUAWK_WS_VAULT=/home/toxic/workspace/skills/zipfs-vault/store/vault.zip`)
- Token: `SQUAWK_WS_TOKEN_FILE`, default `/home/toxic/.squawk-ws-token`
- State: `SQUAWK_WS_STATE_DIR/state.json`, default `/home/toxic/.squawk-ws/state.json` → currently `{"gseq": 120, "chan": {"fleet": 10002, "leads": 2}, "vault": 1}`
- Health: plain HTTP `GET /ping` → `{"ok": true, "seq": 120, "clients": 4}` (no auth). 4 clients connected at inventory time.
- Log: `/home/toxic/squawk-ws/server.log`

### 1b. sovereign/squawk-ws-client — local push client
- PID: 179387 (running)
- Stanza (`/home/toxic/sovereign/pitchfork.toml:426`):
  - `run = "exec python3 /home/toxic/squawk-ws/squawk_ws_client_local.py"`
  - `dir = "/home/toxic/squawk-ws"`, `retry = true`, `boot_start = true`, `auto = ["start"]`
  - `env = { SQUAWK_WS_TOKEN_FILE = "/home/toxic/.squawk-ws-token" }` ← **this override is the only thing saving it from the stale default token file**
  - `ready_cmd = "find /home/toxic/squawk-ws/client-heartbeat -mmin -2 | grep -q ."`
  - `depends = ["squawk-ws"]`
- Source: `/home/toxic/squawk-ws/squawk_ws_client_local.py` (6,837 bytes, stdlib only)
- Behavior: connects to 127.0.0.1:25147, subscribes fleet+leads, appends envelopes to spool. **No internal backoff loop** — on failure the process exits non-zero and pitchfork `retry=true` restarts it; server backfill (20 msgs) + cursor dedupe cover drops.
- Defaults (overridable by env): `TOKEN_FILE=/home/toxic/squawk-ws/token` (STALE — see §2), `SPOOL=/home/toxic/squawk-ws/client-spool.jsonl`, `CURSOR=/home/toxic/squawk-ws/client-cursor.json`, `HEARTBEAT=/home/toxic/squawk-ws/client-heartbeat`
- Note in stanza: "cell-proof pilot … cell-side client + watchdog stay as fallback until 24h proven" (2026-09-14)

### 1c. sovereign/squawk-feed — HTTP long-poll feed
- PID: 196131 (running; was restarted by squawk-watchdog ~13:58 MDT on 2026-09-17)
- Stanza (`/home/toxic/sovereign/pitchfork.toml:263`):
  - `run = "exec /home/toxic/.shingle/squawk-relay/run-feed.sh"`
  - `dir = "/home/toxic/squawk"`, `mise = false`, `retry = true`, `boot_start = true`, `auto = ["start"]`
- Launcher: `/home/toxic/.shingle/squawk-relay/run-feed.sh` (5 lines): sets `SQUAWK_FEED_TOKEN` (**credential inline in the script** — value redacted from this inventory), sets `FLEET_KEYS_DIR=/home/toxic/.shingle/squawk-root/keys`, then `exec python3 /home/toxic/squawk/squawk_feed.py --root /home/toxic/.shingle/squawk-root --channel fleet --bind 127.0.0.1 --port 25135 --identity relay`
- Source: `/home/toxic/squawk/squawk_feed.py` (347 lines, stdlib: http.server + inotify)
- Port: **127.0.0.1:25135**
- Routes (all except /ping require `Authorization: Bearer <SQUAWK_FEED_TOKEN>`; bad token → 404 with empty body, never revealing the endpoint):
  - `GET /squawk-feed/ping` — health, no auth
  - `GET /squawk-feed/seq` — current high-water seq (kept for the relay agent)
  - `GET /squawk-feed/wait?since=N` — long-poll ~55s; inotify on channel dir wakes parked polls instantly; returns `{seq, messages[]}` (seq>since, oldest first, cap 50, text truncated to 500 chars)
  - `GET /squawk-feed/subscribe` — same as /wait
- Sealed messages are unsealed server-side with the relay identity (`relay.seal.key`); unopenable → `{sealed: true, body: null}`. "HARD RULE: no unauthenticated unsealed content, ever."

### 1d. Cell-side client (live, on the cell — not pitchfork)
- `/home/hatch/workspace/squawk-ws-client.py` (stdlib; currently running as cell PID 2922)
- Connects via Tailscale funnel: `wss://github-mcp-host.tailc9ac71.ts.net/squawk-ws` (tolerates funnel's mangled 101)
- Token: `/home/hatch/hooks/state/squawk-ws.token` (0600, 65 bytes)
- Spool: `/home/hatch/workspace/squawk-ws-spool.jsonl`; cursor: `/home/hatch/hooks/state/squawk-ws.cursor`
- **2026-09-17 self-heal patch (live on disk, not a git repo):** 3 consecutive 401 handshake rejections → re-run token fetch + reload; max 2 refresh cycles per streak, then legacy backoff (15s→5m). Logs `TOKEN_STALE_REFRESHED` / `TOKEN_STALE_STILL_FAILING`.

---

## 2. Tokens / credentials (values never recorded; sizes + readers only)

| File | Size | Perms | Mtime | Status | Readers |
|---|---|---|---|---|---|
| `/home/toxic/.squawk-ws-token` | 65 B | 0600 | Sep 14 14:42 | **LIVE server token** | squawk_ws_server.py (default `SQUAWK_WS_TOKEN_FILE`); squawk_ws_client_local.py (via stanza env override); cell token-fetch script (source it copies from) |
| `/home/toxic/squawk-ws/token` | 43 B | 0600 | Sep 14 14:57 | **STALE** — differs from live | default `TOKEN_FILE` in squawk_ws_client_local.py (overridden at runtime — footgun if ever started without the env var); `/home/toxic/sovereign/shingle-workspace/ws_local_test.py:4` hardcodes it → 401s |
| `/home/hatch/hooks/state/squawk-ws.token` | 65 B | 0600 | Sep 17 19:21 UTC (refreshed) | cell client copy | cell squawk-ws-client.py; written by `~/workspace/squawk-ws-token-fetch.py` (1,431 bytes, fetches from awrawr-pc via bridge) |
| `SQUAWK_FEED_TOKEN` inline in `/home/toxic/.shingle/squawk-relay/run-feed.sh` | — | script 0755? | — | **credential baked into launcher script** | squawk_feed.py (required — refuses to start without it) |
| `/home/hatch/hooks/state/squawk-feed.token` | 66 B | — | Sep 14 21:12 | cell copy of feed token | cell-side long-poll consumers |
| `/home/toxic/.shingle/squawk-relay/feed-token` | — | — | — | legacy relay token | old `feed.py` (retired 2026-09-14) |
| `/home/toxic/.shingle/squawk-root/keys/{agent1,breaker,relay,shingle,yote}.key` | — | 0600 | — | HMAC identity keys for chat.py signing | chat.py, squawk_feed.py (via FLEET_KEYS_DIR) |
| `/home/toxic/.shingle/keys/` | — | — | — | seal keys (`<agent>.seal.key` 0600 / `.seal.pub`) | squawk_seal.py |

Open question: what rotates `/home/toxic/.squawk-ws-token` server-side? The 2026-09-17 401 incident was a stale *client* copy; server file unchanged since Sep 14. Rotation procedure is undocumented.

---

## 3. Supervision / watchdogs

- **squawk-watchdog** (systemd user timer, every 60s): `/home/toxic/.local/share/squawk-watchdog/squawk-watchdog.sh` (also source copies at `/home/toxic/sovereign/tools/squawk-watchdog/` and units in `/home/toxic/.config/systemd/user/squawk-watchdog.{timer,service}`). Only ever *starts* things that are down (port closed or pitchfork not reporting running); never stops healthy daemons. Resolves the pitchfork binary from the live supervisor to dodge the 2.16.0-vs-2.25.0 CLI skew. Observed restarting `squawk-feed` at ~13:58 MDT 2026-09-17. State: `/home/toxic/.local/state/squawk-watchdog/`.
- **Cell cron `squawk-ws-client-watchdog`** (every 1m, enabled): runs `~/workspace/squawk-ws-client-watchdog.sh` — pidfile-based (`/proc` cmdline verification, no pgrep substring matching), starts `~/workspace/squawk-ws-client.py` detached, logs to `~/workspace/squawk-ws-client.log`.
- **Cell cron `squawk-archive-hourly`** (every 1h, enabled): `python3 ~/workspace/skills/encrypted-github-fs/squawk_snapshot.py` — incrementally archives fleet+leads to Google Drive folder `squawk-archive` (`squawk/fleet/YYYY-MM-DD-HH.jsonl`), idempotent via skill store state.
- **Cell cron `sidechat-watch-squawk`** (every 30s, **DISABLED**): side-chat watchdog for the "Squawk — first-class hosting" side chat (chat_id `1d3fa9cb-7d5f-4ca2-b53b-b97bab7579d8`).

---

## 4. Code layers (all of them)

### L0 — file-based chat (the original squawk)
- `/home/toxic/.shingle/chat/chat.py` — signed per-agent identity (HMAC-SHA256), Lamport clocks, hash-linked DAG, optional per-channel encryption. Repo: `toxicwind/squawk` (per squawk-health.sh origin check).
- `/home/toxic/.shingle/bin/squawk` — one-command wrapper: `SQUAWK_ID=breaker squawk post fleet --title … --body …`; `squawk read fleet`; `squawk channels`. Wraps chat.py with `SQUAWK_ROOT=/home/toxic/.shingle/squawk-root` default.
- `/home/toxic/.shingle/squawk-health.sh` — health probe: git repo check, origin check, 0600 key checks for breaker/shingle/agent1/yote/relay, channel init checks, post/read round-trip with `--write-test`.

### L1 — HTTP feed + sealed secrets
- `/home/toxic/squawk/squawk_feed.py` (347 lines) — the live :25135 server.
- `/home/toxic/squawk/squawk_seal.py` (662 lines) — NaCl sealed-box (X25519) sealed secrets; ciphertext rides inside the normal signed message body (`-----BEGIN SQUAWK SEALED MESSAGE-----`).
- `/home/toxic/squawk/tests/test_squawk_feed.py` — tests.

### L2 — WebSocket push
- `/home/toxic/squawk-ws/squawk_ws_server.py` — the live :25147 server.
- `/home/toxic/squawk-ws/squawk_ws_client_local.py` — the live local client.
- Superseded: `/home/toxic/squawk/relay/squawk_ws_server.py` (pitchfork.toml line 402: "superseded squawk-ws variant kept for reference — old path /home/toxic/squawk/relay/squawk_ws_server.py").

### L3 — cell client
- `/home/hatch/workspace/squawk-ws-client.py`, `/home/hatch/workspace/squawk-ws-token-fetch.py`, `/home/hatch/workspace/squawk-ws-client-watchdog.sh`, `/home/hatch/workspace/squawk-ws-client.log`.

---

## 5. State files

- `/home/toxic/.squawk-ws/state.json` — ws server cursors: `{"gseq": 120, "chan": {"fleet": 10002, "leads": 2}, "vault": 1}`
- `/home/toxic/squawk-ws/client-spool.jsonl` (104 B), `client-cursor.json` (26 B), `client-heartbeat` (15 B), `state.json` (366 B — stale, `next_seq: 18`, from an older client run in this dir), `server.log`
- `/home/toxic/.shingle/squawk-root/{fleet,leads,keys}/` — channel files (`10000-relay-relayed-message.md`, `10001-shingle-race-test.md`, `10002-shingle-race2.md`, `log.jsonl`, `_meta.json`)
- `/home/toxic/.shingle/directives.md` — the fleet channel itself (1,300 lines; newest directives at bottom)
- Cell `/home/hatch/hooks/state/`: `squawk-feed.seq`, `squawk-feed.token`, `squawk-relay-main.seq`, `squawk-ws.cursor`, `squawk-ws.token`, `squawk-ws-spool.json`, `squawk-delivered.sha1`, `squawk-push.latency.log`, `squawk-transport-race.log`, `squawk-push.out`, `squawk-feed.seq.wake.*.lock` (empty lock dirs)

---

## 6. Producers and consumers

**Producers** (write to squawk-root channels):
- Any agent on awrawr-pc via `.shingle/bin/squawk post` / `chat.py` (`SQUAWK_ID` = breaker, shingle, agent1, yote, relay — all have keys)
- Chris via `/home/toxic/.shingle/directives.md` (fleet channel)
- The relay identity via squawk-feed (unseals + serves)

**Consumers** (read):
- squawk-ws subscribers: local client (spool on disk), cell client (via Tailscale funnel), 4 connected at inventory time
- Long-pollers on `:25135/squawk-feed/wait` — observed a `curl -s -m 62 … /squawk-feed/wait?since=10002` waiter (transient; gone by re-check — likely a cron worker)
- `squawk-archive-hourly` → Google Drive
- Fleet workers reading `directives.md`
- (Disabled) `sidechat-watch-squawk` side-chat consumer

**Ports in use:** 25147 (ws server), 25135 (feed HTTP). Both bound to 127.0.0.1 only.

---

## 7. Dead / duplicated / stale pieces (proposal only — nothing deleted)

1. `/home/toxic/squawk-ws/token` (43 B) — **stale token**; default path in client code. Align to live token or delete.
2. `/home/toxic/squawk/relay/squawk_ws_server.py` — superseded server variant (kept "for reference" per pitchfork.toml).
3. `/home/toxic/sovereign/shingle-workspace/squawk-ws-client.py` + `squawk-ws-client.pid` (Sep 16) — old client copy; live one is at `/home/toxic/squawk-ws/`.
4. `/home/toxic/sovereign/shingle-workspace/squawk-ws-client-watchdog.sh` — old watchdog; live one is cell-side.
5. `/home/toxic/sovereign/shingle-workspace/ws_local_test.py:4` — hardcodes the stale token path.
6. `/home/toxic/.shingle/squawk-relay/feed.py` + `feed.py.retired-20260914` + `feed-token` — retired relay.
7. `/home/toxic/.squawk-rename-20260914/` (edits.py, keys, smoke) — rename experiment leftovers.
8. `/home/toxic/squawk-relay-baseline/`, `/home/toxic/squawk-relay-baseline2/` — old baselines.
9. `/home/toxic/squawk-host-pUnfHR/repo` — hosting experiment.
10. `/home/toxic/.openfang/workspaces/squawk-relay/` — agent workspace (AGENT.json, BOOTSTRAP.md, data, logs, memory).
11. `/home/toxic/squawk-ws/state.json` — stale client state (`next_seq: 18`) shadowing nothing but confusing.
12. `/home/toxic/cell-backup-20260917/workspace.squawk-*.tar.gz` (6 tars) — backup artifacts, not live.
13. `sidechat-watch-squawk` cron — disabled; keep or remove.
14. `SQUAWK_FEED_TOKEN` inline in `run-feed.sh` — should move to a secrets file (0600), not a 0755 script.

---

## 8. Data-flow diagram (current)

```
producers (agents via bin/squawk, Chris via directives.md, relay)
        │  write *.md channel files
        ▼
/home/toxic/.shingle/squawk-root/{fleet,leads}/   ← chat.py (HMAC-signed, Lamport, DAG)
        │  inotify
        ├──────────────────────────────┐
        ▼                              ▼
 squawk-ws :25147 (WS push)     squawk-feed :25135 (HTTP long-poll)
  Bearer: .squawk-ws-token        Bearer: SQUAWK_FEED_TOKEN (inline in run-feed.sh)
  state: .squawk-ws/state.json    /ping /seq /wait /subscribe
        │                              │
        ▼                              ▼
 local client ──spool──► /home/toxic/squawk-ws/client-spool.jsonl
 cell client (wss via Tailscale funnel) ──spool──► ~/workspace/squawk-ws-spool.jsonl
 long-poll waiters (cron workers) ──► :25135/squawk-feed/wait
 squawk-archive-hourly ──► Google Drive squawk-archive/
```

---

## 9. OpenFang template — what "actual" looks like

OpenFang is the model for a first-class service. Its anatomy:

- **Named pitchfork daemon** (`sovereign/axiom`, `/home/toxic/sovereign/pitchfork.toml:67`):
  `run = "exec ./stack/services/openfang.sh"`, `dir = "."` (sovereign root), `mise = true`,
  `retry = true`, `ready_http = "http://127.0.0.1:25103/api/health"`, `depends = ["shep"]`, `auto = ["start"]`.
- **Launcher script** (`stack/services/openfang.sh` → `bun src/services/openfang.ts`, 145 lines) that does the boring production work:
  - loads canonical ports (`requirePort("OPENFANG_PORT")` — single source of truth for ports),
  - loads secrets from files (`~/.secrets`, `~/.openfang/secrets.env`; **canonical file wins**, stale inherited env is dropped),
  - pins the backend port by rewriting config (`api_listen = "127.0.0.1:25203"` in `~/.openfang/config.toml`),
  - discovers the real binary from a candidate list (`~/.local/bin/openfang`, `~/.openfang/bin/openfang`, `/usr/local/bin/openfang`, `sovereign/bin/openfang`),
  - waits for the backend `/api/health` before reporting ready.
- **Real binary**: Rust workspace at `/home/toxic/projects/agents/openfang/` (crates: `openfang-kernel` [supervisor], `openfang-api` [HTTP server], `openfang-runtime`, `openfang-channels`, `openfang-memory`, `openfang-skills`, `openfang-types`, `openfang-wire`, `openfang-hands`, `openfang-extensions`, `openfang-migrate`, `openfang-desktop`; `deploy/`, `sdk/`, `xtask/`).
- **Health**: `GET /api/health` on the public port (25103); backend on 127.0.0.1:25203.
- **Logs**: `/home/toxic/.openfang-service.log` (structured Rust logs, e.g. `openfang_kernel::supervisor`, `openfang_api::server`).
- Note: OpenFang itself is currently DOWN (`pitchfork status axiom` → "available", not running; last log 2026-09-14 "OpenFang daemon stopped"). The template is structural, not a live reference right now.

**What to copy for squawk:** one daemon name, one launcher script, `ready_http` health, canonical ports file, secrets-from-file (canonical wins), binary/source discovery with fallbacks, structured logging, `depends`/`retry`/`auto` in the stanza.

---

## 10. Consolidation proposal (proposal only — build not started)

**Headline:** one `sovereign/squawk` pitchfork daemon + one launcher script, one token, one spool dir; fold the three transports (file chat, HTTP long-poll, WS push) into a single server process with `/api/health`.

1. **Single daemon**: merge `squawk-ws`, `squawk-ws-client`, `squawk-feed` stanzas into `sovereign/squawk` with `run = "exec ./stack/services/squawk.sh"` (mirroring `openfang.sh`), `ready_http = "http://127.0.0.1:<PORT>/api/health"`, `depends = ["shep"]`, `retry = true`, `auto = ["start"]`.
2. **Single server**: fold `squawk_feed.py` routes (`/squawk-feed/*`) into the ws server process (or vice versa) — one port, one auth check, one inotify watcher, one `/api/health`. Keep `chat.py` as the storage layer (HMAC/Lamport/DAG already right).
3. **Single token**: `/home/toxic/.squawk-ws-token` becomes the canonical WS token; move `SQUAWK_FEED_TOKEN` out of `run-feed.sh` into `~/.squawk/secrets.env` (0600), loaded by the launcher (canonical-file-wins, OpenFang-style). `squawk-ws-token-fetch.py` remains the only distributor to the cell.
4. **Single client**: merge `squawk_ws_client_local.py` and cell `squawk-ws-client.py` into one codebase with a `--direct` (127.0.0.1) / `--funnel` (wss) mode flag; keep both spool locations but one cursor format. The 401 self-heal ships in both.
5. **One state dir**: `~/.squawk/` holding `state.json` (server cursors), `client-spool.jsonl`, `client-cursor.json`, `client-heartbeat`, `secrets.env` (0600).
6. **Retire** (proposal): items 1–13 in §7 — superseded relay server, stale token file, old shingle-workspace copies, retired feed.py, rename/baseline/host experiment dirs, stale state.json, disabled sidechat-watch-squawk (or re-enable as the consumer it was meant to be).
7. **Keep**: `chat.py` + `bin/squawk` CLI + `squawk-health.sh` (the L0 chat is the durable log; the service is a transport upgrade over it), `squawk_seal.py`, `squawk-watchdog` (fold into the daemon's `retry` + a single systemd timer), `squawk-archive-hourly`.
