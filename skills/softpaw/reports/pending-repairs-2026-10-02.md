# Pending cron-body repairs — 2026-10-02 (classifier-sweep run)

`cron.update` is unusable from a scheduled execution in the current runtime:
every call fails with `resolve cron chat owner: execution has no durable
presentation chat owner`, including no-op field updates on disabled jobs
(verified on `duet-watchdog` enabled=false → same error, no state changed).
This is a platform/execution-context limitation, not a body-validation issue.

The repairs below are staged and verified — apply from an execution with a
durable presentation chat owner (e.g. Main chat) using `cron.update`.

## 1. standing-guard — prepend V2 directive (missing)

- Job id: `standing-guard` (enabled, interval@15m). Confirmed live via
  `cron.view`; saved body lacks the V2 marker. Mirror already repaired:
  `/home/hatch/workspace/cron.d/minutely/standing-guard__interval@15m.md`
  carries the directive exactly once (launch-audit --repair, this run).
- Body to apply (directive from `~/workspace/system/task-directive.md`,
  verbatim, + blank line + the existing saved body):
- Exact prepared body (from repair-plan.json) — USE THE BODY ONLY, not the
  frontmatter block the audit tool embedded in the plan file:
  `/home/hatch/workspace/skills/classifier-project/reports/repair-plan.json`
  → plan[0].body, lines after the first `\n\n` + directive (the directive is
  the first paragraph; the rest of the body is the unchanged saved body).
- Verify after: `cron.view standing-guard` — marker appears exactly once at
  the top.

## History (2026-10-02 run)

- File repairs applied directly (no cron needed):
  - `~/workspace/skills/classifier-project/SKILL.md` — removed two literal
    quotes of the old v1 directive marker (shape `old-directive-marker`);
    replaced with shape-ID references to `src/triggers.ts`.
  - `~/workspace/skills/tau-fork-pinning/SKILL.md` — `sudo chattr +i` →
    `chattr +i` (shape `sudo-passwordless`; administrative commands run
    directly, pre-authenticated, intentional per Chris).
- Intentionally untouched:
  - `_archive/*` mirrors (dead snapshots, no live schedules).
  - `cron.d/runonce/*` probes (diagnostic probes excluded from repair;
    one-shots already fired). `wave4-529-retry` (archived runonce) still
    carries `zero-approval` phrasing — flagged, left as historical record.
  - `classifier-project/SKILL.md` lines 26-28 — shape-ID references
    (`yolo`, `sudo-passwordless`, `asleep-act`), explicitly permitted by the
    sweep body ("referenced by shape ID").
  - System jobs (feed-pulse-*, deterministic-doctor, profile-image) —
    never touched.
- Marker check: all live non-system tasks carry the V2 marker exactly once,
  except standing-guard (pending above).
