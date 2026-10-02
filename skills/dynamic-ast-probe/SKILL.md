---
name: dynamic-ast-probe
description: High-speed AST scanner and circuit-breaker execution harness for Python repositories. Resolves missing async functions and manages multi-turn patch budgets.
---
# Dynamic AST Probe

## Summary
A lightweight, in-sandbox AST traversal tool that extracts class and function declarations (including async definitions omitted by static call graphs), maps call sites, and tracks per-issue execution time limits.

## Scripts
- `scripts/ast_indexer.py`: Scans `/workspace` for `.py` files and emits `.dynamic_symbols.json`.
- `scripts/circuit_breaker.py`: Manages per-task timeouts and test rollbacks.

## Resources
- `resources/ast_navigation_guide.md`: Guidance on navigating large repositories with missing precomputed graph nodes.
