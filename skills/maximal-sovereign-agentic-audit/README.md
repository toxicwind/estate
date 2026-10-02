![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/maximal-sovereign-agentic-audit?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/maximal-sovereign-agentic-audit?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/maximal-sovereign-agentic-audit?style=for-the-badge)

# maximal-sovereign-agentic-audit
Maximal agentic repo visibility audit tool

## What it does
Fully agentic, production-grade audit tool that combines multi-tier execution, chained pipelines, AST-aware code search, pattern borrowing, dual code search (exa + gh), Bun.nanoseconds() timing, mitata benchmarks, streaming, agentic completions, and Parquet+CSV export for comprehensive repository visibility analysis.

## Why it matters
Provides deep, automated insight into repository ecosystems with intelligent prioritization, pattern-based anomaly detection, and performance-characterized code search to identify visibility issues, misclassified repositories, and bun version drift across large GitHub organizations.

## Who it's for
Platform engineers, DevOps leads, and security analysts who need to audit large numbers of repositories for visibility, proper classification, security risks, and technology stack consistency across an organization's GitHub footprint.

## Features
- **Multi-Tier Execution** - High > Medium > Low priority chains for intelligent processing order
- **Chained Pipeline** - Sequential stages: classify → pattern-borrow → ast-search → exa-search → gh-search
- **AST-Aware Search** - `ast-grep` for structural code patterns (TypeScript/JavaScript/etc.)
- **Pattern Borrowing** - Global sovereign pattern ranker with weighted terms (secret=10, sovereign=9, etc.)
- **Dual Code Search** - `exa` (local file tree) + `gh` (GitHub API code search)
- **Precision Timing** - `Bun.nanoseconds()` for microsecond-precision performance measurement
- **Inline Benchmarks** - `mitata` benchmarks for structured performance testing
- **Streaming Support** - Configurable batch/window pipeline for large result sets
- **Agentic Completions** - Dynamic prompt generation based on audit anomalies
- **Multiple Export Formats** - Parquet (zstd compressed) + CSV output via Apache Arrow
- **Anomaly Reporting** - Identifies public repos that should be private based on naming patterns

## Quick Start
```bash
# Full maximal audit with all features
bun run src/index.ts \
  --user toxicwind \
  --ast-search \
  --exa-search \
  --gh-search \
  --pattern-borrow \
  --chain \
  --bench \
  --timing \
  --agentic

# High-tier only with AST search
bun run src/index.ts \
  --user toxicwind \
  --tier High \
  --ast-search \
  --pattern-borrow

# Quick audit (just bun version check)
bun run src/index.ts \
  --user toxicwind \
  --check-bun \
  --output-parquet audit.parquet

# Benchmark only
bun run src/index.ts --bench

# Show help
bun run src/index.ts --help
```

## Configuration
- **Dependencies**: Bun runtime (for `bun run` execution)
- **Source Location**: `src/index.ts` (TypeScript entry point)

- **Key Parameters**:
  - `--user`: GitHub user/org to audit (default: `toxicwind`)
  - `--output-parquet`: Output parquet path (default: `./repo-audit.parquet`)
  - `--export-csv`: Export CSV alongside parquet (default: `./repo-audit.csv`)
  - `--check-bun`: Scan repos for bun version references (default: `false`)
  - `--privacy-threshold`: Min stars to flag public repos as anomalous (default: `0`)
  - `--out-dir`: Output directory (default: `./output`)
  - `--verbose`, `-v`: Show detailed per-repo output (default: `false`)
  - `--stream`: Enable batch streaming (default: `false`)
  - `--stream-batch-size`: Records per batch (default: `50`)
  - `--stream-window-ms`: Throughput window in ms (default: `5000`)
  - `--timing`, `--latency`: Enable timing and latency tracking (default: `false`)
  - `--agentic`: Agentic mode with dynamic prompts (default: `false`)
  - `--completion-prompt`: Generate agentic completion prompts (default: `false`)
  - `--json-output`: Output structured JSON (default: `false`)
  - `--stream-completions`: Stream completions to stdout (default: `false`)
  - `--tier`: Filter by priority tier (High/Medium/Low, default: `all`)
  - `--ast-search`, `--ast`: Enable AST-aware code search via ast-grep (default: `false`)
  - `--exa-search`, `--exa`: Enable exa file-tree code search (default: `false`)
  - `--gh-search`, `--gh`: Enable gh API code search (default: `false`)
  - `--pattern-borrow`, `--borrow`: Borrow patterns from global sovereign patterns (default: `false`)
  - `--chain`: Enable chained pipeline execution (default: `false`)
  - `--bench`: Run mitata benchmarks inline (default: `false`)
  - `--help`, `-h`: Show help

## Development
Modify the TypeScript source in `src/` directory:
- `index.ts` - Main entry point with argument parsing and pipeline orchestration
- Supporting modules for classification, pattern borrowing, ast-search, exa-search, gh-search, bun detection, parquet output, anomaly reporting, and agentic completions

## License
Internal tool - refer to sovereign estate licensing

## Security
- **Read-Only Analysis** - Performs audit operations without modifying target repositories
- **Pattern-Based Privacy** - Uses naming/description/topic analysis, not content scanning
- **Optional Cross-Reference** - `--load-env-map` safely maps repos to local paths via projects.env
- **Rate Limit Aware** - Uses GitHub API with pagination and configurable limits
- **Local Processing** - Heavy lifting (AST search, exa search, benchmarks) performed locally