# Port SSOT — `config/ports.env`

`config/ports.env` is the single source of truth for every port on the
sovereign estate. Pitchfork (`pitchfork.toml`) sources it at daemon launch;
`bin/claim-port` allocates from it; `scripts/port-audit.py` diffs it against
live listeners.

## The guard

Kimi launch paths must never port-walk. Every Kimi invocation carries the
SSOT port and `--no-port-walk`:

- `pitchfork.toml` — the Kimi daemon stanza
- `src/services/forks.ts` — fork launcher
- `src/services/registry.ts` — service registry

Without the guard, a duplicate Kimi instance that hits `EADDRINUSE` silently
walks to `port+1…+100` and can squat a neighbor's port (observed 2026-09-20:
a duplicate walked onto `ANTIGRAVITY_GATEWAY_PORT` 25128 and probed shep's
25127 on the way). With the guard, the launch fails fast and loud instead
of drifting.

Verify the guard any time:

```bash
python3 scripts/kimi-no-port-walk-check.py
```

It binds a sacrificial listener on a scratch port, launches the real
`dist/main.mjs` against it with `--no-port-walk`, and asserts: non-zero
exit, a refusal on stderr, and nothing listening on the next port.

## The sweep

```bash
scripts/port-audit.py [--ssot config/ports.env] [--json]
```

Diffs the SSOT against `ss -tlnp`, attributing each listener via
`/proc/<pid>/cmdline` + cwd (so `python3`, `bun`, `node` resolve to the
real service). Exit 1 on real conflicts, 0 otherwise.

Findings:

| Kind | Meaning | Action |
|---|---|---|
| DOUBLE-BOOKED | two unrelated SSOT names, one port | fix the registry |
| LIVE BUT UNREGISTERED | listener in 25xxx/83xx with no SSOT entry | register it or record why not |
| SQUATTERS | SSOT port held by a non-owner process | kill or re-point the squatter |
| EXPECTED BUT DARK | SSOT port with no listener | informational (many daemons optional) |

Intentional multi-name ports live in `ALIAS_GROUPS` in the script
(e.g. `LLAMA_SWAP_PORT`/`HERD_PORT` — herd.sh launches the llama-swap
binary). Ports 25001–25099 are the llama-swap dynamic backend pool
(`herd.yaml` startPort) and are informational.

**Protected (verify-only, never re-point or kill):** squawk ws `25147`,
squawk feed `25135`, bridge exec-ws `8379`.

## 2026-09-20 sweep results

Fixed:

- `RUST_WEB_PORT` was `25101` (model-guard's port); corrected to `25201`
  (the rust-web daemon). Added `MODEL_GUARD_PORT=25101`.
- `GEMINI_MCP_PORT` was stale at `8378`; gemini-mcp runs on `25202`
  (pitchfork stanza synced to match).
- `SHEP_PORT=25127` added — shep is the live mesh gateway on the historic
  `mcpproxy-go` port (mcpproxy-go has no daemon anymore).
- `ZEDRA_HOST_PORT=25146` removed — stale, no daemon; `WHATSAPP_MCP_PORT`
  owns 25146.
- Duplicate `NULL_G_PROXY_PORT=25107` definition removed.
- Registered: `EXEC_WS_PORT=8379` (bridge), `ORACLE_CORE_PORT=25151`
  (oracle-core), `AWR_MCP_PORT=25198` (MCP bridge).

Left unregistered (non-sovereign / third-party, reported not fixed):
`:25193` flock, `:25194` ralph-dashboard, `:25195` codebase-memory-mcp
(transient), `:25197` boundless.

Known stale public routes (tailscale serve, out of SSOT scope — flagged
for a serve-map pass, not changed here): `/mcp → 127.0.0.1:8377` and
`/gemini-mcp → 127.0.0.1:8378` both point at dark ports; the live
services are on `:25198` and `:25202`.
