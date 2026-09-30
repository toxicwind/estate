# tmux-mcp v2.0

MCP server for tmux session inspection and control. Hardened for multi-socket estates.

## Tools

| Tool | Access | Description |
|------|--------|-------------|
| `tmux_list` | Read-only | Lists sessions across **all** discovered tmux sockets (default + named like `tauhyperfix`) |
| `tmux_capture` | Read-only | Captures pane scrollback (last 100 lines). `target` like `session:window.pane`, optional `socket` |
| `tmux_send` | **Destructive-gated** | Sends keys to a pane. Requires explicit `confirm:true` — refused otherwise |

## Socket discovery

Scans `/tmp/tmux-<uid>/` (or `$TMUX_TMPDIR`) for socket files. The default socket plus any named sockets (e.g. `tauhyperfix`) are enumerated. The old v1 only saw the default socket.

## Destructive-send gating

`tmux_send` is never accidental: the schema requires `confirm:true`, and the server logs every confirmed send to stderr. Never send to interactive shells without the user's informed intent.

## Running

```bash
/home/toxic/.bun/bin/bun /home/toxic/sovereign/tools/tmux-mcp/server.ts
```

Registered in the shep gateway (`projects/range/ranch/barn/shep/mcp_config.json`) as `tmux` (currently disabled pending deployment review).

## See also

- [Fleet Knowledgebase](../../docs/fleet-knowledgebase.md) — crew `tau-tmux-mcp`
- [Shep gateway](../../projects/range/ranch/barn/shep/) — canonical MCP config
