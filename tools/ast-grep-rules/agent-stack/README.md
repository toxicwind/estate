# agent-stack ast-grep checks

Run via `mise run e2e-agent-stack` (includes D8) or:

```bash
ast-grep run -p 'name: "ghas_$NAME"' --lang typescript \
  ~/github-advanced-search-mcp/apps/mcp/src/tools.ts
```

Port SSOT is enforced by reading .env.local (not inventing ports).
