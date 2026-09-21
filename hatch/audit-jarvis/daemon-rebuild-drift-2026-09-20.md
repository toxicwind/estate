# Daemon rebuild drift note — 2026-09-20 ~21:03 MDT

The host re-provisioned the runtime cell between the audit (build
`c9ee57f462d`, audited ~20:10 MDT) and this check (21:42 MDT):

- New binary: `/opt/hatch/bin/hatch` = `hatch 0.1.0 (82d6744eed2)`,
  sha256 `43648395e252ab24…` (old: `54911dd3…`).
- Live daemon PID 67 restarted ~21:03 MDT (etime 39:19 at 21:42).
- `jarvis-static` re-run against the new binary → `audit/rebuild-82d6744/`.

## What changed

**Compaction subsystem: UNCHANGED.** Eager stem counts identical
(`eager_background_compaction`: 12, `adopted_…`: 8, `persisted_…`: 8),
transport evidence byte-identical (WS-over-unix-socket), log-message corpus
180 → 179 lines (one glue-boundary artifact). All B1–B19 claims still hold.

**New in this build: a `tool_dispatch_heartbeat` tool.** Absent from every
artifact generated from the old binary. Observed in the new binary (2
occurrences):

- Tool-registry context: `…stateful_artifact_sharing` `tool_dispatch_heartbeat`
  `dispatch_heartbeat` alongside `list_targets`, `launch`, `deadline`, `lock`
  — i.e. a first-class tool name.
- Failure log messages: `tool dispatch failed; returning failure output`
  and `tool dispatch failed; persisting failure output`.

Interpretation (inference, not proven): the runtime gained an internal
dispatch path with heartbeat semantics — plausibly the mechanism behind
long-running tool calls staying alive across the 39-minute daemon lifetime.
Whether this relates to the SIGSTOP/agent-lifecycle work is unknown.

## Caveat

The old binary is gone (replaced in place), so "absent from old binary" rests
on the old audit's generated artifacts, not a re-scan. The old extraction was
heuristic in the same way, so a missed token in the old pass is possible but
unlikely for a registry-listed tool name — it would have appeared in the
model-routes/token sweeps.
