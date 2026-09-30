---
crew: 'vex-html-cors'
scope: 'Squawk HTML-first-class + CORS (Chris direct order 2026-09-21): raw HTML/CSS renders as authored in ui.html (renderer passes tags, inline styles, <style>/<script> blocks through; fenced code stays literal), CORS on feed :25135 (OPTIONS preflight 204 + ACAO on JSON/UI/404); tests html_body_served_verbatim + cors_preflight_and_headers; renderer 19/19 node checks; live POST round-trip byte-identical'
owner: 'Vex (Ember''s crew)'
status: 'DONE (2026-09-21) -- commit 615a38c69a (origin/main, ls-remote verified): ui.html renderer first-class HTML, squawk_feed.py CORS, 2 new tests; proofs: 14/14 feed tests, 19/19 node renderer checks, live POST round-trip byte-identical (fleet seq 12898), preflight 204 + ACAO live on :25135'
order: 91
registered: '2026-09-21'
updated: '2026-09-29'
---

# vex-html-cors

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
