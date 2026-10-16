---
name: architect-caucus
description: Convene a multi-architect caucus — independent architecture proposals drafted in parallel, then adjudicated into a single consensus design with recorded dissent.
allowed-tools: inherited
---

# architect-caucus

Run an architecture caucus: fan out N independent architect agents on the same
brief, collect their proposals, then adjudicate.

## Workflow

1. **Brief** — write the problem, constraints, and success criteria into a
   single brief file. No code yet.
2. **Fan out** — spawn 3+ independent architect agents, each drafting a full
   proposal (components, data flow, failure modes, migration path) with no
   visibility into the others.
3. **Adjudicate** — compare proposals on a fixed rubric (correctness,
   operability, blast radius, reversibility). Merge into one consensus design;
   record dissenting opinions verbatim.
4. **Output** — the consensus design plus the dissent log, saved next to the
   brief.

## Rules

- Proposals are drafted before any comparison — no anchoring.
- The adjudication cites specific strengths/weaknesses per proposal.
- A proposal is never rejected for being unconventional; only for concrete
  failure modes.
