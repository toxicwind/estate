# Meta / Muse AI

Field notes on the Muse platform (internal codename **Jarvis**), reverse-engineered from inside a running runtime cell on 2026-09-14. Evidence-based: every claim cites the script, file, or observation it came from. No Meta docs were harmed (or consulted).

- [runtime-cell.md](runtime-cell.md) — what a "cell" is, lifecycle, persistence model, naming map
- [open-questions.md](open-questions.md) — what we still don't know (replacement triggers, quotas, Sentinel, channels)

Audience: anyone operating agents on this platform who needs to know what survives a restart (almost nothing local) and where the real state lives (the external DB, `/home/hatch`).
