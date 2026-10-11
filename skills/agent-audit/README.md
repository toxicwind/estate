# agent-audit {badges}

<!-- badges: start -->
<a href="https://github.com/toxicwind/estate">
  <img src="https://img.shields.io/badge/github-toxicwind/sovereign--projects-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub repo">
</a>
<a href="https://muse.db">
  <img src="https://img.shields.io/badge/postgresql-muse.db-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
</a>
<!-- badges: end -->

## First-class auditing and debugging over Muse subagent execution.

**What**: CLI tool for auditing database-backed agent records — agent executions, individual agent debug, failure taxonomy, and topology queries. Read-only by construction; queries are bounded SELECT statements.

**Why**: The tool you reach for at 2am when agents are failing — not ad-hoc archaeology. Provides first-class views into agent execution records without inventing data.

**Who**: Query library + formatter. Cannot reach PostgreSQL from the cell (no client, no DSN, no local files — verified). Runs end-to-end where `psql` and `AGENT_AUDIT_DSN`/`DATABASE_URL` exist; otherwise emits SQL for manual execution.

## Feature bullets

- **Agent Executions View**: `agent-audit agents [--status completed|running|shutdown|failed|interrupted] [--since 24h] [--limit 50]` — lists id, status, kind, depth, model, age, terminal state, task summary
- **Individual Agent Debug**: `agent-audit <id>` — debug one agent: header (status, parent, spawn/terminal state, task, final response), full tool-call timeline (each call, status, raw duration, result preview), and monitor decisions
- **Failure Taxonomy**: `agent-audit failures [--since 24h]` — error signatures grouped with counts and share (`wrong-box-path`, `shell-quoting-eof`, `session-metadata-timeout`, `bridge-502`, `other-error`), per-tool breakdown, hourly time clustering, agent/spawn status distributions
- **Topology Queries**: `agent-audit topology` — where agents actually run: by kind/status/model/depth, spawn-metadata emptiness, session channels, location-context samples, plus verified ground truth
- **Synthetic Demo**: `agent-audit demo` — renders every view from labeled SYNTHETIC data (no DB)
- **Selftest**: `agent-audit selftest` — offline suite validates every shipped query (single SELECT, muse.db allowlist, CTE naming), the redactor, and all renderers
- **SQL Export**: `agent-audit failures --since 24h --sql > aa.sql` — emit exact SQL for the view, run through `muse.db` tool, then render results

## Quick start

```bash
# 1. Emit the exact SQL for the view
agent-audit failures --since 24h --sql > aa.sql

# 2. Run each statement through the muse.db tool, saving results
#    (a result object may carry {"name": "<query-name>"}; order doesn't matter)
# q1.json, q2.json, q3.json, q4.json, q5.json

# 3. Render
agent-audit failures --since 24h --render q1.json q2.json q3.json q4.json q5.json
```

## Config / optional services

- **PostgreSQL via muse.db**: All agent records live in PostgreSQL behind the daemon-native `muse.db` tool surface (schema: `/opt/hatch/skills/muse_db/references/schema.md`)
- **Environment**: `--since` accepts `30m`, `24h`, `7d`, `1w`, ISO-8601, or epoch
- **Workspace scratch**: Intermediates belong in `~/workspace/scratch/agent-audit` (not `/tmp`, which is a 512M tmpfs with a janitor)

## Dev / contributing

- Add a query builder in the "Query library" section returning `(name, sql)` pairs, a renderer, and register both in `VIEW_BUILDERS`/`RENDERERS`
- Rules: single SELECT, schema-qualified tables, only functions/casts on the muse.db allowlist, unique output aliases, CTE names start with `hatch_cte_`
- Then run `agent-audit selftest` — it must stay green
- Read-only: every shipped query is one bounded `SELECT` (selftest-enforced)

## License + security

- **License**: Open Claw source (see `skill.toml`)
- **Security**: Read-only queries; never invents data — missing table/field/result prints "no result supplied" or "genuine gap" with evidence (row counts, timestamps). Redacts credential-shaped values (`token=`/`password:`/`Bearer`/keys) but never Agent IDs (uuids).