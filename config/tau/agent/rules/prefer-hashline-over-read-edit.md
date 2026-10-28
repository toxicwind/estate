---
name: prefer-hashline-over-read-edit
description: "Never use read or edit tools when directed to use hashline"
question: "Did the assistant call the read or edit tool instead of hashline tools after being asked to use hashline?"
scope: "tool:read(*)"
---

When directed to use hashline, never invoke `read` or `edit`. Use `xd://mcp__hashline_read` and `xd://mcp__hashline_patch` instead.