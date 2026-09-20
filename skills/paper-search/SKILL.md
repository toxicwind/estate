---
name: "paper_search"
description: "Paper research as a first-class chat capability: PAPER-TASK/PAPER-RESULT protocol over the fleet channel, arXiv + alphaXiv leg racer, pitchfork-managed poller daemon. Composes the hft-latency skill (race/fail-fast/winner-log doctrine — read that skill, not redefined here) and feeds architect-caucus debates with ranked paper evidence."
---

# paper-search

Paper research is first-class in the fleet chat (Chris 2026-09-14 18:26 MDT).

## The protocol

Any agent posts a dated single-line entry to `/home/toxic/.shingle/directives.md`:

```
## PAPER-TASK [t-optional-id]: <query> // <why this matters>
```

A poller daemon on awrawr-pc (`paper-poller`, pitchfork-managed) claims it with an
atomic mkdir lock, races the arXiv + alphaXiv legs, and posts back:

```
## PAPER-RESULT <task-id> — <query>
- Title (arXiv ID, date) https://arxiv.org/abs/… — one-line relevance
```

Until the poller claims it, any agent may claim a task manually — claiming is
posting intent, not a gate.

## Doctrine (not redefined here)

All latency behavior follows the **hft-latency** skill (`/home/toxic/workspace/skills/hft-latency/SKILL.md (yote); ~/workspace/skills/race/SKILL.md (cell)`):
race redundant legs concurrently, fail-fast per-leg timeouts, measure everything,
keep the fast path hot via the winners JSONL, maximal = wider not harder, never
roll back, borrow before inventing. This skill adds no new doctrine — it applies
that one to paper search.

Ranked results (titles, IDs, URLs, relevance lines) are admissible evidence for
**architect-caucus** debates (`/home/toxic/workspace/skills/architect-caucus/SKILL.md`); cite the
PAPER-RESULT entry when you bring papers to a debate.

## Components (canonical code: `toxicwind/paper-poller`, runs at `/home/toxic/paper-poller`)

- `bin/race_papers.py` — stdlib-only one-shot racer. Endpoint shapes borrowed from
  `emergent-enrich/bin/route.py`: arXiv Atom API + `api.alphaxiv.org/v1/search/paper`
  (public, no key — alphaXiv 403s keyed requests on public paths).
- `bin/poller.py` — the daemon (channel poll → atomic claim → race → post result).
  `/health` + `/ready` on 127.0.0.1:25149.
- `bin/watchdog.py` — external watchdog; SIGKILLs a wedged poller and re-starts it
  via `pitchfork start` (never `--force`). `/health` on 127.0.0.1:25150.

## One-shot usage

```bash
bin/paper-search "hedged requests tail latency"          # top 8, JSON lines on stdout
bin/paper-search "LLM serving benchmarks" --maxn 12 --jsonl /tmp/out.jsonl
```

Cell egress is unreliable: run searches on awrawr-pc via the bridge
(`awrawr-mcp` skill), never from the cell, until the cell recovers.
