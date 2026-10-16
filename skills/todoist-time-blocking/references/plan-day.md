# Reference: plan_day Workflow
This document contains the detailed execution steps, templates, and verification commands for the `plan_day` workflow of the todoist-time-blocking skill.

## Function: plan_day

**Default target date:** tomorrow (user's local TZ). Accept an explicit date override.

### Step 0 — Verify calendar access

Before proceeding, confirm calendar tools are reachable and return non-empty results for the target date. If calendar access fails or returns zero events across all calendars, **flag this immediately** — proceeding without calendar context has caused repeated scheduling conflicts in the past. Do not assume or guess at the user's schedule.

### Step 1 — Gather fixed commitments

Call `gcal_list_calendars`, then `gcal_list_events` on every calendar that represents real commitments. Include owner/reader calendars for personal, family, work, sports schedules, and travel feeds. **Exclude** holiday calendars and the Todoist calendar itself (its events are the output of this skill; counting them would be circular). Skip resource calendars.

Use the target date as `timeMin` / `timeMax` in the user's local timezone.

Record each event's: `summary`, `start`, `end`, `location` (for buffer sizing), and **`transparency`**.

**Transparency filter:** Only treat events with `transparency` = `opaque` (or unset, which defaults to opaque) as fixed busy blocks. Events with `transparency` = `transparent` are marked "free" in Google Calendar and **must not** be treated as time-blocked commitments — they're informational only and don't reduce available work time. Surface them in the proposal table as context (e.g., italics with a "free" label) so the user sees them, but don't slot tasks around them.

### Step 2 — Establish the work window

Default **08:00–16:00 local**, minus a 30-min lunch flex between 12:00 and 13:00. Ask if the date looks unusual (weekend, holiday, travel day per the Travel calendar).

The work window governs only the sequential deep-work portion of the day. Items the user designates as evening/household (shopping, personal errands, light decisions) can be placed outside the work window with an explicit evening time — they don't compete for work-window slots and don't count against the slate ceiling.

### Step 3 — Read candidate tasks

```bash
td task list --filter "(due before: <end-of-week+1 day>) | no date | ##Ideas" --json
```

The query extends through end-of-week (not just the target day) to surface tasks soft-scheduled by a prior `weekly_review` — they're eligible to pull forward when the target has capacity.

> **Filter note:** `##Ideas` excludes the Ideas project per the Excluded Project rule above.

Partition:
- **Target-day candidates:** dated on or before the target (overdue items roll into candidacy).
- **Rest-of-week bucket:** dated to later days this week — count by day, eligible to pull forward when rationale supports it.
- **Undated:** near deadlines or unblocking someone else.
- **Deadline-driven:** `deadline` within ~3 days of the target.

Filter out recurring operational tasks (`isRecurring: true` in the due object) from the slate — they belong in residual gaps, not prime slots.

### Step 3.5 — Surface one stalled-project nudge

A project is **stalled** when both hold (14-day look-back):
- No tasks completed in the project in the last 14 days.
- No active tasks in the project dated within the last 14 days or the next few days.

(Task modification timestamps aren't exposed by `td task list`, so the stalled check relies on completion history plus active-task dates.)

Identify candidate projects via `td project list --json`, then inspect each: `td task list --filter "##<project name>" --json` for active-task `due` dates, and scan `td completed --since <target-14d> --until <target+1d>` filtered by `projectId` for recent completions. If multiple projects qualify, pick the one stalled longest.

Select **one** concrete next-action task from that project as the nudge — prefer tasks with clear verbs and small scope over vague headings. Mark it distinctly in the proposal; it's not counted toward the six-task ceiling unless the user accepts.

If no project qualifies, skip this step silently.

### Step 4 — Propose up to six, ordered

Rank by true importance: deadline pressure, whether the task unblocks someone else, reversibility cost, concrete-next-action clarity. Fewer than six is fine — do not pad. See [references/heuristics.md](references/heuristics.md) for task-type prioritization.

The stalled-project nudge (if any) is proposed **separately** from the main slate — user accepts or rejects it. If accepted, it joins the slate and gets time-blocked; if rejected, take no action on it (don't re-date it).

**Rest-of-week buckets.** If the query returned tasks dated to later days this week (typically from `weekly_review`), show a one-line summary in the proposal: `Rest-of-week: Tue=4, Wed=3, Thu=2, Fri=3`. If the target day has headroom and a later day is overweight, **propose** pulling one task forward — surface the rationale (overloaded source day, deadline interaction, cognitive fit) and let the user accept or reject. Pulled tasks get re-dated to the target and time-blocked like any other slate item.

### Step 5 — Fit blocks around fixed events

Compute free windows = work window − fixed events (opaque only) − buffers. Default buffers: **10–15 min** around remote meetings, **15–30 min** around in-person events (gym, errand, off-site). Give deep work the longest unbroken window, usually morning. Avoid splitting a deep-work task across a fixed event.

Additional rules when fitting:

- **Transparent (free) events are not fixed blocks.** They appear in the calendar but don't consume scheduling capacity. Treat them as context only.

- **Recurring tasks as fixed load.** Recurring operational tasks dated on the target day (filtered from the slate in Step 3) still occupy time on the Todoist calendar. Treat them as additional fixed blocks when computing free windows — same as calendar events.
- **Pre-set task times yield to calendar events.** If a slate task carries a pre-set time (often inherited from a prior `weekly_review` or manual dating) and that time overlaps a fixed calendar event, re-time the task silently to the nearest suitable free window. Do not flag as a conflict — calendar events always win.
- **No calendar-vs-calendar conflict flags.** If two fixed calendar events overlap, that's the user's calendar to reconcile, not `plan_day`'s. Just slot tasks around whatever calendar time remains free.

Present the **full day's agenda** as a single chronological table that interleaves proposed Todoist blocks with the fixed calendar events from Step 1 — the user needs to see the whole day to approve the decisions. Mark fixed events clearly (italics, source label, or both) so there's no ambiguity about what the user is approving vs. what's already committed.

**Before presenting the proposal, run a reality check:**

- Confirm every proposed block's start+end time does NOT overlap any opaque calendar event.
- Confirm every proposed block fits within the declared work window (unless explicitly marked as evening).
- Confirm total deep-work blocks ≤ 2 per day.
- If any check fails, fix silently before presenting — never surface a conflict to the user.

| Time | Item | Duration | Source | Why here |
|---|---|---|---|---|
| 08:00 | Update Session 4 notebook | 2h45m | Todoist (proposed, #1) | longest morning block; deadline tomorrow |
| 11:00 | *Strength 50 class* | 50m | Personal (fixed) | — |
| 11:50 | Bring bikes in to be tuned | 30m | Todoist (proposed, #2) | errand, post-gym, on the way back |
| 12:20 | *(lunch / buffer)* | 30m | — | — |
| 12:50 | Read Devin's soccer book | 30m | Todoist (proposed, #3) | light post-lunch slot |
| … | … | … | … | … |

Include gaps/buffers as their own rows when material (>15 min) so the day reads end-to-end. Any straggler actions from Step 6 go in a separate short list under the table, not in it.

### Step 6 — Identify stragglers

Tasks already dated on the target day that **aren't** in the chosen slate. For each, propose a **default action** (typically push 1–3 days forward or un-date) and present it as the recommendation. The user may override per straggler.

**Do not bulk-decide, and do not allow unresolved stragglers.** If the user approves the slate without addressing every straggler, re-prompt explicitly: “You still have N stragglers — pick an action for each before I write anything back.”

### Step 7 — Wait for approval

Output the full proposal (slate + straggler actions + stalled-project nudge if any) and stop. Accept edits: reordering, swapping tasks in/out, adjusting times, accepting/rejecting the nudge.

**No writeback may proceed until every straggler has a chosen action.** Leaving a task date-only on the target day is not permitted — it creates a ghost entry with no time block.

### Step 8 — Write back

```bash
# Each chosen task (time + duration):
td task update <id> --due "YYYY-MM-DD at H:MMam" --duration <Xh|XhYm|Xm>

# Stragglers moved to another day (date only; user can time-block later):
td task update <id> --due "YYYY-MM-DD"

# Stragglers un-dated:
td task update <id> --due "no date"
```

Known-good `--due` formats: `"today at 8:00am"`, `"tomorrow at 1:20pm"`, `"2026-04-16 at 8:00am"`, `"Apr 16 at 8:00am"`. Prefer explicit `YYYY-MM-DD at H:MMam/pm` to avoid parser ambiguity.

### Step 9 — Verify

> **CRITICAL:** Use `--ndjson` or `--full` for verification. The default `--json` flag truncates `due.datetime` to a plain date, making it impossible to confirm that time-blocking actually stuck.

```bash
# Verify: every task due the target day is time-blocked (datetime + duration)
td task list --filter "due: YYYY-MM-DD" --ndjson \
  | jq 'select((.due.datetime // .due.date | test("T") | not) or .duration == null) | {content, due: .due, duration}'
```

Expected: **no output**. Any output means unresolved stragglers remain — abort writeback and return to Step 6.

Then verify the slate itself:
```bash
td task list --filter "due: YYYY-MM-DD" --ndjson \
  | jq '{content, due: .due, duration}'
```

Expected: exactly the chosen slate, each with a `due` containing a `datetime` field (`T` present) and a `duration`. Tell the user to refresh Google Calendar in ~1 minute if blocks aren't visible.
