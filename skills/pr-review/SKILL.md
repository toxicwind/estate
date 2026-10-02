---
name: pr-review
description: Audit a GitHub PR and render a verdict — LGTM or NOT LGTM, every finding evidence-backed. Readiness gate first (merge conflicts / red CI = no verdict, stop), then a five-frame substance pass, a two-lane reviewer race, and our quality bar (real repro, in-tree regression test, raced designs, no monkeypatch). Draft is the deliverable; publishing to GitHub needs explicit approval of the exact text.
---

# pr-review

Borrowed from [smoreg/ccc's pr-review](https://github.com/smoreg/ccc/blob/HEAD/skills/review-toolkit/skills/pr-review/SKILL.md) (readiness gate, five-frame substance pass, evidence bar, verdict discipline), adapted to this estate: our `github` skill instead of the `gh` CLI, herd-routed reviewer lanes instead of a fixed model pair, our quality bar from real upstream work, Chris-voice PR bodies.

**TRIGGER**: the user asks to review, audit, or quality-check a GitHub Pull Request — URL (`github.com/.../pull/N`), shorthand (`owner/repo#N`), bare number (`#1234`), or a "this PR" reference resolvable from context. Do NOT trigger for replying to existing review comments, labeling/triaging issues, or general code questions about a branch with no PR.

## Arguments

- PR ref (positional, optional): URL, `owner/repo#N`, or number. If omitted, detect from the current branch.
- `--publish`: post the review to GitHub. **Without it the draft is the deliverable and nothing leaves this box.** `--publish` enables the option; the user's explicit approval of the exact text triggers the action. Never one without the other.

## Step 1 — Scope: the API is truth

Local branches go stale. Never use bare `main`/`master`/base in diffs — always `origin/<branch>`. Verify PR scope through the GitHub API (via `~/workspace/skills/github/bin/gh.py get`), not local git:

- PR metadata: head ref, base ref, commit count, changed files.
- File list and commit list from the API.

If `git diff origin/$BASE...origin/$HEAD --stat` disagrees with the API file list, trust the API and investigate the local discrepancy first. Print head SHA, commit count, file count, file list so the user can confirm the state under review.

## Step 1.5 — Readiness gate (before any substance)

Fast pass on whether the PR is reviewable at all. Two independent conditions → **gate mode**: an early exit producing a short note with **no** `LGTM` / `NOT LGTM` verdict, because a verdict on unmergeable or broken code is noise.

- **Merge conflicts**: `mergeable == "CONFLICTING"` or `mergeStateStatus == "DIRTY"` → gate. The diff is unstable until rebased; skip all analysis.
- **Red CI plausibly caused by the diff**: failed build/compile/test/lint/typecheck/vet/schema checks → gate. Still-running, pending, or manual-approval checks are NOT red. Failures that clearly cannot come from the diff (missing fork secrets, flaky external service, rate-limited registry) do NOT gate — note and continue. Test: "could this red check plausibly be caused by the diff?" If yes — or you cannot tell — gate.

Gate-mode output: what blocks readiness (named checks/conflicts), the concrete ask (rebase, fix checks, re-request review), nothing about code quality — you haven't reviewed it. Then stop: present the note, do not run the reviewer lanes.

## Step 2 — Business context

Before reading code, frame WHY the PR exists, in order: PR title + full body, linked issues and their acceptance criteria, existing reviews (never repeat a raised point without new evidence). One-sentence summary of the business problem. Every later finding is evaluated against it.

## Step 3 — Five-frame substance pass

Frames 1–3 are a maintainer's gate on whether the change SHOULD exist — any one can independently produce `NOT LGTM` even when the code is flawless. Frame 5 delegates to Step 4.

1. **Problem real, repo right?** Verify the symptom against current code/behavior, not just the PR description — trace "X causes Y". Locate the ROOT CAUSE. If it lives upstream, in a dependency, or in a consumer's misconfiguration, a fix here bakes a permanent deviation into this repo — that's a blocker, not a feature. Name where the cause actually lives, with evidence.
2. **Right approach, right layer, worth its permanent cost?** Enumerate 2–3 realistic alternatives (different layer, config-only, fix upstream, compose existing pieces, do nothing) and why each loses. Weigh value vs maintenance cost explicitly: this code is maintained FOREVER. A cleaner alternative needing less/no code in this repo makes the heavier approach a blocker even when it works — but name and ideally demonstrate the alternative; bare "not worth it" is a non-blocking note.
3. **Tradeoffs & scope.** Is this the minimal honest change? Name the minimal acceptable subset; block the over-reach.
4. **Docs sync.** Open the actual user-facing doc page and read it before declaring docs in sync. Stale docs in the changed area = blocker.
5. **Code quality** → Step 4.

## Step 4 — Two-lane reviewer race

Two independent reviewer passes over the diff, routed through **different herd models** (never the same model twice — a single model's blind spots are the failure mode). Each lane produces findings with `file:line`. Then cross-validate — a finding ships only with evidence:

- Both lanes found it + evidence → high confidence.
- One lane found it + evidence → include.
- One lane found it, evidence missing → EXCLUDE; list under disproven/dismissed.
- Lanes contradict → dig deeper; the evidence-backed conclusion wins.

**Evidence format**: each finding carries an `**Evidence**:` line — what was checked, what proves it (source link, spec clause, observed behavior). Counter-example (rejected): "X might cause Y" with no check of the mechanism. No speculation ships.

## Step 5 — Our quality bar

On top of the frames, every PR is held to what our shipped upstream work proved necessary:

- **Builds clean** on current HEAD of the target repo. Never installs or replaces running software to verify.
- **Real reproduction** for bugfix PRs: the bug is demonstrated (command, output, before/after), not asserted from reading.
- **In-tree regression test** covering the full contract — valid use AND rejected/invalid/boundary behavior, not happy-path only.
- **No monkeypatch.** Minimal diff. Where the fix wasn't obvious, competing designs were raced and the loser is preserved in history with the rationale recorded.
- **Tests gate**: area already has tests + new/changed code without contract-defining tests = NOT LGTM. (Area with no test convention: recommend, don't block.)
- **No-regression gate**: what worked keeps working across configs, defaults, and flags. "Few users", "edge case", "rare config" never justify a regression. Only an explicitly declared, migration-documented breaking change passes, surfaced in the verdict — never silent.

## Step 6 — Classify

- **Blockers → `NOT LGTM`** (REQUEST_CHANGES): production bugs, security holes, data-loss risks, broken API contracts, broken variants, tests-gate failures, regressions, silent-failure error handling, resource leaks, stale docs in the changed area, unmet ticket requirements, value/design blockers from Frames 1–3 (with the same evidence bar — root-cause location, spec clause, or demonstrated cleaner alternative).
- **Action items** (non-blocking): tech debt worth tracking, naming/abstraction, non-urgent perf, internal doc gaps, pre-existing issues adjacent to (not touched by) the PR — each gets a home (filed issue, parked branch, memory entry) before the gate closes.

## Step 7 — Draft the review

First line: `<LGTM | NOT LGTM> — <one-sentence why>`. Then business context (one sentence), blockers (`**File**: path:line`, `**Issue**`, `**Evidence**`, `**Impact**`, `**Fix**`), non-blocking follow-ups, ticket compliance if applicable, disproven findings.

Style: findings only — no praise, no "overall looks good". No AI attribution ("Claude says", "automated review found"). No private infrastructure (cluster names, IPs, client names). No internal tool names or skill paths. English. Inline comments only on lines that exist in the diff.

## Step 8 — Present

Show: verdict + the API event it would carry (APPROVE / REQUEST_CHANGES), full body, inline comments with file:line, disproven list. **If `--publish` was not passed, this is the deliverable — stop.** Do not call any write-side GitHub API.

If `--publish` was passed: this output is an approval gate. Apply any requested changes, re-present, and continue to Step 9 only after explicit approval of the exact text.

## Step 9 — Publish (only `--publish` + explicit approval)

Post via the `github` skill (`bin/gh.py`; extend it with POST support if the review endpoint needs it — never hand-roll auth, the credential stays in the vault). Reuse-vs-new: update your existing review in place ONLY when your latest non-dismissed review already carries the intended state (APPROVE / CHANGES_REQUESTED); a verdict change always posts a NEW review, since the update endpoint can't change a submitted review's event. Gate-mode notes post as COMMENT with no verdict word. Print the review URL for verification.

## Standing rules

- **Draft by default.** Nothing reaches GitHub without the flag AND the user's approval of the exact text.
- **Readiness gate before substance.** No verdict on unmergeable/broken code.
- **No evidence, no finding.** Speculation is dropped, not softened.
- **API is truth; `origin/` refs only.** Stale local branches produce phantom findings.
- **Scope of action**: reviewing PRs anywhere is fine. *Opening* upstream PRs follows standing policy — our `toxicwind/*` forks are the default target; mainline super-repo PRs need Chris's explicit word each time. Never open anything against an original upstream on your own initiative.
- **PR footer**: when the review leads to a PR body we author, use the cross-link pattern in `~/workspace/goals/stars-to-consulting-pipeline/files/pr-crosslink-pattern.md` (rotate the related-project link — Brand is deprecated, link a live project).