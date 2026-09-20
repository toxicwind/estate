# README audit — toxicwind/herd @ bb45d12dbe25 — 2026-09-14

**Verdict:** REWRITE

Headline: the README is the **upstream llama-swap README** with a fork section bolted on. It never mentions "herd" once (0 occurrences), misattributes the fork as `toxicwind/llama-swap`, and points badges, remotes, and clone URLs at the wrong repos. Herd-specific recent work (own unified images, rootless-build fix, lens suite) is absent.

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| Title "# llama-swap"; badges for `mostlygeek/llama-swap` (downloads, CI, stars) | README.md:1-6; API: repo full_name is `toxicwind/herd`, not mostlygeek | WRONG — badges report upstream numbers, not this repo |
| "→ Fork: toxicwind/llama-swap" | README.md:10; API full_name `toxicwind/herd` | WRONG — misattributed fork |
| "Last synced with upstream: Jul 20, 2026" + diff link to llama-swap compare | README.md:11; link targets `toxicwind/llama-swap/compare/...mostlygeek`, not herd | STALE/UNVERIFIED |
| `GET /models/sse` synthesized for Zed | internal/server/models_sse.go:14-16 | VERIFIED |
| SSE normalization via `normalize_sse` / `upstream.normalize_sse` | internal/config (NormalizeSSE + config_posix_test.go:225-261) | VERIFIED |
| IPv4 loopback default 127.0.0.1 (localhost→::1 breakage) | internal/config/model_config.go:166 | VERIFIED |
| Free stale port with `fuser -k` before spawn | internal/process/process_command.go:430 | VERIFIED |
| AST Matrix V2: token bucket + 5-strike circuit breaker, 30s cooldown | internal/astmatrix/circuit.go, ratelimit.go | VERIFIED |
| 8 routing strategies (hybrid, ast_race, sticky_affinity, weighted_elo, least_latency, round_robin, free, circuit_chain) | all 8 strings in internal/astmatrix/*.go | VERIFIED |
| 13 built-in providers w/ listed base URLs | internal/astmatrix/providers.go:84-155 (exactly 13 `ID:` entries) | VERIFIED (free-tier ✓ column UNVERIFIED) |
| `astMatrix:` config keys (astStrategy, requestTimeout, maxRetries, healthProbeInterval, enableCoalescing) | internal/config/config.go:193; internal/astmatrix/config.go:5-18 | VERIFIED |
| `/astmatrix/status`, `/astmatrix/metrics` endpoints | internal/astmatrix/ui.go:18-23 | VERIFIED |
| Bench Orchestrator at `cmd/bench-orchestrator/`, `internal/bench/` | `ls cmd/` → no bench-orchestrator; code is in internal/bench/orchestrator.go | WRONG path — cmd/bench-orchestrator does not exist |
| AST Matrix Go Port: `internal/astmatrix/`, zero external deps | internal/astmatrix/ (stdlib-only imports) | VERIFIED ("193 string refs", "~40ms→sub-ms" UNVERIFIED) |
| Sovereign listen `http://127.0.0.1:25100` | internal/astmatrix/providers.go:84 (`http://127.0.0.1:25100/v1`) | VERIFIED |
| Model inventory `tools/llama-swap/MODEL_INVENTORY.md` | no `tools/` dir in tree; mechanical check FAIL | MISSING |
| Remotes: `fork https://github.com/toxicwind/llama-swap.git (this repo)` | README.md "Remotes"; API: this repo is toxicwind/herd | WRONG |
| Build: `cd ~/projects/llama-swap-main && go build -o llama-swap .` | local path; repo clones as `herd` | STALE |
| Quickstart: `git clone https://github.com/mostlygeek/llama-swap.git` + `make clean all` | Makefile:18,21 has all/clean; clone URL is upstream, not this repo | WRONG URL (builds upstream, not the fork) |
| Binary symlink `/home/toxic/sovereign/tools/llama-swap/llama-swap` → `projects/llama-swap-main/llama-swap` | local-machine path, not in repo | UNVERIFIED (local-only) |
| Docker: unified/legacy images only from `ghcr.io/mostlygeek/llama-swap` | README.md Docker section | STALE — fork publishes its own namespace (see Missing) |

Mechanical notes: `mentioned-paths-exist` FAIL only on the two local-machine paths above (expected — not in repo). `versions-match-manifests` WARN on "127.0.0" is a false positive (regex hit on 127.0.0.1 IPs). `external-links-alive` WARN on the shields.io downloads badge is an egress timeout, not a dead link.

## Missing from README

- **The repo is named herd.** Zero mentions. Title, badges, remotes, clone URL all say llama-swap/mostlygeek.
- **Fork's own unified Docker images**: `ghcr.io/toxicwind/herd:unified-<backend>` published by `.github/workflows/unified-docker.yml:114` (`DOCKER_IMAGE_TAG: ghcr.io/${{ github.repository }}:unified-...`), built by `docker/unified/build-image.sh`. README documents only upstream images.
- **bb45d12 rootless-build fix (2026-09-14)**: rootless stage must use plain `docker build` (docker driver), not `buildx` container driver, so `FROM ghcr.io/toxicwind/herd:unified-<backend>` resolves the local tag — documented only in `docker/unified/build-image.sh` comment + commit message. Nightly unified builds had been failing for a week.
- **Agentic lens suite** (5 commits 2026-09-03 + tectonic-drift.yml workflow): stylometric authorship, OSINT infra recon, cryptographic leak detection, tectonic drift lenses (`src/_11ty/lenses/*.js`), lens orchestrator (`lib/lens-orchestrator.js`), `.env.example` lens config. No README coverage.
- `README_ASTMATRIX_V2.md` exists as a second, overlapping AstMatrix doc — README doesn't reference it.

## Quickstart check

- [x] Commands exist (Makefile `all`/`clean`; `go build`)
- [ ] Ports/config keys match code — :25100 and `astMatrix:` keys match, but clone URL/build dir point at upstream
- [ ] A fresh user could follow it end to end — **no**: they would clone mostlygeek/llama-swap (upstream, none of the fork's patches), and nothing tells them the repo is herd or where the fork's own images live

## Action taken

- None — REPORT ONLY per task. Recommended: rewrite README with herd identity (title, badges, remotes, clone URL), add fork's unified-image publishing + rootless build note, add lens suite section, fix `cmd/bench-orchestrator` path to `internal/bench`.

## Fix applied — 2026-09-14 ~12:20 MDT

Two dispatched fix workers died within ~2 minutes (runtime routed them under a
completed coordinator; they exited after backgrounding the clone). Fix was done
directly: README rewritten via the GitHub API (tree verified at main via the
recursive tree + contents APIs; the awrawr-pc bridge was timing out).

- Commit: `23c82cb5` — "docs: rewrite README with herd identity"
- Push: `199b6b73..23c82cb5 main -> main` (ref moved via API, verified)
- New README: `# herd` title, toxicwind/herd badges/remotes/clone URL, unified
  images (`ghcr.io/toxicwind/herd:unified-<backend>`), 2026-09-14 rootless-build
  note, AST Matrix V2 (8 strategies, 13 providers, config keys, endpoints, link
  to README_ASTMATRIX_V2.md), agentic lens suite, bench orchestrator path fix
  (`internal/bench/orchestrator.go`), ports table (25100 / 25001–25099), Why-a-fork
  (normalize_sse, GET /models/sse, fuser -k, IPv4 loopback), no local-machine paths.
- Note: commit `b7ac515e` ("commit local work") added a `mesh/gateway/cmd/mcpproxy/`
  Go tree to this public repo just before the fix — filenames look like legit code,
  but a secrets scan of that commit is worthwhile.
- Orphaned worker scratch dir `/home/toxic/readmefix-herd-7f3a9c2e` on awrawr-pc
  may hold a partial clone (bridge was down; cleanup unconfirmed).
