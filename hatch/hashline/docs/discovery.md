# hashline discovery notes — 2026-09-30 (quill)

## What it is

**Hash-anchored file editing for AI coding agents.** Every line gets a stable
xxh32 content hash (`42:a3`); patches reference anchors, not fragile text
matches. If the file changed between `read` and `patch`, the patch is
**hard-rejected** (exit 1, `ERR STALE`) — fail-fast instead of silent corruption.
Atomic writes (temp file + rename). Agent-first compact output by default.

## Identity (all verified on yote)

- Binary: `/home/toxic/.local/bin/hashline` — 5,368,336 bytes, 2026-09-26
- Version: **0.9.19** == latest GitHub release (checked 2026-09-30; `update-check.json` agrees)
- Repo: **https://github.com/quangdang46/hashline** — third-party (quangdang46), MIT, Rust, 447 commits, 20 stars. **Not toxicwind.**
- Config/log: `/home/toxic/.hashline/` (`hashline.log`, `update-check.json`)
- Credit line: idea from can1357's oh-my-pi (same lineage as our TAU fork — hence `/home/toxic/bin/tau-hashline-fix.sh`, the probe→read→verify→backup→patch→build→revert precedent)

## Verified surfaces (real runs on yote scratch files, 2026-09-30)

| Surface | Evidence |
| ------- | -------- |
| `read` (CLI) | `hashline read --json /tmp/quill-hashline/t.txt` → `{"hash":"4e66","lines":[{"content":"alpha","hash":"c8","n":1},…]}` |
| `patch` (CLI) | `SWAP 2:89:` → `OK …#dabe edits=1 changed=1`, file verified changed |
| `find-block` (CLI) | anchor `4:b3` → returned enclosing `inner()` fn, `lang=JavaScript` |
| MCP `initialize` | server `hashline 0.9.19`, `instructions` field present (auto-discovery) |
| MCP `tools/list` | **6 tools**: `read`, `patch`, `write`, `find_block`, `remove_file`, `rename_file` |
| MCP `read` | arg is `file` (not `path`); returned `[…#42c2]` + anchors |
| MCP `patch` | `SWAP 2:0e:` → `OK … edits=2 changed=1`, file verified `MCP-EDITED-VIA-MCP` |
| MCP `find_block` | returned enclosing block over MCP |

## The "find and grep" question (Chris's follow-up)

- **find** = `find-block` / `find_block`: structural find — enclosing syntactic block around an anchor (brace-delimited, indent-based, Ruby `def…end`). Verified on both surfaces.
- **grep**: **does not exist, by design.** No `grep`/`search` subcommand in 0.9.19 CLI help, no search tool in MCP `tools/list`, and the upstream README states it explicitly: *"Text-search edits — hashline does not support `sed s/old/new/g` — use `sed` when you need regex replacement across non-hashable text."* Use `grep`/`rg`/`ffs` for search, then anchor the edit with hashline.

## Gotchas (all hit during verification)

1. **MCP framing is newline-delimited JSON**, not `Content-Length` headers (spec-style framing gets zero response). One `{"jsonrpc":"2.0",…}\n` per message, one line per reply.
2. **MCP arg is `file`**, not `path` — wrong name returns a JSON-RPC error, not a hint.
3. **`hashline patch` takes the patch as argv or stdin `-`** (`*** Begin Patch` … `*** End Patch`); there is no `--patch-file`.
4. **Shell quoting over yote-conn**: the cell's bash expands `$(…)` inside double quotes *before* sending — wrap the remote command in single quotes so `$(printf …)` runs on yote. `$(…)` itself is fine on the wire (the old exec.py mangling doesn't apply to yote-conn).
5. **pkill footgun**: `pkill -f <pattern>` matches the exec shell's own argv — use the `[b]racket` grep trick, never bare pkill -f with the pattern inline.
6. Anchor format is `line:hash` (`4:b3`), ranges `2:89..4:9c`; bare line numbers work as fallback.
7. `hashline update` self-updates (sha256-verified, atomic); restart MCP sessions after. Notices gated on tty stderr; agents set `HASHLINE_NO_UPDATE_CHECK=1`.
