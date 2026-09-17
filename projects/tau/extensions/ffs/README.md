# tau-ffs

Tau/omp extension that makes [fast_file_search](https://github.com/quangdang46/fast_file_search)
(`ffs`) first-class inside Tau sessions — the emergent finder that replaces
`fd` + `rg` for LLM agents.

## What it adds

Slash commands (interactive):

| Command | Replaces |
|---|---|
| `/ffs-find <pat> [--root <dir>]` | `find`, `fd` |
| `/ffs-grep <pat> [--root <dir>]` | `grep`, `rg` |
| `/ffs-read <file> [--budget N] [--full]` | `cat` |
| `/ffs-outline <file>` | — (tree-sitter structure) |
| `/ffs-symbol <name> [--expand]` | ctags-style lookup |
| `/ffs-refs <name>` | definitions + usages |
| `/ffs-map [--root <dir>]` | workspace overview |
| `/ffs-index [--root <dir>]` | rebuild indexes |
| `/ffs-status` | binary / version |

LLM tools (the agent reaches for these instead of shelling out):

`ffs_find`, `ffs_grep`, `ffs_read`, `ffs_outline`, `ffs_symbol`, `ffs_refs`,
`ffs_impact`.

## Install

```bash
cd /home/toxic/sovereign/tau/extensions/ffs
bun install
tau plugin link .
```

Requires `ffs >= 0.1.30` on PATH (or set `FFS_BINARY`).

## Env

- `FFS_BINARY` — explicit binary path
- `FFS_TIMEOUT_MS` — per-run timeout (default 60000)
- `FFS_DISABLED=1` — skip the extension
- `FFS_DEBUG=1` — stderr debug logging
