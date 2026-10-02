# Emergent MCTS & Subgraph Induction Skill

## Summary
Implements test-time compute scaling via MCTS (inspired by SWE-Search arXiv:2410.20285 and CodeMonkeys arXiv:2501.14723) and dynamic runtime execution subgraph induction (inspired by Code Graph Model arXiv:2505.16901).

## Scripts
- `scripts/mcts_engine.py`: UCT-based tree exploration and reward backpropagation engine.
- `scripts/dynamic_subgraph_inducer.py`: Extracts call chains from runtime tracebacks and AST nodes.

## Resources
- `resources/mcts_tree_search_guide.md`: Guidance on managing tree expansion within per-task time limits.