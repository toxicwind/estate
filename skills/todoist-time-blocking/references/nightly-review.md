# Reference: nightly_review Workflow
This document contains the detailed execution steps, output format, and writeback commands for the `nightly_review` workflow of the todoist-time-blocking skill.

## Function: nightly_review

**Default target date:** today (the day ending). Accept an explicit override for retrospective cleanup. **Skip on Fridays** — `weekly_review` subsumes Friday's end-of-day reconciliation.

### Step 1 — Pull the day's slate

```bash
td task list --filter "due: <date> | ##Ideas" --json
```

This returns tasks still due today (excluding `#Ideas`). Tasks the user already moved to another day won't appear here — they'll surface in Step 3.

### Step 2 — Pull completions

```bash
td completed --since <date> --until <date+1> --json
```

**Note:** the output wraps results in `{"results": [...]}`, not a flat array. Parse with `.results[]`.

This may include tasks completed today that **weren't on the original slate** (bonus completions) — surface these as a positive signal.

### Step 3 — Partition into three groups

Compare the day's original slate against both the open-task list (Step 1) and completions (Step 2). Partition into:

- **Completed** — in the completions list. Include bonus completions (tasks not on the original slate) as a separate note.
- **Already moved** — tasks that were on today's slate but no longer appear in either list (the user already rescheduled or moved them during the day). Report these as-is; no action needed.
- **Incomplete** — still due today, not completed. These need decisions.

Report the completion rate against the original slate size (e.g., "2 of 6 completed, 1 already moved, 3 incomplete").

### Step 4 — Propose one action per incomplete task

User confirms per-task:

- **Carry into tomorrow's slate** — set `td task update <id> --due "YYYY-MM-DD"` (date only, no time). The next `plan_day` will re-evaluate the time slot — don't assume today's blocked time still fits tomorrow.
- **Push to a specific future date** — `td task update <id> --due "YYYY-MM-DD"` (date only, no time).
- **Un-date** — `td task update <id> --due "no date"`. Returns to backlog.
- **Delete** — `td task delete <id>`. Only if the task is no longer relevant.

**Flag tasks that have rolled over three or more times** — they likely need to be broken down, reprioritized, or dropped. Surface this for the user's judgment; don't auto-decide.

**Stale times:** Tasks that were time-blocked today retain their start time even when pushed to a new date. When carrying forward, use date-only `--due` to clear the time so `plan_day` can re-slot them fresh.

### Step 5 — Write back after approval

Execute the agreed actions in one batch. Do not act on any subset without a full-slate confirmation.

### Step 6 — Offer the hand-off

Ask whether to run `plan_day` for tomorrow now. If yes, pass forward the "carry into tomorrow" items as pre-selected candidates.
