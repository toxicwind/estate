---
name: slidev
description: >-
  Create effective technical presentations with Slidev, focused on data science,
  statistics, and developer talks. Opinionated toward the neversink theme with
  the-unnamed as an alternative. Use when the user wants to build, edit, review,
  or export slide decks. Covers Slidev syntax, neversink/the-unnamed theme
  features, visual design principles, storytelling structure, and export
  workflows.
---

# Slidev: Effective Technical Presentations

Opinionated guidance for building slide decks with Slidev. Load the references
below as needed; do not try to fit all content into the initial response.

## When to Use

- Building a new technical presentation, workshop, or conference talk
- Editing or restructuring an existing deck
- Converting a Jupyter notebook, blog post, or paper into slides
- Reviewing a deck for visual clarity and narrative flow
- Setting up export (PDF, SPA) or CI deployment
- Adding code examples, math, diagrams, or data visualizations to slides

## References

Load a reference when the task matches. Do not load multiple overlapping
references for the same task.

| When you need to... | Load this file |
|---------------------|----------------|
| Scaffold a new project | [scripts/scaffold.sh](scripts/scaffold.sh), then [references/workflows.md](references/workflows.md) for dev server setup |
| Lint an existing `slides.md` | [scripts/review.py](scripts/review.py) |
| See how the author's decks actually look (443-slide dataset) | [references/visual-preferences.md](references/visual-preferences.md) |
| Pick a theme (neversink vs. the-unnamed) | [references/themes.md](references/themes.md) |
| Look up a neversink layout, slot syntax, or color scheme | [references/neversink-theme.md](references/neversink-theme.md) |
| Customize the-unnamed colors | [references/the-unnamed.md](references/the-unnamed.md) |
| Add a slide (layout selection, color rules, notes format) | [references/workflows.md](references/workflows.md) |
| Copy a common pattern (title, quote, math, code, image grid) | [references/quick-patterns.md](references/quick-patterns.md) |
| Check what not to do | [references/anti-patterns.md](references/anti-patterns.md) |
| Understand non-negotiable design rules, contrast, image quality, or logo placement | [references/visual-design.md](references/visual-design.md) |
| Structure a talk arc (hook, pacing, closing) | [references/storytelling.md](references/storytelling.md) |
| Add code with highlighting or click reveals | [references/code-slides.md](references/code-slides.md) |
| Add math, Mermaid diagrams, or figure layouts | [references/math-diagrams.md](references/math-diagrams.md) |
| Export PDF/SPA or set up CI deployment | [references/exporting.md](references/exporting.md) |
| Use a built-in component (Link, Toc, VClick, etc.) | [references/components.md](references/components.md) |


## Editing an existing deck

- Before changing visual design in an established deck, inspect the surrounding slides and any reference decks the user names. Reuse a pattern already present unless the user explicitly asks for a new visual direction.
- Preserve the deck's flow. A request to improve one slide is not permission to add new concepts, equations, layouts, color schemes, components, or visual metaphors. Fix the stated problem at the smallest scope that solves it.
- If the user asks for a specific dimension ("typeface", "color scheme", "spacing", "layout"), change that dimension only. Do not redesign structure while claiming to adjust typography.
- When uncertain about what "better" means, ask before editing. Prefer one short question with 2-3 concrete options grounded in existing deck patterns.
- Always visually inspect the slide after editing and compare it to adjacent slides. Name the actual visual issue observed (e.g. labels too small, weight too heavy, color inconsistent) before making additional changes.
- Generic frontend design advice does not override deck conventions. Slidev theme defaults, existing slide patterns, and user-provided examples are the source of truth.

## Launching an existing deck

- When asked to launch or open Slidev slides, inspect the deck's `package.json` scripts first and run the existing script/CLI from the deck directory. Do not invent CLI flags; confirm flags with `slidev --help` only if the script is unclear.
- For presenter mode, use the exact URL printed by Slidev's server output (including host and trailing slash), typically `http://localhost:<port>/presenter/`. Do not substitute `127.0.0.1` for `localhost` unless the server output says so.
- After starting the server, open the presenter URL directly. If opening fails, check the server log/process immediately before retrying with a different URL.

## Resources

- Slidev documentation: https://sli.dev
- Neversink theme docs: https://gureckis.github.io/slidev-theme-neversink/
- The-unnamed theme: https://github.com/estruyf/slidev-theme-the-unnamed
