# 2026-10-29 — tau deep-audit & fleet-restore session (tau)

All items verified with live probes / real traffic this session.
Charter: every anomaly gets a capability-contract test before its fix is
trusted.

Parquet precondition: `pens/estate/snapshots/sessions-20261029/tau-sessions-full.parquet` (239,438 events) + `kappa-messages-full.parquet` (43,897). Squawk daemon was DOWN (ECONNREFUSED :25120) at announce time — file-bus fallback used for the plan artifact; announce missed (caveat per protocol).

## 61. Bare regex queries route to REST and silently return 0
**Symptom:** `ghas_search_code "/nzbhydra.yml/i"` → 0 results; substring same terms → 10. Telemetry `before_filter: 0`.
**Root cause:** `needsBlackbirdEngine()` (packages/github-client/src/blackbird.ts) had branches for `path:`/`content:`/`symbol:`/`filename:` but none for bare `/regex/flags` — fell through to REST `/search/code`, which has no regex semantics.
**Fix:** bare-regex branch added; TDD 8 cases red→green; commit `436d73a` (github-search).
**Contract test:** MCP `ghas_search_code "/config.yml/i"` via :25113 returns real hits (katsuokaisao/influxdb-go-play …) post-restart; unit suite 16/16.

## 62. GitHub code-search regex constructs — silent-0 traps
**Symptom:** alternation `(a|b)`, `$` anchors, `+`, `.{0,3}`, and over-escaped `\\.` all return count 0 with no error; a burst of probes then 429s masquerading as more 0s.
**Root cause:** GitHub code-search regex (both Blackbird UI index and legacy REST) rejects unsupported constructs silently; 429 windows also surface as empty results.
**Fix:** not a code fix — a documented engine contract + probe discipline. Memory + skill captured.
**Contract test:** `/nzbhydra/i` → 256; `/nzb(hy|y)dra/i` → 0 (valid-but-unsupported); `/config\.yml/i` → results. Rate-limit cooldown-then-retest before concluding "unsupported".

## 63. secretsmith `get` on missing label silently returns an arbitrary credential
**Symptom:** `secretsmith get GITHUB_SESSIONS --json` returned `MOONBOX_CHAOS_API_KEY` (50 bytes, label mismatch) with exit 0.
**Root cause:** kryptos secretsmith `get` falls back to an arbitrary keyring item when the label is absent instead of erroring.
**Fix:** ghas side hardened — keyringSession now requires returned label == requested label AND session-cookie shape (≥100 chars, base64-ish); commit `2477d55` (github-search). **Kryptos upstream fix still owed.**
**Contract test:** unit suite 16/16 incl. label-mismatch rejection; live probe shows wrong-label item filtered.

## 64. taas-telegram service shipped without a supervisor entry
**Symptom:** thresher showed `taas-telegram connected: False, tools: 0, status: error`; :25243 dead; no process.
**Root cause:** flotilla-mcp ship session (D-2026-10-28) registered the server in thresher config but never added a pitchfork daemon — service died with its session.
**Fix:** `[daemons.taas-telegram]` added to pitchfork monolith (SSOT per anomaly 6): run=overlord/src/taas.ts, dir=pens arroyo (absolute per anomaly 41/45), env VANS_TAAS_PORT=25243. Daemon started; thresher reconnected (`connected: True, tools: 2, status: ready`).
**Contract test:** `GET :25243/telegram/status` responds; thresher `/api/v1/servers` shows connected. **`ok:false` = user StringSession expired — phone MTProto re-auth owed (architect-gated).**

## 65. Ghost `/home/toxic/estate` recreated (anomaly 48 regression)
**Symptom:** dir existed again (Oct 29 03:26) with `.state/*.json`; pairs-apply check output `WOULD PATCH /home/toxic/estate → pens/estate`; systemd units still reference `%h/estate` paths (arrival-classifier, awrawr-mcp WorkingDirectory).
**Root cause:** systemd user units from the pre-cutover era still point into the ghost path and runtime state writers (keygate/live-models lane) recreate `.state/` there.
**Fix:** state archived to `~/sovereign/scratch-archive/20261029-tau-ghost-estate-state/`, dir removed; `name-fix.ts` ESTATE const repointed to pens (committed with estate sweep `f27ce28d9b` context). **Systemd unit path sweep still owed.**
**Contract test:** `ls -d /home/toxic/estate` → GONE post-remove; re-check after next flush (writers may recreate).

## 66. xerj "index didn't work" — engine never booted
**Symptom:** cosmic-disclosure indexing/search assumed broken; nothing on :9200-9202, no data dir.
**Root cause:** vendored engine simply never started — no daemon, no boot run.
**Fix:** booted per its README (`bin/xerj --insecure --port 9200 -d ~/.xerj-data`); TDD ingest+search suite green 4/4 (commit `2ad64e3` in vendored tree, local). bge-m3→qdrant cross-lingual ingest separately proven (en query → zh hit 0.819 on :25133).
**Contract test:** `bun test tests/cosmic-disclosure-search.test.ts` 4/4; qdrant search top-hit `揭露宇宙 第三季`.

## 67. Deep-audit surfaced the will-use-then-stop anti-pattern programmatically
**Symptom:** agent declared tool use then yielded without calling (observed ~6× in one turn by the architect); audit previously only caught phantom-todos (over-claim variant).
**Root cause:** intent-declared-then-yielded sessions (2-4 events, completed:false, low tool density) had no detection band.
**Fix:** `kleio helper/deep-audit.ts` — saved script (commit `5c6f5d4`): real unknown_types, tool density, max tool/todo bursts, failure timeline, will-use-then-stop band → **48 sessions flagged**; dataframe TSV/JSON. Also `session-audit` bin on PATH (estate-ops, manifest-corrected) + AGENTS.md doctrine codified (`f27ce28d9b`).
**Contract test:** run `session-audit /tmp/out` → 372 sessions/43,897 events, bands + will-use-then-stop list emitted; `.tsv` 373 lines.

## 68. tau `mcp.json` mesh-gateway transport mismatch
**Symptom:** `mcp://` reads unresolvable; thresher reachable but tau-side server shows error.
**Root cause:** `~/.tau/mcp.json` declared `transport: "sse"`; thresher only speaks streamable-http at `/mcp` (no `/sse` — 404). Anomaly-21's enum class of bugs, client side.
**Fix:** transport → `"http"` in `~/.tau/mcp.json`.
**Contract test:** raw initialize to :25127/mcp unauth loopback → 200 + `Mcp-Session-Id` (tau restart needed to pick up — flagged).
