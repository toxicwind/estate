---
crew: "vanta"
scope: "Marquee lane: star-grade maximalization of toxicwind/duet (survey -> audit -> fix -> verify -> ship). Distinct from skimmer APK project."
owner: "Ember"
status: "DONE (2026-10-01) — commit de627069"
order: 205
registered: "2026-10-01"
updated: "2026-10-01"
---

# vanta

Marquee maximalization lane (wave 3) — COMPLETE.

**Repo:** toxicwind/duet (real-time two-way file sync over SSH)
**Result:** 5/21 -> 17/21 audit checks; CI fixed and green; shipped to master.

Commits:
- 73aa3cb: docs: marquee star-grade pass (README, docs/, examples/, community files)
- 6a6e64b: ci: self-contained workflow (was upstream-dependent, never ran)
- 528541b: ci: add workflow_dispatch
- de62706: ci: tolerate missing TS tests

**Gaps fixed:** badges, quickstart, docs/, examples/, CONTRIBUTING, CoC, SECURITY, issue/PR templates, topics (10), install.sh repo URL, CI infrastructure.
