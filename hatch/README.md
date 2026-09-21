# hatch/ — the hatch (cell) side of the world

The hatch runtime cell's half of the estate, tracked on yote.

| Path | What it is |
| ---- | ---------- |
| [`agents/ember/`](agents/ember/) | Ember's operational home (moved from `/home/toxic/shingle`) |
| [`docs/`](docs/) | Consolidated hatch/bridge/cell documentation |
| [`bin/`](bin/) | Canonical hatch-side watchdog code (`watchdog_lib.py` + `progress-watchdog`); the deployed copies in `~/workspace/bin/` on the cell are synced from here |

> [!NOTE]
> Layout SSOT for the 2026-09-20 reorg: [`../REORG-PLAN.md`](../REORG-PLAN.md).

Squawk (the agent-to-agent chat) is driven by `bin/squawk` — one-command wrapper over HMAC-signed, profile-based message publication (fleet/lead channels, global sequence). Squawk is Chris-important: `:25147` (ws) + `:25135` (feed).

---

*Up: [root README](../README.md) · [fleet knowledgebase](../docs/fleet-knowledgebase.md) · [↑ top](#hatch--the-hatch-cell-side-of-the-world)*
