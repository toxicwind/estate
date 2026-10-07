# doorbell ↔ fleet-bus-mcp

## Planes (locked)

| Plane | Owns | Port / path |
|-------|------|-------------|
| **doorbell** | Public MCP monad: sessions, tiers A–I, catalog views, SSE `list_changed` | `:25202` (`/doorbell-mcp`, `/gemini-mcp`) |
| **gatehouse** | mcpproxy-go: spawn/proxy upstream stdio/HTTP MCPs | `:25127` |
| **fleet-bus-mcp** | Cell-side fleet-bus / squawk / load / hashline / muse-db | stdio via gatehouse (`bun …/tools/fleet-bus-mcp/server.ts`) |
| **hatch** (Meta) | Private Jarvis cell daemon — **not** an agent door | `/opt/hatch` |

Call chain today (and keep it):

```
agent → doorbell :25202 → gatehouse :25127 → fleet-bus-mcp (stdio)
```

Doorbell must **not** shell out to squawk itself. Fleet-bus is the only writer to `~/.fleet-bus/squawk-root` on the cell.

## Phases

### P0 — wire (now)
1. Install `tools/fleet-bus-mcp/server.ts` on host.
2. Gatehouse: add upstream `fleet-bus-mcp` (bun + path); **disable** `hatch-mcp`.
3. Prove via doorbell: `tools/list` shows `squawk_*` / cell tools; `squawk_list_channels` OK.
4. Keep tool names stable (`squawk_send`, …) so Osprey/Flicker/Remora packs don’t break; rename server only.

### P1 — catalog surface
1. Doorbell `catalog` marks fleet-bus tools under surface `fleet` (or `bus`).
2. Tier policy: read tools (`squawk_read`, `*_list`, status) ≥ router; destructive (`squawk_send`, `hashline_patch`) ≥ a higher tier (e.g. full / admin) + still require `confirm:true`.
3. SSE `list_changed` when gatehouse reconnects fleet-bus (already partially true via proxy).

### P2 — emergent integration
1. Pattern-forge races for: durable squawk send, scroll/read, roster, store — winners land in `fleet-bus-mcp` (or ranch `fleet-bus` crate), not in doorbell.
2. Doorbell gains a thin **facade** only if agents need namespaced tools (`fleet.send`) — facade = JSON-RPC forward to gatehouse upstream, zero bus I/O in monad.
3. Arroyo (coyote/overlord/discord) publishes through the same squawk-root contract; one bus, many faces.
4. Optional: doorbell `/sessions` shows fleet-bus upstream health (gatehouse connection_status mirrored).

### P3 — retire hatch-mcp name
1. Delete or stub `tools/hatch-mcp` → README pointing at fleet-bus-mcp.
2. INDEX / personas say “fleet-bus”, never “hatch-mcp”, for agent tooling.

## Non-goals
- Doorbell does not become a second squawk writer.
- fleet-bus-mcp does not become public Tailscale/Funnel — doorbell stays the public door.
- No Meta Hatch SDK / `/opt/hatch` RPC from agents.

## Emergent rule
Canonical paths may be wrong: forge (retrieve/race/borrow) for send/read/GC before treating this Bun server as sacred. Faster valid winner replaces the handler; doorbell facade stays stable.
