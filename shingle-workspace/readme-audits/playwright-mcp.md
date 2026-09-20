# README audit — toxicwind/playwright-mcp @ 88d45b1733de — 2026-09-14

**Verdict:** NEEDS UPDATE

Method: GitHub tarball endpoints 404'd (codeload), so the tree was reconstructed via the git trees/blobs API at HEAD `88d45b1733de` ("ci: make Upstream Sync and Publish workflows safe by default", 2026-09-14; 40 blobs). Mechanical checks via `skills/readme-audit/bin/audit.py`; semantic pass against the tree and last 20 commits. REPORT ONLY — nothing edited, committed, or pushed.

## Mechanical results (audit.py)

- readme-exists: PASS (66,874 chars, 1,734 lines)
- mentioned-paths-exist: FAIL on `.grok/config.toml`, `.junie/mcp/mcp.json`, `.kiro/settings/mcp.json` — **false positive**: these are user-side editor config paths (README L357, L378, L403), not repo paths.
- relative-links-resolve: PASS
- versions-match-manifests: WARN on `0.0.0`, `127.0.0` — **false positives** (`0.0.0.0` bind address L537/L753; `127.0.0.1` L26/L39). No version claims in README to check; package.json and server.json both say `0.0.80` (consistent).
- badge-workflows-exist: PASS
- quickstart-entrypoints-exist: WARN on `//` — false positive (comment marker).
- external-links-alive: WARN — retested manually: `modelcontextprotocol.io/quickstart/user` → 308 (alive; audit.py timeout was sandbox egress flakiness). insiders.vscode.dev install-redirect URLs unverifiable from sandbox, not proven dead.

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| Fork note: maintained at `toxicwind/playwright-mcp`, headed rebrowser workflow, keeps upstream compat, auto-syncs from upstream `main` (L3–10) | Repo is toxicwind/playwright-mcp; `.github/workflows/upstream-sync.yml` runs every 6h (`17 */6 * * *`); sync commit `6cf285c94ac4` merged upstream today | VERIFIED |
| `npx @toxicwind/playwright-mcp@latest --cdp-endpoint … --caps vision,devtools` (L25–27; scope used 25×) | npm registry returns `"Not Found"` for `@toxicwind/playwright-mcp` as of 2026-09-14; `publish.yml` canary job gated on `NPM_CANARY_ENABLED` with comment "set it to 'true' once npm trusted publishing is configured" — i.e. publishing not configured | STALE — quickstart fails today |
| Firefox live control: `node launch-firefox-remote.js`, `FIREFOX_AGENT_PROFILE` env (L55–82) | `launch-firefox-remote.js:31` reads `FIREFOX_AGENT_PROFILE`; `:43` `headless: false`; matches commit `d1aba979` "feat: add headed firefox live control and remoteEndpoint support" | VERIFIED |
| `node sovereign-launch.js` with `PLAYWRIGHT_MCP_BROWSER`/`PLAYWRIGHT_MCP_REMOTE_ENDPOINT` or `--browser`/`--remote-endpoint` flags (L64–74) | `sovereign-launch.js:26` does `require('./packages/playwright-mcp/package.json')` but **no `packages/` dir exists** after today's "restructure to single-package layout" (`6cf285c94ac4`) → script crashes on load; `:24` uses `require('playwright/lib/mcp/program')` while the new layout's `cli.js:18-19` uses `playwright-core/lib/coreBundle` | WRONG — headline fork feature is broken |
| `cd sovereign-maximal/mcp-forks/playwright-mcp` (L57) | Machine-specific relative path; meaningless in a fresh clone — should be the repo root | WRONG |
| `.grok/config.toml` example with `/home/toxic/sovereign-maximal/mcp-forks/playwright-mcp/sovereign-launch.js` (L86–92) | Chris's personal absolute path hardcoded in a public repo README | WRONG |
| Upstream sync policy: workflow "keeps `main` aligned … by fast-forwarding from upstream when possible" + manual `git merge --ff-only` steps (L~97–110) | `upstream-sync.yml`: "Fast-forward if possible" → push; else opens PR branch. Manual steps accurate | VERIFIED |
| `remoteEndpoint` config option (L725) | Present in `config.d.ts`; matches commit `d1aba979` | VERIFIED |
| Docker example `/app/cli.js --headless --browser chromium --no-sandbox --port 8931 --host 0.0.0.0` (L940) | `Dockerfile` ENTRYPOINT `node /app/cli.js --headless --browser chromium --no-sandbox`; copies `cli.js`+`package.json` to `/app` | VERIFIED |
| VS Code / VS Code Insiders install badges (L155, L467) | Decoded URLs install `@playwright/mcp@latest` (Microsoft's package), not the fork — inherited from upstream, never rebranded | STALE |
| Kiro "Add to Kiro" badge (L401) | Decoded config installs `@playwright/mcp@latest` (upstream) | STALE |

## Missing from README

- `gate-runtime-extract.js` (repo root): unmentioned one-off OpenFang gate scraper with hardcoded sovereign infra (`ws://localhost:14724?token=sovereign-browserless-2026-change-me`, `host.docker.internal:14719/openfang/#runtime`) committed to the public repo. Either document or delete.
- `launch-firefox-from-profile.sh`: unmentioned zsh helper for real-profile Firefox takeover (feeds the currently-broken `sovereign-launch.js`).
- Publish status: README's quickstart assumes npm availability, but npm trusted publishing is not configured (`NPM_CANARY_ENABLED` gate). No git-based install alternative documented.
- No mechanism to re-apply the fork preamble (L1–~110) after an upstream sync touches README.md — `package.json`'s `lint` script references `node update-readme.js`, which **does not exist in the tree** (so `npm run lint`, and therefore both publish jobs, would fail). Next upstream README change forces the sync workflow into PR mode.
- `src/README.md` still says "Playwright MCP source code is located in the Playwright monorepo …/packages/playwright-core/src/tools/mcp" — stale upstream note; post-restructure the repo is a thin wrapper (`cli.js`, `index.js`, `config.d.ts`) over `playwright-core` bundles.

## Quickstart check

- [x] Most commands/flags exist (`--cdp-endpoint`, `--caps`, `--browser`, `--remote-endpoint`, env vars)
- [ ] **Install target missing**: `@toxicwind/playwright-mcp` is not on npm → `npx …@latest` fails
- [ ] **Fork launcher broken**: `sovereign-launch.js` crashes (stale `packages/` require)
- [ ] A fresh user could follow it end to end: **no** — install fails, firefox path broken, examples contain `/home/toxic/…` paths

## Action taken

- None (report-only task). Suggested fixes for whoever owns it: repair `sovereign-launch.js` requires for the single-package layout (mirror `cli.js`'s `playwright-core/lib/coreBundle` usage); genericize L57/L89 paths; rebrand the VS Code/Kiro install badges to `@toxicwind/playwright-mcp` (or remove until the package is published); document publish/canary status or add a git-install path; decide the fate of `gate-runtime-extract.js`; restore or remove the `update-readme.js` lint step.
