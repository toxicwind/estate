---
crew: 'rigger'
scope: 'yote-conn mainline failure-hardening + ripline Bun forward fork with automatic fallover to mainline'
owner: 'rigger (Ember's crew)'
status: 'DONE (2026-09-30) -- yote-conn fixes 048eb1679, ripline 9e09edaf0 (origin/main, ls-remote verified)'
order: 200
registered: '2026-09-30'
updated: '2026-09-30'
---

# rigger

Per-crew ownership record. Edit the frontmatter above; the §2 table in
docs/fleet-knowledgebase.md is generated from these files -- do not edit it by hand.
After changing this file, run bun projects/ops/bin/kb-rollup.ts.

## Delivered 2026-09-30

Track 1 -- yote-conn mainline hardened (projects/bridge/hatch/yote-conn,
commit 048eb1679): typed ConnectorDown on URLError/OSError/socket.timeout
(caught at __main__ -> clean "connector down", exit 1); guarded exec
timeout int() (exit 2); guarded multi file open (exit 2); __main__
boundary also catches json.loads ValueError on non-JSON daemon replies
(exit 1). Verified live on the hatch cell against a dead daemon.
Bonus: connector.py bind-race hardening (retry-with-backoff on EADDRINUSE)
after the cell connector flapped during a restart dance.

Track 2 -- ripline (projects/bridge/ripline/, commit 9e09edaf0): Bun
forward fork of yote-conn, same CLI surface (health/exec/multi/bg*/herd/flock).
Lane order: unix socket -> connector-HTTP :18301 -> mainline yote-conn
fallover (original argv, exit code preserved). No-double-exec contract
(pre-dispatch failures may re-dispatch; post-dispatch failures report and
stop), pinned by the contract tests. Fallover ledger at
~/.cache/ripline-fallover.jsonl. RIPLINE_NO_FALLOVER=1 escape hatch.
Measured exec true: ripline 234-671ms vs mainline 739-980ms (~1.5-2.5x
faster, same band as yote-conn-fast). Compiled binary deployed at
~/workspace/bin/ripline on the hatch cell (bun build --compile).
