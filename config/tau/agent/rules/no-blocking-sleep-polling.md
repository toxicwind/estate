---
name: no-blocking-sleep-polling
description: "Never block on `sleep` to wait for a background process, service, or UI to settle — poll with a real readiness check"
condition: ["\\b(sleep|sleep\\s+\\d+)\\b\\s*[;&|]", "sleep\\s+\\d+", "\\bsleep\\s+[0-9]+", "bash\\s+[`\"'].*\\bsleep\\b", "\\bsleep\\s+\\d+;?\\s*$"]
scope: ["tool", "text"]
---

Never wrap a `bash` call in `sleep N` to wait for something to come up. `sleep` blocks the tool call for the full duration, burns wall-clock, and returns before the condition is met anyway — I used it repeatedly here to "wait" for wezterm panes, tau processes, and background greps, then had to re-poll.

Use the mechanism the harness already provides:

- **Starting a long-lived service** — `bash` with `name:` plus `ready: { port }` or `ready: { log:<regex> }`. The call returns only when it is actually serving.
- **Waiting on a job or process** — `bash` with `async: true`; results are delivered automatically. NEVER poll for it.
- **Waiting for a UI/text change** — issue the input, then read the surface with the next tool call (`wezterm cli get-text`, `read`, `pgrep`). The re-read *is* the delay; if it raced, read again rather than sleeping first.
- **Genuinely needing a bounded delay** — fold it into the command that does the work, e.g. `cmd &` then a readiness loop that exits on success or on timeout, so the call returns as soon as the condition holds rather than after a fixed sleep.

If a wait cannot be expressed as a readiness check, say what you are waiting for instead of burning a sleep.