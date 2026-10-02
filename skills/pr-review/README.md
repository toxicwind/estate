![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/pr-review?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/pr-review?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/pr-review?style=for-the-badge)

# pr-review
Audit a GitHub PR and render a verdict — LGTM or NOT LGTM, every finding evidence-backed

## What it does
Complete GitHub Pull Request review system that implements readiness gates, five-frame substance passes, two-lane reviewer races, and quality bars to produce evidence-backed LGTM/NOT LGTM verdicts.

## Why it matters
Provides systematic, evidence-based PR reviews that prevent merges of problematic code while avoiding false positives, ensuring only safe, well-understood changes enter the codebase.

## Who it's for
Maintainers, tech leads, and developers responsible for reviewing pull requests who need a structured, evidence-based approach to maintain code quality and safety.

## Features
- **Readiness Gate** - Early exit for merge conflicts or red CI plausibly caused by diff (no verdict on unmergeable/broken code)
- **Five-Frame Substance Pass** - Evaluates problem validity, approach correctness, tradeoffs/scope, and documentation sync
- **Two-Lane Reviewer Race** - Independent reviews via different herd models with evidence requirements for findings
- **Quality Bar** - Requires clean builds, real repro for bugfixes, in-tree regression tests, no monkeypatching, and test/no-regression gates
- **Evidence-Driven Findings** - Every claim includes evidence line showing what was checked and what proves it
- **Draft-by-Default** - Nothing reaches GitHub without explicit approval of exact review text
- **Auto-Publish** - Post-approval publishing to GitHub with update-vs-new logic preservation

## Quick Start
```bash
# Draft review (default, nothing published)
pr-review github.com/user/repo/pull/123

# Draft review from current branch
pr-review

# Publish review after explicit approval
pr-review --publish github.com/user/repo/pull/123
# (Review output shown, then you must explicitly approve the exact text)
```

## Configuration
- **PR Reference** (positional, optional): URL (`github.com/.../pull/N`), shorthand (`owner/repo#N`), or bare number (`#1234`)
- **`--publish` Flag**: Enables posting to GitHub; without it, draft is deliverable and nothing leaves the box
- **Trigger Sources**: PR URL, shorthand, bare number, or "this PR" resolvable from context
- **Backing Services**: 
  - `github` skill for API calls (`~/workspace/skills/github/bin/gh.py`)
  - Herd-routed reviewer lanes (different models per lane)
  - `.super-ralph/workflow.db` for database grounding (telemetric oracle)

## Development
Review logic implemented in SKILL.md with estate-specific adaptations:
- Uses `github` skill instead of `gh` CLI
- Herd-routed reviewer lanes instead of fixed model pairs
- Quality bar derived from real upstream work
- Chris-voice PR body requirements

## License
Internal tool - refer to sovereign estate licensing

## Security
- **API Truth**: Uses `origin/` refs only, never trusts local stale branches
- **No Keystroke Injection**: Observational only, never injects `tmux send-keys` or synthetic prompts
- **Credential Safety**: Relies on existing `custom.github` credential, never prompts for keys
- **Scope Limitation**: Review authority limited to PR scope, no general code questions about branches without PRs