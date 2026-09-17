# Meta-Research Toolkit

A polyglot research scaffold combining shell tooling analysis, lottery EV computation,
and LLM refusal-geometry meta-analysis. Built with Bun + Python + Perl.

## Submodules
- `vendor/ble.sh` — Bash line editor internals
- `vendor/awesome-selfhosted` — Curated self-hosted software index
- `vendor/nushell` — Rust-based shell reference implementation
- `vendor/brush` — Bash-compatible Rust shell (POSIX test target)

## Quick Start

```bash
# Python env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest --cov=src/python --cov-report=html

# Bun env
bun install
bun test
bun run build
```

## Structure
- `src/python/` — Core analysis modules
- `src/typescript/` — API clients and prompt strategies
- `src/perl/` — Legacy shell linting tools
- `tests/` — Pytest + Bun test suites
- `docs/` — Research notes and citations
