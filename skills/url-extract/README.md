# url-extract

Universal URL content extractor. Handles JS-rendered SPAs via cascading Playwright, curl, and OG-meta strategies. Triggers on: "url extract", "web scraping", "JS-rendered", "OG-meta".

&larr; **Back to top** <!-- for-the-badge alignment -->

## Hero

Extracts main content from any URL using a cascading strategy: Playwright (headless Chromium) for JS-rendered SPAs, curl + heuristic parse for SSR pages, and OG meta fallback for title + description. The first-class handler supports Meta AI, ChatGPT, Claude, Gemini, GitHub, and HuggingFace.

## What It Does

- **Extraction cascade**: Three strategies in order: (1) Playwright full JS render, (2) curl + heuristic parse, (3) OG meta fallback
- **First-class site handlers**: Meta AI (`meta.ai/share/a/...`), ChatGPT (`chatgpt.com/share/...`), Claude (`claude.ai/share/...`), Gemini/AI Studio (`aistudio.google.com/...`), GitHub (gists, issues, PRs, files), HuggingFace (model cards, spaces)
- **Output formats**: `md` (default, markdown with title, metadata, content sections), `json` (full structured ExtractResult), `text` (plain text with header)
- **Site-specific selectors**: Each handler defines `match(url)`, `waitSelector`, `contentSelectors`, `removeSelectors`, `settleMs`

## Features

| Feature | Detail |
|---|---|
| **Cascade priority** | 1. Playwright (headless Chromium) — full JS render, waits for site-specific selectors, removes nav/sidebar noise<br>2. curl + heuristic parse — fast HTML strip + JSON-LD extraction for SSR pages<br>3. OG meta fallback — title + description from Open Graph / Twitter Card tags |
| **Site handlers** | Meta AI, ChatGPT, Claude, Gemini/AI Studio, GitHub, HuggingFace — plus "Any URL" generic extraction |
| **Output formats** | `md` (default, markdown), `json` (structured), `text` (plain text) |
| **Playwright requirement** | Required for SPA extraction; install via `bun add -g playwright` + `bunx playwright install chromium` |
| **Custom timeouts** | `--timeout N` for slow pages (ms) |
| **File output** | `--out PATH` saves result to a file |

## Quick Start

```bash
# Basic extraction (outputs markdown)
bun run ~/sovereign/skills/url-extract/extract.ts https://meta.ai/share/a/46d497f6-...

# JSON output
bun run ~/sovereign/skills/url-extract/extract.ts https://chatgpt.com/share/... --format json

# Save to file
bun run ~/sovereign/skills/url-extract/extract.ts https://claude.ai/share/... --out ${TMPDIR:-$HOME/.cache}/extracted.md

# Custom timeout for slow pages
bun run ~/sovereign/skills/url-extract/extract.ts https://example.com --timeout 60000

# Add new site handler
# Edit SITE_HANDLERS array in extract.ts — each handler defines match(), waitSelector, contentSelectors, removeSelectors, settleMs
```

## Config

- **Playwright**: `bun add -g playwright` + `bunx playwright install chromium` (required for SPA extraction)
- **Timeout**: `--timeout N` milliseconds (default: no ceiling)
- **Output format**: `--format json|md|text` (default: md)
- **File output**: `--out PATH` to save result to custom location

## Adding New Site Handlers

Edit `SITE_HANDLERS` array in `extract.ts`. Each handler defines:

- `match(url)` — hostname/path predicate
- `waitSelector` — CSS selector to wait for before extracting
- `contentSelectors` — ordered list of selectors to try
- `removeSelectors` — noise elements to strip
- `settleMs` — extra wait after selector appears

## License

Open Claw — see `skill.toml` for details.

## Security

- No credential handling; all extraction is URL-driven
- Playwright extracts only the main content; no private data is persisted beyond the extraction session
- Custom site handlers should respect robots.txt and terms of service