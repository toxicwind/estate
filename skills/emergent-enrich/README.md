# emergent-enrich

Routed emergent enrichment: free sources first, Exa only with explicit opt-in. Triggers on: "emergent enrich", "enrich", "literature search", "paper search", "code search".

&larr; **Back to top** <!-- for-the-badge alignment -->

## Hero

Provides a routed approach to emergent research enrichment — starting with free, no-auth sources (GitHub code search, arXiv, OpenAlex, Semantic Scholar) before any paid/costly calls (Exa). The routing order ensures you get maximum coverage from free sources first, and Exa is only used when explicitly opted in. Prints a JSON result with per-source blocks and a `credits_spent` flag.

## What It Does

- **Free-first routing order**: GitHub code search → arXiv → OpenAlex → Semantic Scholar → Exa (last resort)
- **No-auth paper legs**: arXiv, OpenAlex, and Semantic Scholar all work without authentication; generous free limits
- **Exa with explicit opt-in**: Only when `--exa-ok` is passed, which requires the user's explicit approval for that call
- **JSON output**: Per-source blocks with relevance and a `credits_spent` flag tracking cost
- **Shared arXiv rate limiter**: One budget across both `emergent-enrich` and `arxiv-mcp` skills
- **Dynamic credentials**: Hatch cell surrogate auth is optional; on hosts without /opt/hatch (e.g. awrawr-pc), authenticated legs degrade gracefully and all keyless paper legs keep working

## Features

| Feature | Detail |
|---|---|
| **Free-first strategy** | GitHub code search (free, authenticated via custom.github) — best-match relevance order, never star-sorted |
| **Literature legs** | arXiv (relevance-sorted, throttles aggressively with first-class limiter), OpenAlex (250M+ works incl. arXiv content), Semantic Scholar (200M+ papers; abstracts + citation counts + PDFs) |
| **Exa cost tracking** | Credits spent only on explicit opt-in; `credits_spent` flag in output JSON |
| **Shared rate limiter** | One arXiv budget across both `emergent-enrich` and `arxiv-mcp` skills |
| **No auth needed for paper legs** | All keyless paper legs work without authentication; on hosts without /opt/hatch, graceful degradation |
| **JSON result format** | Per-source blocks with relevance, source identification, and credits_spent flag |

## Quick Start

```bash
# Basic emergent enrichment — free sources first, Exa only with opt-in
bin/route.py "LLM serving benchmarks"

# With explicit Exa opt-in (costs credits)
bin/route.py "LLM serving benchmarks" --exa-ok

# Search with specific focus
bin/route.py "arxiv machine learning papers 2024"

# Check what sources were used and credits spent
# Output is JSON on stdout with per-source blocks and credits_spent flag
```

## Config

- `EXA_OK` environment variable or `--exa-ok` flag: explicitly opt into Exa calls (required; defaults to no Exa)
- GITHUB_HOSTS: `["api.github.com"]` — for GitHub code search authentication via custom.github
- ARXIV_BASE: `https://export.arxiv.org` — arXiv API endpoint
- OPENALEX_BASE: `https://api.openalex.org` — OpenAlex API endpoint
- S2_BASE: `https://api.semanticscholar.org` — Semantic Scholar API endpoint
- USER_AGENT: `shingle-emergent-enrich/1.0` — custom user agent for all API calls
- Dynamic credentials: Hatch cell surrogate auth is optional; degrades gracefully without /opt/hatch

## Output Format

JSON on stdout with per-source blocks:

```json
{
  "github": {..., "relevance": "high", "credits_spent": false},
  "arxiv": {..., "relevance": "medium", "credits_spent": false},
  "openalex": {..., "relevance": "medium", "credits_spent": false},
  "semantic_scholar": {..., "relevance": "high", "credits_spent": false},
  "exa": {..., "relevance": "low", "credits_spent": true}  // only if --exa-ok passed
}
```

Each source block includes relevance scoring and identification. `credits_spent: true` only appears for Exa calls that were explicitly opted in.

## Contributing

Route work through the free-first strategy: GitHub code search → arXiv → OpenAlex → Semantic Scholar → Exa (last resort). The shared arXiv rate limiter budget is shared across both `emergent-enrich` and `arxiv-mcp` skills. Keep paper legs keyless and working without authentication.

## License

Open Claw — see `skill.toml` for details.

## Security

- No credential handling for paper legs (arXiv, OpenAlex, Semantic Scholar all work without auth)
- Exa calls only happen with explicit user opt-in (`--exa-ok`); real credentials never in chat/argv/logs
- GitHub code search authenticated via `custom.github` surrogate; real key never persisted
- On hosts without /opt/hatch, authenticated legs degrade gracefully; keyless legs keep working
- All API calls use a custom user agent (`shingle-emergent-enrich/1.0`)