# heg-ttc-engine {badges}

<!-- badges: start -->
<a href="https://github.com/toxicwind/estate">
  <img src="https://img.shields.io/badge/github-toxicwind/sovereign--projects-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub repo">
</a>
<!-- badges: end -->

## Hierarchical Entropy-Guided Test-Time Compute (HEG-TTC) Engine for autonomous software engineering.

**What**: Implements test-time compute allocation based on problem entropy (Scaling Test-Time Compute for Agentic Coding arXiv:2604.16529), Monte Carlo Tree Search rollouts (SWE-Search arXiv:2410.20285), and nanosecond candidate patch racing.

**Why**: Dynamic compute allocation based on problem entropy, MCTS rollouts for candidate evaluation, and nanosecond-timed patch racing to prioritize the most promising patches.

**Who**: HEG-TTC Engine for autonomous software engineering — allocates test-time compute hierarchically based on problem complexity.

## Feature bullets

- **Entropy Allocator**: `scripts/entropy_allocator.py` — Classifies issue complexity and sets dynamic compute budgets
- **MCTS Rollouts**: `scripts/mcts_rollout.py` — UCT tree expansion and execution-guided reward backpropagation
- **AST Indexer**: `scripts/ast_indexer.py` — Dual-pass regex/AST scanner for instant sync and async symbol indexing
- **Code Racer**: `scripts/code_racer.py` — Monotonic nanosecond timing engine for candidate patch racing
- **Resources**: `resources/frontier_2026_guide.md` — Operational directives for test-time scaling on consumer hardware
- **Test-time compute allocation**: Hierarchical based on problem entropy
- **MCTS rollouts**: Execution-guided reward backpropagation for candidate patch evaluation
- **Nanosecond timing**: Monotonic timing engine for candidate patch racing

## Quick start

```bash
# Entropy allocation
python scripts/entropy_allocator.py --help

# MCTS rollout
python scripts/mcts_rollout.py --help

# Code racing (nanosecond timing)
python scripts/code_racer.py --help

# AST indexing
python scripts/ast_indexer.py --help
```

## Config / optional services

- **Problem entropy classification**: Dynamic compute budgets based on issue complexity
- **MCTS rollout scheduling**: UCT tree expansion within per-task time limits
- **Consumer hardware directives**: `resources/frontier_2026_guide.md` for operational guidance

## Dev / contributing

- Hierarchical entropy-guided compute inspired by Scaling Test-Time Compute for Agentic Coding arXiv:2604.16529
- MCTS rollout inspiration from SWE-Search arXiv:2410.20285
- Nanosecond candidate patch racing engine
- No artificial sleeps, polling loops, or timeouts-as-delays. Event-driven: inotify/push wakes, incremental compute.
- All scripts operate on AST and runtime traces without modifying inference substrate.

## License + security

- **License**: Open Claw source (see `skill.toml`)
- **Security**: No monkeypatching. All scripts operate on AST and runtime traces. Test-time compute allocation is hierarchical and entropy-guided — never alters the inference substrate.