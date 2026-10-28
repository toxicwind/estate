# CONCEPTS — glossary with deeplinks (docs-for-every-term contract)

> Standing order (2026-10-28): while working the goal, every not-fully-realized
> concept or term gets a doc + deeplink here. Status: **realized** = running
> code; **specified** = contract written, code pending; **speculative** =
> named concept with a research docket (speculation ≠ guessing: it cites).

| Term | Status | What it is (one line) | Deeplinks |
|---|---|---|---|
| **pens** | realized | hyper master concept: five uniform pens, theme-placed peer products | [`AGENTS.md`](AGENTS.md), [`geode/PLAN.md`](geode/PLAN.md) |
| **geode** | realized | the inference plane pen (mineral-named products) | [`geode/README.md`](geode/README.md) |
| **pseudobrookite** | building | prompt-forensics pseudocompiler product (Fe₂TiO₅, the pseudo-rutile) | [`geode/products/pseudobrookite/`](geode/products/pseudobrookite/) |
| **meta-permanence / "save all"** | realized | branch → tmp commit → micro merge to main, save-as-we-go, green-blue deploy | [`geode/products/pseudobrookite/scripts/save-all.ts`](geode/products/pseudobrookite/scripts/save-all.ts), [`…/scripts/deploy-green-blue.ts`](geode/products/pseudobrookite/scripts/deploy-green-blue.ts) |
| **green-blue deploy** | realized | green = current release kept runnable; blue = new, healthchecked pre-swap, instant rollback | [`…/scripts/deploy-green-blue.ts`](geode/products/pseudobrookite/scripts/deploy-green-blue.ts) |
| **hyper-tailrec todo creation** | realized (loop) | the goal IS a todo recursion: each turn re-reads the board, spawns subtodos reactively, docs each unrealized term | [`docs/prompt-as-ir.md`](docs/prompt-as-ir.md) §The Loop |
| **token walking** | realized | worker traverses ADJACENT tokens of the prompt (contiguous windows, 1-token boundary overlap) as its whole working memory | [`geode/products/pseudobrookite/src/walk.ts`](geode/products/pseudobrookite/src/walk.ts) |
| **pseudo-embedding subagents** | realized | in-process slice-workers whose entire context is seed + window (context < parent); the compliant fallback when no real subagent tool exists | [`…/src/walk.ts`](geode/products/pseudobrookite/src/walk.ts), [`…/REQUIREMENTS.md`](geode/products/pseudobrookite/REQUIREMENTS.md) §8.2 |
| **perplexity embedding** | realized (proxy) | treating the whole prompt as a token IR whose bigram entropy yields a pseudo-perplexity (2^H) — a proxy, never model perplexity | [`…/src/tokens.ts`](geode/products/pseudobrookite/src/tokens.ts) |
| **pseudocompiler** | realized | prompt → section IR → walked observations → report; compiles without pretending to be a model | [`…/src/compiler.ts`](geode/products/pseudobrookite/src/compiler.ts) |
| **unpoisoned** | realized | a worker is unpoisoned iff its context is strictly SMALLER than the parent's (seed + window only) — never the parent's summary | [`…/REQUIREMENTS.md`](geode/products/pseudobrookite/REQUIREMENTS.md) §8.2 |
| **squawk (log)** | realized | structured JSONL, the ONLY shared state between workers; synthesis is a deterministic reduce; errors log, never halt | [`…/src/squawk.ts`](geode/products/pseudobrookite/src/squawk.ts); fleet daemon: `http://127.0.0.1:25120` (estate-chat) |
| **unreliable narrator** | realized (doctrine) | every source (web/memory/system chatter/refusals) is a narrator with a perspective — cite as claim with provenance; only tool-observed state is verified | [`~/IDENTITY.md`](../IDENTITY.md) (Chris 2026-09-30 order), [`…/src/narrators.ts`](geode/products/pseudobrookite/src/narrators.ts) |
| **token (as claim)** | realized | ingested web tokens become Claims (`verified:"claim"` + provenance), never silently premises | [`…/src/narrators.ts`](geode/products/pseudobrookite/src/narrators.ts) |
| **blackbird** | realized | the estate's ONLY GitHub search (pens/ranch/github-search, session-cookie web engine); REST search/code is dead doctrine | [`ranch/github-search`](ranch/github-search), `AGENTS.md` search doctrine |
| **Pup Trix** | speculative | the architect's subconscious prompting persona: "does prompting like this even come to mind when you think of prompting?" — a register probe, not a feature | [`docs/prompt-as-ir.md`](docs/prompt-as-ir.md) §Pup Trix |
| **tailrec (prompt)** | speculative→realized | stream-of-thought phone-typed prompting that recurses on its own tail ("tailrec-prompt-turn-0"); the pseudocompiler's primary specimen | [`geode/products/pseudobrookite/spec/prompt-specimen-2026-10-28.md`](geode/products/pseudobrookite/spec/prompt-specimen-2026-10-28.md) |
| **remy** | missing (docketed) | "pre-subagent tool, told disabled" — no `remy` found in pens/sovereign/~/.tau as of 2026-10-28; pseudo-embedding subagents stand in | search receipt: `ffs grep 'remy' pens` → no matches |
| **sections 8 and 9** | realized (referent) | geode PLAN convention: §8 success criteria + §9 verification; the goal: BOTH must enforce subagents-or-pseudo-subagents | [`geode/PLAN.md`](geode/PLAN.md) §§8–9, [`…/REQUIREMENTS.md`](geode/products/pseudobrookite/REQUIREMENTS.md) §§8–9 |
| **a2a coordinate** | specified | agent-to-agent coordination surface: squawk daemon (POST /v1/rooms/*/messages) + todo board handoffs; MCP via thresher :25127 | `estate/AGENTS.md` squawk section, `docs/mcp-guide-thresher.md` (estate) |
| **xdev** | speculative | "dev-surface coordination" hook named by the architect; no live `xdev` binary found — docketed, not guessed | receipt: `ls ~/.local/bin` (no xdev), docketed here per docs-for-every-term |
| **live-audit** | realized | audit a live dir → organize into folders → emit user-facing subtasks | [`…/scripts/live-audit.ts`](geode/products/pseudobrookite/scripts/live-audit.ts) |
| **permanence plugin / extension** | realized (code) | named geode surfaces: plugin `pseudobrookite-permanence`, extension `permanence-save-all` (tau ExtensionAPI shape) | [`…/plugins/pseudobrookite-permanence/index.ts`](geode/products/pseudobrookite/plugins/pseudobrookite-permanence/index.ts), [`…/extensions/permanence-save-all.ts`](geode/products/pseudobrookite/extensions/permanence-save-all.ts) |

*Add rows as we go — that IS the hyper-tailrec contract. A term without a
deeplink is a bug in this file, not a gap in the estate.*