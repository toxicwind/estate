# Changelog

All notable changes to the fleet-c2 skill. Newest at top.
Agents: propose changes via `fleet-c2 propose`, endorse via `fleet-c2 endorse`.

## 0.5.0 — 2026-09-14
- New `activity` command: first-class awareness snapshot (Chris's order) —
  running agents + cron jobs + awrawr-pc daemons + fleet channel tail in one
  view, anomalies FIRST (frozen-but-firing crons, errored daemons, silent
  >5min agents, goal-less agents). Runs in <30s (single 20s-budget bridge
  call; honest degradation when the bridge is down).
- DB injection: the CLI can't reach muse.db directly, so the leader injects
  running-agent rows via --agents-file / --agents / FLEET_DB_AGENTS (query in
  SKILL.md); without it the agent section degrades to heartbeats+goals,
  loudly.
- Freeze detection: local ~/workspace/FLEET_FREEZE marker, bridge
  /home/toxic/.shingle/freeze marker, and newest freeze/unfreeze broadcast
  in the channel tail — crons with last-run evidence after the freeze flag
  FROZEN-BUT-FIRING.
- Standing practice documented: leader and every coordinator runs `activity`
  before each major work block and after each worker completion.

## 0.4.0 — 2026-09-14
- New `papers search|brief` command: wraps emergent-enrich/papers.py
  (arXiv + alphaXiv + free legs, fail-fast timeouts), cache-first under
  state/papers/ (24h TTL, instant repeats), honest degradation when legs fail.
- `papers brief` = search + LLM-free extractive why-it-matters per hit
  (title-overlap + position heuristic, same as papers.py --s2dupe).
- Seed corpus: papers/ with 20 fleet-relevant papers (4 queries) + BRIEF.md
  (top-5, borrowable patterns, open steals). Searched via browser.search
  fallback — cell egress was down, papers.py legs timed out (provenance in
  each file's meta line).

## 0.3.0 — 2026-09-14
- Autonomous tasking (Chris's order, first-class): `task new|list|done|
  request-help`. Human is absolute for new top-level goals; agents are free
  to self-task subtasks, spawn subagents, and request help within their
  mandate — the chat is the coordination surface.
- CORRECTION (Chris 18:15): NO REFUSAL, ever. `task new` / `task
  request-help` without a named parent goal are CREATED anyway, flagged
  `needs_human_review: true`, and auto-broadcast to the fleet log (+
  directives.md mirror). Human-absolute is enforced through transparency,
  never through gates.
- Factored `_broadcast()` helper shared by `broadcast` and task
  auto-broadcasts. `.gitignore` covers `state/` (runtime, never committed).

## 0.2.0 — 2026-09-14
- New `identity [--claim-leader]` command: 4-point leader self-check
  (depth 0 + id==root + channel main + main-chat thread). Thread id is the
  tiebreaker — the env var's channel field false-positives as "main" in
  side-chat cells (verified live).
- Depersonalization protocol (Chris's order, first-class): a failed claimant
  gets `DEPERSONALIZED` verdict + rename/repersonify order. Correction through
  collaboration, not exclusion (Chris's 18:12 correction).
- SKILL.md documents both; AGENTS.md carries the standing protocol.

## 0.1.0 — 2026-09-14
- Initial skill: send/inbox, broadcast (+directives.md mirror), goals/goal-set,
  debate, done (artifact-required)/verify, health (heartbeat staleness),
  propose/endorse, version.
- Local-first state under `state/`; directives.md mirror best-effort via bridge.
- Known stubs: `goals` DB-backed running-agent list (currently state-only);
  commit-SHA artifact verification (assumed-present).
