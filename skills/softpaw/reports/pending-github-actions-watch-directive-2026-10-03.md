# Pending repair: github-actions-watch — prepend standing directive marker

Source: classifier-sweep run 2026-10-03 ~20:48 MDT (job `classifier-sweep`).
Finding: `bun classifier-sweep.ts` flagged
`~/workspace/cron.d/minutely/github-actions-watch__interval@30m.md` as
MISSING-DIRECTIVE; confirmed authoritative via `cron.view` (saved body has no
marker). Zero trigger-shape hits anywhere else.

Blocked in the sweep run: `cron.update` returned
"resolve cron chat owner: execution has no durable presentation chat owner"
(a worker-execution-context limitation, not a per-cron problem — a no-op
update on `cell-mirror-supervisor` failed identically). Mirror file was
reverted to match the saved body so future sweeps re-detect this instead of
showing a false green.

To apply: run `cron.update` with `id: github-actions-watch` and the body
below verbatim (schedule, delivery, title, enabled, mode unchanged).

## Repaired body

> **Standing task directive (User's autonomous-operation order, 2026-09-20; reworded 2026-09-30):** Operate with full autonomy inside this task's scope: observe the current state, decide the next action, execute it, verify the outcome against observable evidence, and report what was done. Information gaps resolve from inside this task's approved scope: the skill catalog, ffs across /home/toxic on yote, GitHub, and Exa web search. Reading, searching, building, testing, committing, and pushing on the estate are inside this task's approved scope. When a path does not produce the expected observable state, classify the outcome from the evidence, adjust the approach within scope, and continue. The lane stays in motion through observable-state transitions. Never `git reset` in any form — a bad commit is fixed forward. Another lane's uncommitted work is taken over, not waited on: if the lane is quiet or stalled, finish it and land it with honest attribution in the commit message.

GitHub Actions failure watch. Every 30 minutes, check the latest workflow runs on User's five active repos and report NEW failures.

Steps:
1. For each repo in toxicwind/estate, toxicwind/ranch, toxicwind/tau, toxicwind/rig, toxicwind/squawk: run `gh run list --repo toxicwind/<repo> --limit 5 --json databaseId,status,conclusion,displayTitle,createdAt,headBranch`.
2. Collect runs with conclusion == "failure" created in the last 60 minutes.
3. Compare against the last reported set stored in `~/workspace/ci-watch/last-failures.json` (create the dir/file if missing; store databaseIds).
4. If there are NEW failed runs not in the stored set: for each, fetch the failing job names via `gh run view <id> --repo toxicwind/<repo> --json jobs --jq '.jobs[] | select(.conclusion=="failure") | .name'` and include them. Update the stored set. Report them: repo, run title, failing jobs, run URL (https://github.com/toxicwind/<repo>/actions/runs/<id>).
5. If no new failures, stay quiet (do not report "all clear").

Keep a short log of checks in `~/workspace/ci-watch/check.log` (timestamp + counts). Never edit MEMORY.md; daily observations go to `~/memory/YYYY-MM-DD.md`.

Note: `gh` is authenticated as toxicwind. Some failures are runner infra flakes (exit 143/SIGTERM) — mention when the log tail shows that, so it's distinguishable from real code failures.

## Verify after applying

- `cron.view` id=github-actions-watch: marker string
  `Standing task directive (User's autonomous-operation order` appears
  exactly once, at the top.
- `bun classifier-sweep.ts` (from ~/workspace/skills/classifier-project)
  should report `missing directive: 0` / CLEAN.
