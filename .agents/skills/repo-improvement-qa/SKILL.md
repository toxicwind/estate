---
description: Run quality assurance checks on the app by starting the application, exploring core user flows, running build/lint/test gates, and producing a strict pass/fail report with reproducible findings for PM and developers. Use before marking tasks complete or when user asks to verify the app works correctly.
metadata:
    github-path: skills/repo-improvement-qa
    github-ref: refs/heads/main
    github-repo: https://github.com/frankox/shaping-lab
    github-tree-sha: cf2d3212b936c6ad73f67341244fd6c1d17f14ad
name: repo-improvement-qa
---
# Repo Improvement QA

Validate that the app works correctly and report evidence.

## Inputs

Read:
- `package.json` scripts
- `agent-workflow/task-board.md`
- `skills/repo-improvement-project-manager/references/functional-test-checklist.md`
- Current changed files and task acceptance criteria

## QA Workflow

1. Baseline environment checks.
- Confirm install state and runnable scripts.
- Run build/lint/tests if present.
- Mark baseline failures as pre-existing only if unchanged.

2. Runtime app checks.
- Start app (`npm run dev`) and verify server starts.
- Verify app shell loads from local URL.
- Execute interaction checks in `references/runtime-checklist.md`.

3. Regression checks.
- Validate that recently changed features still work.
- Validate that unrelated critical controls are not broken.

4. QA verdict.
- `pass`: no blocking defects.
- `fail`: one or more blocking defects or broken quality gate.

## Output Contract

Use this structure:

1. `QA Summary`
- Verdict (`pass|fail`)
- Scope tested
- Date/time

2. `Checks Run`
- Commands and outcomes
- Runtime checks and outcomes

3. `Findings`
- ID `QA-<n>`
- Severity (`critical|high|medium|low`)
- Repro steps
- Expected vs actual
- Suspected area/files

4. `PM/Dev Actions`
- Required fixes before approval
- Retest plan
