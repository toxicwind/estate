# Compression-proxy state map — 2026-10-02

Read-only recon by Vesper (evening-shepherd lane), ~15:05 MDT.
No processes killed, nothing restarted. All facts verified against live state
(`ss`, `/proc`, `bili doctor --json`, proxy instance records, proxy logs).

## TL;DR verdict

**PID 1816974 on :18788 is the stale instance. Cut it, keep :18789.**

- Two proxies both claim lane `"omp"` (`:18788` and `:18789`) — that is the
  "serving double".
- The lane registry (`/home/toxic/.local/state/billion-context/port-zone.json`)
  says `{"lanes":{"omp":18789}}` — `:18789` is the current holder.
- `:18788` runs older in-memory code (self-tags `v=0.1.179` in the shared log;
  `:18789` tags `v=0.1.180`).
- The proxy itself warns on startup: *"both processes will write the same
  sessions directory; stop one to avoid state pollution (#394)"*.
- No sigma build is running anywhere. Everything live is the old
  `billion-context` npm install (0.1.180 on disk).

## PID table

| PID | PPID | Started (MDT) | Binary | argv `--port` | Lane | Instance ID | Code fingerprint |
|---|---|---|---|---|---|---|---|
| 1816974 | 1816058 (tau) | 2026-10-02 01:49:17 | `/usr/bin/node /home/toxic/.bun/install/global/node_modules/billion-context/dist/index.js` | 18787 | `omp` | `3b8d4d92-5c33-4c50-9695-6acaf54c562e` | `c4b8ec46c5a4c7b2445804b27edb99d7083015db30a967596501d5ef1fdf7ef4` |
| 1254081 | 1253140 (tau) | 2026-10-02 03:04:47 | same | 18788 | `omp` | `d5bab0b5-598e-43aa-b73f-b2ee7f4a7b63` | `33a34990a9955fa3869bde40d29809f082491791cd1038be92f9ab5045be98d1` |
| 473557 | 1 (reparented) | 2026-10-02 14:39:42 | same | 32847 | *(none — manual)* | `52e0db4e-8bb8-4d02-b4a0-c24a3ef591dd` | `ec84b2360c4251c2e0f32b435ec8b860f574942e70e6a1adf0ebec7bbdecd754` |

Notes:

- `argv --port` ≠ listening port for the two tau-spawned instances (off by
  one). `bili doctor --json` → `processes[]` confirms the real ports
  (18788 / 18789 / 32847), matching `ss`. Working theory: each instance
  bumped +1 on EADDRINUSE at startup (at 01:49 something held 18787; at 03:04
  :18788 was held by the first instance).
- Fingerprints come from the proxies' own instance records in
  `/home/toxic/.local/state/billion-context/instances/*.json`. All three
  differ; the fingerprint is not a pure code hash (per-instance data is mixed
  in), so version is read from the processes' own log self-tags instead:
  `:18788` → `v=0.1.179`, `:18789` and `:32847` → `v=0.1.180`
  (correlated via `[exposure] uptime=` lines against process start times).
- `bili doctor` reports `staleCopy: false` for all three — that check compares
  the on-disk file, not the code loaded in memory, so it misses the
  0.1.179-in-memory staleness of `:18788`.

## Port table

| Port | Listener PID | argv claimed | Lane claim | Verdict |
|---|---|---|---|---|
| 18787 | — (nothing) | 18787 (pid 1816974) | — | requested port was occupied at spawn; instance sits on 18788 |
| 18788 | 1816974 | — | `omp` (instance record) | **STALE** — double-serving the omp lane; older code (0.1.179) |
| 18789 | 1254081 | — | `omp` (instance record + `port-zone.json`) | **CURRENT** — lane registry holder |
| 32847 | 473557 | 32847 | none (unregistered) | third wheel — started 14:39, 3 min after the `acp_status` failure below; CONFIRMED manual start (`BILI_PARENT_PID` absent; the session-owned :18788/:18789 have it) — the exact pattern the plugin refuses to attach to (#1322/#1335): outlives its starter, ignores config edits; still shares the sessions dir |

`/health` on all three returns `{"ok":true,"upstream":"https://api.anthropic.com"}`.
No `/version` or `/fingerprint` HTTP endpoints exist (probed; the proxy
forwards unknown paths upstream).

## Session table (tau → proxy)

| Tau PID | Started (MDT) | Spawned proxy (Δt) | Proxy URL | Attach status |
|---|---|---|---|---|
| 1816058 | 2026-10-02 01:49:15 | 1816974 (+2s) | `http://127.0.0.1:18788` | **STALE** — lane registry moved on to :18789 at 03:05 |
| 1253140 | 2026-10-02 03:04:45 | 1254081 (+2s) | `http://127.0.0.1:18789` | **CURRENT** — matches `port-zone.json` |
| 233542 | live | none spawned | via lane registry → `:18789` | — |
| 1719010 | live | none spawned | via lane registry → `:18789` | — |

Each proxy was spawned ~2s after its parent tau (`pi-coding-agent`) session
started — the omp native plugin self-spawns a session-owned proxy. Both
parents are still alive; both were launched from interactive `-bash` shells.
All four tau sessions run the **old** `@oh-my-pi/pi-coding-agent` bundle
(the `omp → tau` rename has not reached the running processes).

On `native-attach`: no such command exists anywhere in the tree (searched the
estate, `/home/toxic/estate/sigma`, tau docs, `$PATH`, and the
`billion-context` dist). The functional equivalent — which proxy a session is
attached to and whether its code matches — is the lane registry plus the
instance-record fingerprints, reported in the tables above. Fingerprint
summary: `:18789` matches the registry (attached, current);
`:18788` is attached to nothing current (orphan double, code-older);
`:32847` is attached to nothing (unregistered).

## Failing tools — what they hit

**`acp_status`** (proxy-injected tool, executed server-side by the proxy).
Proxy log, 2026-10-02 14:36:56 MDT (`bili.log.old`):

```
[warn] [v=0.1.180] [plugin] NO MODEL REQUESTS seen for conversation
01a0fe4f-d5f6-7669-9c7e-08c7c8f5afd3 (tool "acp_status"): the model answered
without any of its requests reaching this proxy — candidates: its LLM
transport bypasses the intercepted fetch (SDK-injected fetch or non-global
dispatcher), the host's attribution left this traffic unclaimed by the proxy,
or the conversation id is stale after a host resume. Verify: send a message
and look for processTurn lines in bili.log — none appearing means the traffic
never reaches the proxy; routing through the client's bili launcher (baseURL
rewrite) reaches it regardless of which fetch the transport uses.
```

The tool call landed on a proxy instance that never saw that conversation's
model traffic — the expected symptom of two lane-claimants splitting one
session's view of the world.

**`acp_cache`** (`bili acp-cache diff`, offline CLI). Current behavior:

```
bili acp-cache: no ACP_DUMP_BODY dumps found under
/home/toxic/.local/state/billion-context (expected *-REQ.txt / *-INCOMING.txt
in ., ./raw or ./dumps) — enable ACP_DUMP_BODY=1 first
```

No dumps exist, so there is nothing to diff — not an error, just empty input.

**`search_context`** (proxy-injected tool like `acp_status`). No direct failure
line in the proxy logs, but it reads the same shared session state that the
`[instances]` warning below calls polluted.

**Root-cause line**, from the `:32847` instance's own startup log
(2026-10-02 14:39:44 MDT, `/home/toxic/.local/state/billion-context/bili.log`):

```
[warn] [instances] another bili instance is running (pid 1816974, http://127.0.0.1:18788) — both processes will write the same sessions directory; stop one to avoid state pollution (#394)
[warn] [instances] another bili instance is running (pid 1254081, http://127.0.0.1:18789) — both processes will write the same sessions directory; stop one to avoid state pollution (#394)
```

Three instances, one sessions directory (`/home/toxic/.local/state/billion-context/`).

## Sigma status

`/home/toxic/estate/sigma` exists (`dist/agent/omp-native.js` present) but
`bili doctor` flags it **stale**: copy version `0.1.160` vs registry `0.1.180`.
No sigma process is running. The queued `bili → sigma` rename has not landed
in the live proxy layer — all live proxies are `billion-context`.

## Recommended cutover (for Ember's call — not executed)

1. Stop PID 1816974 (`:18788`, stale omp double, 0.1.179 in memory).
2. Confirm `:18789` remains the sole `omp` lane holder (`port-zone.json`
   already agrees).
3. Stop PID 473557 (`:32847`) too: confirmed manual `bili start`, no `BILI_PARENT_PID` — the known-bad pattern from Sep 27 (pid 1020129). The plugin itself refuses to attach to these because they outlive the session and ignore config edits, and it is writing to the shared sessions dir.
4. Do NOT touch the tau sessions themselves; they re-resolve via the lane
   registry.
