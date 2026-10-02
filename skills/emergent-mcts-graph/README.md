# emergent-mcts-graph {badges}

<!-- badges: start -->
<a href="https://github.com/toxicwind/sovereign-projects">
  <img src="https://img.shields.io/badge/github-toxicwind/sovereign--projects-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub repo">
</a>
<!-- badges: end -->

## Monte Carlo Tree Search and Dynamic Runtime Subgraph Inducer for autonomous software engineering.

**What**: Implements test-time compute scaling via MCTS (inspired by SWE-Search arXiv:2410.20285 and CodeMonkeys arXiv:2501.14723) and dynamic runtime execution subgraph induction (inspired by Code Graph Model arXiv:2505.16901).

**Why**: Scaling test-time compute for agentic coding and enabling dynamic subgraph extraction from runtime tracebacks and AST nodes.

**Who**: MCTS engine and subgraph inducer for autonomous software engineering tasks.

## Feature bullets

- **MCTS Engine**: `scripts/mcts_engine.py` — UCT-based tree exploration and reward backpropagation engine
- **Dynamic Subgraph Inducer**: `scripts/dynamic_subgraph_inducer.py` — Extracts call chains from runtime tracebacks and AST nodes (dual-pass regex/AST scanner)
- **Tree Expansion**: UCT-based within per-task time limits
- **Resources**: `resources/mcts_tree_search_guide.md` — Guidance on managing tree expansion within per-task time limits
- **Test-Time Compute**: Scaling via MCTS for autonomous software engineering

## Quick start

```bash
# MCTS engine exploration
python scripts/mcts_engine.py --help

# Dynamic subgraph induction
python scripts/dynamic_subgraph_inducer.py --help
```

## Config / optional services

- **Per-task time limits**: Manage tree expansion within time constraints
- **Resources**: `resources/mcts_tree_search_guide.md` for guidance on tree expansion

## Dev / contributing

- MCTS scaling inspiration: SWE-Search arXiv:2410.20285 and CodeMonkeys arXiv:2501.14723
- Subgraph induction inspiration: Code Graph Model arXiv:2505.16901
- Manage tree expansion within per-task time limits
- No artificial sleeps, polling loops, or timeouts-as-delays. Event-driven.

## License + security

- **License**: Open Claw source (see `skill.toml`)
- **Security**: No monkeypatching. All scripts operate on AST and runtime traces without modifying inference substrate.