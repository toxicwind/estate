# websearch-mcp

Stdlib-only MCP wrapper for the `websearch-skill` CLI package (v0.6.1).

## Why

`websearch-skill` 0.6.1 ships no MCP server — it's CLI-only. This wrapper exposes its capabilities over MCP stdio using only the Python standard library (no extra dependencies).

## Tools

| Tool | Description |
|------|-------------|
| `web_search` | Web search via `websearch web-search --json` |
| `web_fetch` | Fetch a URL via `websearch web-fetch --json` |
| `arxiv_search` | arXiv search |
| `github_search` | GitHub code/repo search |

## Running

```bash
python3 /home/toxic/sovereign/tools/websearch-mcp/server.py
```

Requires the `websearch` CLI on PATH (`uvx websearch-skill` provides it).

## Verification

Live-tested 2026-09-20: initialize + tools/list + real `web_search` for "Model Context Protocol" returned live Wikipedia results.

## See also

- [Fleet Knowledgebase](../../docs/fleet-knowledgebase.md) — crew `tau-tmux-mcp`
- [Mesh gateway](../../projects/mesh/gateway/) — registered as `websearch-mcp`
