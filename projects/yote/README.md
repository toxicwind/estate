# Yote — Sovereign Lightweight Agent

**Yote** is a minimal, embeddable agent runtime for the Sovereign ecosystem.

- **Port**: `:25102` (per ecosystem topology)
- **Inference**: Routes through Herd (`:25100`) via llama-swap dynamic swap
- **MCP**: Connects to `http://127.0.0.1:25127/mcp`
- **Purpose**: Light agent tasks, diffing, scaffolding, and tool orchestration

## Quickstart

```bash
# Verify yote is responsive
curl -sf http://127.0.0.1:25102/health && echo "✅ yote HEALTHY"

# Check model availability via Herd
curl -sf http://127.0.0.1:25100/v1/models | jq '.data[].id' | grep -i yote
```

## Configuration

Yote integrates with the Sovereign stack through:

- **Herd**: Primary inference router at `:25100`
- **MCP Gateway**: Tool federation via `:25127/mcp` (mcpproxy-go)
- **Tau**: Agent orchestration and subagent coordination

## Status

Yote is under active development as a first-class citizen of the Sovereign monorepo.

*Added as part of sovereign/tau/herd consolidation.*
