# README audit — toxicwind/ontological-atlas @ 2c0887f3 — 2026-09-14

**Verdict:** NEEDS UPDATE

Repo: public, Python, 74 KB, default branch `main`, 9 commits total. Audited via shallow clone at `2c0887f3d2442c0c27be17c8652d4df4369281be` (tarball endpoint 404'd; git clone used instead). Mechanical checks all PASS (trivially — 25-line README, no bad links).

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| "modular research framework mapping the co-constitutive nature of reality" | GitHub repo description identical; SKILL.md:4 overview matches | VERIFIED |
| Module links 01–07 → `modules/<name>/` | All 7 dirs exist in tree (modules/01-rendering-engine … 07-substrate) | VERIFIED |
| 01 "Observer is the apparatus" | modules/01-rendering-engine/README.md:3 "subject-object split is a rendering artifact" | VERIFIED |
| 02 "Ebu Gogo, little people gradient" | modules/02-folklore-interface/ has ebu-gogo-decompression.md, global-little-people-gradient.md; README.md:3 matches | VERIFIED |
| 03 "UAP, DMT, music" | modules/03-consciousness-technologies/: uap-control-system.md, dmt-entity-research.md, somatic-bypass-music.md; README.md:3 matches | VERIFIED |
| 04 "Constitutional immune response" | modules/04-ai-alignment-ontology/constitutional-immune-response.md; README.md:3 "Guardrails are ontological enforcement" | VERIFIED |
| 05 "Orch OR" | modules/05-quantum-biology/orch-or.md | VERIFIED |
| 06 "Primary sources" | modules/06-source-archive/README.md:3 "OSINT primary sources and methodology" (dir holds only that README) | VERIFIED |
| 07 "Audio forensics + system tools" | modules/07-substrate/README.md:3 "Audio forensics and system survival tools"; scripts/ has als.py, stems.py (audio) + cdp.py, pyfix.py, gh_recon.py (system) | VERIFIED |
| Quickstart: `python3 scripts/loader.py boot` | scripts/loader.py:6 `boot()` exists; runs OK (arg ignored, prints booted JSON) | VERIFIED |
| Quickstart: `python3 scripts/audit.py` | scripts/audit.py exists, runnable entry point | VERIFIED |
| Quickstart: `python3 scripts/test.py` | scripts/test.py exists; self-checks required files, all pass | VERIFIED |
| "License: CC0 1.0 Universal" | No LICENSE/COPYING file anywhere in tree | UNVERIFIED |

## Missing from README

Real features/changes with no README coverage:

- **v4.1 (10d8dbb3, 2026-08-17) added `scripts/swarm.py` (swarm orchestrator), `scripts/monitor.py` (live monitor), and `.github/workflows/universal-skill-ci.yml` ("Universal Skill CI", runs on push + every 6h)** — none mentioned. Commit message explicitly flags these as headline features ("MAX LEVEL").
- `scripts/push.py` and `scripts/fix.py` exist but quickstart omits them (SKILL.md documents `push.py` and `--full` audit flag; README's `audit.py` has no flags).
- No LICENSE file to back the CC0 claim.
- (SKILL.md-only issue, not README: architecture diagram lists `env/{apt,venv,bin}/` which is absent from the tree — created only as a side effect of running `loader.py boot`.)

## Quickstart check

- [x] Commands exist
- [x] Ports/config keys match code (none involved; pure Python scripts)
- [x] A fresh user could follow it end to end (loader runs, audit/test have working entry points)

## Action taken

- None — REPORT ONLY per task. Suggested fixes for owner: add a LICENSE file (or drop the CC0 line), and add one line to the README covering `swarm.py` / `monitor.py` / CI from v4.1.
