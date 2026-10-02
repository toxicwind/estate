# arxiv-mcp

arXiv integration skill for the fleet — handles arXiv paper search and retrieval with rate limiting and shared budgets. Works in conjunction with the `emergent-enrich` skill; shares one arXiv rate limiter budget across both skills. Triggers on: "arxiv", "paper search", "arxiv search".

&larr; **Back to top** <!-- for-the-badge alignment -->

## Hero

Provides arXiv paper search and retrieval capabilities with aggressive rate limiting and a shared budget across the `emergent-enrich` skill. All keyless paper legs work without authentication; on hosts without /opt/hatch, authenticated legs degrade gracefully and all keyless paper legs keep working.

## What It Does

- **arXiv paper search**: Via the arXiv API with relevance-sorted results
- **Aggressive rate limiting**: Throttles requests to prevent API abuse; first-class limiter with 429 backoff and JSONL timing audit
- **Shared budget**: One arXiv rate limiter budget shared across both `emergent-enrich` and `arxiv-mcp` skills
- **No authentication needed**: All keyless legs work without API keys; on hosts without /opt/hatch, graceful degradation
- **JSONL timing audit**: Logs request timing and outcomes for audit and optimization

## Features

| Feature | Detail |
|---|---|
| **Rate limiting** | Aggressive throttling with 429 backoff; JSONL timing audit across all calls |
| **Shared budget** | One arXiv budget shared across `emergent-enrich` and `arxiv-mcp` |
| **No auth required** | Keyless paper legs work without API keys; graceful degradation without /opt/hatch |
| **Rate limiter state** | Persisted via JSONL audit file; one budget across skills |
| **arXiv API** | Standard arXiv API with relevance-sorted results |

## Quick Start

```bash
# Search arXiv papers
# (calls are routed through emergent-enrich which shares the rate limiter)
bin/route.py "machine learning papers 2024"

# The shared rate limiter ensures across both skills:
# - No API abuse via aggressive throttling
# - JSONL timing audit at ~/workspace/skills/arxiv-mcp/bin/ for analysis
# - Graceful degradation if rate limits are hit
```

## Config

- arXiv API endpoint: `https://export.arxiv.org`
- Shared rate limiter budget: one budget across `emergent-enrich` and `arxiv-mcp`
- JSONL audit file: tracks timing and outcomes for optimization
- Dynamic credentials: optional Hatch cell surrogate auth; degrades gracefully

## Contributing

Shared arXiv rate limiter budget is a first-class constraint — keep paper legs keyless and working without authentication. The JSONL timing audit at the shared path supports optimization across both `emergent-enrich` and `arxiv-mcp` skills. If arXiv is throttling, OpenAlex/Semantic Scholar legs carry the literature load.

## License

Open Claw — see `skill.toml` for details.

## Security

- Keyless paper legs work without API keys; all arXiv calls are anonymous
- On hosts without /opt/hatch, authenticated legs degrade gracefully; keyless legs keep working
- JSONL timing audit supports optimization and abuse detection
- Rate limiting is aggressive by design — 429 backoff prevents API exhaustion