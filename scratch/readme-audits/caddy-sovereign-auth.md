# README audit — toxicwind/caddy-sovereign-auth @ e452dcfc — 2026-09-14

**Verdict:** REWRITE (no README exists at all)

Repo: public, no description. HEAD `e452dcfc` (2026-09-14T09:40:23Z). 15 commits total, 13 files.

## Claims

No README.md exists in the tree (checked `README.md`, `readme.md`, `README`, `README.MD`
via Contents API + recursive git tree — all 404/absent). There are no claims to verify.

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| *(none — no README)* | `git/trees/main?recursive=1` → 13 files, no README | N/A |

## Mechanical results

`bin/audit.py --path <tree>`:

- `readme-exists`: **FAIL** — "README.md not found" (only check run; no README to analyze further)

Note: tarball download via `api.github.com/.../tarball/{HEAD,main}` 404s after the
302 to codeload (auth header not honored there). Ground truth obtained via
`git/trees/main?recursive=1` + Contents API raw downloads instead.

## Missing from README

Everything. What a README would need to cover, from source:

- **Caddy auth module** (`sovereignauth.go`): `http.handlers.sovereign_auth` middleware —
  API-key auth via `Authorization: Bearer` or `X-API-Key`, Tailscale identity via
  `X-Tailscale-User-Login` header, trusted-network bypass, 401
  `{"error":"unauthorized"}` with `WWW-Authenticate: Bearer realm="sovereign"`.
- **Build facts** (`go.mod`): module `github.com/toxicwind/caddy-sovereign-auth`,
  go 1.26.5, caddy v2.11.4. All deps marked `// indirect` — no direct requires;
  no Caddyfile, Dockerfile, or build instructions anywhere in the tree.
- **Agentic lens system** (`lib/lens-orchestrator.js`, `src/_11ty/lenses/`): auto-discovers
  `lens_*.js` modules exposing `name` + `analyze()`; 4 lenses ship —
  `lens_cryptographic.js` (leak detection), `lens_osint.js` (recon),
  `lens_stylometric.js`, `lens_tectonic.js` (drift). Latest commit `e452dcfc` fixed
  `lensDir` to resolve to an absolute path.
- **Env config** (`.env.example`, 11 vars): `LENS_ENABLED`, `LENS_SWARM_CONCURRENCY`,
  `LENS_AUTO_COMMIT`, `SWARM_MAX_CONCURRENCY`, `SWARM_TIMEOUT_MS`, `GITHUB_TOKEN`,
  `OPHEL_VAULT_PATH`, `MODELBEATS_API_ENDPOINT`, `ZEDRA_DAEMON_HOST`, `MUSEPOOL_CDN_PRIMARY`,
  `MCP_TRANSPORT`.
- **CI** (`.github/workflows/`): `agentic-lens-ci.yml` (lens pipeline + MCP smoke test;
  skips bun install when no `package.json` — there is none), `tectonic-drift.yml`
  (daily 06:00 UTC drift check against repo `effusion-labs`).
- **Recent changes with zero docs**: 2026-09-14 CI repairs (`846a021b` unterminated-quote
  fix, `18397ddf` dropped broken bun/npm install step); 2026-09-03/04 the entire
  agentic lens pipeline + both workflows + orchestrator added (`d7679a00`,
  `10db403c`, `5d4ca044`, `4c252960`, `277dd21a`, `3bcf2c30`, `ac66d37d`).
  Nothing was ever documented.

## Observations for the rewrite author

- The repo is really **two unrelated halves** (Go Caddy module + JS agentic-lens CI
  harness). The README should say so up front, not imply one product.
- `TrustedNetworks` matching in `sovereignauth.go:33-37` is a crude
  `strings.HasPrefix` on `RemoteAddr` (not real CIDR parsing) — document as-is,
  don't oversell it.
- `AGENTS.md` (7 KB, agent hard rules) exists but is not a substitute for a README.

## Quickstart check

- [ ] N/A — no README, no quickstart to check

## Action taken

- None — report only, per task rules. README needs to be written from scratch.
