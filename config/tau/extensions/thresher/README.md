# Thresher MCP Extension for Tau (`thresher`)

Bridges the estate's Thresher MCP federation gateway (`:25127`) directly into Tau as native agent tools.

## Exposed Tools
- `thresher_discover`: Query all connected MCP servers and their tool counts
- `thresher_retrieve_tools`: BM25 natural language search across all federated tools
- `thresher_call_tool`: Call any federated tool on servers like `exa`, `ffs`, `github`, `filesystem`
- `thresher_activity`: Inspect real-time audit log of tool invocations

## Testing
```bash
bun test /home/toxic/pens/estate/config/tau/extensions/thresher/index.test.ts
```
