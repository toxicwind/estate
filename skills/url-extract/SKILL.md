---
name: url-extract
description: Universal URL content extractor — handles JS-rendered SPAs (Meta AI, ChatGPT, Claude, Gemini shares) and static pages via cascading Playwright → curl → OG-meta strategies
---

# URL Extract Skill

Universal link content extraction with cascading strategies for JS-heavy share pages.

## Supported Sites (first-class handlers)

- **Meta AI** — `meta.ai/share/a/...` (artifact + conversation shares)
- **ChatGPT** — `chatgpt.com/share/...`
- **Claude** — `claude.ai/share/...`
- **Gemini / AI Studio** — `aistudio.google.com/...`
- **GitHub** — gists, issues, PRs, files
- **HuggingFace** — model cards, spaces
- **Any URL** — generic article/main content extraction

## Extraction Cascade

1. **Playwright** (headless Chromium) — full JS render, waits for site-specific selectors, removes nav/sidebar noise
2. **curl + heuristic parse** — fast HTML strip + JSON-LD extraction for SSR pages
3. **OG meta fallback** — title + description from Open Graph / Twitter Card tags

## Usage

```bash
# Basic extraction (outputs markdown)
bun run ~/sovereign/skills/url-extract/extract.ts https://meta.ai/share/a/46d497f6-...

# JSON output
bun run ~/sovereign/skills/url-extract/extract.ts https://chatgpt.com/share/... --format json

# Save to file
bun run ~/sovereign/skills/url-extract/extract.ts https://claude.ai/share/... --out /tmp/extracted.md

# Custom timeout for slow pages
bun run ~/sovereign/skills/url-extract/extract.ts https://example.com --timeout 60000
```

## Prerequisites

```bash
# Playwright (required for SPA extraction)
bun add -g playwright
bunx playwright install chromium
```

## Output Formats

- `md` (default) — Markdown with title, metadata, content sections
- `json` — Full structured ExtractResult object
- `text` — Plain text with header

## Adding New Site Handlers

Edit `SITE_HANDLERS` array in `extract.ts`. Each handler defines:

- `match(url)` — hostname/path predicate
- `waitSelector` — CSS selector to wait for before extracting
- `contentSelectors` — ordered list of selectors to try
- `removeSelectors` — noise elements to strip
- `settleMs` — extra wait after selector appears
