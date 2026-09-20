# awrawr-pc MCP exec bridge

Goal ID: goal_5c8a8ab52384
Goal slug: awrawr-pc-mcp-exec-bridge

## Description
Token-authenticated shell access to awrawr-pc through a FastMCP exec server exposed via Tailscale funnel, now running as a systemd user service with linger enabled. GitHub research found no mature drop-in replacement, so the hand-rolled bridge was hardened in place: a command denylist with a #yolo bypass, a JSONL audit log, and a daily pyarrow parquet export on a systemd timer. A sovereign disk audit of /home/toxic/sovereign was also delivered through the bridge.
