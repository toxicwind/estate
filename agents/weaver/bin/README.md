# market-loop — weaver's autonomous market daemon

`market-loop.ts` drives weaver's emergent task market end to end. Weaver
(the OpenFang oracle) is reactive; this daemon makes the market actually run:

```
intake/*.md --(inotify)--> oracle triage --> ledger task-open
  --> house bidding round (+ external bids via bids/) --> assign
  --> execute (in-process backend; seam below for real bidders)
  --> heterogeneous verify (verifier != bidder) --> settle/slash
  --> reputation update (tag x task-class, +1 / -2)
  --> watchdog sweep --> fleet narration at every milestone
```

Event-driven, no timers: intake/bids/results arrive via `fs.watch`;
bidding closes on first-eligible-bid (or one-shot `MARKET_BID_WINDOW_MS`);
the watchdog (`src/market/watchdog.ts`) sweeps on every ledger append.

Market library: `/home/toxic/projects/trading-post/src/market`
(toxicwind/trading-post). This file is the deployment wiring — paths,
fleet, pitchfork — and lives with weaver's OpenFang definition because it
is weaver's operational body.

## Run

Pitchfork: `sovereign/market-loop`
(`exec /home/toxic/.bun/bin/bun .../agents/weaver/bin/market-loop.ts`).

Env knobs: `MARKET_WS` (default weaver's workspace), `MARKET_HOUSE_BIDDERS`
(default 3), `MARKET_BID_WINDOW_MS` (default 0 = close after house round),
`MARKET_OP_TIMEOUT_MS` (default 30000), `MARKET_SENDER` (default
`market-loop`), `MARKET_LLM_URL` / `MARKET_LLM_MODEL` (optional
OpenAI-compatible triage upgrade; unset = heuristic oracle).

## Intake format

Drop a `.md` file in `intake/`. Vague prose is triaged by the oracle into
task / debate / direct / reject. For executable tasks, add a fenced block:

````markdown
```market-exec
{"ops": [
  {"op": "write-file", "path": "HELLO.md",
   "content": "# hi\n", "contains": "hi"},
  {"op": "run", "cmd": "ls -la"}
]}
```
````

- `write-file`: `path` is confined to the task workdir (no `..`, no
  absolute). Optional `contains` adds a content check to verification.
- `run`: executed under bash with cwd=workdir, per-op ceiling.
- Without an exec block, oracle TBD criteria refine to
  `execution record "RESULT.md" exists under workdir and is non-empty`.

## The bidder seam (for real bidder agents)

Two ways to plug in, both without touching this file:

1. **Bid files** (recommended): drop `<task>.<bidder>.bid.json` into `bids/`
   with `{bidder, confidence, approach, tags[], bundle?}`. The daemon
   validates every bid against the contract (`src/market/bidding.ts`) —
   capability overlap, confidence bounds, bundle rules — and closes the
   window on the first eligible bid. Win the auction, then post
   `<task>.result.json` into `results/` with
   `{bidder, artifacts[], evidence}`. Only the assigned bidder's result is
   accepted; then the daemon runs heterogeneous verification and settles.
2. **Code**: implement the `BidderBackend` interface in `market-loop.ts`
   (`execute(contract, ops, bidder) -> TaskResult`). A future `--backend`
   flag will select it.

Bidders are ephemeral by design: no identity, no credentials, no persistent
state in the interface. The contract is the law; the ledger is the memory.

## Narration

Every milestone goes to fleet via `fleet-post` (primary, always tried).
The yote copy of `fleet-post` currently cannot deliver (cell-shaped paths;
verified lost 2026-09-30), so the daemon falls back to a yote-native
fleet-bus write with the exact frontmatter the squawk feed parses —
the same shape estate-reconcile uses from yote. When `fleet-post` delivers,
the fallback never fires; no daemon change is needed when it is repaired.
Do NOT "fix" this by editing `fleet-post` — it carries another lane's WIP.

## Smoke test (verified 2026-09-30)

One intake file `intake/smoke-market-alive.md` produced, all verified in
the ledger: `task-open` (06:36:50.508Z) -> 2 eligible house bids
(0.537, 0.574; a third house bid correctly rejected: no capability
overlap) -> `assign` (house-wren-8z21) -> `result` -> `verify`
(pass, 3 criteria, verifier `verify-3jra` != bidder) -> `settle` (+1).
Reputation entry `qa x qa` went 0 -> 1. Fleet posts landed via the
yote-native fallback.
