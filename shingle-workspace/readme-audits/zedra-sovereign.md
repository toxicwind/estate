# README audit — toxicwind/zedra-sovereign @ 53f9909e — 2026-09-14

**Verdict:** REWRITE (no README exists at all; GitHub description doubles as the summary and is wrong on two of its four claims)

## Claims

The repo has no README on `main` (only branch). Claims below are from the GitHub
repo description, the de-facto public summary:

| Claim (repo description) | Evidence | Verdict |
|---|---|---|
| "Private mirror" | API: `private: false` — repo is PUBLIC | WRONG |
| "mirror of zedra" | Tree has 18 entries, zero Rust code: no `crates/`, no `Cargo.toml`, no `vendor/`. zedra source is not in the repo at HEAD | WRONG |
| "host daemon" | Only `check-zedra-host.sh`, which shells out to `/home/toxic/projects/zedra-tanlethanh` on awrawr-pc — not in the repo | WRONG |
| "bound to sovereign router (:25104)" | Only 3 mentions, all inside `AUDIT.md` describing a wrapper at `/home/toxic/.local/bin/zedra-ai-wrapper.sh` (awrawr-pc-local, not in repo). No code in the tree touches `:25104` | WRONG |
| "AUDIT.md inside" | `AUDIT.md` exists at root (7186 bytes), documents zedra + sovereign integration | VERIFIED |

Mechanical (`bin/audit.py`): `readme-exists` → FAIL ("README.md not found").

## Missing from README

There is no README, so everything real is uncovered. The repo's actual current
content (per the last ~20 commits, all 2026-09-03 → 2026-09-14) is an **agentic
lens experiment**, not a zedra mirror:

- `lib/lens-orchestrator.js` (c940bc08) — auto-discovers `lens_*.js`, v2.0.0-agentic
- 4 lenses in `src/_11ty/lenses/`: tectonic (drift scoring, 7b8d2f4e), stylometric (edbde595), osint (728270c5), cryptographic leak detection (9790cfbe)
- `.github/workflows/agentic-lens-ci.yml` (64d83dd8, c636d3ee) + `tectonic-drift.yml` (b5a1bd16, 53f9909e) — daily drift cron + push CI
- `.env.example` (c5fd139f) — `LENS_ENABLED`, `ZEDRA_DAEMON_HOST=localhost:17357`, etc.
- `fetch-vendor.sh` / `check-zedra-host.sh` (7b15f6a6) — hardcode awrawr-pc paths (`/home/toxic/projects/zedra-tanlethanh`); non-portable, undocumented

Also stale: `AGENTS.md` claims "Stack: Rust, GPUI, TypeScript" and "Fork stays private under toxicwind" — no Rust in the tree, and the repo is public.

## Quickstart check

- [ ] Commands exist — N/A, no README/quickstart
- [ ] Ports/config keys match code — N/A
- [ ] A fresh user could follow it end to end — No. Scripts reference `/home/toxic/...` paths and would fail anywhere else.

## Action taken

- None (REPORT ONLY). README needs to be written from scratch, or the repo
  description corrected at minimum: drop "Private", drop "mirror of zedra".
  Note: authenticated `/tarball/HEAD` 404s for this repo while the
  unauthenticated endpoint works — audit used the unauth tarball + API tree
  (verified identical: 18 entries, HEAD 53f9909e).
