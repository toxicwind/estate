# Audit Checklist — the full runnable list

Priority order. Fix top-down; items 1–5 decide the 10-second verdict.

## P0 — the 10-second verdict
- [ ] `README.md` exists at repo root
- [ ] README has a shields/badges row at the top
- [ ] README has a one-line description (what/for whom/benefit)
- [ ] README has a demo (GIF/screenshot/asciinema) above the fold
- [ ] README has a quickstart (copy-paste to first success)
- [ ] `LICENSE` or `LICENSE.txt` exists at repo root with holder/year filled in

## P1 — trust signals
- [ ] CI configured and badge is green (not red, not 404)
- [ ] Repo description set on GitHub (< 140 chars, keyword-rich)
- [ ] Topics set (8–12 relevant, popular spellings)
- [ ] Social preview image uploaded (1280×640)
- [ ] `CHANGELOG.md` exists and has a recent entry

## P2 — depth and docs
- [ ] `docs/` directory or wiki with beyond-README documentation
- [ ] `examples/` with runnable examples (each one actually runs)
- [ ] README sections in order: About → Built With → Getting Started → Usage → Roadmap → Contributing → License
- [ ] Every code block in README/docs is tested and works

## P3 — community friction removers
- [ ] `CONTRIBUTING.md` exists and is short (< 100 lines ideal)
- [ ] `CODE_OF_CONDUCT.md` exists (Contributor Covenant)
- [ ] `.github/ISSUE_TEMPLATE/` has bug-report and feature-request templates
- [ ] `PULL_REQUEST_TEMPLATE.md` exists and is < 15 lines
- [ ] `SECURITY.md` exists (required if security/network/auth-adjacent)

## P4 — star-killer sweep
- [ ] No "TODO" or placeholder text in README
- [ ] No broken badge URLs (all return 200)
- [ ] No jargon-first one-liner
- [ ] Recent commit activity (or a fresh "alive" commit + changelog entry)
- [ ] Repo name is searchable (contains a keyword for what it does)
- [ ] Default branch is `main`
- [ ] No dead branches cluttering the picker

## Scoring
- P0 all pass: repo is presentable (floor for public release)
- P0+P1 all pass: repo is trustworthy (stars can start accumulating)
- P0–P3 all pass: repo is star-grade (maximal legitimate appeal)
- P4 clean: no self-sabotage
