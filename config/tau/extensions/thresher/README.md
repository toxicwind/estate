# Thresher MCP Extension for Tau (`gatehouse`)

Bridges the estate's Thresher MCP federation gateway (`:25127`) directly into Tau as native agent tools.

## Exposed Tools
- `gatehouse_discover`: Query all connected MCP servers and their tool counts
- `gatehouse_retrieve_tools`: BM25 natural language search across all federated tools
- `gatehouse_call_tool`: Call any federated tool on servers like `exa`, `ffs`, `github`, `filesystem`
- `gatehouse_activity`: Inspect real-time audit log of tool invocations

## Testing
```bash
bun test /home/toxic/estate/config/tau/extensions/gatehouse/index.test.ts
```
