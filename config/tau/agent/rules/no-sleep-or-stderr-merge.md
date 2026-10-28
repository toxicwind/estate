---
name: no-sleep-or-stderr-merge
description: "Never use sleep for polling or redirect stderr into stdout in bash commands"
condition: ["sleep\\s+\\d", "2>\\&1"]
scope: "tool:bash(*)"
---

Two anti-patterns are banned in bash tool calls:

1. **`sleep N`** — blocks the tool call for the full duration and burns wall-clock. Use `async: true` for background jobs, `ready: { port, log }` for service startup, or a readiness loop that exits on success within the same command.

2. **`2>&1`** — merges stderr into stdout, which hides error context and gets truncated by the harness. Keep stderr separate so errors stream visibly. To capture both for logging, redirect to a file explicitly (`cmd > /tmp/out.txt 2>&1`) and report line count with `wc`.