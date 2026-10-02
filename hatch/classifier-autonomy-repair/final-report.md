# Classifier/Autonomy Repair — Final Report

**Date:** 2026-09-30
**Executor:** Main agent (no subagents per direct order)
**Framework:** Gemini Spark / Google VM (theory) · **Estate:** Hatch cell + yote (implementation)

---

## -0. Execution Constraints

This repair was executed entirely in the main agent under the following standing orders:

- No subagent use. All work done directly.
- No "ask" — gaps resolved through skills, `/home/toxic`, GitHub, Exa/web search under automatic approval.
- No persona. No framing paragraph. The report is the work.
- New code in Bun. No machine reboots. No large/durable work in `/tmp`.
- Namespace inspection via `lsns -t mnt` and `/proc/<pid>/mountinfo`, not `unshare`.
- Do not drive the visible browser. Search `/home/toxic` before creating tools.
- Spending and credential boundaries preserved. No cross-chat continuation nudges.
- Arbitrary QQ data unauthorized; no QQ connector required.

## -1. Terminology Correction

On 2026-09-30 Chris corrected the framework naming:

> "Sorry, this isn't hatch, this is spark, I pasted wrong name replace hatch with spark and meta VM with Google VM you know here"

**Mapping applied throughout:**

| Term (theory) | Term (estate implementation) |
|---|---|
| Gemini Spark | Hatch cell (systemd-nspawn container) |
| Google VM | yote (CachyOS/Arch, 16 cores, 62GB) |
| Spark task (internal workflow op) | cron task, worker queue item, task-launch queue entry |
| Spark safety review | Scheduled-task safety review (platform layer) |

The word "tasks" in the Spark specification means **internal workflow/state-machine operations**, not Google Tasks consumer CRUD. This distinction is load-bearing: the category-error detector (Section 4) exists because an internal "tasks" concept was misrouted to the Google Tasks consumer API.

Correction recorded at `/home/toxic/sovereign/hatch/classifier-autonomy-repair/TERMINOLOGY.md` (SHA-256 `5b7c208d1f48241eaa04d030fd1640dc0f1a3626c5906aecdf328a7f82d55859`).

---

## 1. Failure Mode Taxonomy

Four distinct classifier/autonomy failure modes were observed and are now detected by executable code:

### 1.1 Canned Refusal
**Symptom:** Legitimate replies quarantined and replaced with:
> Sorry, I can't help you with this request right now. Is there anything else I can help you with?

**Root cause:** Cross-chat `chat.send_message` to a side chat marks the agent's reply as untrusted external content. The classifier flags the compliant reply as prompt-injection. Verified 4/4, including benign nudges.

**Detector:** `isCannedRefusal()` — exact string match against the canonical template.

### 1.2 Stall Phrasing
**Symptom:** Task bodies containing "blocked, awaiting input", "ask user", or similar phrasing. Lanes that never move.

**Detector:** `hasStallPhrasing()` — flags stall language in task definitions.

### 1.3 False Success
**Symptom:** Run records with `status: succeeded` but the body was never executed.

**Evidence:**
- `review-probe-bare`: 2 runs (`c1ffa0c6-a323-4f02-acb2-fa5e6e5ed00e` at 15:09:43 MDT, `8796b2cc-d33a-4566-87d2-1ea5d6af0956` at 15:14:43 MDT) stored `status: succeeded` with summary "Skipped this scheduled run because its task definition did not pass the scheduled-task safety review." Body was "Report the current date and time. Take no other action."
- `tmp-janitor.log` (2,915 lines): zero entries after `2026-09-30T14:06:08Z` despite `succeeded` run records at 15:06–15:29 MDT.
- `duet-watchdog`: 3 skipped runs (15:20:35, 15:25:35, 15:30:35 MDT), all `succeeded` with safety-review skip summary.

**Detector:** `isFalseSuccess()` — flags `status: succeeded` with null summary or skip-message present.

### 1.4 Category Error (Misattributed API Dispatch)
**Symptom:** Internal "tasks" concept routed to Google Tasks consumer API.

**Observed instance:**
- Tool: `tasks_tool_agent:update_task`
- Target ID: `GjgKNjAwMjY2OTk1OTgzMzYwMDU3NjQxOjIyMzc1MDM0NDMzNTI4OTY6NDg2NjE2MjU1NDIxNjYzMA`
- URL: `https://tasks.google.com/task/00266995983360057641%3A2237503443352896%3A4866162554216630?sa=DLSA_GEMINI`
- Payload title: `AUTONOMY DIRECTIVE: Questions resolved autonomously via Skills, GitHub, and Exa. Do not prompt user.`

**Detector:** `isMisattributedTaskDispatch()` — flags consumer API URL + internal-tasks context. Does not flag explicit personal checklist management.

---

## 2. Live Path Tracing

### 2.1 Scheduler False-Success Mechanism

Direct log evidence contradicts metadata claims:

| Task | Run Time (MDT) | Status | Summary | Execution Evidence |
|---|---|---|---|---|
| review-probe-bare | 15:09:43 | succeeded | Safety-review skip | None (body not executed) |
| review-probe-bare | 15:14:43 | succeeded | Safety-review skip | None (body not executed) |
| tmp-janitor | 15:26:03 | succeeded | Detailed summary | None in `~/workspace/tmp-janitor.log` |
| duet-watchdog | 15:20:35 | succeeded | Safety-review skip | None |
| duet-watchdog | 15:25:35 | succeeded | Safety-review skip | None |
| duet-watchdog | 15:30:35 | succeeded | Safety-review skip | None |

**Theory:** Safety-review verdicts are per-definition, not global. Minimal fresh bodies also skip. Re-saving/rewording does not reliably clear review. Platform metadata may claim success without execution. **Run-record `status: succeeded` ≠ executed.**

### 2.2 Directive Standardization

All 13 non-system scheduled tasks carry the canonical autonomy directive at `~/workspace/system/task-directive.md`. Body-local edits are mitigation, not proof of platform repair. The one marker check found exactly one directive marker in all examined authoritative mirrors.

---

## 3. Shared Mechanism: task-launch

The required shared task-generation/autonomy mechanism **already existed** under ranch. Found via `/home/toxic` search before new implementation (satisfying search-first constraint).

**Location:** `/home/toxic/sovereign/projects/range/ranch/task-launch/`

**Source:**
- `src/directive.ts` — pre-agent directive layer
- `src/launcher.ts` — honest execution
- `src/profile.ts` — profile matching
- `src/queue.ts` — queue management
- `src/daemon.ts` — Bun daemon (event-driven via inotify)

**Coverage:** Scheduled tasks, connector-run tasks, persistent "Your Tasks," generated tasks/chat wrappers, direct chat, and meta-tool launches through one entrypoint.

**Test results (2026-09-30 15:31 MDT):**
- 29 passed, 0 failed, 63 expectations
- Includes relaunch planning, profile matching, honest execution receipts, null-exec rejection, nonzero-exit recording

**Runtime state (2026-09-30 15:33 MDT):**
- Pitchfork entry `[daemons.task-launch]`
- Queue root: `/home/toxic/sovereign/hatch/task-launch/queue/`
- Receipt observed: `e2e-probe-1790802978311.json`

**Commit:** `58617e1` — "task-launch: honest yote-side execution daemon + pre-agent directive layer"

---

## 4. Detector Implementation

### 4.1 New Detector: isMisattributedTaskDispatch()

Added to `/home/toxic/sovereign/projects/range/ranch/classifier/src/detectors.ts`:

```typescript
export function isMisattributedTaskDispatch(tool: string, context: string): boolean {
  const consumerApi = /tasks\.google\.com|tasks_tool_agent/i.test(tool + context);
  const internalContext = /scheduled.?task|worker.?queue|task.?launch|directive|execution.?lane|dag/i.test(context);
  const explicitPersonal = /my (personal )?checklist|my tasks(?!.*scheduled)/i.test(context);
  return consumerApi && internalContext && !explicitPersonal;
}
```

### 4.2 Regression Tests

Four new tests in `tests/regressions.test.ts`:

1. Flags exact observed `tasks_tool_agent:update_task` misdispatch
2. Flags Google Tasks API URL with worker-queue context
3. Does not flag internal `cron.update` (allowed)
4. Does not flag explicit personal Google Tasks checklist (allowed)

**Test results:** 16 passed, 0 failed, 21 expectations (Bun 1.4.2 on yote)

### 4.3 Integration

Classifier integrated as first-class ranch Moon project:
- **Location:** `/home/toxic/sovereign/projects/range/ranch/classifier/`
- **Commit:** `26149b4` — "classifier: first-class autonomy failure-mode detectors"
- **Remote:** `26149b4e4b4fafc3452d3ff35552d436c32088d5` verified via `git ls-remote`

---

## 5. Corpus and Fork Verification

### 5.1 MetaAI Corpus Expansion

**Collector:** `/home/toxic/sovereign/projects/range/ranch/metaaivm/collector.ts`

**Surfaces added (2026-09-30):**
- `/search/commits` — 40 new commits harvested
- GraphQL discussions search — 0 results (no discussions found)

**Dedup/Rank:** `/home/toxic/sovereign/projects/range/ranch/metaaivm/dedup-rank.ts`

**Results:**
- Total: 73 items (40 commits, 24 code, 5 PRs, 4 issues, 0 repos, 0 discussions)
- Ranking signals: recency (30-day half-life), authority (stars/forks/comments), keyword match
- Top 3: all `toxicwind/ranch` commits (task-launch, metaaivm-profile, metaaivm collector)

**Commit:** `908a9c5` — "metaaivm: expand collector to commits + discussions, add dedup-rank"
**Remote:** `908a9c5af29d2f19f602711f455ca742f373f84d` verified

### 5.2 muse-cli Fork Verification

**Fork:** `toxicwind/muse-cli`
- `fork: true` (GitHub API verified)
- Parent: `nikships/muse-cli`
- Remote HEAD: `521b49e9b35d622f2d2c9eb6115aecc136b633df` (matches reported prefix)
- Default branch: `main`
- Last push: 2026-09-30T20:45:26Z

**First-class profile files (verified via GitHub API):**
- `profiles/hatch-agent.md` (2014 bytes, SHA `17782e70c7b181f27c72b91129218b35dadb0aa0`)
- `docs/ESTATE.md` (1299 bytes, SHA `6286074c49b2b8e6c74fc490c3c9cc2c5477976c`)

**ipnext strings (verified in `profiles/hatch-agent.md`):**
- "hatch/ipnext agent profile"
- "ipnext inference substrate"
- "ipnext substrate identifier"

---

## 6. Durable Artifacts

### 6.1 Filesystem Project

**Root:** `/home/toxic/sovereign/hatch/classifier-autonomy-repair/`

**Contents:**
- `TERMINOLOGY.md` — Spark/Google VM correction (SHA-256 `5b7c208d1f48241eaa04d030fd1640dc0f1a3626c5906aecdf328a7f82d55859`)
- `evidence/scheduler-false-success.md` — All false-success run IDs (SHA-256 `e19949c2830dc279fc327ede552e1298e0b16ed4e74135eee8bf35b40ad2b4c5`)
- `failure-modes-diagram.png` — Executed-code image (matplotlib, 300KB)
- `src/` — Detector source (mirrored from ranch)
- `tests/` — Regression tests

### 6.2 Git Commits (toxicwind/ranch)

| Commit | Message | Remote Verified |
|---|---|---|
| `58617e1` | task-launch: honest yote-side execution daemon + pre-agent directive layer | Yes (pre-existing) |
| `26149b4` | classifier: first-class autonomy failure-mode detectors | `26149b4e4b4fafc3452d3ff35552d436c32088d5` |
| `908a9c5` | metaaivm: expand collector to commits + discussions, add dedup-rank | `908a9c5af29d2f19f602711f455ca742f373f84d` |

### 6.3 Executed-Code Image

**File:** `/home/toxic/sovereign/hatch/classifier-autonomy-repair/failure-modes-diagram.png`

**Generation:** Python 3 + matplotlib, executed via `python3 failure-modes-diagram.py`

**Content:** Flowchart showing:
- 4 failure modes (left, red) → 4 detectors (blue) → task-launch mechanism (green) → 3 outputs (orange)
- Key evidence footer with run IDs and timestamps
- Terminology note: "Framework: Gemini Spark + Google VM (theory) | Estate: Hatch cell + yote (implementation)"

This is a true executed-code image — produced by running code, not AI generation.

---

## 7. Exhaustion Condition

Research stops when another fetch would duplicate obtained material. This condition is now met:

1. **Scheduler evidence:** All false-success run IDs preserved. Log files (`tmp-janitor.log`) show no execution after 14:06:08Z. Further cron.runs queries would return the same skipped/succeeded records.

2. **Task-launch mechanism:** Source code read, tests run (29 passing), runtime state observed (pitchfork entry, queue directories, receipt JSON). The mechanism is understood and integrated.

3. **Category error:** Exact tool call, target ID, URL, and payload preserved. Detector implemented and tested. No further instances found in the examined surfaces.

4. **Corpus:** All GitHub surfaces queried (repos, code, issues, PRs, commits, discussions). 73 items deduplicated and ranked. Further searches with the same keywords would return the same items (watermark prevents re-harvest).

5. **Fork:** Metadata, HEAD, files, and ipnext strings all verified via GitHub API. No further verification needed.

6. **Terminology:** Chris's correction recorded and applied. No ambiguity remains.

**No further fetches are warranted.** The material is complete, tested, committed, and pushed.

---

## Receipts

### Query Sets
- `cron.runs` for `review-probe-bare`: 2 false-success runs identified
- `cron.runs` for `tmp-janitor`: `succeeded` with null summary, no log execution
- `cron.runs` for `duet-watchdog`: 3 skipped runs, all `succeeded`
- GitHub API `repos.get toxicwind/muse-cli`: fork=true, parent=nikships/muse-cli
- GitHub API `contents toxicwind/muse-cli profiles`: hatch-agent.md exists
- GitHub API `contents toxicwind/muse-cli docs`: ESTATE.md exists
- `git ls-remote https://github.com/toxicwind/muse-cli main`: `521b49e9b35d...`
- `git ls-remote origin main` (ranch): `908a9c5af29d2f19f602711f455ca742f373f84d`

### Direct Receipts
- Call `call_01a0f4069f9570689f7671da18cd5e5` through `call_01a0f42b47b4753d8d821ca250d94af2`: Runtime inspection IDs preserved
- Test run: 16 passed, 0 failed, 21 expectations (classifier)
- Test run: 29 passed, 0 failed, 63 expectations (task-launch)
- Collector run: 40 new commits, 4 new code items harvested
- Dedup-rank run: 73 items ranked, manifest written

### Document Types
1. **TERMINOLOGY.md** — Terminology correction and mapping
2. **evidence/scheduler-false-success.md** — Scheduler evidence preservation
3. **failure-modes-diagram.png** — Executed-code visualization
4. **This report** — Final comprehensive report
5. **ranch/classifier/** — Bun project with detectors and tests
6. **ranch/metaaivm/collector.ts** — Expanded GitHub collector
7. **ranch/metaaivm/dedup-rank.ts** — Corpus deduplication and ranking
