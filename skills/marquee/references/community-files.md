# Community Files — lowering the bar for contributors

Stars follow engagement. Engagement follows low friction. These files are the friction removers.

## CONTRIBUTING.md
The on-ramp. Keep it short — nobody reads a 2000-word contributing guide before their first PR.
- How to set up a dev environment (commands, not prose)
- How to run tests
- The PR process (branch naming, what reviewers look for)
- What "good first issue" means in this repo
- Link it from the README's Contributing section — never inline the whole thing

## Code of Conduct
`CODE_OF_CONDUCT.md` — use the Contributor Covenant, don't write your own. Its presence signals "this is a safe project to contribute to." Its absence signals "the maintainer hasn't thought about community." One file, standard text, done.

## Issue templates (`.github/ISSUE_TEMPLATE/`)
Pre-structured issues get better reports and get answered faster, which signals an alive project.
- `bug-report.md` — what happened, what was expected, repro steps, environment, version
- `feature-request.md` — problem statement, proposed solution, alternatives considered
- `config.yml` — blank-issue fallback text pointing to discussions, plus contact links
- Use YAML frontmatter (`name:`, `about:`, `labels:`) so GitHub renders the template picker

## Pull request template
`PULL_REQUEST_TEMPLATE.md` at repo root or `.github/`:
- What this PR does (one paragraph)
- Checklist: tests pass, docs updated, changelog entry
- Keep it to 10 lines — a 50-line template gets deleted by contributors

## FUNDING.yml (optional)
`.github/FUNDING.yml` — GitHub Sponsors, Open Collective, etc. Only add if you actually want funding; an empty sponsors button is noise. But if the project takes off, retrofitting funding is harder than having it from day one.

## Security policy
`SECURITY.md` — how to report vulnerabilities (private channel, not public issues). Required for any project that touches security, auth, or network input. Its absence on a security-adjacent project is itself a star-killer.

## Discussions vs Issues
Enable GitHub Discussions for Q&A and ideas; keep Issues for actionable work. A repo where every question becomes an issue looks messy. Pin a "start here" discussion for newcomers.
