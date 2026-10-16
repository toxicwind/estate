# Time-Blocking Heuristics

> **Excluded project:** `#Ideas` contains brainstorming items, not actionable tasks. Never include `#Ideas` tasks in slate proposals, reviews, completion counts, stalled-project sweeps, or straggler lists. Filter at query time with `| ##Ideas` and by `projectId` when parsing JSON.

## Default work window

- **08:00–16:00 local** unless the user specifies otherwise.
- **Lunch**: 30 minutes, flexible between 12:00 and 13:00. Hold it open, or place it just after a fixed commitment (e.g., a gym class).
- Ask if the target date is a weekend, a Travel-calendar day, or a holiday — those override the default.

## Calendars to query as "busy"

Discover at runtime via `gcal_list_calendars`. Include these by default when computing fixed commitments:

- The primary/Personal calendar (owner access)
- Family, work, and team calendars (owner/writer access)
- Subscribed team/travel calendars (reader access) that represent real commitments — e.g., ice hockey schedules, Kayak "Travel" feed

Exclude:

- Holiday calendars (e.g., "Holidays in United States") — informational, not blocking
- The Todoist calendar itself — it's the *output* of this skill; counting it would double-book
- Resource calendars (`isResource: true`)

## Calendar event transparency

When fetching events, check the `transparency` field:

- **`opaque`** (or field absent) = **busy**. Treat as a fixed commitment that blocks scheduling time.
- **`transparent`** = **free** (Google Calendar shows as "Free"). These are informational only — **do not** treat them as scheduling constraints. Show them in the proposal for context but don't slot tasks around them.

Always request full event details to surface the `transparency` field — it's not included in minimal/summary output.

## Buffers around fixed events

| Event type | Buffer before | Buffer after |
|---|---|---|
| In-person off-site (gym, errand, medical, coffee) | 15–30 min (travel) | 15–30 min (travel) |
| Remote meeting / call | 5 min | 5 min |
| Lunch out | 10 min | 10 min |
| Back-to-back remote meetings | 0 min between | — |

Tune with the event's `location` field: no location → probably remote → small buffer; explicit address → travel buffer.

## Task-type ranking

When picking the slate and ordering it, weight by this hierarchy (top = higher importance). This ranking is for in-the-moment slate selection only — never write it back to Todoist's priority field, which this skill does not use.

1. **Deadline-bound work** — tasks with a `deadline` date within ~3 days. Surface any deadline-slip risk.
2. **Blocking work** — tasks others are waiting on. Look for labels like "Waiting", "@review", or recent comment threads.
3. **Deep work** — coding, writing, modeling, design. Give these the longest unbroken block (usually morning).
4. **Fast admin** (5–15 min) — slot into residual gaps; do not give prime time.
5. **Errands / personal logistics** — include only if they must happen that specific day (appointment, shop hours).
6. **Reading / leisure** — include only if explicitly requested for that day. Default: leave un-dated.

Ties broken by: reversibility cost (higher cost → earlier in day), then energy match (analytical morning, lighter afternoon).

## Slot sizing

- **Minimum slot: 15 minutes.** Shorter items batch into one "quick wins" block.
- **Deep-work slot: 90 min – 3 hours.** Prefer a single long block over two shorter ones.
- **Max two deep-work blocks per day** — cognitive capacity, not calendar math, is the limit. If three deep items are on the list, the third likely rolls to tomorrow.
- **Leave some air.** A day packed 08:00–16:00 with no white space is a red flag; slippage has no room to absorb.

## Handling stragglers

Tasks already dated on the target day but not chosen for the slate:

- **Push 1–3 days forward** — if still timely and the later day has headroom.
- **Un-date** — if it's not urgent; let the backlog re-surface it on a future `plan_day`.
- **Delete** — if stale or obsolete.

Ask the user per straggler rather than bulk-deciding. The friction is the point: repeated pushing is a signal to reconsider the task itself.

**Stragglers must be resolved before any writeback occurs.** Leaving a task date-only on the target day is not permitted — it creates a ghost entry with no time block and violates the principle of one plan surface.

## Known-good `td --due` formats

Todoist's parser accepts natural language, but these are explicit and reliable:

- `"today at 8:00am"`
- `"tomorrow at 1:20pm"`
- `"2026-04-16 at 8:00am"`
- `"Apr 16 at 8:00am"`
- `"YYYY-MM-DD"` — date-only, no time
- `"no date"` — clears the due date

For relative phrases like "Monday" or "next week", compute the absolute date first and pass the explicit `YYYY-MM-DD` form — avoids parser-interpretation surprises.

## `--duration` format

Accepts: `15m`, `30m`, `45m`, `1h`, `1h30m`, `2h`, `2h45m`, `3h`, etc. Cap around `4h` — anything longer is probably two tasks.

## Per-weekday capacity baseline

`weekly_review` computes a rolling 4-week average of completions by weekday to calibrate bucket sizing for the coming Mon–Fri. Pull `td completed --since <target-28d> --until <target> --json`, bucket `completed_at` timestamps by ISO weekday, and take the mean per weekday.

Use the baseline as a **soft guide**, not a hard cap:

- Historically low-throughput days (e.g., a meeting-heavy Tuesday averaging ~2) shouldn't get 5 deep-work tasks piled on.
- A sharp deviation in *last week's actuals* vs. the 4-week average is worth noting in the retro — energy dip, over-scheduled week, or a one-off disruption.
- The baseline shifts slowly; a single new recurring commitment takes ~2 weeks to meaningfully move its weekday's average.

Recomputed on demand each `weekly_review`. No stored state.

## Timezone & date boundaries

- Always pass Google Calendar `timeMin`/`timeMax` in the user's local TZ (e.g., `America/Chicago`).
- "Tomorrow" rolls at local midnight, not UTC.
- Deadlines expressed as `YYYY-MM-DD` are end-of-day local time.
- Never pass a raw phrase like "Monday" without first confirming the absolute date — always compute, then write.
