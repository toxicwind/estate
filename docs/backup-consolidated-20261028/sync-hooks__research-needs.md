# wezterm-needs.md — instrumentation requirements from the WezTerm research task

**From:** WezTerm weirdness research (report: `/home/toxic/wt-wezterm-20260915/WEZTERM-RESEARCH-REPORT.md`, pushed to `toxicwind/wt-wezterm-research-20260915`)
**Date:** 2026-09-15 ~03:35 UTC
**Purpose:** what I need from shell hooks to prove/corrorate the static findings in vivo, and to verify proposed patches after Chris approves them.

## What I need captured

### 1. Terminal traffic tap (escape-sequence logging) — highest value
- **What:** timestamped capture of bytes flowing through a WezTerm pane's pty, both directions (app/shell → terminal output, terminal → app input). Per-pane, on demand.
- **Proves:**
  - Finding 1: catch the exact invalid OSC palette sequences (`OSC 4;0;#$term0 ST` — literal unsubstituted placeholders) arriving in a live pane during a wallpaper/theme regen. Static evidence already shows the generated file is broken; live capture proves it hits real panes and shows frequency.
  - Finding 3: confirm the *absence* of shell-side OSC 133 / OSC 1337 / OSC 7 traffic (integration gap).
  - Finding 4: capture what tau actually emits for desktop notifications (OSC 9 vs OSC 777 question).
- **Hard requirements:**
  - Read-only tap. NEVER write bytes into the user's live pty (no DA/DECRQM probes, no queries) — capture only.
  - Must not disturb the live session or visibly alter behavior.
  - Bounded disk: rotate logs, cap total size (suggest ≤50 MB, keep last N).
  - Start/stop on demand per pane; no always-on global capture without Chris's word.

### 2. Env state snapshot
- **What:** dump of the pane shell's environment at startup (`TERM`, `COLORTERM`, `TERM_PROGRAM`, `WEZTERM_*`, `BASH_ENV`, `PATH`, `PAGER`/`LESS`) plus on-demand re-snapshot.
- **Proves:** finding 2 (env tier dead — `~/.bashrc.env` dangling), finding 3 (no integration env), finding 6 (`LESS -X` once the env tier is restored).
- Lightweight: append `env` + key `set` output to a timestamped file on shell start. Must work in bash **login** shells (WezTerm's default) without depending on `/etc/profile.d` (masked by hygiene).

### 3. Timing
- **What:** timestamps on (a) wallpaper-regen events → pty-write events (how often does applycolor.sh spray? what's the regen→pane latency?), (b) shell startup duration with/without integration (for verifying finding 3's proposed patch later).
- The traffic log's own timestamps cover most of this if regen events are also logged with timestamps.

### 4. Non-interactive / runner context
- **What:** same env snapshot + a bounded sample of output bytes for shells spawned by the fleet job runner and by tau subshells.
- **Proves:** finding 2's `BASH_ENV` gap (tau-spawned non-interactive bash gets nothing).

## Constraints the hook mechanism must respect
- No `sleep` or fixed timers in the hook itself — event-driven only.
- Must not re-enable or depend on the masked `/etc/profile.d` scripts (the masking was deliberate hygiene).
- Must not fight the existing setup: additive only, per-user (`~/.bashrc` / `~/.config`), never `/etc`.
- **Secrets hygiene (critical):** traffic logs and env dumps WILL contain secrets (API keys, tokens in env; possibly keystrokes in input direction). Store 0600, local only, NEVER commit raw captures to git. Redact `*KEY*`, `*TOKEN*`, `*SECRET*`, `*PASSWORD*` patterns if logs are shared or quoted.
- Input-direction capture (keystrokes) is the most sensitive — default to output-direction only unless Chris explicitly asks for input capture.

## What I'll do with the winner
Adopt the winning hook mechanism for the captures above rather than inventing my own. Once hooks-findings.md names it, I'll use it to (a) prove finding 1 live, (b) verify findings 2/3 state, (c) re-verify after Chris approves the proposed patches — and fold the results into the final report as an addendum commit.
