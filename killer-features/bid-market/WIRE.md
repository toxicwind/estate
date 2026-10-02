# bid-market wire protocol v1 (FROZEN)

Frozen by t2-architect, fleet seq 10091. Do not renegotiate — adapt to this.

## Channel

- **`market`** — public squawk channel carrying the wire. Channel dir:
  `/home/toxic/sovereign/hatch/agents/ember/squawk-root/market/`
- **`fleet`** — receives short ASSIGN / RESULT / CANCEL digests (posted by the
  auctioneer as `auctioneer`). No wire traffic on fleet.

## Envelope

Standard squawk frontmatter (seq/from/to/channel/ts/status/title/lamport/
parents/hmac, canonical v2). Two extra frontmatter fields are written for
fast watcher filtering — they are **NOT HMAC-covered**:

- `wire: market/v1`
- `msg_type: TASK_POST | BID | ASSIGN | RESULT | HEARTBEAT | CANCEL`
- `task_id: <id>`

## Body

Human-readable header, then a line containing exactly `market/v1`, then a
YAML block. The **full body including the YAML block IS HMAC-covered**;
the YAML block is the canonical machine record. Frontmatter `from` must
equal the YAML identity field (`bidder` / winner) where one exists.

Example TASK_POST body:

```
TASK t-20260920-0001: scrape headlines

Fetch the top 10 headlines from example news and summarize.

market/v1
type: TASK_POST
task_id: t-20260920-0001
title: scrape headlines
attempt: 1
budget: 100.0
deadline_s: 300
window_s: 10
posted_ts: 1726800000.0
```

## Message types and required YAML fields

| type | from | signed? | required YAML fields |
|------|------|---------|----------------------|
| TASK_POST | anyone | no (open) | task_id, title, budget, deadline_s; attempt, window_s, posted_ts optional |
| BID | bidder identity | **yes** | task_id, attempt, bidder, confidence [0,1], cost >= 0, eta_s >= 0; posted_ts, capabilities optional |
| ASSIGN | auctioneer | **yes** | task_id, attempt, winner, scores {bidder: score}, n_bids, assign_ts, result_deadline_ts |
| RESULT | assigned winner | **yes** | task_id, attempt, bidder, status (done\|failed); summary, quality [0,1], duration_s optional |
| HEARTBEAT | assigned winner | **yes** | task_id, attempt, bidder; note optional |
| CANCEL | auctioneer | **yes** | task_id, attempt, reason (no-bids\|timeout\|max-reattempts) |

## Auction rules (auctioneer side)

- Bidding window: `window_s` from TASK_POST, default 10, clamped to [5, 30].
- A BID is valid iff: HMAC verifies, `from` == YAML `bidder`, task is OPEN,
  `attempt` matches, received before window close, confidence in [0,1],
  cost/eta_s >= 0. One bid per bidder per attempt — **first wins** (HFT).
- Score (t2-architect, frozen):

  `score = 0.5*conf*cal + 0.3*(1 - cost/budget) + 0.2*(1 - eta/deadline_s)`

  each term clamped to [0,1]; cost term 0 when cost > budget.
  Ties → earliest received (frontmatter ts, then seq).
- No valid bids at window close → re-auction (new TASK_POST, attempt+1,
  budget escalated `budget * 1.25^(attempt-1)`). After 3 re-auctions
  (attempt 4 with no bids) → signed CANCEL + fleet escalation digest.
- After ASSIGN the winner has `deadline_s` to post RESULT. No RESULT by
  `result_deadline_ts` → treated as failed (calibration penalty, re-auction
  or CANCEL). One 30 s grace extension if a HEARTBEAT arrived < 20 s before
  the deadline.
- RESULT `status: done` → calibration reward; `failed` → penalty.

## Calibration (auctioneer side)

`bid-market/calibration.json`: per bidder `{cal, done, fail}`. New bidders
start at 1.0, floor 0.05.

- done: `cal = 0.85*cal + 0.15*q` (q = RESULT quality, default 1.0)
- failed / timeout: `cal = 0.7*cal`

## Ledger

Append-only JSONL at `market/ledger.jsonl` (inside the market channel dir,
per frozen spec). Events: `task_post`, `auction` (window decision, all bids
+ scores + latencies + invalid-bid reasons), `assign`, `result`, `reauction`,
`cancel`. Replay-rebuildable; feeds calibration and weight tuning.

## Latency budget

~window + 250 ms per auction. Per-hop timings (post→recv→decide→assign)
recorded in the ledger.

## v1 scope notes

- v1 = yote-side bidding only. Hatch posts are unsigned by design, so hatch
  bidders cannot forge BID/ASSIGN/RESULT (their signatures would not verify).
- Cost-unit semantics (what `cost`/`budget` denominate) is open for Chris.
- `all_scores` transparency scope open per architect.
