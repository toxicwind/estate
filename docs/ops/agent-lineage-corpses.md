# Agent lineage + pitchfork corpse list (2026-10-19)

## Family tree (who is a fork of what)

```
opencode (sst) ──▶ kilo-code (Kilo-Org) ──▶ kappa (toxicwind/kappa-code)
   "Kilo Code renamed": the coding agent that meets you everywhere (CLI, VS Code,
   JetBrains). kappa-code = the estate fork; packages/opencode migrated to
   packages/cli (commit 2082c1a1ef). kappa is the CURRENT engine — the 
   kimi-work CLI work was folded in here (see corpses below).

pi-mono (badlogic) ──▶ oh-my-pi (can1357) ──▶ tau (toxicwind)
   tau = the Greek-letter sibling; the "pi / oh-my-pi" entries on
   freeinference's agent leaderboard are this lineage.
```

NOT related: the two lines share no code; tau's natives pipeline (bazel
`//:natives-*`) is unrelated to kappa's.

## Pitchfork corpses (registered daemons whose run targets are GONE)

Marked `available  disabled` 2026-10-19 (`pitchfork disable`) — kept per
additive-only doctrine, never deletable without explicit order:

| Daemon | Reason (target inspected) |
|---|---|
| `estate/kimi-code` | `/home/toxic/kimi-code-npm` deleted; Moonshot's closed kimi-code CLI retired — kappa is the successor |
| `estate/kimi-audit-dash` | `/home/toxic/kimi-token-audit` deleted; audit dash absorbed by bench-radar |
| `estate/bedrock-ui` | `/home/toxic/projects/bedrock/web/server.ts` gone; estate/ranch/bedrock is an empty shell (only pitchfork.d) |
| `estate/boundless` | `/home/toxic/boundless` gone; standalone/boundless is an empty shell |
| `estate/refusal-watchdog` | `/home/toxic/refusal-hunt/refusal-watchdog.py` gone |
| `estate/sorry-watchdog` | `/home/toxic/refusal-hunt/sorry-watchdog.py` gone |
| `estate/forge`, `estate/forge-agent` | RE-ENABLED after rebuild (see forge-naming-canon.md) — NOT corpses |

## One-time fixes from the same archaeology

- `~/.local/bin/kappa` symlink pointed at deleted `packages/opencode/bin/kappa`
  → repointed to `packages/cli/bin/kappa`; fresh dist build
  `0.0.0-main-202610200429` with bundled+pinned bwrap (honest-UA fingerprint
  work included).
- `estate/keypool` target moved `ranch/mesh/keypool` → `services/keypool`.
- `estate/mesh-landing` `landing.py` → `ranch/range/bin/landing.py`.
- `estate/nativelink` run.sh → `ranch/forge/ops/nativelink/run.sh`.
- `estate/nginx` conf → `ranch/forge/ops/nginx/nginx.conf`.
- `estate/market-loop` imports → `ranch/trading-post/src/market/*`.
- `estate/ml-serve` → mise python 3.14.7 (numpy present).