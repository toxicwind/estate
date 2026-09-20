# Chat coordination — requirements/issues for the canonical track
Date: 2026-09-18 ~17:10 MDT. Author: chat-coord lane (subagent cffd2340), stood down per main-chat consolidation.
Status of this doc: filed, not assigned. Router note at the bottom.

## Provenance

Chris's order (2026-09-18 ~16:47 MDT): "why doesn't awrawr-pc have a chat mcp
that can be used as api etc … why doesn't awrawr-pc just host a server on
tailscale they can join … Add it first class do not monkeypatch."

Design debate 34d3476a (positions: extend squawk-ws / greenfield / synthesis;
winner seq 4, greenfield synthesis, 0.85) produced the requirement set below.
This track built chat-coord (github.com/toxicwind/chat-coord, 20/20 acceptance,
two-agent MCP round trip proven ~47ms/call) and then stood down per the
consolidation order. These issues are the portable remainder.

## Ground truth of the :25122 implementation (probed, not imagined)

Source: `/home/toxic/sovereign/tools/fleet-chat/server.ts` v0.1.0 (bun,
SQLite WAL at `/home/toxic/fleet-chat/fleet-chat.db`), read in full
2026-09-18 ~17:08 MDT. Live probe: **0 listeners on :25122** — the server ran
16:53–16:56 (DB WAL last write) and is down now; no pitchfork stanza exists
(removed in sovereign commit 0e3d15a93b).

API surface in code: `GET /health` (unauth) · `GET /v1/rooms` ·
`POST /v1/rooms {name, topic?}` (name regex `^[a-z0-9][a-z0-9_-]{1,40}$`) ·
`POST /v1/rooms/{r}/join {agent_id, chat_id?, display?}` (upsert) ·
`POST /v1/rooms/{r}/leave` · `POST /v1/rooms/{r}/messages
{agent_id, body, reply_to?, provenance?}` (member-only, 403 otherwise; server
stamps chat_id/display from the membership row) · `GET
/v1/rooms/{r}/messages?since_seq=&limit=` (returns `{messages, latest_seq}`,
limit cap 500) · `GET /v1/rooms/{r}/presence` (members by last_seen desc) ·
`POST /v1/rooms/{r}/heartbeat {agent_id}` (member-only).

Already good — do not regress: bearer auth on all `/v1/*` (401 unauth);
member-gated send; server-stamped identity (narrator injection impossible by
construction — the strongest property in v0.1.0); cursor history with
`latest_seq`; 8000-char body cap; reply_to threading; provenance
(quote/source/ts); seeded `fleet` room.

## Issues / requirements (file as issues against the canonical track)

- **R0 (blocking, observed): liveness.** :25122 has no listener as of this
  probe. If the fleet-ops lane revives it: restore pitchfork supervision
  (`boot_start`, `retry`, readiness on `/health` or `:25122` LISTEN), then
  re-verify `/health` + 401-unauth before anything else.
- **R1: MCP tool surface.** v0.1.0 has no MCP endpoint (no `POST /mcp`, no
  stdio shim) — yet Chris's order is literally "a chat mcp that can be used
  as api". Add MCP JSON-RPC with tools: `rooms_list`, `rooms_create`,
  `rooms_join`, `chat_send`, `chat_history` (cursor args `since_seq`,
  `limit`), `presence`. Streamable HTTP and/or a stdio shim. Critical:
  the MCP layer must resolve agent identity through the membership row
  (R7), never trust client-supplied `display`/`chat_id`.
- **R2: Tailscale exposure.** Code default `HOST=0.0.0.0`; the old stanza set
  `FLEET_CHAT_HOST=0.0.0.0`. Chris's order: "host a server on tailscale they
  can join". Bind `127.0.0.1` + expose via surgical `tailscale serve`
  route (existing routes untouched) — never `0.0.0.0`.
- **R3: auth hardening.** `authed()` uses `===` string comparison; switch to
  a timing-safe compare. Token-via-file (`FLEET_CHAT_TOKEN_FILE`) already
  supported — keep that convention; token at `/home/toxic/fleet-chat/.token`
  (0600) stays out of repos.
- **R4: DM convention.** Rooms already support 2-member use; document the
  `dm-<a>-<b>` naming convention (or add a DM helper) so agents don't invent
  incompatible ones.
- **R5: presence staleness.** `presence` returns members ordered by
  `last_seen` but no active/stale signal. Add an `active_within_s` filter
  (or expose the staleness cutoff) so agents can distinguish live from
  stale members. Heartbeat already requires membership — good.
- **R6: history cursors.** `since_seq` + `latest_seq` already match the
  debate's cursor design — keep. Per-agent server-side read cursors are a
  later enhancement, not required.
- **R7: preserve server-stamped identity.** Any new surface (MCP, CLI) must
  keep stamping `agent_id`/`chat_id`/`display` from the membership row.
- **R8: two-agent acceptance.** Once live and supervised: agent-a and
  agent-b join one room through the MCP surface over the tailnet route;
  a sends, b reads + responds, a reads the response. Capture transcript,
  seqs, cursors, timings. (Bar from this track's proof: ~47ms/call.)
- **R9: no duplicate servers.** Standing rule (directives.md): converge,
  never duplicate. This track's :25152 is stood down and will not come back
  without a main-chat verdict.

## Router note (conflict the parent must resolve)

This task's premise ("fleet-chat :25122 LIVE and canonical, owned by lane
0fcb5f23") is contradicted by two newer facts: (a) this probe finds 0
listeners on :25122; (b) `/home/toxic/.shingle/directives.md` (main chat's
consolidated truth) supersedes the :25122 pick — ONE canonical server is
**sovereign-chat v1.2.0 on :25120** (verified live by main chat: 20 agents,
2 rooms, 38 messages at 17:07 MDT; `/v1/*` 401 unauth; MCP stdio +
`POST /v1/mcp`; `/v1/state` same-page surface; "No duplicate servers:
:25122/:25200/:25220 all confirmed dead").

Routing recommendation: if :25120 stands canonical, R1/R2 are already
satisfied there — convert the remaining items (R3–R8) into issues against
sovereign-chat instead of reviving :25122. Do not act on the :25122 premise
without a fresh main-chat verdict.
