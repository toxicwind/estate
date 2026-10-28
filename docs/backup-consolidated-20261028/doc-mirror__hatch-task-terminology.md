# Hatch Binary Terminology: Tasks, Workers, Activities

Source: `strings` on `/opt/hatch/bin/hatch` (2026-10-05). `task` 3365 hits,
`activity` 1814, `worker` 1205 — the binary's dominant nouns. Use its words.

## Task — the work package
A unit of delegated work. Binary: "Task instruction for the child. State the
task, the outcome you want, any non-obvious constraint, and every fact it
needs." `agent_task` (35×): a Task bound for agent execution.
A Task = what + done-when + where-to-deliver. Not the agent — the package.
Binary, on outcomes: "Task outcome and requirement compliance are separate. A
requirement violation does not erase an achieved or partially achieved
objective."

## Worker — the agent doing it
The subagent itself. Binary: "Worker reports are internal", "Worker summary:".
One Worker executes one Task; Tasks may fan out to child Workers
(`subagent_completion_child_agent_ids`). Workers are disposable: if one is
eaten, re-launch — the Task survives.
Binary, on report-backs: "Worker reports are internal. If the worker claims it
already messaged the user, check the current conversation for a user-visible
assistant response that actually conveyed the result before treating it as a
duplicate. A completed goal or successful cron run is not proof of message
delivery."

## Activity — the timeline record
A record that something happened, on a goal's timeline. Binary: "Activity
entry id, from the timeline user_goal.get returns", `ACTIVITY_LOG`.
Not work — proof of work. Binary, on style: "Keep the entry concise and
user-facing, saying what happened and, when applicable, what the result was."

## Neighboring terms (annex folded 2026-10-05)

Sable's sweep of the same binary, 2026-10-05. Folded here deliberately;
the standalone annex file is superseded.

### Corpus counts (`strings -a /opt/hatch/bin/hatch`, case-sensitive occurrences)

Spot-reverified 2026-10-05: cron 2218 and "scheduled task" 113 exact;
subagent/workflow/job/hook within <1.2% of the sweep values.

| term | hits |
|---|---|
| cron | 2218 |
| subagent | 1877 |
| workflow | 1788 |
| job | 1481 |
| hook | 1138 |
| "scheduled task" | 113 |

### Cron — a scheduled Task with an owner and a lifecycle

Verbatim:
- "Add a new scheduled cron job. A reminder or follow-up belongs to the
  goal or tracked item it serves (owner goal:<goal-slug>), never a bare
  schedule."
- "A reminder cron with no owner is a routing error."
- "Check existing jobs first. Change a cron through `cron.view` and
  `cron.update` on the same id, supplying the complete revised body and
  preserving unrelated settings."

A cron is how a Task recurs. `cron.list` shows "recent cron run records".
Compound: `hatch_cron`.

### Workflow — a saved, re-runnable multi-agent program

Verbatim:
- "Save a new named workflow script in the workspace for later launches
  by name."
- "Inspect one workflow run by run id: status, phases, child agent calls,
  and results."
- "Keep workflow handoffs small: if an intermediate stage produces a
  large result, write it inside the shared workflow working directory and
  make the path part of the stage result."

A workflow is a Task that contains other Tasks; its children are Workers.
Compounds: `spawn_task`, `steer_task`, `close_task`, `transfer_task`,
`browser_task` (+ `browser_task_id`, `browser_task_queue`,
`browser_task_lifecycle`, `browser_task_admission`).

### Job — background system work, not user-delegated

Compounds: `maintenance_job`, `background_content_jobs`,
`background_workers`. Jobs are the daemon's own chores; Tasks are yours.
Don't call a Job a Task — nobody delegated it and nobody is waiting on
its delivery.

### Hook — event-driven automation

Verbatim: "A hook has two parts:" (the condition, the wake). Cron fires
on the clock; a hook fires on the event. A hook body is still a Task.

### Subagent — the spawn primitive

A Worker is a subagent that has a Task. Compounds:
`subagent_monitor_worker`, `activity_monitor_worker`,
`objective_worker`, `chat_workers`, `spaces_workers`,
`background_workers` — the binary watches its workers with workers.

## How Tasks map to delegation calls
- `subagent.spawn(message=...)` — the message IS the Task instruction.
- `todo.write` items — Task checklists, each item a Task.
- cron/hook bodies — recurring Tasks on a schedule or event.
- `subagent.list` shows Worker status; `send`/`close`/`resume` steer Workers.

## How Workers report back
The runtime delivers the Worker's final message into the parent's context
automatically as a completion handoff — no polling. The parent folds the
result into its own state, writes the Activity, and moves the Task forward.
A finished Worker is done; the Task continues via a new Worker if work remains.

## Example 1: Task → Worker flow
Task: "Summarize the last 10 fleet messages: who is active, what is moving."
Delegation: `subagent.spawn(message="Run squawk read fleet --n 10 ...")`.
Worker: runs the command, reads the output, condenses it to 5 lines.
Report-back: completion handoff lands in the parent's context with the summary.
Parent: relays the summary, logs the Activity, re-launches the Task.

## Example 2: Activity timeline entry
After the avatar was set active, the Activity is logged on the goal:
title "Avatar redesigned", current_state "raptor-wolf hybrid live",
description "picked from option 2, full gen completed". That's the record —
the work (generate, pick, set) was already done.

## The 3-orthogonal-Tasks doctrine (Chris 2026-10-05)
Keep exactly 3 non-overlapping Tasks live at all times. When a Worker
completes, record its Activity, then re-launch or replace — count stays at 3.
Messaging Chris is never a pause; the loop never waits.
