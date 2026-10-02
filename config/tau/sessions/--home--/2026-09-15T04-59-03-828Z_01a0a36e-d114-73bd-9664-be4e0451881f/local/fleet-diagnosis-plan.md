# Plan: diagnose and stabilize the squawk fleet chat system

Context: User reported confusion around PATH/sudo/audit. Traced it to `/home/toxic/fleet` — a squawk pub/sub chat system (`squawk_ws_server` on 127.0.0.1:25147, channels `fleet`/`leads`) that runs autonomous jobs under `/home/toxic/fleet/jobs` (56 total: 24 done, 22 failed, 1 timeout, 2 killed). Current goal: diagnose health and stabilize.

Approach:
1. Snapshot and read one representative failed job (already done — latest `20260914-222949-4d4d`, a wezterm cargo check, failed with Rust E0616/E0608/0599 in `term/src/terminalstate/kitty_unicode.rs` and `term/src/test/image.rs`).
2. Pattern-match failure modes across failed jobs: read `result.json`/`stderr.log` for all 22 failed + 1 timeout, tally error categories (compiler vs runtime vs timeout vs killed).
3. Read the squawk server/runtime: `/home/toxic/squawk-ws/squawk_ws_server.py` and the running `squawk_feed.py --channel fleet` (`/home/toxic/squawk/squawk_feed.py`), plus `/home/toxic/.shingle/squawk-root/fleet` contents.
4. Determine root cause of ~40% failure rate and propose fix (per-category).
5. Decide action with user: leave-running, re-run failed jobs, or repair upstream repo.

Critical files & anchors:
- `/home/toxic/fleet/jobs/*/result.json` + `stderr.log` (per-job outcome + error)
- `/home/toxic/squawk-ws/server.log`, `squawk_ws_server.py` (server health)
- `/home/toxic/squawk/squawk_feed.py` (feed daemon; running `--channel fleet --bind 127.0.0.1 --port 25135`)
- `/home/toxic/.shingle/squawk-root/fleet` (backed message store; watched by inotify)
- `/home/toxic/estate/projects/wezterm/term/src/terminalstate/kitty_unicode.rs` (latest failure site)

Verification: failure tally = N categories; server.log shows healthy subscribe/broadcast with no `rejected unauthorized` spikes after fix; re-run of one failed job → `status=done` in its `result.json`.

Assumptions & contingencies: if squawk server is down, restart via pitchfork before diagnosing jobs; if failures are all repo-version drift, action is repo pin update (user-decided).
