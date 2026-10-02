![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/dynamic-ast-probe?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/dynamic-ast-probe?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/dynamic-ast-probe?style=for-the-badge)

# dynamic-ast-probe
High-speed AST scanner and circuit-breaker execution harness for Python repositories

## What it does
Lightweight in-sandbox AST traversal tool that extracts class/function declarations (including async definitions missed by static call graphs), maps call sites, and tracks per-issue execution time limits.

## Why it matters
Solves the problem of missing async functions in static analysis by using dynamic AST scanning to capture the full runtime-definable symbol set, enabling accurate code navigation and impact analysis.

## Who it's for
Developers working with Python codebases who need accurate symbol extraction including async functions, and teams managing multi-turn agent execution with time budgets.

## Features
- **Async-Aware AST Scanning** - Extracts class and function declarations including `async def` omitted by static call graphs
- **Call Site Mapping** - Tracks where symbols are referenced across the codebase
- **Execution Time Tracking** - Manages per-task timeouts and implements test rollbacks via circuit breaker
- **Workspace Symbol Index** - Generates `.dynamic_symbols.json` for fast symbol lookup
- **Circuit Breaker Pattern** - Prevents runaway execution with configurable timeouts and automatic rollback capability

## Quick Start
```bash
# Scan workspace for Python symbols
python3 scripts/ast_indexer.py

# Execute with time limits and rollback capability
python3 scripts/circuit_breaker.py --task "your-task-here" --timeout 300

# View generated symbol index
cat .dynamic_symbols.json
```

## Configuration
- **ast_indexer.py**: Scans `/workspace` for `.py` files by default, outputs to `.dynamic_symbols.json`
- **circuit_breaker.py**: Manages per-task timeouts with test rollback capabilities, default timeout 5 minutes

## Development
Prompt-only skill - functionality is implemented in the provided Python scripts. Modify scripts/ast_indexer.py and scripts/circuit_breaker.py to adjust scanning behavior or timeout policies.

## License
Internal tool - refer to sovereign estate licensing

## Security
Operates entirely in-sandbox with no network access. Reads local Python files and writes symbol indices to the local workspace.