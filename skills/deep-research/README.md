![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/deep-research?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/deep-research?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/deep-research?style=for-the-badge)

# deep-research
Deep research combining Google Drive full-text search with Perplexity AI deep search

## What it does
Combines two powerful search surfaces: 1) Google Drive (full-text search inside Docs, PDFs, Sheets via native Drive index), and 2) Perplexity (high-effort AI search with reasoning via API or browser) to provide comprehensive research that spans both private documents and public knowledge sources.

## Why it matters
Enables thorough research that leverages both internal organizational knowledge (in Google Drive) and current public information (via Perplexity), eliminating the blind spots of searching only one source.

## Who it's for
Researchers, analysts, engineers, and anyone who needs to conduct deep investigations that require both confidential/internal information and up-to-date public knowledge, particularly for technical research, competitive analysis, or trend forecasting.

## Features
- **Google Drive Search**:
  - Uses Drive's native `fullText contains` — searches inside Google Docs, PDFs, etc. without downloading
  - `bin/gdrive-search.py` — fast Drive search, no rsync needed
  - Filename search: `gdrive-search.py "query"`
  - Full-text inside docs: `gdrive-search.py "query" --content`
  - Type-limited search: `gdrive-search.py "query" --content --type=doc --limit 20` (doc|sheet|slide|pdf)
- **Perplexity Deep Search**:
  - High-effort search with reasoning via two paths:
    - **API** (preferred, needs PERPLEXITY_API_KEY):
      ```
      curl https://api.perplexity.ai/chat/completions \
        -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
          "model": "sonar-deep-research",
          "messages": [{"role": "user", "content": "QUERY"}]
        }'
      ```
      Models: `sonar-deep-research` (highest effort), `sonar-reasoning-pro` (high), `sonar-pro` (standard)
    - **Browser fallback**: If no API key: use `browser.spawn_task` with perplexity.ai, ask in deep-research mode
- **Combined Workflow**:
  1. Search Drive first (your private context): `gdrive-search.py "topic" --content`
  2. Search Perplexity (public knowledge): high-effort query
  3. Synthesize: private docs + public research = complete picture
  4. Cite sources: Drive webViewLinks + Perplexity citations
- **Use Cases**:
  - "Find the research on X" — checks your Drive AND the web
  - Paper-finder style deep dives
  - Anything where your private docs + public sources both matter
  - Chris's "high perplexity search" = sonar-deep-research model

## Quick Start
```bash
# Search Google Drive for filename
bin/gdrive-search.py "research topic"

# Search Google Drive full-text inside documents
bin/gdrive-search.py "research topic" --content

# Search Google Drive with type and limit filters
bin/gdrive-search.py "research topic" --content --type=doc --limit 20

# Search Perplexity via API (requires PERPLEXITY_API_KEY)
curl https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-deep-research",
    "messages": [{"role": "user", "content": "your research question"}]
  }'

# Search Perplexity via browser fallback (if no API key)
# Use browser.spawn_task with perplexity.ai in deep-research mode
```

## Configuration
- **Google Drive Search**:
  - Script: `bin/gdrive-search.py`
  - No rsync needed; uses Drive's native full-text search
  - Supports doc|sheet|slide|pdf types with --type filter
  - --content flag enables full-text search inside documents
- **Perplexity Search**:
  - API method: Requires `PERPLEXITY_API_KEY` environment variable
  - Preferred model: `sonar-deep-research` for highest-effort reasoning
  - Fallback: Browser-based search via `browser.spawn_task` when API unavailable
- **Synthesis**:
  - Manual step: Combine private Drive results with public Perplexity findings
  - Citation: Use Drive webViewLinks + Perplexity citations for attribution

## Development
Modify the Google Drive search script at `/home/toxic/estate/skills/deep-research/bin/gdrive-search.py` to adjust:
- Search parameters and filters
- Output formatting and citation generation
- Error handling and rate limiting
- Integration with Drive's API for different file types

## License
Internal tool - refer to sovereign estate licensing

## Security
- **Google Drive** - Uses native Drive index; no document downloading required for search
- **Perplexity API** - Requires proper API key handling; never exposes key in logs or output
- **Browser Fallback** - Relies on existing browser automation safeguards
- **Private/Public Separation** - Explicitly searches Drive first (private context) then Perplexity (public)
- **Citation Integrity** - Preserves source links for attribution and verification