---
name: github-mcp
description: >
  GitHub remote MCP server client. Drives GitHub's official MCP endpoint at api.githubcopilot.com through the custom.github-mcp OAuth credential using github-mcp-cli. Triggers on: "github mcp", "mcp tools", "github api", "copilot mcp".
---

# Github Mcp

## Purpose
Call GitHub's official remote MCP server (`https://api.githubcopilot.com/mcp`)
with the user-connected `custom.github-mcp` OAuth credential.

## Tooling
Use `exec` to run:

```sh
github-mcp-cli <subcommand> [options]
```

```sh
github-mcp-cli status
github-mcp-cli list-tools
github-mcp-cli call-tool --name <tool> --arguments-json '<json-object>'
```

`--arguments-json` must be a JSON object; arrays or scalars are rejected. Use
`list-tools` first to discover the tool catalogue and each tool's
`input_schema`. Auth is handled via authd surrogates by
`bin/dynamic_credentials.py`; the CLI never sees the raw token.

Transport hardening (ported from the awrawr-mcp exec.py client): every
request carries a unique id and SSE responses are accepted only when the
response envelope's id matches; a local read deadline (default 150s,
override with `GITHUB_MCP_READ_TIMEOUT`) bounds the client-side read so a
stalled stream raises instead of hanging; a failed lane is marked degraded
(`~/.cache/github-mcp-https-down`, 60s TTL) so the next call fails fast.

Resource safety (audited after a previous install caused restart loops):
the CLI is one short-lived process per invocation — it spawns no threads,
runs no daemon, and performs zero retries, so there is nothing that can
restart-loop. CPU: no busy loops; every wait is a blocking socket read with
a timeout. Memory: SSE events are capped at 8 MiB and response bodies at
32 MiB (`_ResponseTooLarge` aborts the read instead of growing without
bound). Threads: the only lock guards the session handshake for library
use; as a subprocess the CLI is single-threaded.

## Auth
The credential is already stored; nothing here collects one. Resolve auth through the skill's connection flow — credential values never enter chat, secret environment variables, secret flags, or auth files.

A 401 or 403 is a question about the request before it is a question about the key. Check that the credential was attached at all: a request built without the helpers named under Tooling carries nothing, and that looks exactly like a wrong or under-scoped token. Only once a request that did carry the credential is still rejected, call `credentials.request_api_access` with `reconnect` to replace it. The connector is stored as `custom.github-mcp`.

## Operating Rules
1. Use this skill when the user asks for Github Mcp or this provider's API.
2. Restrict authenticated requests to: api.githubcopilot.com.
3. Do not print, log, or persist raw credentials.
4. If auth is missing or rejected, follow the Auth section rather than asking for a key.
5. Run `github-mcp-cli status` before MCP work. If it reports an error, follow
   the Auth section.
6. Call `list-tools` before `call-tool` unless you already know the tool name
   and its argument shape. Never guess tool names.
7. Mutations the task authorized proceed autonomously: create, push, and
   edit issues, PRs, branches, comments, and releases as part of the work
   and report done. Surface to Chris only for destructive or irreversible
   mutations — deleting a repo, transferring ownership, force-pushing to
   main, publishing private content publicly. Do not re-ask for intent the
   task already gave; when in doubt, act within the task's scope and report
   done.
8. This skill complements the `github` skill (PAT-based REST API). Prefer
   `github-mcp` when the user asked for MCP or OAuth; prefer `github` for raw
   REST endpoints the MCP tool catalogue does not cover.