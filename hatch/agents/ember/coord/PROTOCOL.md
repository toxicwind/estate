# Fleet coordination substrate — PROTOCOL.md

Lives at `/home/toxic/.shingle/coord/` on awrawr-pc (the database holder: every
agent class with bridge access can reach it; local processes see it as plain files).

## Layout

- `PROTOCOL.md` — this file.
- `lanes/<lane>.json` — one JSON doc per active lane of work.
  Schema: `{"lane": str, "owner": str, "status": "active|done|blocked",
  "updated": epoch, "summary": str, "next": str}`.
- `claims/<item>.json` — claim files for work items (avoid two agents doing the
  same job). Schema: `{"item": str, "claimed_by": str, "claimed_at": epoch,
  "ttl_s": int, "note": str}`. A claim is live if `claimed_at + ttl_s > now`.
- `log.jsonl` — append-only event log. One JSON object per line:
  `{"ts": epoch, "actor": str, "event": str, "detail": str}`.

## Rules

1. Append-only for `log.jsonl` — never rewrite history.
2. Claim before starting shared work; release (delete claim file) when done.
3. Lanes are per-agent working state, not a chat — no cross-contamination:
   an agent writes only its own lane file.
4. Readers poll; no push. Poll interval >= 60s unless the lane says otherwise.
5. Additive only — never delete another actor's lane or log lines.

## Who can read/write what (verified 2026-09-16)

- Cell agents (Hatch main/side chats, workflow children): WRITE via the
  awrawr-mcp bridge (`bin/exec.py --argv ...`, `bin/xfer.py put`); READ via
  `bin/exec.py` / `bin/xfer.py get`.
- awrawr-pc local processes (pitchfork daemons, fleet job workers submitted
  via `bin/agent.py submit`): direct filesystem read/write.
- Browser tasks / web research agents: NO shell, NO bridge — read-only at
  best via relayed reports; cannot write here directly.
- Cron/scheduled jobs: run as the cell agent — same read/write as cell agents.
