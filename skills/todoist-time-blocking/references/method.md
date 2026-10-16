# Method — Origin and Adaptations

## Origin: the Ivy Lee method

In 1918, productivity consultant Ivy Lee gave Charles M. Schwab (president of Bethlehem Steel) a deceptively simple routine. Schwab reportedly sent Lee a $25,000 check some months later. The rules:

1. At the end of each workday, write down the **six most important things** to accomplish tomorrow. No more than six.
2. **Prioritize** the six in true order of importance.
3. The next day, concentrate on the first task. Work until finished before moving to the second.
4. Treat each task the same way. At day's end, move unfinished items to a new list of six for the next day.
5. Repeat every working day.

Reference: https://www.todoist.com/productivity-methods/ivy-lee-method

## What this skill keeps

- **Small ordered list.** The ceiling of six exists because small lists force real prioritization.
- **Sequential execution.** Work task #1 to completion before starting #2. The morning brain doesn't re-litigate priorities.
- **Nightly roll-over.** Unfinished items become candidates for the next day's slate, reconciled in `nightly_review`.

## What this skill changes

- **"Up to six" is a ceiling, not a target.** Strict Ivy Lee says exactly six. We accept fewer — three real priorities beats six with filler.
- **Explicit time-blocks.** Classical Ivy Lee is list-based. This skill adds a start time and duration for each slate item, via Todoist's `--due` + `--duration` fields, so the Todoist Google Calendar surface renders the day visually.
- **Calendar-aware slotting.** The slate is fitted around fixed commitments already on the user's calendars, with realistic buffers — not planned in isolation.
- **Separation of `plan_day` and `nightly_review` as named operations.** Gives the two halves of the loop distinct, repeatable workflows.

## Why a ceiling rather than exactly six

- **Forces prioritization downward as well as upward.** Some days genuinely have three priorities. Padding to six invents work and dilutes focus.
- **Matches attentional budget.** A realistic workday rarely produces more than six substantive completions; trying to fit more is aspirational arithmetic.
- **Empty slots are data.** A short slate signals either light real workload or an uncaptured backlog — both worth noticing.

## Why strict order still matters

Sequential execution prevents context-switching. If task #3 turns out more urgent than #1 by the morning, the ordering was wrong the night before — surface that pattern in the next `nightly_review` rather than quietly re-sorting mid-day.

## Boundary cases

- **Fewer than six reasonable tasks.** Fine. Don't pad.
- **A task is too large for a day.** Break it into a concrete day-sized next action. The item on the slate should be completable in one sitting.
- **Dependencies on others** (waiting on review, waiting on a reply). These shouldn't occupy a slate slot — they're backlog, not day-plan.
- **Recurring operational work** (email, standups, slack triage). Treat as background load during gaps, not as slate slots.
- **Pure leisure items** (reading, hobbies). Include only if the user explicitly wants them on the day-plan. Default: leave un-dated or weekend-dated.
- **A task that has rolled over three or more days.** Surface it — likely needs to be broken down, reprioritized lower, or dropped entirely.

## Interaction with time-blocking

The time-blocking overlay is optional-but-default. If the user wants a plain ordered list with no times, skip `--duration` and use `--due "<YYYY-MM-DD>"` only. The slate discipline still applies; the Todoist calendar just won't render blocks.

## Weekly cadence

The daily loop (`plan_day` → `nightly_review` → `plan_day` …) handles day-level execution. The weekly loop (`weekly_review`, run Fri afternoon through Sun evening) handles two things the daily loop can't:

1. **Calibration.** A rolling 4-week per-weekday completion average — how much actually gets done per weekday — so next week's per-day bucket sizing matches real capacity rather than aspiration.
2. **Stalled work.** Projects that haven't moved in 14+ days. `plan_day` nudges on one stalled project per day; `weekly_review` sweeps all qualifying projects and forces a per-project decision (revive / defer / archive / skip).

Output: **date-only** `--due "YYYY-MM-DD"` on tasks for the coming Mon–Fri (plus optional Sat/Sun for obvious household items). No times, no durations — those land when `plan_day` runs each morning. This preserves the "one plan surface" rule: Todoist's Google Calendar layer still only shows what `plan_day` has time-blocked.

Friday `nightly_review` is skipped — `weekly_review` subsumes its end-of-day reconciliation via the past-7-day incomplete-task sweep.
