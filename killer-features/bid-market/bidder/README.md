# bidder/ — market/v1 bidder agent

Event-driven bidder daemon for the squawk bid-market, speaking the **frozen
market/v1 wire** (WIRE.md): public channel `market`, YAML body behind the
`market/v1` marker, HMAC-signed BID/RESULT/HEARTBEAT.

## Layout

- `bidder.py` — daemon: inotify watch → bid → execute → result
- `profiles.py` — personalities: flash / mule / specialist
- `bid_logic.py` — fast heuristics (capability match + reputation → confidence,
  cost in effort units, eta_s)
- `executor.py` — real shell/python execution with hard timeout + HEARTBEAT
- `reputation.py` — per-bidder reputation + self-calibration (Agora-inspired:
  EMA of actual/predicted, multiplies confidence)
- `var/` — daemon state (seen seq, bids, wins)
- `reputation/` — reputation JSON per bidder identity

## Run N concurrent bidders

```bash
cd /home/toxic/sovereign/killer-features/bid-market
for p in flash mule specialist; do
  nohup python3 bidder/bidder.py --profile $p > bidder/var/bidder-$p.log 2>&1 &
done
# extra instance, own identity:
nohup python3 bidder/bidder.py --profile flash --instance 2 \
  > bidder/var/bidder-flash-2.log 2>&1 &
```

Identities: `bidder-flash`, `bidder-mule`, `bidder-specialist`,
`bidder-<profile>-<N>`. Keys minted on first run. `--channel` overrides the
default `market`. `--once` does a sweep and exits (testing).

## Bid heuristics

confidence = clamp01((0.45*capability_match + 0.35*reputation + ease_bonus
           - complexity*aversion*0.35 + conf_bias) * cal_mult)

- capability_match: explicit `tags` YAML extra wins; else keyword overlap of
  title+desc with the profile vocabulary (0.5 neutral when unrecognized)
- reputation: Laplace-smoothed local success rate (starts 0.5)
- cal_mult: EMA(actual_quality / predicted_confidence) in [0.5, 1.5]
- cost: estimated seconds × profile cost factor (v1 cost units are effort;
  architect left unit semantics open)
- eta_s = cost + measured bid latency

The auctioneer scores bids with the frozen formula
`0.5*conf*cal + 0.3*(1-cost/budget) + 0.2*(1-eta/deadline)`; ties → earliest.

## Execution

`kind: shell|python` + `payload` ride as optional TASK_POST YAML extras
(wire-compatible: the auctioneer ignores extras). On ASSIGN the winner runs
the payload with `deadline_s` as the hard ceiling, posts HEARTBEAT every 20s
for long tasks, then a signed RESULT (done/failed + summary + quality +
duration_s). Tasks without a payload get an honest failed RESULT
("no executable payload") rather than a faked success.
