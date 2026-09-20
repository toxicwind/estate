# Meta / Muse AI

Field notes on the Muse platform (platform codename **hatch**), reverse-engineered from inside a running runtime cell on 2026-09-14. Evidence-based: every claim cites the script, file, or observation it came from. No Meta docs were harmed (or consulted). `JARVIS` remains only as the runtime-cell internal codename.

- [runtime-cell.md](runtime-cell.md) — what a "cell" is, lifecycle, persistence model, naming map
- [open-questions.md](open-questions.md) — what we still don't know (replacement triggers, quotas, Sentinel, channels)

Audience: anyone operating agents on this platform who needs to know what survives a restart (almost nothing local) and where the real state lives (the external DB, `/home/hatch`).
- approvals.md — how approvals/permissions actually behave; *(not yet written)* the agent CAN open the user Settings via the ui namespace (the shipped docs were wrong)
- fleet-freeze-20260914.md — full fleet inventory *(not yet written)* + stop procedure from the 2026-09-14 freeze; activity cards outlive their agents

---
## Estate docs

- **Fleet knowledgebase** — the canonical estate map, active crews, repo index,
  standing rules, and docs index (source of truth; this README does not
  duplicate it):
  <https://github.com/toxicwind/sovereign-projects/blob/main/docs/fleet-knowledgebase.md>
- **Master README** — the doc-graph root:
  <https://github.com/toxicwind/sovereign-projects/blob/main/README.md>
