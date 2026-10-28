# 2026-10-28 anomalies — village sovereignty session (tau)

All items verified with live probes / real traffic this session.
Charter: every anomaly gets a capability-contract test before its fix is trusted.

| # | Anomaly | Essence | Fix (committed) |
|---|---------|---------|-----------------|
| 1 | **Keyring emitter skips `--secret-file` items** | `secretsmith set --secret-file F --label X` returns `stored: <path>`, the object exists in the keyring with correct attrs — but `secretsmith env` silently omits it (`catch { continue; }` swallows the read failure per item). stdin-path items emit fine. Seven rig vein keys were invisible to their consumer while `set` reported success — a silent credential gap masquerading as done. | diagnose + reroute: `sync-store-to-keyring.py` proves the gap (sha MISMATCH ×7), keys re-minted via the proven path; secretsmith fix pending in `pens/barn/secretsmith` |
| 2 | **Thresher dead-mirror config** | Live gateway (:25127, pid via `ss -ltnp`) ran `--config=/home/toxic/estate/ranch/thresher/mcp_config.json`; the estate copy at `estate/config/thresher/mcp_config.json` (54 servers) was a stale mirror — edits to it silently no-op (registered upstreams "not visible"). Two truths, one daemon. | found real path via `/proc/<pid>/cmdline` (not pgrep — it self-matches); both upstreams registered in the live config: `taas-telegram` connected (2 tools) |
| 3 | **Gateway self-kill by enum guess** | Adding gemini-mcp upstream with `protocol: "streamable_http"` (underscore) — mcpproxy-go's enum is `streamable-http` (hyphen) — crashed the ENTIRE gateway on config reload (`invalid protocol: mcpServers[66]`), taking down the estate's only MCP door mid-session. Guessed config value = fleet-wide outage. | fixed enum → `{"status":"ok"}` restored; contract test: `/api/v1/servers` (Bearer MCPPROXY_API_KEY) shows upstream connected+tool_count |
| 4 | **rig CLI lying error strings** | `rig cron create` printed `✘ Failed: ?` for all 11 jobs — every job actually registered (verified via `rig cron list` process truth: 11/11 present, correct exprs). Meanwhile names fail with `Invalid agent ID: invalid character: found 'g'` despite `--help` claiming "Agent name or ID" — only UUIDs work. | cron jobs verified via list (process truth over CLI claims — Unreliable Narrator); renames documented; rig fix pending upstream |
| 5 | **PATH binary copy drift (bin contract violation)** | `~/.local/bin/rig` was a 1-copy binary, not a symlink — source at `pens/ranch/rig` (HEAD 230ae62, pushed) invisible to PATH; `target/release/rig` absent from tree. Ghost-deployment class (splice/shep-repair precedent). | rebuild from source (wasmtime-heavy, bg); symlink per contract pending build |
| 6 | **Port SSOT squat** | `ports.env` said `GEMINI_MCP_PORT=25202`; doorbell-mcp actually owns :25202 (pitchfork `ready_http` proves it); gemini-mcp daemon loop-crashed on `address already in use` for hours of retries. | single truth `GEMINI_MCP_PORT=25227`; serve.sh reads ports.env SSOT (never trust daemon env — it carried the stale value); live: health ok, token gate 401 |
| 7 | **Google keypool header wall** | keypools.yaml sent `x-goog-user-project: 654595778272` on every gemini pool; the ONLY live key (EAP Standard, gcloud-verified 200) 403s exactly on that header (`Caller does not have required permission to use project` — despite owner IAM). Bare key: 200. Stale config doc claimed the header was required. | header dropped from all 4 gemini pools (`a3c1fb87` estate); live re-probe: GEMINI_EAP_KEY → healthy (latency 162ms); generation still 402 (billing, user-gated) |
| 8 | **GitHub repo naming rot** | `The-kappa-engine-open-source-AI-coding-agent-runtime`-class sentence-names on 4 repos + "Chris's personal infrastructure monorepo" description + upstream marketing copy on thresher. Slop leaked into the estate's public face. | 4 renames (kappa-engine, kappa-monorepo, kappa-cli, antigravity-gateway) + 2 description fixes; sweep: 100 repos, zero slop patterns / zero chris mentions remain |

## Capability-contract tests (live, this session)

- pgate: 4/4 unit + live burst (6-way → permits release, 502s from dead upstream not gate) + `/api/gate` endpoint
- router strike classes: 23/23 after test-fixture fix (model_strikes field)
- eidolon: health `{"status":"ok","version":"1.3.2"}` on :25244
- TaaS MCP: JSON-RPC initialize/tools/call round-trip + thresher federation (connected: true, tool_count: 2)
- IRC village: NAMES shows 9 nicks in #village (18 sockets incl. zombie twins)
- gemini-mcp: health ok + `401` without token (gate enforced)
- tau binary: fresh build boots estate config (qwen3.6-35b resolved, MCP connected) in tmux smoke
- modelOverrides: `maxConcurrency: 1` flows data.ts → codegen → models.yml
