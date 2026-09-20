# README audit — toxicwind/qed @ ed21f1e0 — 2026-09-14

**Verdict:** REWRITE

The README describes a Rust AI-native code editor forked from zed-industries/zed.
The repo is actually a JavaScript text-analysis toolkit (4 "lens" modules + an
orchestrator + 2 CI workflows). 12 commits total; the README was last touched
2026-08-17 (`6a464cc7` "sovereign rebrand") and predates all actual code
(2026-09-03..04). Nearly every factual claim is WRONG.

## Mechanical (bin/audit.py)

- readme-exists: PASS (2191 chars, 53 lines)
- relative-links-resolve: FAIL — `./LICENSE` linked twice, file absent
- badge-workflows-exist: FAIL — badges reference ci.yml, lint.yml, test.yml, security.yml, upstream-sync.yml; actual workflows: `.github/workflows/tectonic-drift.yml`, `.github/workflows/agentic-lens-ci.yml`
- quickstart-entrypoints: WARN — `./target/release/qed` not in tree (no Cargo project at all)
- external-links-alive: WARN — badge image URLs return HTTPError

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| "The definitive AI-native code editor" | Tree: 4 JS lens modules, `lib/lens-orchestrator.js`, 2 workflows, no editor code anywhere | WRONG |
| "fast, Rust-based editor ... same foundation" as Zed | No `Cargo.toml`, no `.rs` files; only `.js`/`.yml`/`.md` | WRONG |
| Feature table: enforced AI editing, interleaved reasoning, NVIDIA native, universal MCP proxy, full autonomy | No such code; lenses do regex/trigram analysis only | WRONG |
| Quickstart: `cargo build --release` + `./target/release/qed` | No Rust project, no binary target | WRONG |
| "437 commits ahead with autonomous enhancements" | 12 commits total (API `commits?per_page=20`, newest `ed21f1e0` 2026-09-14T09:41:04Z) | WRONG |
| "Daily automated sync via GitHub Actions" with zed upstream | No upstream-sync workflow; only scheduled job is `tectonic-drift.yml` (cron `0 6 * * *`), which runs a repo-health lens, not a sync | WRONG |
| "Upstream code remains under its original license" / sync capability with zed-industries/zed | No fork relationship evidence in tree; no sync code | WRONG |
| "Sovereign Open License (SOL) v1.0 — see LICENSE" | No LICENSE file in tree; `./LICENSE` link 404s | WRONG |
| "QED enhancements are licensed under SOL v1.0" | Same — no license file | UNVERIFIED |
| Badge: Upstream Sync workflow | `upstream-sync.yml` does not exist | WRONG |
| Star CTA / "The proof is complete" | Marketing copy, not a repo claim | UNVERIFIED |

## Missing from README

Real features with no README coverage (all landed 2026-09-03..04, after the README was last touched 2026-08-17):

- `lib/lens-orchestrator.js` — LensOrchestrator auto-discovers `lens_*.js` modules (`ce1b921f`)
- `src/_11ty/lenses/lens_tectonic.js` — repo health/drift scoring (`24a5a7de`)
- `src/_11ty/lenses/lens_osint.js` — URL/email/IP regex extraction (`3d70317d`)
- `src/_11ty/lenses/lens_stylometric.js` — trigram fingerprinting, entropy (`44c29a8c`)
- `src/_11ty/lenses/lens_cryptographic.js` — key/hash/GitHub-token detection (`b8a54593`)
- `.github/workflows/agentic-lens-ci.yml` — push/PR lens pipeline + MCP smoke (`95b63a04`, `fa402c77`)
- `.github/workflows/tectonic-drift.yml` — daily scheduled drift check (`b077a521`, fixed `ed21f1e0`)
- `.env.example` — LENS_*/SWARM_* config keys (`29519c56`)

## Quickstart check

- [ ] Commands exist — `cargo build --release` fails (no Cargo project)
- [ ] Ports/config keys match code — no ports mentioned; config keys (`LENS_ENABLED` etc.) not mentioned
- [ ] A fresh user could follow it end to end — NO: build command invalid, LICENSE link broken, all badges dead

Note: `AGENTS.md` is equally stale (describes a Rust GPUI editor at `/home/toxic/projects/qed`) but is outside README scope — flagged here for the follow-up pass.

## Action taken

- None — REPORT ONLY per task. Repo untouched; scratch under /tmp/readme-audit-qed-dl/qed.
