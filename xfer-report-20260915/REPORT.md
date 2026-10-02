# awrawr-pc save-path repair — final report (2026-09-15)

## Objective
Chris: "fix awrawr save issues via modifying bdirge or whatever" + "maximal".
Added constraint: the mechanism must work from /home/toxic's real
interactive/login bash, not just bridge exec.

## What was built
`xfer` — binary-safe, resumable file transfer over the awrawr bridge.
No base64, no shell quoting: native binary WebSocket frames, size + SHA-256
verification, atomic server-side install, `.part` resume, per-path
concurrency lock, 64 KiB default frame (race winner).

- Client: `toxicwind/gear` → `awrawr-mcp/bin/xfer.py` (+ shared `wsframe.py`)
- Server: `toxicwind/sovereign-projects` → `shingle-workspace/awrawr_ws_exec.py`
  (live: `/home/toxic/awrawr_ws_exec.py`, pitchfork `sovereign/awrawr-ws-exec`)
- `exec.py`: `--argv` (shell-free arg transport), `--timeout N` (server cap
  1800 s), socket/daemon wait ceilings derived from the requested timeout,
  explicit refusal (no silent HTTPS fallback) when `--argv`/`--timeout` are
  used but WS is down.

## Test evidence (all observed live, awrawr-pc)

| # | Test | Result |
|---|------|--------|
| 1 | 32 MiB random file, sha256 `0267e5f9…78072fb`, uploaded 3x (64/256/1024 KiB frames) | PASS — remote hash matched all 3; 36.1 s / 36.4 s / 44.9 s → **64 KiB default** |
| 2 | Filename with spaces/quotes/`$` + content with backticks/`$()`/NUL/`0xff` | PASS — `cmp` byte-identical |
| 3 | >90 s bridge transfer: 8 MiB, 175.3 s, sha256 ok | PASS |
| 4 | Kill mid-transfer → `.part` resume → sha256 ok | PASS |
| 5 | Two concurrent puts, same path → clean `transfer busy` → retry → sha256 ok | PASS |
| 6 | `--argv printf` with backticks/`$()`/quotes | PASS — byte-literal, no substitution |
| 7 | `--timeout 120 --argv sleep 95` | PASS — ran 1 m 35 s (old 90 s ceiling would kill it) |
| 8 | `--timeout 150 --argv sleep 100` | PASS — ran 1 m 40 s (derived-ceiling chain verified) |
| 9 | Real `bash -l -i` (real `~/.bashrc`, dangling `BASH_ENV`) `xfer --via direct` put 8 MiB | PASS — sha256 ok, 0.5 s |
| 10 | Same shell: backtick filename + backtick/`$()`/NUL/`0xff` round trip | PASS — `cmp` identical |
| 11 | Same shell: >90 s direct transfer, 168.4 s, sha256 ok | PASS |
| 12 | Symlink `/home/toxic/xfer-test/evil-link` → `/etc`, `xfer get …/passwd` | PASS — blocked: `path escapes /home/toxic and /tmp` |
| 13 | Listener `127.0.0.1:8379`, daemon child of pitchfork supervisor (ppid 2947304) | PASS |

## Commits pushed
- `toxicwind/gear` main: `fabe51b` (xfer v1) → `9625c9a` (busy-retry) →
  `711ad0c` (300 s busy window) → `2e8b37a` (64 KiB default, throttle removed,
  timeout propagation, no silent fallback)
- `toxicwind/sovereign-projects` main: `a0fdcbe357` (server v1) →
  `5d7fc591f3` (per-path put lock) → `c9bb36064f` (realpath hardening) →
  `561ed315fa` (pitchfork runs tracked source)
- NOTE: `3650fcd977` on sovereign-projects duplicates `gear/awrawr-mcp/`
  content — committed there by accident when `gear/.git/HEAD` went missing
  and git walked up to the parent repo. Left in place (no revert, ever);
  the canonical home is `toxicwind/gear`. The matching content is correctly
  committed there as `2e8b37a`.

## Deployment state
- pitchfork.toml now points `sovereign/awrawr-ws-exec` at the tracked source
  `shingle-workspace/awrawr_ws_exec.py`; old live copy kept as synced fallback.
- Daemon respawned by supervisor after kill (retry=true); listener verified.
- Caveat: pitchfork CLI 2.25.0 vs supervisor 2.16.0 mismatch — `pitchfork
  restart` reports "not found in config or state". Kill-by-PID + supervisor
  respawn is the working restart path. The supervisor re-reads pitchfork.toml
  on its own restart; until then the daemon runs the identical live copy
  (synced via `cp` after every server commit).

## Flags for Chris / other workers (not mine to fix)
1. **Git metadata damage**: `.git/HEAD` vanished from BOTH
   `/home/toxic/sovereign` and `/home/toxic/sovereign/gear` in the same
   window (both restored by me from `refs/heads/main`). Something is
   deleting HEAD files — worth hunting.
2. **Working-tree deletions I did not make**: `git status` in both repos
   shows deleted files under `herd/`, `docs/`, `.opencode/`, and several
   skill dirs (another worker's doing). I committed only my own files.
3. `/tmp/bridgesave` on the cell vanished mid-session (fratricide or cell
   wipe) — nothing durable lost, everything was already pushed.
4. `pitchfork list` shows `sovereign/awrawr-ws-exec` as "errored exit code 1"
   while the daemon runs fine — known stale-status lie, do not trust it.

## Bottom line
The save path no longer goes through the shell at all: no quoting, no
substitution, no 90 s ceiling, resume on kill, hash-verified both directions,
symlink escapes blocked, and it works from Chris's actual interactive login
shell. Done, pushed, verified.
