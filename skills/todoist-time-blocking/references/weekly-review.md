# Reference: weekly_review Workflow
This document contains the detailed execution steps, bucket sizing logic, and writeback commands for the `weekly_review` workflow of the todoist-time-blocking skill.

## Function: weekly_review

**Default target window:** the upcoming Mon–Fri (user's local TZ). When run Fri afternoon through Sun evening, targets next week. Accept explicit overrides.

**Unique vs `plan_day`:** `plan_day` time-blocks a single day. `weekly_review` writes **date-only** `--due "YYYY-MM-DD"` on tasks to produce a **soft schedule** for the week — no times, no durations. Each morning's `plan_day` time-blocks whichever tasks landed on that day (and may pull forward from later days).

**Replaces:** Friday `nightly_review` (subsumed) and Sunday-night prep (same operation).

### Step 1 — Retro (read-only, for calibration)

Pull completions over two windows (excluding `#Ideas` tasks by filtering `projectId` when parsing):

```bash
td completed --since <target-7d> --until <target> --json
td completed --since <target-28d> --until <target> --json
```

> After retrieving, filter out any items whose `project_id` matches `#Ideas` before bucketing or counting.

Group the 28-day set by the weekday of each task's original `due.date` and compute the mean per weekday — the **per-weekday capacity baseline** used in Step 4. `td completed` doesn't expose a completion timestamp; `due.date` is the reliable proxy. Completions with no `due.date` (undated tasks the user finished ad-hoc) aren't bucketed into weekday averages — report their total count separately as ambient work. Recomputed every run; no stored state.

Example jq pipeline for the 7-day view (substitute `-28d` for rolling average):

```bash
td completed --since <target-7d> --until <target> --json | jq '[.results[] | {content, due: .due.date}] | group_by(.due[0:10] // "undated") | map({day: (.[0].due[0:10] // "undated"), count: length, items: [.[].content]})'
```

Report shape:

```
Last 7 days: 18 completions
  Mon 5 / Tue 2 / Wed 6 / Thu 3 / Fri 2

4-week per-weekday average:
  Mon ~4.8 / Tue ~3.1 / Wed ~5.2 / Thu ~2.7 / Fri ~2.4
```

No decisions here — informational for Step 4's bucket sizing. Note any sharp deviation between last week and the 4-week average.

### Step 2 — Stalled-project sweep

Same stalled definition as `plan_day` Step 3.5 (14-day look-back on completions and active-task dates). Surface **every** qualifying project, not just one.

For each, present four actions in a batch:

- **Revive** — pick a concrete next-action task from the project; it joins the candidate pool in Step 3.
- **Defer** — propose creating a "Review <project> direction" task dated ~4 weeks out. The user must explicitly approve the creation; do not auto-create tasks.
- **Archive** — archive the project in Todoist.
- **Skip** — acknowledge; resurfaces next week if still stalled.

Collect marks for all projects in one pass. Writeback happens in Step 5, not mid-flow.

### Step 3 — Build the candidate pool

> **All streams exclude `#Ideas` tasks.** Append `| ##Ideas` to every `td task list` query and filter completions by `projectId` when parsing.

Combine four streams:

**3a. Past-7-day incomplete carry-forwards.** Partition tasks dated in the past 7 days (same logic as `nightly_review` Step 3):
- **Completed** — count only.
- **Already-moved** — count only.
- **Incomplete** — eligible for the coming week's pool. Flag any task rolled over 3+ times for user judgment.

"Past 7 days" is inclusive of the run day itself — when run Fri afternoon through Sun evening, the run-day's still-open tasks count as incomplete carry-forwards (there's no Friday `nightly_review` to catch them otherwise).

**3b. Deadline-driven work.** Tasks with a `deadline` within 14 days of the target start. Each pre-stages to a day that leaves prep buffer before the deadline.

**3c. Revived next-actions** from Step 2 (already excludes `#Ideas` since stalled sweep filters it).

**3d. Currently-dated tasks in the target week.** Query with `| ##Ideas` to exclude brainstorming items.
- Date-only → eligible for rebucketing across days.
- Date+time set → weekly_review does not re-date them (they read as appointment-like commitments at this stage). `plan_day` may still re-time them silently when the pre-set time collides with a target-day calendar event.

Exclude recurring operational tasks (`isRecurring: true`) from all four streams — they belong in residual gaps, handled by Todoist's own recurrence.

### Step 4 — Bucket per day (batched proposal)

Calendar context: call `gcal_list_events` across the target Mon–Fri on the same calendars `plan_day` uses; compute per-day meeting load. Don't surface calendar-vs-calendar overlaps — those are the user's own calendar to reconcile; `weekly_review` just reports meeting density so buckets can size appropriately.

Assign each pool task to a weekday, weighted by:

1. **Deadline (hard):** must land on or before deadline with ≥1 day prep buffer.
2. **Per-weekday capacity baseline** (Step 1): avoid piling onto historically low-throughput days.
3. **Calendar load:** deep work → lighter-meeting days; admin → meeting-heavy days.
4. **Energy/type match:** deep work Mon–Wed by default; admin/lighter items drift to Thu–Fri.
5. **Project clustering:** same-project tasks prefer the same day when timing allows.

Soft target: **3–4 tasks per day.** Exceed when the week genuinely demands it — flag overloaded days clearly in the output so the user can cut or defer during review. No hard cap, no overflow machinery — if the combined pool is unreasonable, that's a signal to pare, not mechanically drop.

**Weekend (Sat/Sun):** include only when a task obviously belongs there (household, shop-hour errands, explicitly-requested leisure). Don't auto-sweep household tasks onto the weekend.

Output format (per-day grouped):

```
## Mon 2026-04-27  (baseline ~4.8 / cal load: 1h)
- Update Session 4 notebook  (proj: NCSU, deadline Tue)
  └─ deadline pressure; deep work needs unbroken morning
- Review K's draft  (proj: BSEM)
  └─ blocking K

## Tue 2026-04-28  (baseline ~3.1 / cal load: 3h — heavy)
- Bike tune-up errand
  └─ shop hours; fits between afternoon meetings
- Email triage
  └─ admin fits a fragmented day

## Wed 2026-04-29  (baseline ~5.2 / cal load: 1.5h)
...

## Sat 2026-05-02  (household only)
- Replace porch light
  └─ obvious household; not a weekday item
```

**Unscheduled stragglers** from 3a that didn't make any bucket: show below with per-task actions — un-date / push beyond target week / delete.

### Step 5 — Approval and writeback

Present the full picture in one view: retro stats (read-only) + stalled-project action grid + per-day buckets + unscheduled straggler actions. Wait for explicit approval of the whole package before any writes.

**All straggler actions must be resolved before any writes.** If the user approves the bucketed schedule without addressing unscheduled stragglers, re-prompt explicitly.

On approval, execute in one batch:

```bash
# Bucketed tasks (date-only, no time):
td task update <id> --due "YYYY-MM-DD"

# Stalled deferrals (ONLY if user explicitly approved creation):
td task add "Review <project> direction" --due "YYYY-MM-DD" -p "<project>"

# Stalled archives:
td project archive <id>

# Un-dated stragglers:
td task update <id> --due "no date"

# Deleted stragglers:
td task delete <id>
```

Exact command flags vary — check the `todoist-api` skill for current `td` syntax.

### Step 6 — Verify

```bash
td task list --filter "due after: <target-1d> & due before: <target+7d>" --json \
  | jq '[.results[] | {content, due: .due.date // .due.datetime}] | group_by(.due) | map({day: .[0].due, count: length})'
```

Expected: each target weekday shows the approved bucket size, and entries have a `date` field (not `datetime`) — confirms they're ready for `plan_day` to time-block each morning.

### Step 7 — Hand-off

Offer to run `plan_day` for the upcoming Monday. If yes, pass Monday's bucket forward as pre-selected candidates.
