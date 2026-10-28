# PENS — the hyper master concept (one contract above all products)

> **pens IS the estate's master idea**: five uniform pens, one shape. Every
> product — tau, kappa, mimetite, thresher, pseudobrookite — is a **peer
> standalone checkout** under the pen whose *theme* it serves, referenced
> never owned, symlinked into `~/.local/bin` by the estate-ops manifest.
> Any guide written below another level must refine, never contradict, this
> file. Guides are **added as we go** (append a `## Guides` row, never fork a
> second truth).

## The five pens (placement rule = theme, verified in `geode/PLAN.md` §0)

| Pen | Theme | Examples |
|---|---|---|
| `pens/estate/` | **control plane** — config, pitchfork, services, state, docs | pitchfork.toml, config/ports.env, docs/ |
| `pens/geode/` | **inference plane** — catalog, routers, engines, auditors | mimetite, rhodochrosite, bornite, chalcopyrite, azurite, pseudobrookite |
| `pens/barn/` | **ops tooling** | thresher, weave, secretsmith, estate-ops |
| `pens/ranch/` | **fleet & model components** | squawk, github-search (blackbird), rename-roundup |
| `pens/olympus/` | **Greek-named products** | tau, kappa, sigma, keryx, muse |

## The three commands every product answers to

1. **Meta-permanence ("save all")** — branch → tmp commit → micro merge
   straight to main, forward-only, save-as-we-go; live green-blue deploy
   (green stays runnable, blue healthchecked, swap, instant rollback).
   Primitive: `pens/geode/products/pseudobrookite/scripts/save-all.ts`,
   `…/scripts/deploy-green-blue.ts`.
2. **Hyper-tailrec todo creation** — the goal IS the todo loop: every turn
   re-reads the board, spawns subtodos reactively (architect-approved),
   writes docs for every not-fully-realized concept it touches, and
   deeplinks them. Loop doc: [`docs/prompt-as-ir.md`](docs/prompt-as-ir.md).
3. **Blackbird-forward search** — any skill that touches GitHub search uses
   **blackbird** (`pens/ranch/github-search`, session-cookie web engine)
   exclusively; the REST `/search/code` path is dead doctrine
   (`AGENTS.md` search doctrine, 2026-10-28).

## Guides (add as we go — one row each, deeplinked)

| Guide | Deeplink | Refines |
|---|---|---|
| Pens placement + five-pen shape | [`geode/PLAN.md`](geode/PLAN.md) §0 | this file |
| Prompt-as-IR / pseudocompiler whitepaper | [`docs/prompt-as-ir.md`](docs/prompt-as-ir.md) | hyper-tailrec todo loop |
| Concept glossary (deeplinks for every term) | [`CONCEPTS.md`](CONCEPTS.md) | everything |
| Save-all + green-blue permanence | [`geode/products/pseudobrookite/REQUIREMENTS.md`](geode/products/pseudobrookite/REQUIREMENTS.md) | command 1 |
| Mobile-autocorrect audit (extension "sucks" docket) | [`geode/products/pseudobrookite/docs/audit-mobile-autocorrect.md`](geode/products/pseudobrookite/docs/audit-mobile-autocorrect.md) | tau extensions |
| Tool-path audit (find/grep/shim/spawn traps) | [`geode/products/pseudobrookite/docs/tool-audit.md`](geode/products/pseudobrookite/docs/tool-audit.md) | agent runtime |

## Boundaries (refining `~/.local/bin` + estate-ops manifest doctrine)

- Products own their entrypoints; `~/.local/bin` links point into pens. Never
  a second copy. `bin-verify.sh` FAILs a broken link.
- Secrets: secretsmith keyring only, never committed.
- No `git submodule add`, no gitlinks; the pen's kitchen-sink `.gitignore`
  auto-ignores product checkouts.
- The desktop is live: additive-only on user-facing surfaces; never disrupt
  the running session to wire an extension — ship the installer, wire on next
  restart.