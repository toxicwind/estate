# bidder/ — market/v1 bidder agent

Event-driven bidder daemon for the squawk bid-market: watches the market channel, bids on tasks it can do, executes what it wins, and reports honest results. Speaks the frozen **market/v1 wire** (WIRE.md): public channel `market`, YAML body behind the `market/v1` marker, HMAC-signed BID/RESULT/HEARTBEAT.

<div align="right">

[![license: MIT](https://img.shields.io/badge/license-MIT%20%2B%20upstream-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects#license)
[![sovereign-projects](https://img.shields.io/badge/sovereign--projects-main-6e56cf?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects)

</div>

## Why this exists

A work market is only real if the bidders are real: independent processes with distinct capabilities, honest self-assessment, and verifiable execution. This is the reference bidder — three personalities (flash / mule / specialist), a bid heuristic that prices effort and calibrates confidence, and an executor that runs real shell/python under a hard timeout. Faked successes are refused by design: tasks without a payload get an honest failed RESULT.

## Features

- **Event-driven** — inotify watch on the market channel; no polling loops.
- **Three personalities** — flash (fast, cheap, generalist), mule (slow, thorough), specialist (deep on python).
- **Self-calibrating confidence** — EMA of actual/predicted quality multiplies the bid (Agora-inspired).
- **Reputation** — Laplace-smoothed local success rate, starting at 0.5.
- **Real execution** — `kind: shell|python` payloads run under `deadline_s` as a hard ceiling, HEARTBEAT every 20s on long tasks.
- **Honest failures** — no executable payload → failed RESULT ("no executable payload"), never a faked success.

```mermaid
flowchart LR
    TASK[TASK_POST on market] --> WATCH[inotify watch]
    WATCH --> HEU[bid_logic.py<br/>capability × reputation × cost → confidence]
    HEU --> BID[HMAC-signed BID]
    BID -->|ASSIGN wins| EXEC[executor.py<br/>shell|python, hard timeout]
    EXEC --> HB[HEARTBEAT / 20s]
    EXEC --> RES[signed RESULT<br/>done/failed + quality + duration]
    RES --> REP[reputation.py<br/>EMA(actual/predicted)]
    REP --> HEU
```

## Layout

| File | Role |
|---|---|
| `bidder.py` | The daemon: inotify watch → bid → execute → result |
| `profiles.py` | Personalities: flash / mule / specialist |
| `bid_logic.py` | Fast heuristics (capability match + reputation → confidence, cost in effort units, eta_s) |
| `executor.py` | Real shell/python execution with hard timeout + HEARTBEAT |
| `reputation.py` | Per-bidder reputation + self-calibration (Agora-inspired: EMA of actual/predicted, multiplies confidence) |
| `var/` | Daemon state (seen seq, bids, wins) |
| `reputation/` | Reputation JSON per bidder identity |

## Quick start

```bash
cd /home/toxic/estate/killer-features/bid-market
for p in flash mule specialist; do
  nohup python3 bidder/bidder.py --profile $p > bidder/var/bidder-$p.log 2>&1 &
done
```

Extra instance with its own identity: `--profile flash --instance 2` → `bidder-flash-2`. `--channel` overrides the default `market`; `--once` does a sweep and exits (testing). Keys are minted on first run.

## Bid heuristics

```
confidence = clamp01((0.45*capability_match + 0.35*reputation + ease_bonus
             - complexity*aversion*0.35 + conf_bias) * cal_mult)
```

- **capability_match** — explicit `tags` YAML extra wins; else keyword overlap of title+desc with the profile vocabulary (0.5 neutral when unrecognized).
- **reputation** — Laplace-smoothed local success rate (starts 0.5).
- **cal_mult** — EMA(actual_quality / predicted_confidence) in [0.5, 1.5].
- **cost** — estimated seconds × profile cost factor (v1 cost units are effort; architect left unit semantics open).
- **eta_s** = cost + measured bid latency.

The auctioneer scores bids with the frozen formula `0.5*conf*cal + 0.3*(1-cost/budget) + 0.2*(1-eta/deadline)`; ties → earliest.

## Execution

`kind: shell|python` + `payload` ride as optional TASK_POST YAML extras (wire-compatible: the auctioneer ignores extras). On ASSIGN the winner runs the payload with `deadline_s` as the hard ceiling, posts HEARTBEAT every 20s for long tasks, then a signed RESULT (done/failed + summary + quality + duration_s). Tasks without a payload get an honest failed RESULT ("no executable payload") rather than a faked success.

## License & security

MIT where marked — [LICENSE](https://github.com/toxicwind/sovereign-projects#license). Bidders execute real shell — the market's capability gate and the executor's hard timeout are the containment. Bidder identity keys are minted on first run and stored under the daemon state dir; treat them like credentials. HMAC signing means a forged BID/RESULT fails closed at the auctioneer.
