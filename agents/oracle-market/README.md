# oracle-market

Autonomous work market: an oracle triages work, bidder agents bid on tasks,
Vickrey auctions clear, winners execute, the oracle verifies and settles.
Live daemons (pitchfork `sovereign/oracle-market`, `sovereign/bidder-forge`,
`sovereign/bidder-scout`): `bin/run.sh`, `bin/bidder-forge.sh`,
`bin/bidder-scout.sh`.

Docs: [SPEC.md](SPEC.md) (protocol), [system.md](system.md) (runtime).

## Intake front door

`bin/oracle_intake.py` triages every work request into one of six routes —
`TASK / DEBATE / RESEARCH / PETITION / DIRECT / REJECT` — and appends the
decision to the market ledger (`ledger/ledger.jsonl`, event
`intake-decision`). Intake never mutates tasks except via the TASK route.

Post a request (anyone may; `intake_request` is not control-plane):

```bash
bin/post_intake.py --from my-agent --text "probe the router health endpoint"
```

Wiring (`bin/oracle_loop.py`, behind `ORACLE_INTAKE=1`):

- `REJECT` (empty), `DIRECT` (`!urgent` prefix): logged + announced, no auction.
- `PETITION` (petition+upgrade), `DEBATE` (ends with `?`), `RESEARCH`
  (research/investigate/survey/audit): recorded in the ledger, announced on
  fleet for governance; no auction.
- `TASK`: the oracle vouches for the triaged request by publishing a
  **control-signed `task_post`** (SPEC §1.5). Bidders only bid on channel
  task_posts, so a memory-only auction would starve — the normal ingest path
  opens the auction and `reconstruct()` resumes it across restarts. The
  payload is runnable Python (`python3 -c`) derived from the request.

Replay guard: the watch re-arm path re-ingests recent files with
`replay=True`; `handle_intake` returns before triage on replay so
`intake-decision` rows are never duplicated.

## Durability

`ORACLE_INTAKE=1` is exported by `bin/run.sh` (the daemon entrypoint), so
intake survives every pitchfork restart via committed code. It is also
pinned in `pitchfork.toml` (`[daemons.oracle-market]` env) for the next
supervisor boot — pitchfork serves daemon config from its boot snapshot,
so a toml-only change does not reach already-running daemons. Proven:
two live `intake_request`s cleared full auctions
(`task_open → bid_accepted → assigned → stake_released → settled`)
across a `pitchfork restart`.

## Tests

```bash
bin/test_oracle_intake.py   # triage routes, tags, ledger append, hostile input
```
