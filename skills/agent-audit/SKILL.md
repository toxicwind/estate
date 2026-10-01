---
name: agent-audit
description: >
  First-class auditing and debugging over Muse subagent execution. The tool for failing agents, not ad-hoc archaeology. Triggers on: agent audit, subagent debugging, failing agents.
---

# agent-audit skill

First-class auditing and debugging over Muse subagent execution. This is the
tool you reach for at 2am when agents are failing — not ad-hoc archaeology.

## What it is

`~/workspace/bin/agent-audit` — stdlib-only Python CLI, read-only by
construction. It audits the database-backed agent records:

- `agent-audit agents [--status completed|running|shutdown|failed|interrupted] [--since 24h] [--limit 50]`
  — list agent executions: id, status, kind, depth, model, age, terminal state, task summary.
- `agent-audit agent <id>` — debug one agent: header (status, parent, spawn/terminal
  state, task, final response), full tool-call timeline (each call, status, raw
  duration, result preview), and monitor decisions.
- `agent-audit failures [--since 24h]` — failure taxonomy: error signatures grouped
  with counts and share (`wrong-box-path`, `shell-quoting-eof`,
  `session-metadata-timeout`, `bridge-502`, `other-error`), per-tool breakdown,
  hourly time clustering, agent/spawn status distributions.
- `agent-audit topology` — where agents actually run, from the records: by
  kind/status/model/depth, spawn-metadata emptiness, session channels, location-
  context samples, plus the verified ground truth (no runner/host/lane fields;
  agents execute runtime-side; the cell sees only dispatched tool calls).
- `agent-audit demo` — renders every view from labeled SYNTHETIC data (no DB).
- `agent-audit selftest` — offline suite: validates every shipped query
  (single SELECT, muse.db allowlist, CTE naming), the redactor, and all renderers.
- `agent-audit watch` — intentionally unavailable: no local DB files/WAL exist to
  watch event-driven; there is no fake live mode.

`--since` accepts `30m`, `24h`, `7d`, `1w`, ISO-8601, or epoch.

## Data source (ground truth, verified 2026-09-20)

- There are NO Muse sqlite/db files on the cell. ALL agent records live in
  PostgreSQL behind the daemon-native `muse.db` tool surface
  (schema: `/opt/hatch/skills/muse_db/references/schema.md`).
- Tool-call telemetry lives in `agent.subagent_progress_tool_events`;
  `runtime.tool_calls` is EMPTY (0 rows) — do not query it for this.
- Records carry NO runner/host/lane fields (`spawn_metadata_json` is empty;
  `originating_location_context_json` is only client IP/timezone).
- Local `ps` on the cell shows zero `agent-*` processes: agents execute
  runtime-side; their tool calls dispatch into the local hatch-execd tree.

## The honest loop (how to run it)

The CLI cannot reach PostgreSQL from the cell (no client, no DSN, no local
files — verified). It is a query library + formatter. Where `psql` and
`AGENT_AUDIT_DSN`/`DATABASE_URL` exist, `agent-audit <view>` runs end-to-end.
Otherwise:

```bash
# Worked example uses a workspace scratch dir, NOT /tmp — the cell's /tmp is a
# 512M tmpfs with a janitor that deletes stale entries, so nothing parked there
# is durable. Big intermediates belong in ~/workspace/scratch.
mkdir -p ~/workspace/scratch/agent-audit && cd ~/workspace/scratch/agent-audit
# 1. emit the exact SQL for the view
agent-audit failures --since 24h --sql > aa.sql
# 2. run each "-- agent-audit-query: <name>" statement through the muse.db tool,
#    saving each result JSON as q1.json, q2.json, ... in listed order
#    (a result object may instead carry {"name": "<query-name>"}; order then doesn't matter)
# 3. render
agent-audit failures --since 24h --render q1.json q2.json q3.json q4.json q5.json
# --render with no files reads one result object (or NDJSON) from stdin
# (avoids intermediate files entirely)
```

Query counts per view: `agents` 1, `agent` 3, `failures` 5, `topology` 6.

## Guarantees

- Read-only: every shipped query is one bounded `SELECT` (selftest-enforced).
- Never invents: a missing table/field/result prints "no result supplied" or
  "genuine gap", with the evidence (row counts, timestamps) it does have.
- Redacts credential-shaped values (`token=`/`password:`/`Bearer`/keys) in output.
  Agent ids (uuids) are never redacted.
- User input (`<id>`, `--status`) is validated before touching SQL templates.

## Known failure signatures (first-class views, from real data)

1. `wrong-box-path` — the #1 cluster: `/home/toxic/...` (yote) paths executed on
   the cell. Fix direction: route the command through the yote bridge.
2. `shell-quoting-eof` — malformed quoting / unexpected EOF in generated shell.
3. `session-metadata-timeout` — runtime infra: `timed out after 15s registering
   session metadata`.
4. `bridge-502` — yote bridge 502 / exec-ws failures.

## Extending it

Add a query builder in the "Query library" section returning `(name, sql)` pairs,
a renderer, and register both in `VIEW_BUILDERS`/`RENDERERS`. Rules: single
SELECT, schema-qualified tables, only functions/casts on the muse.db allowlist,
unique output aliases, CTE names start with `hatch_cte_`. Then run
`agent-audit selftest` — it must stay green.