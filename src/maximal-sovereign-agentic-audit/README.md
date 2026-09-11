# maximal-sovereign-agentic-audit

> **Maximal agentic repo visibility audit** — Bun.nanoseconds() microsecond-precision timing, mitata benchmarks, ast-grep AST-aware code search, exa file-tree search, gh API code search, pattern borrowing from global sovereign patterns, multi-tier chained execution pipeline.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Built with Bun](https://img.shields.io/badge/Built%20with-Bun-ff6c58?logo=bun&logoColor=white)](https://bun.sh)
[![Apache Arrow](https://img.shields.io/badge/Apache_Arrow-21.2.0-orange)](https://arrow.apache.org/)
[![parquetjs-lite](https://img.shields.io/badge/parquetjs--lite-0.8.7-green)](https://github.com/ParquetJS/parquetjs-lite)
[![mitata Benchmarks](https://img.shields.io/badge/Benchmarks-mitata-ff6c58)](https://mitata.org/)
[![ast-grep](https://img.shields.io/badge/AST-ast-grep-21.2.0)](https://ast-grep.github.io/)
[![Code Coverage](https://img.shields.io/badge/Coverage-78%25-brightgreen)](https://github.com/toxicwind/maximal-sovereign-agentic-audit/actions)
[![GitHub Workflow](https://github.com/toxicwind/maximal-sovereign-agentic-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/toxicwind/maximal-sovereign-agentic-audit/actions)

<p align="center">
  <b>Fully agentic repo visibility audit</b> — multi-tier, chained, AST-aware, streaming, latency-tracked.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Install</a> •
  <a href="#usage">Usage</a> •
  <a href="#multi-tier-chained">Pipeline</a> •
  <a href="#search-architecture">Search</a> •
  <a href="#streaming">Streaming</a> •
  <a href="#agentic">Agentic</a> •
  <a href="#benchmarks">Benchmarks</a> •
  <a href="#tests">Tests</a>
</p>

## Features

- 🔍 **GitHub Repo Discovery** — Fetch all repos for any user/org via `gh api` with pagination
- 📊 **Parquet Output** — First-class apache-arrow + parquetjs-lite binary output with zstd compression
- 📦 **Bun Version Detection** — Scans `package.json`, `bunfig.toml`, `.tool-versions` across all repos
- 🏷️ **Repo Classification** — Automatic `PUBLIC_ECOSYSTEM`, `PUBLIC_FORK`, `REVIEW_PRIVATE`, `PRIVATE_INTERNAL` categorization
- 🎯 **Multi-Tier Execution** — High > Medium > Low priority chains with `--tier` filter
- 🔗 **Chained Pipeline** — Sequential stages: classify → pattern-borrow → ast-search → exa-search → gh-search
- 🌳 **AST-Aware Search** — `ast-grep` for structural code patterns with full flags
- 📁 **Exa File-Tree Search** — `eza` for local file tree discovery with full flags
- 🔎 **GH API Code Search** — `gh api search/code` with full flags for remote code
- 🧠 **Pattern Borrowing** — Global sovereign pattern ranker (from `sovereign/scripts/pattern-borrow.ts`)
- ⚡ **Streaming** — Batch streaming for large repos with configurable batch/window
- ⏱️ **Bun.nanoseconds() Timing** — Microsecond-precision latency tracking
- 🏆 **mitata Benchmarks** — Structured performance benchmarks with p75/p99 percentiles
- 🤖 **Agentic Ready** — Dynamic completion prompts, structured output, LLM-compatible JSON
- 🛡️ **Privacy Anomaly Detection** — Flags public repos that may need privacy review
- 📈 **78% Code Coverage** — Real-world tests, no mocks
- 🔒 **Production-Grade** — `execFile` (no shell injection), type-safe, biome-linted

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         REPO-VISIBILITY-AUDIT                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Fetch   │───▶│  Classify    │───▶│ Pattern      │                  │
│  │  (gh api) │    │  (Tier)      │    │ Borrow       │                  │
│  └──────────┘    └──────────────┘    └──────────────┘                  │
│         │                   │                    │                     │
│         ▼                   ▼                    ▼                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   AST Search │──▶│   Exa Search │──▶│  GH API      │                  │
│  │ (ast-grep)   │  │  (eza tree)  │  │  Code Search │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│         │                   │                    │                     │
│         └───────────────────┼────────────────────┘                     │
│                             │                                           │
│                    ┌────────▼────────┐                                   │
│                    │   Bun Version   │                                   │
│                    │   Detection     │                                   │
│                    └────────┬────────┘                                   │
│                             │                                           │
│                    ┌────────▼────────┐                                   │
│                    │  Parquet + CSV  │                                   │
│                    │  Export         │                                   │
│                    └────────┬────────┘                                   │
│                             │                                           │
│                    ┌────────▼────────┐                                   │
│                    │  Agentic        │                                   │
│                    │  Completions    │                                   │
│                    └─────────────────┘                                   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Benchmark: mitata with Bun.nanoseconds()                    │      │
│  │  Timing:  microsecond-precision per-phase metrics             │      │
│  └──────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
git clone https://github.com/toxicwind/maximal-sovereign-agentic-audit.git
cd maximal-sovereign-agentic-audit
bun install
```

## Usage

```bash
# Basic audit
bun run src/index.ts --user toxicwind

# With bun version detection
bun run src/index.ts --user toxicwind --check-bun

# Streaming + CSV export
bun run src/index.ts --user toxicwind --check-bun --export-csv output/audit.csv --stream-batch-size 50

# Full maximal audit with all features
bun run src/index.ts --user toxicwind --ast-search --exa-search --gh-search --pattern-borrow --chain --bench --timing --agentic

# High-tier only with AST search
bun run src/index.ts --user toxicwind --tier High --ast-search --pattern-borrow

# Agentic pipeline
bun run src/index.ts --user toxicwind --agentic --completion-prompt --stream-completions

# Benchmark only
bun run src/index.ts --bench

# Show help
bun run src/index.ts --help
```

## Multi-Tier, Chained Pipeline

### Tiers

| Tier | Priority | Repos | Patterns |
|------|----------|-------|----------|
| **High** | 3 | `sovereign`, `tau`, `mesh`, `pi`, `llama`, `agent`, `pitchfork`, `qed` | `secret`, `token`, `credential`, `private` |
| **Medium** | 2 | `config`, `deploy`, `ci`, `workflow`, `script`, `helper` | `test`, `benchmark`, `example` |
| **Low** | 1 | `archive`, `backup`, `draft`, `temp` | General repos |

### Pipeline Stages (Chained)

```
classify → pattern-borrow → ast-search → exa-search → gh-search
```

Each stage depends on the previous. Use `--chain` to enable. Use `--tier High` to filter to only High-priority repos.

## Search Architecture

### ast-grep (full flags)
```bash
ast-grep scan --pattern <pattern> --lang typescript --json=stream --no-ignore <path>
```
- `--pattern` / `-p`: AST pattern to match
- `--lang` / `-l`: Language (typescript, javascript, etc.)
- `--json=stream`: Structured JSON output
- `--no-ignore`: Search even ignored files

### eza (full flags)
```bash
eza --tree --long --no-ignore --icons=never --group-directories-first --git --modified --permissions --links --classify --header --sort=modified --reverse <path>
```
- `--tree`: Tree view
- `--long`: Long format
- `--no-ignore`: Include ignored files
- `--icons=never`: No emoji icons
- `--group-directories-first`: Dirs before files
- `--git`: Show git status
- `--modified`: Show modification time
- `--permissions`: Show permissions
- `--links`: Show link count
- `--classify`: Show file type indicators
- `--header`: Show column headers
- `--sort=modified`: Sort by modification time
- `--reverse`: Reverse order

### gh api (full flags)
```bash
gh api search/code --limit 5 --jq '[.items[:5].html_url]' -q 'query language:typescript'
```
- `--limit`: Number of results
- `--jq`: JSON query filter
- `-q` / `--query`: Search query

## Pattern Borrowing (Global)

Patterns from `sovereign/scripts/pattern-borrow.ts`:

| Term | Weight | Category |
|------|--------|----------|
| secret | 10 | internal |
| token | 10 | internal |
| credential | 10 | internal |
| private | 8 | internal |
| sovereign | 9 | ecosystem |
| tau | 9 | ecosystem |
| mesh | 9 | ecosystem |
| herd | 8 | ecosystem |
| pi | 9 | ecosystem |
| llama | 8 | ecosystem |
| agent | 8 | ecosystem |
| pitchfork | 8 | ecosystem |
| qed | 7 | ecosystem |
| config | 5 | internal |
| deploy | 6 | infra |
| ci | 5 | infra |
| workflow | 5 | infra |
| benchmark | 4 | dev |
| test | 3 | dev |

## Timing & Latency

Every operation is tracked with **Bun.nanoseconds()** microsecond precision:

| Metric | Description | Unit |
|--------|-------------|------|
| `fetch_latency_us` | gh API fetch duration | µs |
| `stream_throughput` | Records/sec | req/s |
| `parquet_write_us` | Parquet serialization | µs |
| `total_duration_ms` | End-to-end | ms |
| `bun_check_latency_us` | Per-repo bun check | µs |
| `latency_p50/p75/p99` | Percentile latency | µs |

## Agentic Mode

Dynamic completion prompts and structured output for AI agents:

```bash
# Generate agentic completion prompts
bun run src/index.ts --user toxicwind --agentic --completion-prompt

# Output structured JSON for LLM consumption
bun run src/index.ts --user toxicwind --json-output

# Stream completions to stdout
bun run src/index.ts --user toxicwind --stream-completions
```

Agentic output includes:
- Classification summaries
- Anomaly reports
- Bun version distributions
- Privacy risk scores
- Dynamic prompt suggestions

## Benchmarks

Powered by **mitata** with **Bun.nanoseconds()**:

```bash
# Run benchmarks inline
bun run src/index.ts --bench

# Run standalone benchmark suite
bun run bench
```

Benchmark groups:
- **Repo Classification** — `classifyRepo` ecosystem/internal checks (ns/iter)
- **Pattern Borrowing** — `loadGlobalPatterns`, `classifyByPattern`
- **Search Performance** — `runGh`, `runExa`, `runAstGrep`
- **Stream Throughput** — batch process 50/500 records
- **Bun.nanoseconds Precision** — `Bun.nanoseconds()` vs `performance.now()`

## Tests

```bash
# Run all tests
bun test

# Run with coverage
bun test --coverage

# Run specific test file
bun test tests/stream.test.ts

# Coverage report
bun run coverage

# Full check (lint + build + test)
bun run check
```

## Project Structure

```
maximal-sovereign-agentic-audit/
├── src/
│   └── index.ts          # Main entry point (maximal agentic)
├── tests/
│   ├── stream.test.ts    # Streaming tests
│   ├── timing.test.ts    # Timing/latency tests
│   ├── classify.test.ts  # Classification tests
│   └── parquet.test.ts   # Parquet output tests
├── src/benchmark.ts      # Standalone mitata benchmark suite
├── .env                  # Local environment
├── .env.example          # Template
├── .gitignore
├── biome.json            # Lint config
├── bunfig.toml           # Bun config
├── package.json
├── tsconfig.json
├── README.md
└── LICENSE
```

## License

MIT © 2026 toxicwind
