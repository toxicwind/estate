# Gatehouse MCP Integration

The repeatable workflow for turning any capability into a first-class
Gatehouse MCP server. Proven on the rsync lane (2026-09-30):
`toxicwind/rsync-mcp`, server name `rsync`, 5 tools live through Gatehouse.

## 0. Non-negotiables

- **Bridge first.** Before GitHub or new code: sweep yote with `ffs` using
  several keyword variants — the tool usually already exists on the bridge.
- **Absence needs four witnesses.** Never say "doesn't exist" off one
  search: (1) skill catalog, (2) `ffs` across `/home/toxic`, (3) GitHub-wide
  (github skill `search-repos` + code search), (4) web search. Name every
  place you looked.
- **Fork policy.** Our forks (`toxicwind/*`) are canonical. Finished work
  pushes directly to the fork's `main`: fetch-first, never force-push,
  preserve full upstream ancestry (no squashing), verify the remote ref with
  `git ls-remote` afterwards. **Never open PRs against original upstreams.**
- **New estate code is Bun/TypeScript**, zero npm deps where possible.
- **No secrets** in code, configs, logs, commits, or reports. Gatehouse
  entries carry only non-secret env (host aliases, paths, flags). SSH keys
  and aliases — never credential values.
- **Restart Gatehouse only** through its owned path. Never reboot, never
  touch squawk (`:25147`/`:25135`).

## 1. Search (in order)

1. **yote**: `ffs grep <kw> --root /home/toxic` with several keyword
   variants; also `ffs find`. Map canonical vs stale vs dead duplicates —
   `/home/toxic` is full of them.
2. **GitHub**: github skill ranked search (`search-repos`), then code
   search. Rank like an operator: recency + relevance beat stars.
3. **Web**: public search for "<capability> mcp server".
4. If nothing adequate exists, build it (Bun/TS) — don't linger.

## 2. Adopt or fork

- **Adopt directly** if the implementation meets the bar: maintained,
  right transport, safe defaults, license acceptable.
  (Licenses don't gate anything — Chris 2026-09-30.)
- **Otherwise fork**: `gh repo create toxicwind/<name>`, clone on yote,
  `git remote add upstream <url>`, `git fetch upstream`,
  `git checkout -b main upstream/main` (full ancestry preserved),
  then land the rewrite/improvements on top. Credit the upstream in the
  README.

## 3. Build to the house transport standard

Gatehouse is mcpproxy-go; its stdio transport is **mark3labs/mcp-go
v0.57.0**, which is **newline-delimited JSON both ways** — NOT
Content-Length framing. The hand-rolled `Content-Length`-only pattern
(`sovereign/tools/tmux-mcp/server.ts`) **never registers**: MCP initialize
arrives as `{...}\n` with no header, the server waits for `\r\n\r\n`
forever, and Gatehouse logs `context deadline exceeded` on every health
check. (This exact failure killed the first rsync-mcp deploy; tmux-mcp has
the same latent bug.)

Server requirements:
- **Read both framings**: if stdin opens with a `Content-Length:` header,
  parse one framed message; else parse one JSON object per line, skipping
  blank/non-JSON lines.
- **Write**: `Content-Length: N\r\n\r\n{...}\n` — the **trailing `\n` is
  mandatory** (mcp-go reads with `ReadString('\n')`; without it the JSON
  line is never delivered). Framed readers parse exactly N bytes and ignore
  the terminator. One writer serves both.
- Gatehouse spawns via `/usr/bin/bash -l -c '<command> <args>'`
  (shellwrap); test with that exact invocation.
- Gatehouse env: entry `"env"` keys only; command/args like the tmux entry:
  `command: /home/toxic/.bun/bin/bun`, `args: ["<abs path>/server.ts"]`.
- Sandbox both ends of any path the server touches; gate destructive ops
  behind explicit `confirm:true` (run a dry-run first).

## 4. Test before registering

- `bun build src/server.ts --outfile /dev/null` — must compile.
- Protocol smoke test in **both modes** (`framed` and `lines`):
  initialize → tools/list → a read-only tool call → confirming that
  path-escape and destructive-without-confirm calls are refused. Keep as
  `tests/smoke.ts`.
- Commit + push to `toxicwind/<name>` main; verify `git ls-remote`.

## 5. Register in Gatehouse

Canonical source: `/home/toxic/estate/projects/range/ranch/barn/gatehouse`
- Live config: `mcp_config.json` (gitignored — the running truth)
- Durable template: `mcp_config.json.dist` (the bootstrap source; the
  serve script copies it when the live config is missing)
- **Write the entry to BOTH.** Back up both files in place first
  (`mcp_config.json.bak-<ts>`, `mcp_config.json.dist.bak-<ts>` next to the
  configs — never /tmp).
- Entry fields: `name`, `command`, `args`, `env`, `protocol: "stdio"`,
  `enabled: true`, `health_check_interval: "15s"`,
  `tool_discovery_interval: "2m0s"`, `isolation: {enabled:false,mode:"none"}`,
  `quarantined: false`. No timestamps — Gatehouse manages those.
- Validate both files as JSON after the edit.

## 6. Restart (Gatehouse only)

```sh
cd /home/toxic/estate && ./bin/pitchfork-restart sovereign/gatehouse
```

Never kill+start in one remote command; never `--help` the wrapper (it
takes a daemon id, not flags). Verify `:25127/health` → 200 afterwards,
and confirm squawk daemons (`sovereign/squawk-ws`, `sovereign/squawk-feed`)
are untouched.

## 7. Verify

- **Server log**: `tail /home/toxic/.local/state/mcpproxy/logs/server-<name>.log`
  — no `Connection failed` / `context deadline exceeded` after the fix.
- **Tool discovery**: speak MCP to `127.0.0.1:25127/mcp` —
  initialize (capture `Mcp-Session-Id`), then
  `tools/call retrieve_tools {"query":"<name>"}` — the server's tools must
  appear as `<server>:<tool>` ids. (Note: `tools/list` only shows the 12
  meta-tools; real tools come via `retrieve_tools`. The /mcp HTTP transport
  is session-based SSE.)
- **End-to-end call**: `tools/call call_tool_read
  {"name":"<server>:<read-only-tool>","arguments":{}}` — real output.
- **Bounded real read** through the new route where the far end is live;
  if the far end is down, record the exact error as the observed state —
  don't fake it.
- **Restart survival**: the entry is in `.dist`, so a bootstrap-from-scratch
  restores it; the pitchfork restart above proves the live config loads it.
- **Secret hygiene**: grep the entry, the server source, and the recent
  server log for credential-shaped values — none.

## 8. Rollback

- Configs: restore `mcp_config.json.bak-*` and
  `mcp_config.json.dist.bak-*` (in-place backups next to the configs),
  then `pitchfork-restart sovereign/gatehouse`.
- Repo: the fork's history is never rewritten — revert with a new commit.

## 9. Land it

- Commit + push any estate changes (fetch-first, no force-push, verify
  remote refs).
- Post completion in fleet: repo path, commit SHA, remote ref check, the
  Gatehouse server name + tool ids, and what verified green.