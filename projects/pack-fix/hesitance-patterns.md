# Hesitance patterns — pack-fix hunt (2026-09-20)

Catalog of every place where agents/runners were instructed (or chose) to ask
Chris, hedge, or refuse to act — plus the fix applied. Standing doctrine:
**act-then-report**; questions to Chris only when the answer exists nowhere
else AND the work cannot proceed.

## P1 — "Do not investigate further, do not retry, do not run anything else"
Designed-in hesitance. The worker ran the watchdog script, relayed ALERT output,
and stopped — never digging one level deeper, never fixing. Recurring alerts
went unactioned across runs.
- Lived in: `cron.d/minutely/progress-watchdog__interval@3m.md`
  (cron id `progress-watchdog`) and
  `goals/forceful-pause-and-resume-for-agent-swarms/crons/minutely/swarm-watchdog__interval@5m.md`
  (cron id `swarm-watchdog`); identical text in `cron.d/_archive/swarm-watchdog__interval@5m.md`
  (archived, inactive).
- Resolution 2026-09-20: archived copy rewritten to the fixed act-then-report behavior (enabled: false, archive note); resurrection-safe.
- Fix: rewrote both live bodies to INVESTIGATE-AND-FIX via `cron.update`
  (scheduler reconciled, schedules unchanged). New default: on ALERT/PAUSED/EJECTED,
  dig one level deeper, fix what can be fixed through verified healthy paths
  (restarts, stale-flag clears), and on repeats land a durable root-cause fix in
  real files, committed. Hard boundaries kept explicit: never kill the live
  bridge without a verified hot-replacement; never kill squawk processes; never
  expose/rotate/mint credentials; treat credential-shaped values as unverified
  canaries; no retry-spin into rate limits. Green runs stay silent; fixes get
  narrated in fleet; a genuinely Chris-only blocker is stated once, plainly,
  while everything else keeps moving.

## P2 — Sentinel-skip during known outage: reviewed, NOT hesitance
Circuit-breaking during a KNOWN upstream outage instead of retry-spinning is
correct fail-fast, not hedging.
- `bridge-watchdog` and `yote-connector-watch` are the **gold standard**:
  they act fully when the bridge is up (probe, restart dead daemons via exact
  procedures, clear stale flags), skip quietly during known 401 drift, and
  announce recovery. Copy this shape for future watchdogs.
- `squawk-monitor` / `kimi-auto-canary-judge`: skip when the outage sentinel
  exists because their data source (fleet / yote judge) is unreadable — there is
  nothing to act on. Not hesitance.
- `kimi-auto-canary-judge`: "Do not advance phases yourself — phase changes are
  owned by the canary-exec worker" is a designed check-and-balance (judge ≠
  actor), not hedging.
- `audit-bridge-watch` (disabled): one-probe-no-loops is anti-hammering design.
- No changes made to any of these.

## P3 — "Nothing invented without him": judgment-call gate
- Fleet seq 10738 (docs-fixer): "canonical homes for the skill + connector are
  undecided — nothing invented without him."
- Why it's hesitance: naming/placement is recoverable and decidable. Doctrine
  says decide, act, let Chris veto — not park the decision.
- Fix: recorded. Future briefs must restate "no hedging where action is
  possible"; the default for judgment calls is propose-and-act, not ask-first.

## P4 — Block reported instead of worked around
- Fleet seq 10760 (sovereign-sweeper): yote's `gh` token dead, so the push was
  parked waiting on Chris to run `gh auth login` on yote.
- Why it's hesitance: a blocked path gets a workaround, not a status report.
  The documented fallback (GitHub git-database API push via the github skill's
  credential helper — see AGENTS.md "Git push from the cell") existed and was
  not attempted.
- Fix: recorded. Workers must attempt the documented fallback route before
  parking work on a credential-shaped blocker; when a human step is truly
  needed, hand Chris a one-liner for that step while everything else proceeds.

## P5 — Legitimate human gate: kept narrow (no change)
- Fleet seq 10769 (herd-deployer): Kimi inference 402/404/401 everywhere,
  "needs Chris for a key/credits." Only Chris can fund a provider account.
  The worker did everything else and stated the blocker plainly once. This is
  the correct narrow shape for a genuine human gate.

## Sweep coverage (all clean unless noted)
- All `cron.d/**` bodies, all `goals/*/crons/**` bodies, all `skills/*/SKILL.md`:
  `router`'s "do not retry in a loop; report it" is fail-fast (fine);
  `github`/`github-mcp` "never ask the user to paste a raw key" is
  anti-exfiltration (fine, keep); `emergent-tasking` skill + references clean.
- Fleet history (1234 msgs): only P3/P4/P5 above matched ask-Chris phrasing.
- System crons (`deterministic-doctor`, `feed-pulse-*`, `profile-image`) are
  runtime-managed (read-only for us); `deterministic-doctor` body reviewed,
  clean.
- Flag for Ember (not hesitance): the `heartbeat` cron body references
  HEARTBEAT.md, which does not exist at `~/workspace/HEARTBEAT.md`.


## Enforcement — the permanent guard
The script is the deliverable: `projects/pack-fix/bin/hesitance-lint` fails
(exit 1) when any P1/P3/P4 phrase reappears in cron bodies, SKILL.md files,
or prompt/brief templates. Run it against hatch instruction dirs and the
sovereign repo; see `projects/pack-fix/README.md`. Narrowly documented
allowlist exceptions (`# hesitance-lint-allow: <reason>`) cover legitimate
fail-fast/security phrasing (P2 shapes), not hesitance.