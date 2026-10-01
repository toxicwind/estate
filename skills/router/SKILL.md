---
name: router
description: >
  Route every command to the right box: hatch cell versus yote bridge routing. Triggers on: route command, which box.
---

# router skill (ember)

Route every command to the right box. The wrong box is not a mistake you
fix — it's a mistake the router refuses to make.

## The rule
- It runs on HATCH (this cell): `send hatch -- <command>`
- It runs on YOTE (awrawr-pc): `send yote -- <command>`
- NEVER run a bare `ls/cat/grep/tail/python` against a path on the other
  box. `/home/toxic/*` is yote. `/home/hatch/*` is hatch. The `send`
  guards enforce this with a hard error (exit 3) naming the fix.

## Usage
```bash
send hatch -- ls /home/hatch/workspace              # this cell
send hatch --argv -- python3 script.py --flag        # exact argv, no shell
send yote -- ls /home/toxic/shingle                  # yote via bridge
send yote --timeout 60 -- ./long-job.sh               # custom timeout
```

## Semantics
- Default: command tokens are joined and run via `bash -c` on the target.
  `--argv`: tokens are the exact argv (no shell — avoids quoting bugs).
- Real exit codes propagate. `--timeout` seconds (default 120).
- `send yote` when yote is unreachable fails fast with the bridge's own
  error and exit 2 — do not retry in a loop; report it.
- MCP callers: `yote_send` on yote's MCP server is the explicitly-routed
  yote endpoint (staged — see ~/workspace/router/yote_send.patch.md);
  `hatch_send` is v2 (see ~/workspace/router/hatch_send-v2-spec.md).

## Guarantees
- Read the guard before the command: a wrong-box invocation never
  executes. The error prints the exact corrected `send …` line — run it.