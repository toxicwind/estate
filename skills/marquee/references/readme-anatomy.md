# README Anatomy — the 10-second hook, section by section

Borrowed from `othneildrew/Best-README-Template` (16k⭐) and `matiassingers/awesome-readme` (21k⭐). Customize the content, not the architecture — this structure is proven.

## The order (top to bottom)

### 1. Shields row (badges)
The first thing the eye hits. Use shields.io. Every badge must be live — a 404 badge is worse than none.
- Build status (CI) — green = "this works"
- Latest version/release
- License
- Stars, forks (social proof — they grow themselves once the rest is right)

Why it matters: badges are compressed trust signals. A visitor pattern-matches "green badges = maintained" in under a second.

### 2. Centered logo (optional but powerful)
`<div align="center"><img src="images/logo.png" width="80"></div>`. A logo makes the project feel real and memorable. Skip if you have nothing — a bad logo is worse than none.

### 3. Centered title + one-line description
```html
<h3 align="center">project-title</h3>
<p align="center">One sentence: what it does and for whom.</p>
```
The one-liner is the single highest-leverage sentence in the repo. If a visitor reads nothing else, this must land. Formula: `[Project] is [what] for [who] that [key benefit]`.

### 4. Action links
```html
<p align="center">
  <a href="docs/">Explore the docs »</a> · <a href="demo/">View Demo</a> ·
  <a href="issues/new?labels=bug">Report Bug</a> · <a href="issues/new?labels=enhancement">Request Feature</a>
</p>
```
Pre-filled issue links with labels (`?labels=bug&template=bug-report---.md`) lower the reporting bar to one click.

### 5. Demo (above the fold — non-negotiable)
A GIF, screenshot, or asciinema cast showing the thing working. Placed BEFORE any prose explanation.
- GIF: < 5MB, < 30 seconds, shows the core loop
- Screenshot: annotated if the UI needs it
- No demo = no excitement = no star. This is the single most-skipped item and the single highest-leverage fix on most repos.

### 6. Table of Contents (collapsible)
```html
<details><summary>Table of Contents</summary>
<ol><li><a href="#about">About</a>...</li></ol>
</details>
```
Collapsible so it doesn't push the demo down. Anchor links to every major section.

### 7. About the Project (+ Built With)
What it does, why it exists, what problem it solves. Then a "Built With" subsection listing key frameworks/libraries with links — this is SEO for developers browsing by stack, and it populates GitHub's dependency graph.

### 8. Getting Started
Two subsections, in this order:
- **Prerequisites** — exact versions, one-liners to check (`node --version`)
- **Installation** — copy-paste commands, numbered steps. The reader should go from zero to running in under 30 seconds. If installation takes longer, that's a product problem the README can't fix — but at least don't add friction.

### 9. Usage
Not a man page — show the 3 most common things, with copy-paste examples and expected output. Link to `docs/` or `examples/` for the rest. Every example must actually run; a broken example destroys trust faster than no example.

### 10. Roadmap
Checklist of what's done and what's next. Signals the project is alive and has direction. Use `- [x]` / `- [ ]` checkboxes. Link to open issues for proposed features — it funnels enthusiasm into engagement.

### 11. Contributing
One paragraph + link to `CONTRIBUTING.md`. The README sells the vision; CONTRIBUTING.md sells the on-ramp. Never put the full contributing guide in the README — it pushes everything else down.

### 12. License
One line: `Distributed under the MIT License. See LICENSE for more information.` The LICENSE file itself does the legal work.

### 13. Contact + Acknowledgments
Maintainer handle, link to discussions/issues. Acknowledgments for borrowed code, inspirations, contributors — generosity signals a healthy project culture.

### 14. The star CTA (bottom)
> Don't forget to give the project a star! Thanks again!

Cheeky, but the 16k⭐ template includes it and it works. One line at the very bottom, after the reader is already convinced.

## What goes where (the fold rule)

- **Above the fold** (no scrolling): shields, title, one-liner, action links, demo
- **First scroll**: TOC, About, Built With
- **Second scroll**: Getting Started, Usage
- **Below**: Roadmap, Contributing, License, Contact, Acknowledgments, star CTA

If the demo isn't visible without scrolling, the README is broken regardless of how good the prose is.
