name: maximal-sovereign-agentic-audit
description: >
  Maximal agentic repo visibility audit tool. Uses Bun.nanoseconds() microsecond-precision timing,
  mitata benchmarks, ast-grep AST-aware code search, exa file-tree search, gh API code search,
  pattern borrowing from global sovereign patterns, multi-tier chained execution pipeline.
  Triggers on: "audit visibility", "check bun versions", "repo privacy", "visibility audit",
  "parquet audit", "find bun versions", "which repos should be private", "repo classification",
  "ast search", "exa search", "gh search", "pattern borrow", "tier audit", "chain audit".
---

# Repo Visibility & Bun Version Audit (Maximal)

## Concept

Fully agentic, production-grade audit tool with:
1. **Multi-tier execution**: High > Medium > Low priority chains
2. **Chained pipeline**: Sequential stages (classify → pattern-borrow → ast-search → exa-search → gh-search)
3. **AST-aware code search**: `ast-grep` for structural code patterns
4. **Pattern borrowing**: Global sovereign pattern ranker (from `sovereign/scripts/pattern-borrow.ts`)
5. **Dual code search**: `exa` (local file tree) + `gh` (GitHub API code)
6. **Bun.nanoseconds()**: Microsecond-precision timing
7. **mitata benchmarks**: Structured performance benchmarks inline
8. **Streaming**: Configurable batch/window pipeline
9. **Agentic completions**: Dynamic prompt generation
10. **Parquet + CSV export**: Apache Arrow tables with zstd compression

## Dynamic argv

```bash
bun run src/index.ts \
  --user toxicwind \
  --output-parquet output/repo-audit.parquet \
  --check-bun \
  --privacy-threshold 0 \
  --export-csv output/repo-audit.csv \
  --tier High \
  --ast-search \
  --exa-search \
  --gh-search \
  --pattern-borrow \
  --chain \
  --timing \
  --agentic \
  --stream \
  --stream-batch-size 50 \
  --stream-window-ms 5000 \
  --bench \
  --help
```

| Flag | Default | Description |
|------|---------|-------------|
| `--user` | `toxicwind` | GitHub user/org to audit |
| `--output-parquet` | `./repo-audit.parquet` | Output parquet path |
| `--export-csv` | `./repo-audit.csv` | Export CSV alongside parquet |
| `--check-bun` | `false` | Scan repos for bun version references |
| `--privacy-threshold` | `0` | Min stars to flag public repos as anomalous |
| `--out-dir` | `./output` | Output directory |
| `--verbose`, `-v` | `false` | Show detailed per-repo output |
| `--stream` | `false` | Enable batch streaming |
| `--stream-batch-size` | `50` | Records per batch |
| `--stream-window-ms` | `5000` | Throughput window in ms |
| `--timing`, `--latency` | `false` | Enable timing and latency tracking |
| `--agentic` | `false` | Agentic mode with dynamic prompts |
| `--completion-prompt` | `false` | Generate agentic completion prompts |
| `--json-output` | `false` | Output structured JSON |
| `--stream-completions` | `false` | Stream completions to stdout |
| `--tier` | `all` | Filter by priority tier (High/Medium/Low) |
| `--ast-search`, `--ast` | `false` | Enable AST-aware code search via ast-grep |
| `--exa-search`, `--exa` | `false` | Enable exa file-tree code search |
| `--gh-search`, `--gh` | `false` | Enable gh API code search |
| `--pattern-borrow`, `--borrow` | `false` | Borrow patterns from global sovereign patterns |
| `--chain` | `false` | Enable chained pipeline execution |
| `--bench` | `false` | Run mitata benchmarks inline |
| `--help`, `-h` | — | Show help |

## Procedure

1. **Fetch**: `gh api users/{user}/repos --per-page 100 --page N --jq ...` (paginated)
2. **Classify**: Rule-based classification with tier assignment:
   - `PUBLIC_ECOSYSTEM` (High): names containing sovereign, tau, mesh, herd, pi, llama, agent, pitchfork, qed
   - `PUBLIC_FORK` (Medium): fork=true derivatives
   - `PUBLIC_OPENSOURCE` (Medium): has stars, language, description
   - `REVIEW_PRIVATE` (Low): non-fork, no ecosystem keywords, low/no stars
   - `PRIVATE_INTERNAL` (High): names containing secret, token, credential, config, private
3. **Pattern Borrow**: Load global sovereign patterns, rank by weight
4. **AST Search**: `ast-grep scan --pattern <rule> --lang typescript --json=stream --no-ignore`
5. **Exa Search**: `eza --tree --long --no-ignore --icons=never --group-directories-first --git --modified --permissions --links --classify --header --sort=modified --reverse --filter=*.ts ...`
6. **GH Code Search**: `gh api search/code --limit 5 --jq [...] -q "query"`
7. **Bun Detection**: Search package.json, bunfig.toml, .tool-versions
8. **Parquet Output**: Write classified Arrow Table to parquet
9. **Anomaly Report**: Public repos classified as should-be-private
10. **Agentic Completions**: Dynamic prompt generation based on anomalies

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

## Search Flow (Chained)

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Classify   │───▶│ Pattern Borrow   │───▶│  AST Search │───▶│   Exa       │───▶│    GH API   │
│  (Tier)     │    │ (Global)         │    │ (ast-grep)  │    │ (eza tree)  │    │ (code search)│
└─────────────┘    └──────────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                    │                    │                    │
       ▼                   ▼                    ▼                    ▼                    ▼
  classification      pattern weights      AST matches         file tree          code matches
  tier assignment     category + weight    code patterns       local files        remote code
```

## Output

Markdown table with columns: `name | visibility | classification | tier | bun_version | stars | ast_matches | exa_files | gh_matches | anomaly`

Anomaly count and recommendations for repos to make private.

## Examples

```bash
# Full maximal audit with all features
bun run src/index.ts --user toxicwind --ast-search --exa-search --gh-search --pattern-borrow --chain --bench --timing --agentic

# High-tier only with AST search
bun run src/index.ts --user toxicwind --tier High --ast-search --pattern-borrow

# Quick audit
bun run src/index.ts --user toxicwind --check-bun --output-parquet audit.parquet

# Benchmark only
bun run src/index.ts --bench

# Help
bun run src/index.ts --help
```

## Build & Test

```bash
bun run check        # lint + build + test
bun run test         # tests with coverage
bun run bench        # mitata benchmarks
bun run lint         # biome check
bun run build        # bun build
bun run audit        # Full audit
bun run audit:agentic # Agentic audit with completions
```
