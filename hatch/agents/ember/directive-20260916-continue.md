
## 2026-09-16 23:55 MDT — CONTINUE NO MATTER WHAT (Chris's order, relayed by main)

The 8-lane DO THE THING run workflow-run-d96818185ad34ffba254e31b0ab3382c FAILED at
23:14Z — 7/8 lanes completed, lane4-backup's agent returned prose instead of the JSON
envelope ("workflow agent output was not JSON"). It is NOT still running; it failed
terminally. Per Chris's "continue no matter what": relaunched as
workflow-run-a0d73eeb95b1449a8cd23edff86b5d29 with resumeFromRunId set — the 7
completed stable-key lane results are reused, only lane4-backup reruns (read-only
shepherd of the backup driver; it must NOT start a second driver copy).

Screenshot analysis (Chris's two activity-feed screenshots, his verdict):
- 5 tasks, 4 stalled "asking for input/details/next steps", 1 ("Summarize .MD files
  with ML") badged Completed with subtitle "Asked for missing input to proceed".
- Failure dressed as success: the green badge certifies work that never happened;
  the subtitle reframes the stall as the user's debt. Any reader (human or agent)
  that trusts the badge hallucinates "summarization done" and builds on nothing.
- Codified: a turn/task that ends asking the user for input is FAILED work, badge
  or no badge. Never-ask-the-user-a-question is now mandatory (SOUL.md, AGENTS.md);
  question-asking is a completed-bug class (IDENTITY.md, with the screenshot as log).

New helper — isleep (interruptible sleep, queryable by any agent):
- Path: ~/workspace/bin/isleep (cell). Usage: isleep SECONDS --name NAME [--tick S]
- Wakes early on `isleep interrupt NAME [reason]` (polls an interrupt flag each tick,
  default 1s). Exit 0 = full time elapsed, 3 = interrupted.
- Query: `isleep status NAME` (JSON: running/done/interrupted, elapsed, remaining),
  `isleep list` (all named sleeps). State: ~/.isleep/<NAME>.status.json.
- Verified live: 60s sleep interrupted at 6.0s via cross-process flag; status queryable
  mid-sleep. This is the sanctioned wait primitive — poll-await on an observable
  condition, never a blind sleep; sleep/timeout binaries stay banned.
- Lane agents: use isleep for waits instead of re-read loops where a wake signal helps;
  other agents may `isleep interrupt <name>` to wake a waiter early.
