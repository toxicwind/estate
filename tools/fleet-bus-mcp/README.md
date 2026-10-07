# fleet-bus-mcp

Cell-side MCP for **fleet-bus / squawk** (stdio, newline JSON-RPC).

**Not** Meta Hatch (`/opt/hatch`). Public agent door stays **doorbell** `:25202` → **gatehouse** `:25127` → this upstream.

## Install (host)

```bash
DST=/home/toxic/estate/tools/fleet-bus-mcp
mkdir -p "$DST"
curl -fsSL -H "Authorization: Bearer $(gh auth token)" -H "Accept: application/vnd.github.raw" \
  "https://api.github.com/repos/toxicwind/estate/contents/tools/fleet-bus-mcp/server.ts?ref=main" \
  -o "$DST/server.ts"
# gatehouse: disable hatch-mcp; enable fleet-bus-mcp → bun $DST/server.ts
```

## Tools

`squawk_*`, `fleet_status`, `hashline_*`, `muse_db_query`, cell load helpers (`hatch_*` names = cell paths, not the product).

See [INTEGRATION.md](./INTEGRATION.md).
