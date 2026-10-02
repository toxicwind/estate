---
name: heg-ttc-engine
description: Hierarchical Entropy-Guided Test-Time Compute (HEG-TTC) Engine for autonomous software engineering.
---
# HEG-TTC Engine

## Summary
Implements test-time compute allocation based on problem entropy (Scaling Test-Time Compute for Agentic Coding arXiv:2604.16529), Monte Carlo Tree Search rollouts (SWE-Search arXiv:2410.20285), and nanosecond candidate patch racing.

## Scripts
- `scripts/entropy_allocator.py`: Classifies issue complexity and sets dynamic compute budgets.
- `scripts/mcts_rollout.py`: UCT tree expansion and execution-guided reward backpropagation.
- `scripts/ast_indexer.py`: Dual-pass regex/AST scanner for instant sync and async symbol indexing.
- `scripts/code_racer.py`: Monotonic nanosecond timing engine for candidate patch racing.

## Resources
- `resources/frontier_2026_guide.md`: Operational directives for test-time scaling on consumer hardware.
