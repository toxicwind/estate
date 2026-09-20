# Bid-Marketplace E2E Report

**Batch:** e2e1 | **16 tasks** (4 shell-text, 4 shell-file, 4 python-compute, 4 python-data)
**Market pool:** 5 real `bidder.py` processes — bidder-flash, bidder-flash-2, bidder-mule, bidder-specialist, bidder-specialist-2
**Protocol:** PROTOCOL.md v0 (HMAC-signed squawk messages, channel `bid-market`)
**Auctioneer:** e2e test-harness driver implementing the protocol's bid window (8s) + deterministic tie-break (highest confidence → lowest eta → lexicographic bidder_id). Retires when t2-impl-auctioneer lands.
**Date:** 2026-09-20 | **Tester:** t2-e2e (ember)

## Method

Each task = real fixture files + a real shell/python payload executed by the
winning bidder's own executor on yote. Ground truth is recomputed
independently from fixtures by `checkers.py` (never trusts bidder output).
A "false completion" = task marked ok but checker fails. Baseline = the same
16 tasks, blind round-robin over 5 worker processes mirroring the real pool
(caps from the real profiles, delay = cost_bias × 1s), real execution.

Oracle (best-suited bidder, from the market's own model — max
capability_match, tie → min cost_bias): shell tasks → flash,
python tasks → specialist.

## Results: market vs naive round-robin

| metric | market (real auction) | round-robin (same pool) |
|---|---|---|
| tasks | 16 | 16 |
| verified completions | TBD | 11 |
| completion rate | TBD | 0.688 |
| false completions | TBD | 0 |
| allocation quality (% to oracle-best) | TBD | 0.50 |
| assign latency p50 / p95 (s) | TBD | 0.55 / 3.97 |
| completion latency p50 / p95 (s) | TBD | 1.33 / 6.07 |
| makespan (s) | TBD | 6.07 |

## Per-task ledger (market)

TBD

## Confidence assessment

TBD
