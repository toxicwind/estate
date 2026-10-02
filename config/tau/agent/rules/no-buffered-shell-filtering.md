---
name: no-buffered-shell-filtering
description: "Never pipe shell output through tail/head/cut/sed or wrap commands in `timeout` or redirection — it blocks streaming and backgrounding; run async and forward output as it arrives"
condition: ["\\btimeout\\s+[0-9]", "\\|\\s*tail\\b", "\\|\\s*head\\b", "\\|\\s*(?:cut|less|more|awk|grep)\\b", "\\bsed\\s+-n\\s+['\"]?[0-9]*,[0-9]*p", "\\bsort\\s*\\|\\s*uniq\\s*\\|", ">>?\\s*\\S+\\s*$"]
scope: ["tool:bash", "text"]
---

Do not wrap commands in `timeout`, do not redirect output to a file, and do not pipe shell output through `tail`, `head`, `cut`, `less`, `sed -n`, or `awk`. Those forms force the whole pipeline to buffer, so the user sees nothing until the command finishes and the call cannot be watched or backgrounded.

Instead:
- Long or uncertain commands: run with `async: true` so results forward as they finish, and never wrap the command in `timeout` — put the deadline on the tool call instead.
- Do not redirect stdout to a file for inspection. Let the harness spill large output and read it back at `artifact://<id>`.
- Reading a file: use the `read` tool with a `:N-M` range, not `head`/`tail`.
- Inspecting the filesystem: use `read` on a directory, or `ffs`/`glob` — not `ls | grep`.

If output must be capped, cap it at read time, not at write time. Never `rm -rf` a shared hardcoded path.