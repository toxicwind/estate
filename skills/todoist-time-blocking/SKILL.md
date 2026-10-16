---
name: todoist-time-blocking
description: Plan and review work on a daily and weekly cadence using a small prioritized task slate (inspired by the Ivy Lee method) with Todoist time-blocking. Use when the user asks to "plan my day/tomorrow", "time block my tasks", wants a "nightly review", a "weekly review" or "weekly planning" (Fri afternoon through Sun evening), or wants to clean up incomplete tasks from a finished day or week. Provides plan_day (proposes up to six ordered tasks fitted around existing calendar events and writes them back as timed Todoist tasks), nightly_review (reconciles completions, reschedules or un-dates incomplete items), and weekly_review (light retrospective + stalled-project sweep + per-day soft schedule for the coming week via date-only Todoist dates). Depends on the `todoist-api` skill (td CLI) and the `gws-calendar` MCP tools.
---

# Todoist Time-Blocking

## Method (brief)

Pick **up to six** prioritized tasks for the day, work them sequentially, and reconcile at day's end. Unfinished items roll into the next day's slate. Derived from the Ivy Lee method — see [references/method.md](references/method.md) for origin, what this skill keeps vs. changes, and boundary cases.

## Excluded project: `#Ideas`

The `#Ideas` project contains non-actionable brainstorming items. **Never** surface, propose, or write back tasks from `#Ideas` in any function (`plan_day`, `nightly_review`, `weekly_review`). Filter it out at query time by appending `| ##Ideas` negation or by excluding `projectId` after parsing JSON. Do not include it in stalled-project sweeps, candidate pools, stragglers, or completion counts.

## Core principle: time-block *through* Todoist, not by creating calendar events

Set `--due` with a time and `--duration` on each task:

```bash
td task update <id> --due "YYYY-MM-DD at H:MMam" --duration <Xh|Xm|XhYm>
```

Todoist's Google Calendar integration renders the block on the "Todoist" calendar automatically (sync lag ~1 min). **Do not create parallel events on the Personal or other calendars** for Todoist-tracked work — it causes duplicates and clutter.

## Never assign Todoist priorities

This skill does **not** use Todoist's priority field. Never include `--priority`, `-p1`/`-p2`/`-p3`/`-p4`, or any equivalent flag in `td task add`/`td task update` calls. Never display `[P1]`/`[P2]` tags in proposals. If a task already has a priority set, leave it untouched — don't read it, don't surface it, don't sort by it. Importance is conveyed by slate position and the per-task rationale, not by a stored priority value.

## Required tooling

- `td` CLI — see the `todoist-api` skill for full syntax.
- Google Calendar MCP tools: `gcal_list_calendars`, `gcal_list_events`.

Verify both before proceeding. If the user's Google Calendar does not show a "Todoist" calendar in the list, mention it — time blocks won't render visually until they subscribe.

## Confirmation discipline

Always **present the proposed plan (or review actions) and wait for explicit user approval** before writing to Todoist. Do not batch "propose + execute" into a single turn. This holds even when the user's request sounds like a direct instruction — judgment calls (which tasks make the slate, how to slot them, which stragglers to push) are exactly what the checkpoint is for.

---

## Function: plan_day

To execute the `plan_day` workflow, you MUST read [references/plan-day.md](references/plan-day.md) first.

---

## Function: nightly_review

To execute the `nightly_review` workflow, you MUST read [references/nightly-review.md](references/nightly-review.md) first.

---

## Function: weekly_review

To execute the `weekly_review` workflow, you MUST read [references/weekly-review.md](references/weekly-review.md) first.

---

## Operational notes

- **Six is a ceiling, not a target.** If only three things matter, block three.
- **Time-box only what you'll actually do sequentially.** Don't block email triage or Slack — those absorb residual time.
- **Respect the order.** Lower-numbered tasks come first chronologically when slot shapes allow. If importance and available slot-shape conflict, surface the conflict rather than silently reordering.
- **Durations are honest.** 30-min tasks get 30 min, not padded to look fuller. Underfilled days are a useful signal.
- **One plan surface.** Todoist is the source; the Todoist Google Calendar layer is the view. Nothing else.
- **Cadence.** `plan_day` runs daily (Mon–Fri plus Sun-for-Mon). `nightly_review` runs Mon–Thu. `weekly_review` runs once per week (Fri afternoon through Sun evening) and subsumes Friday's `nightly_review`.

## References

- [references/method.md](references/method.md) — derivation from Ivy Lee, what's kept vs. changed, boundary cases
- [references/heuristics.md](references/heuristics.md) — work window defaults, calendars to query, buffer table, prioritization hierarchy, slot sizing, `td` command formats, timezone handling
- `todoist-api` skill — full `td` CLI reference
