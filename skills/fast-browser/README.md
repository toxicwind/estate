# fast-browser

One-shot scripted browser automation — deterministic multi-step browser flows (goto, click, fill, extract, screenshot, upload) executed in a single Bun process with zero per-step inference, ~100x faster than agentic click-by-click browsing. Triggers on: "fast browser", "scripted browser", "browsnap", "browser automation", "one-shot browser", "browser flow", "scrape this page".

&larr; **Back to top** <!-- for-the-badge alignment -->

## Hero

Runs known browser flows as scripted one-shots via `browsnap.ts` — a single browser launch, JSON output in under a second. When you know the page and the selectors, don't burn an agentic browser task (one model round-trip per click, ~15s/step); instead, run the whole flow as one scripted shot and get JSON back in under a second.

## What It Does

- **One-shot flows**: Execute deterministic multi-step browser flows as a single Bun process
- **Steps DSL**: goto, click, fill, type, press, select, check, wait, text, texts, attr, eval, title, url, screenshot, upload, reload, back
- **Per-step timing**: Each step timed; output JSON carries per-step `ms` plus total `ms`
- **Known page + known selectors → browsnap.ts**: One process, one browser launch, JSON out
- **Typical performance**: 0.3–2s for a 5-step flow vs ~75s+ for agentic browsing (15s per step)

## Features

| Feature | Detail |
|---|---|
| **Single launch** | One browser launch for the entire flow; no per-step model round-trips |
| **Steps DSL** | Full reference in `browsnap.ts` header: goto, click, fill, type, press, select, check, wait, text, texts, attr, eval, title, url, screenshot, upload, reload, back |
| **Timing** | Every step timed; output JSON has per-step `ms` plus total `ms` |
| **Options** | `--timeout 30000` (per-step ceiling), `--exe /path/to/chromium` (override binary), `--viewport 1920x1080`, `--headed` (headed mode, default headless), `--out result.json` |
| **Requirements** | Runs on yote: `bun` + `playwright-core` + system chromium (`/usr/bin/chromium`); `bun install` in skill dir for hermetic playwright-core |
| **Performance** | Measured 2026-09-30 on yote: cold-launch + goto + extract = **0.45s**; agentic tasks ~**15s per step** |

## Quick Start

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

## Options

| Option | Detail |
|---|---|
| `--timeout N` | Per-step ceiling in ms (default: no ceiling) |
| `--exe PATH` | Override browser binary; also works via `BROWSNAP_EXE` env |
| `--viewport WxH` | Viewport size (default: 1920x1080) |
| `--headed` | Headed mode (default: headless) |
| `--out PATH` | Also write JSON to file |
| `--steps '[]'` | JSON array of step objects (required) |
| `--steps-file PATH` | Read steps from a JSON file |

## Steps DSL Reference

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

## Config

- **Runtime**: yote only; `bun` + `playwright-core` + system chromium
- **Hermetic**: `bun install` in skill dir for local copy of playwright-core
- **Browser binary**: system chromium at `/usr/bin/chromium`; override with `--exe` or `BROWSNAP_EXE` env
- **Viewport**: 1920x1080 default; adjustable with `--viewport`
- **Mode**: headless default; `--headed` for visible browser

## Why This Exists

Measured 2026-09-30 on yote: scripted cold-launch + goto + extract = **0.45s**; agentic browser tasks run ~**15s per step** (one inference round-trip per action). A 5-step known flow: ~1s scripted vs ~75s+ agentic. The estate's browserless :25130 pool was also found degraded (bundled chromium-1223 hangs on launch) — browsnap launches the working system chromium directly, so it doesn't depend on that pool.

## License

Open Claw — see `skill.toml` for details.

## Security

- Runs on yote only; do not run on cell or other boxes
- No persistent state; each run is a fresh browser launch
- Upload step handles file inputs only; do not use for arbitrary file transfers
- Screenshot captures page rendering; be mindful of sensitive content on screen