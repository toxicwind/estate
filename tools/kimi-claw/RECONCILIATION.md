# KimiClaw Repair — Reconciliation (2026-09-20, kimiclaw-deployer)

## What happened to the staging
The repair staged by kimiclaw-port at ~03:14 MDT in `/tmp/kimiclaw-repair/`
(bridge.ts, two instance configs, RECONCILIATION.md, deploy.sh) is GONE on
both boxes: hatch /tmp was wiped, and yote /tmp/kimiclaw-repair/ does not
exist (yote uptime 1d17h — not a reboot; the staging was on hatch only).

## What was reconstructed (this tree)
Source of truth for the rebuild: `/home/toxic/sovereign/tools/kimi-claw/`
- `dist/` (the real KimiClaw port: dist/src/config.js connector semantics,
  dist/src/session-routing.js session keys, dist/src/im/ transports)
- `openclaw.plugin.json` (connector fields: bridge{url,userId,token,
  kimiapiHost,outboundTransport,protocol,instanceId,deviceId,forwardThinking,
  forwardToolCalls,cronSessionTarget,imBypassCommandNames,shell,terminalWs},
  gateway{url,clientId,clientMode,agentId})
- Live OpenFang registry on :4200 (agents coyote, kimiclaw-1, kimiclaw-2 all
  Running) and the sovereign/src/lib/openfang_api.ts chat surface
  (POST :4200/v1/chat/completions with model `openfang:<agent>`).

The pre-repair `bridge.ts` (Sep 17) was inspected and retired to
`bridge.ts.bak-20260920`: it defaulted OpenFang to the dead :25103, kept a
dead direct Coyote route on :25143, and imported a stale client path.

## Repair deltas (bridge.ts, rewritten)
1. OpenFang default route → `http://127.0.0.1:4200` (dead :25103 gone).
2. Direct Coyote :25143 route REMOVED; coyote dispatches via the OpenFang
   agent `coyote` (`dispatchToCoyote`).
3. Per-instance endpoints:
   - kimiclaw-a → instanceId `sovereign-yote-kimiclaw-a`, transport
     `im_rpc`, OpenFang agent `kimiclaw-1`, squawk `@kimiclaw-a`
   - kimiclaw-b → instanceId `sovereign-yote-kimiclaw-b`, transport
     `bridge_ws` (normalized to `im_rpc` at runtime per the port source's
     own `readDeprecatedOutboundTransport` + validation warning), OpenFang
     agent `kimiclaw-2`, squawk `@kimiclaw-b`
4. Connector/session/tooling fields preserved (see header comment in
   bridge.ts); session keys follow the port's `agent:<seg>:<channel>:<acct>`
   scheme.
5. Redaction-safe `.secrets` parsing: presence validated, values never
   logged.
6. Fail-fast AbortController validation: `--check-route` probes
   openfang /api/health, openfang /api/agents (agent present+ready), herd
   /v1/models — 5s timeouts each, zero retries, non-zero exit on failure.
7. CLI: `--instance a|b`, `--check-route`, `--send TEXT [--agent NAME]`,
   `--daemon` (squawk fleet relay: fs.watch on the fleet dir, responds to
   `@kimiclaw-a`/`@kimiclaw-b` mentions, publishes replies as new fleet
   messages, never replies to self, atomic rename publish).

## Deployment
`deploy.sh` (idempotent): bun build check → --check-route both instances →
register `sovereign/kimiclaw-a` + `sovereign/kimiclaw-b` pitchfork daemons
→ start. pitchfork.toml backed up before edit. Bridge (awrawr-ws-exec) and
all squawk processes untouched.

## Rebuildability note
Only `dist/` is checked in; `package.json` expects `src/` + a tsconfig
build that do not exist. The KimiClaw connector cannot be rebuilt from
source in this tree — state plainly, do not claim otherwise.
