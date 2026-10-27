# GHAS Repo Keyword Search Helper

Working, verified helper — GitHub repository keyword search over the estate's
GHAS (GitHub Advanced Search) surface. Fixed the GHAS service startup bug
(`apps/api/src/lib/env.ts` `estate-scripts_ROOT` ReferenceError always crashed
the API/MCP before binding; now resolves `~/estate`). Verified live: query
`mcp` returns `punkpeye/awesome-mcp-servers`, `github/github-mcp-server`,
`microsoft/playwright-mcp`.

## Rapid (GET, proven)

```bash
curl -s "http://127.0.0.1:25112/api/search?query=<keywords>&categories=repositories&per_page=20"
```

Results are at `.data.results[]` (not the top level). Fields per item:
`repository`/`full_name`, `description`, `html_url`.

Example (works):

```bash
curl -s "http://127.0.0.1:25112/api/search?query=mcp&categories=repositories&per_page=3" \
  | jq -r '.data.results[]?.repository'
```

Qualifiers supported (GitHub syntax): `topic:x`, `language:y`, `stars:>N`,
`org:o`, `in:name`. Use the MCP surface too:

## MCP (ghas_search_*)

- `ghas_search_code` — CLI-agnostic code search (`path:`, `lang:`, `filename:`,
  Blackbird globs `path:**/*.ts`).
- `ghas_search_repositories` — repo keyword search (above).
- `ghas_search_issues` / `ghas_search_pull_requests` / `ghas_search_commits` /
  `ghas_search_users` — the other surfaces.

## Category values (SearchCategory)

`unified, code, repositories, issues, pull_requests, users, discussions,
commits, packages, wikis, topics, marketplace`.

## Notes

- Repo `toxicwind/ranch` is PUBLIC → both REST and Blackbird reach our own code
  (no privacy wall).
- `:25112` = search REST API; `:25113` = MCP protocol (needs an MCP initialize
  handshake, not a bare GET).
- Reuse over rewrite: engine is `github-search/packages/{github-client,
search-core, contracts}`. Do NOT hand-drive raw `gh` (flag drift etc.).
