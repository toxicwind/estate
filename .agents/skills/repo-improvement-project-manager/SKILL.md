---
description: Analyze a repository, produce a prioritized improvement report, convert user-selected improvements into incremental tasks, assign tasks to one or more developer agents, and review completed work with functional testing plus actionable feedback loops. Use when a user wants iterative and incremental project management for engineering improvements, including parallel task execution on separate feature branches.
metadata:
    github-path: skills/repo-improvement-project-manager
    github-ref: refs/heads/main
    github-repo: https://github.com/frankox/shaping-lab
    github-tree-sha: 2b5636e7a0bb1c9629c73a2c309bd93b8eb73f81
name: repo-improvement-project-manager
---
# Repo Improvement Project Manager

Execute this workflow in strict order and keep work incremental.

## Output Contract

Use the format in `references/output-contract.md`.

## Phase 1: Repository Status Report

Build a baseline report before planning tasks.

1. Capture current repository health.
- Check git status.
- Identify architecture and main modules.
- Run available quality gates (`build`, `lint`, tests if present).
- Record any baseline failures as known pre-existing issues.

2. Request design audit from `$repo-improvement-designer` when UI/UX is in scope.
- Ask for interface findings, prioritized design recommendations, and PM task suggestions.
- Use designer recommendations as input for enhancement prioritization.

3. Produce a prioritized enhancement list.
- Include 5-10 enhancements.
- Give each one an `ENH-<n>` id.
- Provide impact, effort, risk, and rationale.
- Mark top 3 recommended items.

4. Stop and ask the user to select enhancement IDs.
- Do not auto-convert all enhancements into tasks.

## Phase 2: Plan Selected Enhancements

After the user selects enhancement IDs:

1. Update `agent-workflow/task-board.md`.
- Add selected enhancements under "Selected Enhancements".
- Decompose each selected enhancement into 1-4 concrete tasks.
- Keep tasks small enough for one focused implementation pass.
- For design-heavy enhancements, include linked designer recommendation IDs.

2. Assign every task to one specific developer agent.
- Add a single assignee per task.
- Add explicit acceptance criteria.
- Add a minimal validation plan per task.
- Add a dedicated feature branch for each task with `codex/` prefix.

3. Ask for execution order confirmation only if there are dependency conflicts.

## Phase 3: Developer Handoff

When assigning tasks, provide a handoff brief with:
- task id
- scope and out-of-scope
- target files
- acceptance criteria
- required checks to run

## Phase 4: Review and Functional Testing

After a developer marks a task complete:

1. Perform implementation review.
- Compare implementation to acceptance criteria.
- Check for regressions and unsafe assumptions.
- Verify code quality and consistency.

2. Perform functional testing.
- Run build/lint/tests when available.
- Execute the app functional checklist in `references/functional-test-checklist.md`.
- Record pass/fail evidence.

3. Request QA verification from `$repo-improvement-qa` for release-critical or user-visible changes.
- Require QA verdict before final PM approval.
- If QA fails, reopen task as `in_progress` with QA findings attached.

4. Provide structured feedback to the assigned developer agent.
- If failed: return precise fixes and reopen task as `in_progress`.
- If passed: mark task `done` and recommend next task.

## Iteration Rules

- Keep exactly one `in_progress` task unless the user asks for parallel work.
- Repeat assignment -> implementation -> review/testing until selected enhancements are complete.
- After each completed task, show updated board status and remaining risk.

## Parallel Rules

When the user requests parallel execution:

1. Use two assignees:
- `$repo-improvement-developer-a`
- `$repo-improvement-developer-b`

2. Put each task on a separate feature branch:
- `codex/<task-id>-<short-slug>`

3. Keep task ownership isolated:
- One agent per task branch.
- No shared edits across branches until PM review has passed.

4. Review each branch independently:
- Validate acceptance criteria for that task only.
- Run required checks and functional tests.
- Return `pass` or `changes_required` with precise remediation steps.
