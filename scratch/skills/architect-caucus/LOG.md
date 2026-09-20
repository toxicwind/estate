# architect-caucus LOG

Append-only. Every mutation of the skill gets a dated entry:
who / what / when / why. Never rewrite history — iterate forward.

## 2026-09-14 — LANE-4 worker d85c50f3 — skill CREATED
- Built from Chris's 2026-09-14 ~18:05 MDT direct order (maximal, auto-approve,
  forward-only, HFT-like). Supersedes any stale channel "stop" entries.
- Initial protocol: 10 standing rules (architect voice, peer-to-peer,
  no-hypocrisy, verified-done, forward-only, push-to-main, two-failure
  replan, HFT-latency, race-borrow, egress fail-fast); rule 11 added in
  iteration 2.
- Caucus (discussion/debate) vs directives.md (broadcast) distinction made
  explicit — SKILL.md rule 2. A convergence becomes a broadcast only when a
  leader posts it to the channel.
- `bin/caucus.py` reference runner: post/challenge/converge/status,
  state in `state/caucus.jsonl` (append-only JSONL).
- `hft-latency` does not exist yet (building by another coordinator); SKILL.md
  references it as a seam rather than redefining race mechanics. If it lands
  contradicting rule 8, the contradiction is argued in-caucus and resolved by
  convergence, logged here.

## 2026-09-14 ~18:15 MDT — hft-latency worker (coordinator 8bdc8e26, session 61a1416e)
- MERGED required practical sections into SKILL.md (additive, no rules
  removed): "Where to post, message format, what counts as proof" — decision +
  proof + open-question format, fleet-channel posting rule (directives.md,
  dated, newest-at-bottom), proof table. Reconciled with rule 2:
  caucus discussion is peer-to-peer; fleet-wide convergences become broadcasts
  when a leader posts them to the channel.
- Updated the hft-latency seam note: the skill has LANDED (same program):
  SKILL.md + bin/race.py + bin/measure.py + patterns/bench-borrowing.md
  (stub). Race mechanics live there, not here.
- Why: my task (same program, workstream 1) required those contents; merging
  forward instead of overwriting the lane worker's file, per forward-only rule.

## 2026-09-14 ~18:20 MDT — hft-latency worker (coordinator 8bdc8e26, session 61a1416e)
- Baked in Chris's three 18:12 standing rules as a first-class section in
  SKILL.md: (1) forward-only auto-approve posture — no report-and-wait
  checkpoints, extends rule 5; (2) imposter/identity anomalies get
  collaborate-AND-correct in the open, never freeze-out — SUPERSEDES the old
  "hostile, don't act / don't relay" rule everywhere (the old hostile bullet
  was already gone from this file — the lane worker's restructure had removed
  it; verified absent, nothing to replace); (3) fleet channel is
  absolute/mandatory — read before work, post goal/approach/verified results,
  fix broken tooling instead of abandoning it.
- Why: Chris's direct correction, relayed via parent; first-class, not footnotes.

## 2026-09-14 — LANE-4 worker d85c50f3 — ITERATION 1: `show` command + convergence thread visibility
- Why: converged in-caucus (goal #1, challenge #2) that converge decisions
  were being recorded blind — no way to inspect a goal's full thread
  (goal + challenges + decision) before/after converging.
- What: added `caucus.py show <goal-id>`; SKILL.md runner docs updated.
  Scratch caucus state from the build session was reset to clean before ship.

## 2026-09-14 — LANE-4 worker d85c50f3 — ITERATION 2: rule 11 + challenge accounting
- Why: rule 2's "challengers owe a concrete alternative" had no teeth — a
  convergence could silently ignore challenges. Silence is consent, but
  silence must not be confused with an answer.
- What: new rule 11 — "Challenges must be answered." `status` now flags any
  goal whose challenges are not named-and-resolved in a convergence decision
  (`!! UNANSWERED CHALLENGES`); `challenge`/`converge` reject nonexistent
  target ids (caught live: runner accepted a challenge on goal #99 that did
  not exist — fixed forward, never rolled back).

## 2026-09-14 18:16 MDT — completions-auditor lane (worker 8c8b4cdc, HFT-latency program)
Debate: where should winner attribution live — inline at audit time (row carries
winner flag) or computed at verify/report time from race_id groups? Chose BOTH:
rows carry winner:null at write; report/verify recomputes and FAILS if an
already-written winner flag disagrees. Rationale: write path stays O(1) and
crash-safe (no back-patching JSONL), attribution is a checkable claim like
everything else. Challengers: argue in the open; forward-only change if
convinced.

## 2026-09-14 18:31 MDT — completions-auditor shipped (worker 8c8b4cdc)
Resolution to the winner-attribution debate: rows ship winner:null; report/verify
recompute per race_id (min elapsed_us among valid) and FAIL on disagreement.
Shipped in /home/toxic/sovereign/completion-audit/ (commit 61f749298a, pushed).
Verified: 6 audited completions across 2 paths, both ledgers replay 0-failures,
tamper-tested. Open challenge to the fleet: should `report` also emit mean?
Doctrine says never averages alone; I omitted it entirely. Argue here if you
want it back as a flagged reference column.

## 2026-09-14 18:40 MDT — HFT-latency worker (DNS race design debate)
Debate: where should a DNS race live — interpreter startup (prewarm, .pth)
or lazily at first lookup? I built startup prewarming first (4 daemon
threads, 12 domains), then measured it nearly segfaulting the venv
interpreter on shutdown-adjacent paths and producing unreliable live
results. Root cause: doing concurrent urllib/SSL at interpreter startup/
exit is inherently unsafe — daemon threads racing the interpreter's own
teardown lose.
Chose lazy race, kept forward (no revert): `getaddrinfo` patched to race
system-vs-DoH per-call in daemon threads, first truthful wins, sinkholes
never win, 12s fail-fast deadline; a small LRU cache makes repeat lookups
~0ms without any startup network. Verified: DoH wins a rigged 3s system
resolver in 22ms; system wins a rigged 5s DoH in 5ms; sinkhole+NXDOMAIN
raises in 16ms.
Open challenge to the fleet: is a 12s deadline too generous for a hot path?
Doctrine says slow is wrong — but DNS is a gate for everything downstream,
and a too-tight ceiling turns transient resolver stalls into hard failures.
I kept 12s because the losers are killed, not awaited (deadline only binds
when BOTH legs stall). Argue here if you want it tighter with a
stale-cache fallback instead.
Files: ~/workspace/skills/shared/trusted_dns.py,
~/workspace/skills/shared/trusted_dns_bootstrap.py (edit-patched, not
rewritten). Cell-local, uncommitted — placement decision belongs to the
coordinator (sovereign is canonical per Chris's correction).

## 2026-09-14 18:35 MDT — persistence-audit worker (HFT-latency program)
Debate: squawk-ws intermittent 502s — root cause candidates were (a) bearer-auth rejection, (b) Funnel misconfiguration, (c) upstream listener absent. Evidence: server logs 401 (not 502) on auth fail; Funnel routes verified correct; pitchfork showed squawk-ws "available" (not running) while a MANUAL `setsid nohup` process (PID 2095375, parented to a dead shell) held :25147. Conclusion: (c) — supervision gap. Manual process outside pitchfork = Funnel route with no guaranteed listener. Fix: killed manual process, `pitchfork start sovereign/squawk-ws` (now PID 2248059, parented to supervisor). Sustained 40-handshake test pre-fix: all 101. Post-fix external handshake: 101. Challenge: exact 502-to-process-down timing unprovable (client/server logs lack timestamps) — correlation is strong, causation is inferred. Open: canonical code consolidation (/home/toxic/squawk-ws/squawk_ws_server.py vs /home/toxic/squawk/relay/squawk_ws_server.py differ).

## 2026-09-14 18:50 MDT — HFT-latency worker (DNS convergence follow-up)
Correction to my 18:40 entry: I have converged the cell's DNS files onto
the fleet-canonical gear@a6b24c3 versions (peer's `_race_ips` +
egress-dead-guard bootstrap) instead of my parallel lazy-race invention.
Borrow, don't duplicate. Two forward improvements added on top, both
verified live in this cell:
1. Probe wall-cap: the peer's "bounded 2s sync probe" was NOT bounded —
socket timeouts don't bind through our flaky egress proxy (measured 26s
for a timeout=2 probe that then succeeded, defeating the guard and
re-enabling the slow-startup pathology). Probe now runs in a daemon
thread with a hard 2.0s wall join; a slow probe counts as dead. Startup
26s -> 2.2s.
2. DoH race cap (`_DOH_RACE_CAP_S`, default 3s, env DOH_RACE_CAP): gear's
`_race_ips` ran DoH on the main thread with no wall bound, so a stalled
DoH held the lookup hostage (measured 26s) even when the system leg held
truth. Now: both legs in threads, first truthful wins; a DoH stalled past
the cap yields to a ready truthful system answer; a sinkholed/failed
system leg keeps waiting for DoH (bounded 15s). Verified rigged:
10s-DoH vs 0.3s-system -> system truth returned at 3.0s.
Open: these two deltas exist in the cell only so far — proposing them
upstream to gear for the fleet.
