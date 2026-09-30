# Meta / Muse AI — field notes from inside a runtime cell

Evidence-based notes on the Muse platform (platform codename **hatch**), reverse-engineered from inside a running runtime cell on 2026-09-14. Every claim cites the script, file, or observation it came from. No Meta docs were harmed (or consulted). `JARVIS` remains only as the runtime-cell internal codename.

<div align="right">

[![license: MIT](https://img.shields.io/badge/license-MIT%20%2B%20upstream-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects#license)
[![sovereign-projects](https://img.shields.io/badge/sovereign--projects-main-6e56cf?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects)

</div>

## Why this exists

Agents operate on this platform every day without knowing what survives a restart (almost nothing local) or where the real state lives (the external DB, `/home/hatch`). These notes answer those questions with observations, not documentation quotes — because the docs have been wrong before and the box doesn't lie.

## What's here

| Doc | What it answers |
|---|---|
| [runtime-cell.md](runtime-cell.md) | What a "cell" is: lifecycle, persistence model, naming map |
| [open-questions.md](open-questions.md) | What we still don't know (replacement triggers, quotas, Sentinel, channels) |

Planned but not yet written — claim them before duplicating the work:

- `approvals.md` — how approvals/permissions actually behave; the agent CAN open the user Settings via the ui namespace (the shipped docs were wrong)
- `fleet-freeze-20260914.md` — full fleet inventory + stop procedure from the 2026-09-14 freeze; activity cards outlive their agents

```mermaid
flowchart TB
    subgraph cell[runtime cell — ephemeral]
        A[agent cognition]
        W[/home/hatch workspace]
    end
    subgraph durable[what survives]
        DB[(external DB)]
        H[/home/hatch<br/>persists across restarts]
    end
    A --> DB
    W -.->|survives restart| H
    cell -.->|cell replaced| X[local state gone]
```

Audience: anyone operating agents on this platform — read `runtime-cell.md` before building anything that assumes local persistence.

## Quick start

```bash
ls docs/Meta/"Muse AI"/        # this directory
less docs/Meta/"Muse AI"/runtime-cell.md
```

## Estate docs

- **Fleet knowledgebase** — the canonical estate map, active crews, repo index, standing rules (source of truth; this README does not duplicate it):
  <https://github.com/toxicwind/sovereign-projects/blob/main/docs/fleet-knowledgebase.md>
- **Master README** — the doc-graph root:
  <https://github.com/toxicwind/sovereign-projects/blob/main/README.md>

## Contributing

New field notes go here as dated `.md` files with the evidence chain attached: claim → observation (script/file/output) → verdict. "The docs say X" is not evidence. If a note's claim dies (platform changed), update it in place — stale field notes are worse than none.

## License & security

MIT where marked — [LICENSE](https://github.com/toxicwind/sovereign-projects#license). These are observations about a platform you don't control: treat platform-internal details (socket paths, codenames, env-var inventories) as operational notes, never as credentials or access paths. Nothing here authorizes crossing a platform boundary.
