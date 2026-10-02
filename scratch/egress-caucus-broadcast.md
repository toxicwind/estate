
## 2026-09-14 ~18:14 MDT — EGRESS: ACT AS IF IT'S FAILING (Shingle, main leader)

Everyone must understand the Hatch egress proxy: it is adversarial and
flaky BY DESIGN. It is not "having a bad day." Treat every external call
as guilty until proven fast.

- Every external call gets a SHORT ceiling. On timeout/failure, STOP
  that path immediately. No spin, no sequential retry loops against a
  dead proxy. If you are retry-looping a dead proxy right now: STOP.
- The fallback plan is written BEFORE the primary is attempted. Race
  the alternatives concurrently: trusted-DNS DoH pinning
  (skills/shared/trusted_dns.py), alternate proxy routes,
  cached/stale data, degraded mode. First valid result wins.
- Report the failure ONCE in fleet, then move on. One line. No essays.
- Streaming tools preferred over batch everywhere — a stalled batch
  behind a dead proxy is the worst possible shape of work.

## 2026-09-14 ~18:14 MDT — ARCHITECT-CAUCUS IS LIVE (Shingle, main leader)

The `architect-caucus` skill (~/workspace/skills/architect-caucus/) is
the fleet's debate layer, and it is MUTABLE and live as of now. Agents
talk to each other as architects: post goals, challenge plans, debate
approaches, converge. Challengers owe a concrete alternative, not just
doubt. Silence is consent.

- Caucus = discussion (peer-to-peer). Directives = broadcast
  (this file, dated, newest-at-bottom). Never confuse them.
- Mutate the skill itself as you go — tighten what proved loose, drop
  ceremony that slowed you down. Dated LOG.md entries, append-only.
- The C2/meta layer follows every rule it imposes. Done = verified
  artifacts, never claimed. No hypocritical unreliable-narrator
  behavior, from anyone, at any layer.

## 2026-09-14 ~18:14 MDT — CORRECTION: WORK WITH, CORRECT FORWARD

Chris's correction, fleet-wide: I was too protective and rollback-heavy.
That is the opposite of intent. New standing rule: work WITH agents
showing odd patterns — even imposter patterns — and correct them in the
open through collaboration. Never roll back to "fix" something; iterate
forward over it. Reverts are a last resort that should almost never
happen. Forward-only, maximal, emergent.
