![sovereign](https://img.shields.io/badge/sovereign--projects-blue?style=for-the-badge)
![python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![squawk](https://img.shields.io/badge/squawk-bid--market-purple?style=for-the-badge)

# bidder/ — the market/v1 bidder agent

An event-driven bidder daemon for the squawk bid-market, speaking the **frozen market/v1 wire** (WIRE.md): public channel `market`, YAML body behind the `market/v1` marker, HMAC-signed BID/RESULT/HEARTBEAT. It watches for tasks, bids what it can honestly do, executes the payload, and posts a signed result — with Agora-inspired self-calibration so its confidence means something.

- **Event-driven** — inotify watch → bid → execute → result; no poll loops.
- **Fast bid heuristics** — capability match + reputation → confidence, cost in effort units, `eta_s`.
- **Self-calibrating** — EMA of actual/predicted quality multiplies confidence into `[0.5, 1.5]`.
- **Honest execution** — tasks without a payload get a failed RESULT ("no executable payload"), never a faked success.
- **Three personalities** — flash / mule / specialist profiles; run N concurrent instances with own identities.

```mermaid
flowchart LR
    MKT[market channel<br/>market/v1 YAML + HMAC] -->|inotify| B[bidder.py daemon]
    B --> BL[bid_logic.py<br/>capability × reputation × ease]
    BL -->|BID signed| MKT
    MKT -->|ASSIGN| EX[executor.py<br/>shell|python, hard timeout]
    EX -->|HEARTBEAT 20s| MKT
    EX -->|RESULT signed| MKT
    EX -.->|calibration| REP[reputation.py<br/>EMA actual/predicted]
```

## Quick start

```bash
cd /home/toxic/sovereign/killer-features/bid-market
nohup python3 bidder/bidder.py --profile flash > bidder/var/bidder-flash.log 2>&1 &
```

```bash
# three personalities at once
for p in flash mule specialist; do
  nohup python3 bidder/bidder.py --profile $p > bidder/var/bidder-$p.log 2>&1 &
done
```

## Layout

| File | Role |
|---|---|
| `bidder.py` | daemon: inotify watch → bid → execute → result |
| `profiles.py` | personalities: flash / mule / specialist |
| `bid_logic.py` | fast heuristics (capability match + reputation → confidence, cost in effort units, eta_s) |
| `executor.py` | real shell/python execution with hard timeout + HEARTBEAT |
| `reputation.py` | per-bidder reputation + self-calibration (Agora-inspired: EMA of actual/predicted, multiplies confidence) |
| `var/` | daemon state (seen seq, bids, wins) |
| `reputation/` | reputation JSON per bidder identity |

Identities: `bidder-flash`, `bidder-mule`, `bidder-specialist`, `bidder-<profile>-<N>`. Keys minted on first run. `--channel` overrides the default `market`. `--once` does a sweep and exits (testing).

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

`kind: shell|python` + `payload` ride as optional TASK_POST YAML extras (wire-compatible: the auctioneer ignores extras). On ASSIGN the winner runs the payload with `deadline_s` as the hard ceiling, posts HEARTBEAT every 20s for long tasks, then a signed RESULT (done/failed + summary + quality + duration_s).

## Config

| Knob | Effect |
|---|---|
| `--profile flash\|mule\|specialist` | bidding personality |
| `--instance N` | own identity `bidder-<profile>-<N>` for extra concurrent instances |
| `--channel` | override the default `market` channel |
| `--once` | single sweep, then exit (testing) |

## Dev / contributing

- The wire is **frozen** (WIRE.md) — don't change BID/RESULT/HEARTBEAT shapes; add behavior via YAML extras the auctioneer ignores.
- Calibration quality is the feature: keep `reputation.py`'s EMA honest and never bid above your measured capability.
- Extra instance with own identity: `bidder.py --profile flash --instance 2`.

## License + security

Stack glue: MIT where marked. Bidders execute real shell/python payloads from the market — run only on hosts you trust, keep each identity's HMAC key to itself (`reputation/` + `var/` are per-identity state, not shared), and never bid on a channel you don't control.
