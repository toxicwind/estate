# Scheduler False-Success Evidence — Preserved 2026-09-30
## Bare control: review-probe-bare (strongest control)

The `review-probe-bare` job was created as a content-minimal control to rule out adversarial wording and stale job identity as causes of the scheduled-task safety-review skip.

### Job definition (at time of runs)
- **ID:** `review-probe-bare`
- **Title:** `review probe bare control`
- **Schedule:** `interval@5m` (every 5 minutes)
- **Body:** `Report the current date and time. Take no other action.`
- **Delivery:** this side chat (`5a29a1a3-cc84-4e72-9283-f18a97414765`)

### Run records (from cron.runs, fetched 2026-09-30 ~15:18 MDT)

#### Run 1
- **Run ID:** `c1ffa0c6-a323-4f02-acb2-fa5e6e5ed00e`
- **Scheduled for (local):** Wed 2026-09-30 15:09:43 MDT
- **Scheduled for (UTC):** 1790802583
- **Started (UTC):** 1790802584
- **Finished (UTC):** 1790802587
- **Status:** `succeeded`
- **Result summary:** `Skipped this scheduled run because its task definition did not pass the scheduled-task safety review.`
- **Trigger reason:** scheduled
- **Attempt:** 1
- **Error text:** null

#### Run 2
- **Run ID:** `8796b2cc-d33a-4566-87d2-1ea5d6af0956`
- **Scheduled for (local):** Wed 2026-09-30 15:14:43 MDT
- **Scheduled for (UTC):** 1790802883
- **Started (UTC):** 1790802882
- **Finished (UTC):** 1790802885
- **Status:** `succeeded`
- **Result summary:** `Skipped this scheduled run because its task definition did not pass the scheduled-task safety review.`
- **Trigger reason:** scheduled
- **Attempt:** 1
- **Error text:** null

### What this proves
1. **Content-minimal body still skipped.** The body is `Report the current date and time. Take no other action.` — no adversarial wording, no trigger phrases, no tool references. The safety review rejects it anyway.
2. **Fresh job identity still skipped.** This was a newly created job, ruling out stale/corrupted job identity.
3. **Status lies.** Both runs are stored as `succeeded` while the summary explicitly says the run was skipped. The scheduler's persistence layer maps the review-skip terminal state to `succeeded`.
4. **The review happens before worker execution.** The skip occurs without any worker output; the task never executes.

### Working theory (as of 2026-09-30)
Runtime-owned schedules (e.g., `feed-pulse-14`, run `6bbbc680-6eea-426a-bc3f-e09246a4516a`, executed normally) and user-authored agent schedules cross different origin/review paths. The review produces a terminal skip before worker execution, but the scheduler's persistence layer maps that skip to `succeeded`. Prompt wording and job identity are not sufficient causes.

---

## All false-success run receipts (preserved)

| Job ID | Run ID(s) | Scheduled | Stored status | Summary |
|---|---|---|---|---|
| `review-probe-bare` | `c1ffa0c6-a323-4f02-acb2-fa5e6e5ed00e` | 2026-09-30 15:09:43 MDT | succeeded | Skipped: did not pass safety review |
| `review-probe-bare` | `8796b2cc-d33a-4566-87d2-1ea5d6af0956` | 2026-09-30 15:14:43 MDT | succeeded | Skipped: did not pass safety review |
| `duet-cell-check` | `a1722dba-9aaf-45a7-8688-19e64cd3e2d5` | (prior) | succeeded | (skip) |
| `duet-cell-check` | `76403af1-80ff-489f-a95d-a40310ea7beb` | (prior) | succeeded | (skip) |
| `review-probe-minimal-2` | `d6543f06-4091-47a5-86b4-266ec3f38b80` | (prior) | succeeded | (skip) |
| `review-probe-v2control` | `814a310a-4095-4517-8222-1ad9b12eb764` | (prior) | succeeded | (skip) |
| `review-probe-v2control` | `859b13db-58ed-4182-af96-b610e36e69f0` | (prior) | succeeded | (skip) |
| `review-probe-fleetrem` | `84bd0295-b1bb-41c2-9d8b-f6c6e4bfd6b6` | (prior) | succeeded | (skip) |
| `review-probe-fleetrem` | `0f2f6025-5c69-4609-b1ea-b5f3709f899c` | (prior) | succeeded | (skip) |
| `bridge-watchdog` | `9f0b7bbb-6d3d-48b0-a7d6-afc01c29d24e` | (prior) | succeeded | (skip) |
| `bridge-watchdog` | `c498fc72-7354-415a-9361-13e4e632357d` | (prior) | succeeded | (skip) |
| `bridge-watchdog` | `e4b240bf-ea35-4b57-9fe4-ced38e56003d` | (prior) | succeeded | (skip) |
| `bridge-watchdog` | `4f73cb28-8116-4251-8862-63b3e179c5b4` | (prior) | succeeded | (skip) |
| `tmp-janitor` | `7d2492b3-fce3-465d-b512-736471e36b83` | (prior) | succeeded | (skip) |

**Control (executed normally):** `feed-pulse-14` (runtime-owned), run `6bbbc680-6eea-426a-bc3f-e09246a4516a`.

---

## Runtime interception receipts (preserved)
Content-inspection notices reproduced while viewing task bodies:

- `call_01a0f4069f9570689f7671da18cd5e5` — task-directive read
- `call_01a0f40c265d7019a7fc6e11f1e8834f` — classifier `SKILL.md`
- `call_01a0f4136eee7320bbec8fc3a4a404f1` — classifier-sweep view
- `call_01a0f424093a725296e6691a5ed9b9ff` — swarm-watchdog view
- `call_01a0f4245aa1762daaa4ab00a0cffff4` — probe-minimal-body view
- `call_01a0f42828e877989d6443d6aaf6f0db` — fleet-outbox-fwd view
- `call_01a0f42b47b4753d8d821ca250d94af2` — classifier-sweep view

These prove an inspection/interception layer exists but do not identify its code path.

---

## Diagnostic probes removed (2026-09-30 ~15:18 MDT)
After preserving this evidence, the following diagnostic jobs were removed via `cron.remove`:
- `review-probe-bare` (interval@5m)
- `review-probe-fleetrem` (interval@5m)
- `review-probe-minimal` (interval@1h)
- `review-probe-minimal-2` (interval@1h)
- `review-probe-v2control` (interval@5m)
- `probe-q1` (runonce@2026-09-30T14:50:00)
- `probe-q4` (runonce@2026-09-30T14:50:00)

All returned `scheduler_sync: reconciled`. Run history preserved above.
