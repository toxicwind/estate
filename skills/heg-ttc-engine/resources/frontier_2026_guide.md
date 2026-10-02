# Frontier 2026 Test-Time Compute Scaling Guide

## 1. The Test-Time Compute Paradigm
Frontier reasoning models scale performance by expending compute dynamically at inference time:
- Simple tasks receive minimal budget, protecting the cumulative 12-hour evaluation window.
- Hard, ambiguous tasks receive multi-turn MCTS exploration, evaluating candidate patch trees.

## 2. Dynamic Gating Invariant
Never spend >60 seconds on a bug that has a clear reproduction traceback in a single file. Allocate the remaining 300+ seconds to tasks with multi-file async call dependencies.
