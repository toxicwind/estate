# Repo Metadata — the fields GitHub shows before the README

These are set in the repo's Settings / About section on GitHub (or via the API). They determine whether anyone clicks through to the README at all.

## Description (< 140 characters)
The one-liner under the repo name in search results and profile pages. This is SEO for GitHub search.
- Lead with what it does, not what it's called: "Fast subdomain enumerator with..." beats "A tool for..."
- Include 1-2 keywords people would search for
- No marketing fluff, no "ultimate", no "blazingly fast" without proof
- Update it when the project pivots — a stale description is a lie

## Topics (up to 20)
GitHub's topic tags. They power discovery via topic pages and search filters.
- Use the most popular spelling: check what the top repos in your space use
- Include: language (`python`, `typescript`), domain (`security`, `cli`, `mcp`), and function (`subdomain-enumeration`, `recon`)
- Don't waste slots on obscure tags nobody browses
- 8-12 well-chosen topics beats 20 random ones

## Website
Link to docs site, demo, or landing page if one exists. Empty is fine — a dead link is not.

## Social preview image (1280×640)
What renders when the repo link is shared on Twitter/X, Discord, Slack, etc. GitHub caches this aggressively — changes take days to propagate, so get it right the first time.
- 1280×640px exactly
- Project name + one-liner + visual identity, readable at thumbnail size
- No tiny text — if it can't be read at 300px wide, redesign it
- Set via Settings → Social preview → Upload image

## License
No license file = no enterprise adoption = no stars from anyone who ships software for a living. The choice:
- **MIT** — maximum adoption, minimum friction. Default unless you have a reason.
- **Apache-2.0** — MIT + patent grant. Use if patents matter.
- **GPL** — copyleft. Shrinks the star pool to people comfortable with copyleft; use only deliberately.
- The LICENSE file must be at repo root, named `LICENSE` or `LICENSE.txt`, with the copyright holder and year filled in. A template with `[year]` still in it reads as unfinished.

## Default branch and repo hygiene
- `main` as default (not `master` — the ecosystem moved on)
- No dead branches cluttering the branch picker
- Repo name: lowercase, hyphenated, searchable. `pd-mcp` beats `PD_MCP_Server`. Avoid `awesome-` prefix unless it's actually a curated list.
