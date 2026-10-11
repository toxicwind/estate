---
name: fast-browser
description: >
  Scripted browser automation for known flows. browsnap.ts runs a whole known-page, known-selector browser session as one process and returns JSON in 0.3-2s, instead of spending one agentic model round-trip per click. Triggers on: "browsnap", "scripted browser", "browser flow", "headless browser".
---

# fast-browser skill

Scripted browser automation for **known flows**. When you know the page and the
selectors, don't burn an agentic browser task (one model round-trip per click,
~15s/step) — run the whole flow as one scripted shot and get JSON back in
under a second.

## The rule

- **Known page + known selectors → `browsnap.ts`** (this skill). One process,
  one browser launch, JSON out. Typical: 0.3–2s for a 5-step flow.
- **Genuinely unknown page** (you've never seen it, need to explore) →
  agentic browser task. That's what it's for.

## Usage

```bash
# One-shot: extract data from a page
bun ~/sovereign/skills/fast-browser/browsnap.ts --steps '[
  {"goto": "https://github.com/toxicwind/rig"},
  {"text": "[itemprop=about]", "as": "about"},
  {"texts": ".topic-tag", "as": "topics"},
  {"title": true, "as": "title"}
]'

# From a file, with output saved
bun ~/sovereign/skills/fast-browser/browsnap.ts \
  --steps-file flow.json --out /tmp/result.json

# Screenshot a page
bun ~/sovereign/skills/fast-browser/browsnap.ts --steps '[
  {"goto": "https://example.com"},
  {"screenshot": "/tmp/shot.png", "fullPage": true}
]'

# Multi-step: search flow
bun ~/sovereign/skills/fast-browser/browsnap.ts --steps '[
  {"goto": "https://news.ycombinator.com"},
  {"texts": ".titleline > a", "as": "headlines"}
]'
```

## Steps DSL

One action per step object. Full reference in `browsnap.ts` header. The greatest hits:

| Step | Does |
|---|---|
| `{"goto": url}` | Navigate (fast `domcontentloaded` wait) |
| `{"click": sel}` | Click (CSS, `text=`, `>>` chaining all work) |
| `{"fill": sel, "text": v}` | Fill an input |
| `{"type": sel, "text": v}` | Keystroke typing |
| `{"press": "Enter"}` / `{"pressOn": sel, "key": "Enter"}` | Keyboard |
| `{"select": sel, "value": v}` | Dropdown |
| `{"wait": sel}` / `{"wait": 1500}` | Wait for selector / ms |
| `{"text": sel, "as": name}` | innerText → `data.name` |
| `{"texts": sel, "as": name}` | all innerTexts → `data.name` |
| `{"attr": sel, "name": href, "as": n}` | attribute → `data.n` |
| `{"eval": "() => ...", "as": n}` | arbitrary page JS → `data.n` |
| `{"screenshot": path}` | PNG screenshot |
| `{"upload": sel, "file": path}` | file input upload |

Every step is timed; output JSON carries per-step `ms` plus total `ms`.

## Options

- `--timeout 30000` — per-step ceiling (ms)
- `--exe /path/to/chromium` — override browser binary (`BROWSNAP_EXE` env also works)
- `--viewport 1920x1080`, `--headed` — headed mode (default headless)
- `--out result.json` — also write JSON to file

## Requirements

Runs on **yote** (the bridge box): `bun` + `playwright-core` (falls back to the
global `/usr/lib/node_modules/playwright-core`) + system chromium
(`/usr/bin/chromium`). `bun install` in the skill dir for a hermetic local
copy of playwright-core.

## Why this exists

Measured 2026-09-30 on yote: scripted cold-launch + goto + extract = **0.45s**;
agentic browser tasks run ~**15s per step** (one inference round-trip per
action). A 5-step known flow: ~1s scripted vs ~75s+ agentic. The estate's
browserless :25130 pool was also found degraded (bundled chromium-1223 hangs
on launch) — browsnap launches the working system chromium directly, so it
doesn't depend on that pool.
