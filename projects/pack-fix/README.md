# pack-fix — hesitance hunt

Chris's standing doctrine: maximal autonomous execution. **Asking Chris to do
something decidable is a bug; hedging is a bug.** Act-then-report is the
default. This project hunts every place where agent instructions encode
hesitance — prompts that ask Chris to act, hedge, or refuse to act — and fixes
the root cause.

Lane (per 2026-09-20 lane carve): **hesitance fixes, exclusive.** Orphaned
files found during the hunt go to `repo-integrator-max` via fleet — not
integrated here. The `progress-watchdog` body rewrite is this lane's;
cadence/failure-escalation on that watchdog stays with `runner-watch`.

- [hesitance-patterns.md](hesitance-patterns.md) — the anti-pattern catalog:
  each pattern, where it lived, how it was fixed.
- [../ops/bin/hesitance-scan.sh](../ops/bin/hesitance-scan.sh) — the permanent
  guard (per Chris's purge-max order, fleet seq 11264: every workstream ships
  its runnable in `projects/ops/bin`). Classifies every hit as
  ROT / LEGITIMATE / QUOTE / ANTI; exit 1 only on genuine ROT.
  The script is the deliverable; running it once was just proof.

## Run the guard

On yote (sovereign repo skills, cron prompt files, goal crons):

```bash
/home/toxic/sovereign/projects/ops/bin/hesitance-scan.sh
```

On hatch (cron bodies, goal crons, skills):

```bash
~/workspace/bin/yote-get projects/ops/bin/hesitance-scan.sh /tmp/hesitance-scan.sh
bash /tmp/hesitance-scan.sh ~/workspace/cron.d ~/workspace/goals/*/crons ~/workspace/skills
```

Also scan recent fleet traffic for hesitance rot:

```bash
projects/ops/bin/hesitance-scan.sh --fleet -n 50
```

Allowlist a single line only, narrowly, with a reason:

```md
<!-- hesitance-allow: fail-fast here because the data source is genuinely unreadable during outages -->
```

## What it enforces

The four anti-patterns from the catalog (plus narrowly documented
allowlist exceptions for legitimate fail-fast/security phrasing):

| Pattern | Meaning |
|---|---|
| P1-investigate-refusal | "Do not investigate further, do not retry, do not run anything else" — the designed-in dead end |
| P1-blanket-inaction | blanket "do not retry / do not run anything else" with no path to a durable fix |
| P3-approval-gate | "awaiting approval", "wait for approval", "ask Chris" — operational decisions Chris never needs to make |
| P4-deferral | "defer to Chris", "nothing invented without him" — avoidable judgment-call hesitance |

Hits are classified, not just flagged:

- **ROT** — genuine hesitance rot. Fix at the root (rewrite the brief/doc).
- **LEGITIMATE** — genuinely needs Chris: money, credentials, irreversible
  external sends, or "only Chris can do X" stated once, plainly.
- **QUOTE** — historical quote of the old bad brief (scar documentation in
  SOUL.md/IDENTITY.md/memory), not a live instruction.
- **ANTI** — the line explicitly prohibits the pattern ("asking Chris is a
  bug"). Anti-hesitance doctrine, not rot.

Legitimate narrow human gates stay: provider funding/authorization only Chris
can grant, one-probe/no-loop fail-fast against hammering, skipping a check when
its data source is genuinely unreadable, anti-exfiltration rules. Those are
allowlisted with a reason, not rewritten as action.

## Docs

- Repo master README: [../../README.md](../../README.md)
- Estate map, active crews, standing rules (REQUIRED READING):
  [docs/fleet-knowledgebase.md](../../docs/fleet-knowledgebase.md)
