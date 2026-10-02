# Deep Research

Combines two powerful search surfaces:
1. **Google Drive** — full-text search inside your Docs, PDFs, Sheets (native Drive index, no download)
2. **Perplexity** — high-effort AI search with reasoning (via API or browser)

## Google Drive Search

```bash
# bin/gdrive-search.py — fast Drive search, no rsync needed
bin/gdrive-search.py "query"                    # filename search
bin/gdrive-search.py "query" --content         # full-text inside docs
bin/gdrive-search.py "query" --content --type=doc --limit 20
# --type: doc|sheet|slide|pdf
```

Uses Drive's native `fullText contains` — searches inside Google Docs, PDFs, etc. without downloading.

## Perplexity Deep Search

High-effort search with reasoning. Two paths:

### API (preferred, needs PERPLEXITY_API_KEY)
```bash
curl https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-deep-research",
    "messages": [{"role": "user", "content": "QUERY"}]
  }'
```
Models: `sonar-deep-research` (highest effort), `sonar-reasoning-pro` (high), `sonar-pro` (standard).

### Browser fallback
If no API key: use `browser.spawn_task` with perplexity.ai, ask in deep-research mode.

## Combined Workflow

1. Search Drive first (your private context): `gdrive-search.py "topic" --content`
2. Search Perplexity (public knowledge): high-effort query
3. Synthesize: private docs + public research = complete picture
4. Cite sources: Drive webViewLinks + Perplexity citations

## When to Use

- "Find the research on X" — checks your Drive AND the web
- Paper-finder style deep dives
- Anything where your private docs + public sources both matter
- Chris's "high perplexity search" = sonar-deep-research model