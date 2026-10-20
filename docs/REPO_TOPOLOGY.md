# Repo topology — the estate, ranch, and GitHub, explained once

**Status:** canonical consolidation, 2026-10-20. Supersedes the scattered,
sometimes-conflicting descriptions in `README.md` §Repo-topology,
`docs/CONVENTIONS.md` §13/15, `docs/2026-10-07-estate-forward.md`,
`docs/estate-map.md`, `REORG-PLAN.md`, `findings.md`, `AUDIT.md`, `TODO.md`,
and the tau plans. Where this file conflicts with any of those, **this file
wins** — fix the others.

---

## The one-sentence model

> **estate** is the control plane, **ranch** is the workshop, **hatch/kite** is
> the private cell, and the ~214 components under ranch are **independent
> git checkouts glued by `gitkb/meta` — not git submodules.**

This is a deliberate, hard-won decision (made 2026-09 → 2026-10 against real
breakage). The submodule mechanism is **banned** here. Re-introducing a gitlink
is a defect.

## The two paragraphs that replace the confusion

1. **estate** (`toxicwind/estate`, `/home/toxic/estate`) is the _control
   plane_: the pitchfork daemon inventory, `config/`, `bin/`, `docs/`, the
   fleet, the policies. It supervises and routes. Its `ranch/` child is
   **gitignored** — a separate repo nested in the checkout with its own
   history and its own origin (`toxicwind/ranch`). estate does **not** track
   ranch as a submodule (CONVENTIONS §13.3: "estate treats `ranch/` as a
   separate repo by simply not indexing it").

2. **ranch** (`toxicwind/ranch`) is the _workshop monorepo_: one directory per
   component (herd, hodos, gatehouse, cuttinggate, tau, forge, squawk, keryx,
   roost, …). Every component is its own repo with its own origin
   (`toxicwind/<component>`), coordinated by the `gitkb/meta` manifest
   (`.meta.yaml`, generated from `.gitmodules`): **"repos are PEERS, not
   hierarchy."** Sync everything with `meta git update` / `meta git status` /
   `meta exec '<cmd>'` (exposed in moon as `ranch-sync`/`ranch-status`/`ranch-exec`).

## The canonical mental model (2026-10-07 forward, kept)

| Plane               | Repo / path                                                                 | Role                                                            |
| ------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Ops / master        | `toxicwind/estate` → `~/estate`                                             | pitchfork, config, bin, stack, ports                            |
| Projects / monorepo | `toxicwind/ranch` → `~/estate/ranch`                                        | animals as directories                                          |
| Control cell        | `toxicwind/hatch` (private) → `/home/toxic/hatch` / `/home/toxic/kite/kite` | Ember; light only; real identity **kite**, dodge name **hatch** |
| Bot plane           | `ranch/arroyo/`                                                             | overlord · coyote · discord (+ MCP shim)                        |
| Public MCP          | `ranch/doorbell` (+ satellite `toxicwind/doorbell`)                         | `:25202`                                                        |
| Agent (own cadence) | `toxicwind/tau`                                                             | one SSOT (`~/.tau`)                                             |
| Fleet / oracle      | ranch + `toxicwind/squawk`                                                  | as today                                                        |
| Host                | **yote** = awrawr-pc                                                        | machine ≠ bot product                                           |

Satellites exist only where they must: curl-install (`doorbell`), private cell
(`hatch`), independent release (`tau`, maybe `squawk`). Everything else is a
ranch dir or archive.

## The rules that keep it clean (from CONVENTIONS, ratified)

- **Rule — no gitlinks.** A directory with its own `.git` must not be
  indexed as a gitlink by its parent. "If a sync creates `.git` in the in-tree
  copy, the tree is silently a submodule again. Refuse the sync and clean up."
- **Rule — one `.gitmodules` entry.** Only the github/gitignore single entry
  is allowed. Any addition is a top-level defect to undo.
- **Rule — fork = standalone + in-tree copy (deliberately duplicated).** The
  standalone repo carries the real history + `upstream` remote (merges happen
  only there); the in-tree copy is committed real files so a fresh clone works
  with no submodule and no second checkout. **Do not "deduplicate" this.**
- **Rule — never rebase, squash, or force-push a fork's `main`**; merge commits
  preserve the audit trail. Record every merge in `MERGE-DECISIONS.md`.
- **Rule — compat symlinks are load-bearing** (`/home/toxic/projects`,
  `/home/toxic/ranch`, `/home/toxic/estate`). Don't delete one without grepping.

## Owning-repo lookup (the "where do I commit this?" table)

| Path (on disk)                                                                                            | Owning repo                                                                          |
| --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `/home/toxic/estate/**` (except `ranch/`, `vendored/`, `var/`)                                            | `toxicwind/estate`                                                                   |
| `/home/toxic/estate/ranch/**`                                                                             | per-component (`toxicwind/<component>`) — the component's own repo, driven by `meta` |
| `/home/toxic/estate/ranch/**/moon.yml`, `.moon/**`, `.gitmodules`, `.meta.yaml`, `README.md` (structural) | `toxicwind/ranch`                                                                    |
| `/home/toxic/estate/vendored/**`                                                                          | third-party — own remotes, never indexed                                             |
| `/home/toxic/hatch`, `/home/toxic/kite/kite`                                                              | `toxicwind/hatch` (private)                                                          |
| `~/.tau`                                                                                                  | `toxicwind/tau` (agent engine SSOT)                                                  |

Rule of thumb: **a nested repo's files belong to that repo, not the ancestor.**
Never assume "nested ⇒ same repo"; resolve via the table or `meta context`.

## Known pain points and their fixes (open work, from TODO + findings)

| Pain                                       | Root cause                                                                         | Fix (owner)                                                         |
| ------------------------------------------ | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| "Have to update submodules"                | stray gitlinks / `.gitmodules` growth                                              | sweep gitlinks → `meta` checkouts; enforce one-entry rule (§ sweep) |
| editing/writing the wrong ranch            | duplicate `/home/toxic/ranch` checkout (Oct 3 estate-map: "NOT the daemon target") | delete the duplicate, repoint to `~/estate/ranch`; keep symlink     |
| `.git` reappears in in-tree fork copies    | rule 15.2 violation                                                                | refuse + clean on sync                                              |
| 54+64 "dirty submodules" forward-committed | historical                                                                         | normalize to independent checkouts (TODOs)                          |
| OmniRoute shown as gitlink                 | in-flight union-merge                                                              | land → independent checkout (TODO line 37)                          |
| which-repo-owns confusion                  | scattered docs                                                                     | **this file** + the lookup table                                    |

## Sync, the one way

```bash
cd /home/toxic/estate/ranch
meta git update         # clone missing + pull all (repos are peers)
meta git status         # per-repo state across all components
moon run ranch-sync     # same thing as a moon task
```

---

Companions: [`AGENTS.md`](../AGENTS.md) (standing directives),
[`docs/CONVENTIONS.md`](CONVENTIONS.md) (git rules §13/15),
[`docs/estate-map.md`](estate-map.md) (generated service/topology map),
[`.meta.yaml`](../ranch/.meta.yaml) (the meta peer manifest).
