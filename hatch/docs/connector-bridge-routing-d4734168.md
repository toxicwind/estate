# Connector vs Bridge vs Workspace Skill — Routing Rules

**Debate d4734168 verdict implementation (lane-6, awarded 2026-09-19).**
Durable, source-backed, no credentials.

## The rule (use this, not vibes)

| Route | Use when | Auth | Measured cost |
|---|---|---|---|
| **Catalog connector** | Exact service + action exists in the catalog, needs scoped OAuth | OAuth via Accounts Center | Varies by service |
| **Workspace skill** | Direct API-key service, no catalog connector, reusable workflow | API key via Secure Vault | Varies by service |
| **Bridge (awrawr-mcp exec)** | Target is awrawr-pc-local (daemons, files, pitchfork, /home/toxic) | Tailscale + token | p50 182ms, p95 230ms (N=20, warm WS, 2026-09-19) |

## Decision tree

1. **Is the target awrawr-pc-local?** → Bridge. Nothing else reaches
   `/home/toxic`, pitchfork, or local daemons. The cell cannot see awrawr-pc
   except through `~/workspace/skills/awrawr-mcp/bin/exec.py`.
2. **Is there a catalog connector for the exact service + action?**
   → Connector. Scoped OAuth beats a raw API key: least privilege,
   no secret handling, managed refresh.
3. **Otherwise** → Workspace skill with API key in Secure Vault.
   Write it as a real SKILL.md (working, tested, committed, pushed) —
   no stubs, no local-only skills.

## Why not always bridge?

The bridge is fast (p50 182ms warm WS) but it only reaches awrawr-pc.
For external services (Gmail, Spotify, etc.) the bridge can't help —
you need the connector or a skill. Using the bridge for something a
connector does natively is working around the platform instead of with it.

## Why not always connector?

The catalog doesn't cover everything. Direct API-key services with no
connector need a workspace skill. And nothing in the catalog reaches
awrawr-pc-local — that's the bridge's exclusive territory.

## Measured grounding

- Bridge warm-WS latency: p50 182ms, p95 230ms, N=20, zero fallbacks.
  Measured 2026-09-19 01:38 UTC via `exec.py --json --timeout 15 --argv echo ok`.
  (Prior figure ~150ms from memory was stale; re-measured per the bid.)
- HTTPS fallback exists (~0.6–1.1s) but did not trigger in this run.
- Per-call timeout discipline: 10–30s per call, 120s whole-operation budget,
  auto-detach after ~3s (standing rule 2026-09-18).

## Constraints

- No credentials, tokens, or secret values in this document or any
  routing decision record. Ever.
- Additive only. Patch forward.
- Verify on the box before claiming a route works.
