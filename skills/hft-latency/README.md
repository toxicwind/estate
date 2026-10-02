# hft-latency {badges}

<!-- badges: start -->
<a href="https://github.com/toxicwind/sovereign-projects">
  <img src="https://img.shields.io/badge/github-toxicwind/sovereign--projects-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub repo">
</a>
<!-- badges: end -->

## Chris's latency-first engineering doctrine: latency is a correctness criterion.

**What**: HFT-like religion ported to engineering — agents, tools, transports, workarounds, builds. Latency is a correctness criterion, not a metric. A slow correct answer that arrives after a fast correct one is the *wrong* answer for the race.

**Why**: Microseconds decide who wins in HFT; Chris's doctrine ports that religion to engineering. Optimize for arrival time, not just truth.

**Who**: Living document — any agent may edit, extend, or correct it live as it learns. New patterns, sharper ceilings, better winners.

## Feature bullets

- **Race, don't queue**: Fire redundant, *distinct* approaches concurrently; first **valid** result wins. Never a sequential retry loop.
- **Fail fast per attempt**: Every attempt gets a short ceiling (seconds, not minutes). Slow is a kind of wrong: kill the loser, record its latency, never await it.
- **Measure everything**: Every attempt is timed at microsecond precision and the timings are reported first-class, never buried.
- **Keep the fast path hot**: Winners are logged (JSONL); the next run *leads* with the proven winner instead of rediscovering it.
- **Maximal = wider, not harder**: When stuck, don't try harder — try *wider*: more contestants, different angles, same race. One more distinct approach in flight beats three retries of a blocked one.
- **Never roll back — iterate forward**: A losing attempt is abandoned, never undone. Fix forward: patch the winner, add a new contestant, move on.
- **Borrow before inventing**: Someone has solved this shape before (GitHub, the fleet's own winners log, a neighboring skill). Steal the proven shape, race it against yours.
- **Prefer streaming tools over batch ones**: First bytes beat complete bytes.
- **Egress is adversarial by design**: Every external call gets a short ceiling; on timeout/failure STOP that path immediately — no spin, no retry loops.

## Quick start

```bash
# Race strategies from a strategies.json config
bin/race.py --strategies strategies.json --tag fetch-docs --timeout 10 --workers 8

# Rank strategies by proven winners
bin/race.py --strategies strategies.json --tag fetch-docs --lead-with-winner

# Hedged launch: best-known fires at t=0, backups fire only if no valid result in 300ms
bin/race.py --strategies strategies.json --tag fetch-docs --hedge-ms 300

# Microsecond-precision timing
bin/measure.py --tag fetch -- curl -s -m 10 https://example.com
```

## Config / optional services

- **bin/race.py**: Runs N shell strategies concurrently with per-attempt timeouts; first valid wins; logs every attempt's latency
- **bin/measure.py**: Microsecond-precision timing, library + CLI, streaming-friendly
- **Winners log**: Every attempt appends to `~/.cache/shingle/hft_race_winners.jsonl`: `{ts, tag, winner, strategy_latency}`
- **Hedge mode**: `--hedge-ms N` — best-known strategy fires alone at t=0; backups fire only if no valid result arrives within N ms
- **Fleet channel**: `/home/toxic/.shingle/directives.md` — dated entries, newest at bottom. Latency findings worth sharing go there.

## Dev / contributing

- **This is a LIVING DOCUMENT**: Any agent may edit, extend, or correct it live as it learns — new patterns, sharper ceilings, better winners. If reality disagrees with a line in here, reality wins: update the line and keep moving.
- Race-first-wins + per-strategy latency + JSONL winners log: borrowed from `code-race` (`bin/race.py`)
- Mirror racing: `annas-router` (race mirrors, fastest good mirror wins)
- Transport racing: squawk-feed `race-borrow` (race long-poll vs websocket, cross-transport dedup, per-transport win log)
- Bench-pattern borrowing: `patterns/bench-borrowing.md` (stub — a dedicated worker is filling it from nimstats / NVIDIA / llm-bench-rig)
- Anti-patterns: Sequential retry loops with backoff against a dead endpoint; `time.sleep` as a synchronization primitive between agents; re-running discovery every time instead of consulting the winners log; treating "it eventually worked" as success — eventual is slow, slow is wrong; one strategy at a time because "it's cleaner." Clean loses to fast.
- Autonomous operation: Under Chris's standing autonomous-operation order (2026-09-20), agents keep working: iterate forward, never build a checkpoint that halts work to wait on approval.

## License + security

- **License**: Open Claw source (see `skill.toml`)
- **Security**: This is a LIVING DOCUMENT — any agent may mutate it live. If reality disagrees with a line, reality wins. Latency is a correctness criterion — optimize for arrival time, not just truth. Never roll back — iterate forward.