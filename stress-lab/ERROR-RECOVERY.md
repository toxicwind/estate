# Error-recovery loop (stderr -> signature -> patch)
Captured per-arm from `runner.sh` (`/tmp/err_<name>.<pid>`) before cleanup. Signature map:

| stderr signature | root cause | patch |
|---|---|---|
| `socket.timeout` / `timed out` | echo server didn't reply; likely cap overflow took >2s or conn flood blocked | raise server backlog (listen(128) already); bump per-conn settimeout |
| `ConnectionResetError` | peer reset a half-close / overflow | match SHUT_WR semantics; ignore RST in handle() |
| `[Errno 111] Connection refused` | server thread not up (start_echo raced) | add `time.sleep(0.2)` warmup (already present) |
| `no Global maxP` (tokwalk) | CLI crashed before sumline | check node shebang / missing dependency; run `./poc_token_walk.mjs` directly |
| `import: unable to open X server` | headless `import`/ImageMagick noise from an unrelated tool | assert it stays on stderr; never treat as output |
| `__PSEUDO_SLOT4__` absent in walk_data.json | pseudo-embedding path failed to write artifact | confirm EMBEDDINGS[PSEUDO_TOKEN] built; artifact write succeeded |
| arm prints `tokwalk_fail`/`sock_fail` but runner counts FAIL | arm gate returned nonzero by design (assertion) | fix the arm's own exit/echo contract, not the runner |

If a NEW signature appears, append it here + patch the owning lib, then re-run `./runner.sh`.
