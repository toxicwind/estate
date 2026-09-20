# README audit — toxicwind/sovereign-dispersal @ c265c23c — 2026-09-14

**Verdict:** PASS

Single-commit repo (only commit on main). Mechanical audit: all 7 checks PASS (12 mentioned paths all exist, 0 broken links, versions/badges/entrypoints/URLs clean). CI run 34875885090 = success on this SHA. Semantic pass below — every claim checked against source.

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| Intro: seven-substrate Bun monolith (fs-map, ralph, pi-natives, fastest-wins, backhaul, AVO, event contracts) | `src/index.ts:5-14,21-38` imports and walks all seven | VERIFIED |
| 1. fs-map audits trees, counts symlinks + git repos, surfaces dup top-level names, persists `~/.config/sovereign-fs-map.json` | `src/sovereign/fs-map.ts:52` (symlinks++), `:57` (.git→gitRepos++), `:86` (writes sovereign-fs-map.json), dupPairs in summary line `:95` | VERIFIED |
| 2. ralph strips orphan `planning=`/`development=` keys, always backs up first, sanity-checks string `cmd` + `exa`/`ddgs` enum | `src/ralph/fix.ts:9` ORPHAN_KEYS, `:38-39` writes `.bak-<ts>` backup before editing, `:50` python sanity pass on cmd/provider | VERIFIED |
| 3. pi-natives builds explicit targets one by one, skips cleanly when engine checkout absent | `src/natives/loader.ts:17-19` noEngine→skip path, `:23` per-target loop | VERIFIED |
| 4. fastest-wins: `Promise.any` + AbortController, first OPEN socket wins, rest cancelled, fast failure never beats slower success, `AllProbesFailed` only when all fail | `src/transport/fastest-wins.ts:74` AbortController, `:82` Promise.any, `:86` AllProbesFailed, `:91` controller.abort() | VERIFIED |
| 4b. Route A: zod-validated endpoint set, `verifyLive()` truth table, `dnsFix()` resolver repair | `src/transport/route-a.ts:10` EndpointSchema, `:83` verifyLive, `:124` dnsFix | VERIFIED |
| 5. backhaul: 2.5% → 7.33%, 2.93× lift at 25% discount, zod-validated inputs | `src/profit/backhaul.ts:8` BackhaulInput z.object; `tests/backhaul.test.ts:6-9` pins before=2.5, lift≈2.93 (2.5×2.93=7.325→7.33) | VERIFIED |
| 6. AVO: visual (Z^v) / reasoning (Z^r) latents, router width k ∈ {4,8,16}, seeded reproducible | `src/profit/avo.ts:6` Latent type, `:24-25` mulberry32 PRNG, `:45` seed path; `dashboard.html:60` shows k ∈ {4,8,16} | VERIFIED |
| 7. event contracts: targets, settlement rules, cents-as-probability, trading-prohibition checks | `src/profit/event-contracts.ts:7` target, `:11` settlement, `:36-37` priceToProb cents/100, `:22` isTradingProhibited | VERIFIED |
| Quickstart: `bun install`, `bunx biome check ./src ./scripts ./tests`, `bun test`, `bun run dev` | package.json scripts; CI workflow `.github/workflows/ci.yml:16-17` runs the identical `bunx biome check` + `bun test` strings and CI run 34875885090 is green | VERIFIED |
| Scripts table (dev, route-a, audit, ralph:fix, natives:build, profit:backhaul/avo, deploy) | package.json scripts — all 8 entries match 1:1 | VERIFIED |
| Deploy: `bun run deploy` → bun build → docker build → optional push via `DEPLOY_PUSH=1`, `DEPLOY_IMAGE=…` | `scripts/deploy.ts:7-8` env vars, `:12-26` the three build/push steps | VERIFIED |
| Dockerfile multi-stage, runs as non-root `bun` | `Dockerfile:1,11` two FROM stages, `:15` `USER bun` | VERIFIED |
| Deploy note: edge via Fastly/Qwilt, Modal CloudBucketMount at `/mnt/s3/my-data` | `scripts/deploy.ts:2-3,33` — phrased as operator guidance, consistent with deploy.ts's own summary output | VERIFIED |
| dashboard.html: fastest-wins pulse, backhaul flow, AVO memory bricks, Route A truth table | `dashboard.html:21-23` pulse, `:23` backhaul flow comment, `:26` avo bricks comment, `:64-70` Route A LIVE/FAIL endpoint list | VERIFIED |
| Notes: `cdn` + `sandbox.team` unresolvable by design (expected-FAIL rows) | `src/transport/route-a.ts:27` cdn→FAIL, `:37-40` sandbox.team→FAIL | VERIFIED |
| Notes: `ralph:fix`/`audit` touch `~/.config/`; tests never touch home | `src/ralph/fix.ts:14` writes to homedir .config; `tests/*.ts` contain zero HOME/.config/write references | VERIFIED |

## Missing from README

- `bun run build` (package.json → `bun build src/index.ts --outdir dist --target bun`) is a real script with no row in the Scripts table. Minor.
- CI workflow (`.github/workflows/ci.yml`) exists and is green; README carries no CI mention or badge. Cosmetic; arguably fine for a PoC.

## Quickstart check

- [x] Commands exist (`bunx biome check` string is exactly what green CI runs)
- [x] Ports/config keys match code (no ports claimed; `~/.config` paths match)
- [x] A fresh user could follow it end to end (`bun install` → lint → test → `bun run dev` walks all substrates)

## Action taken

- None — report only, per task rules. Nothing failed; the one finding (`bun run build` omitted from the scripts table) is a minor doc gap, not worth a REWRITE verdict.

Notes for parent: the GitHub API tarball endpoint (`/tarball/HEAD`, `/tarball/main`) 404'd twice even for this public repo (302 → codeload 404), so I shallow-cloned over HTTPS instead and audited at c265c23c, which matches the pushed commit. Also of interest: `bunx biome check` in README quickstart names the short package while package.json's `lint` script uses `bunx @biomejs/biome` — but the repo's own CI runs the short form green, so the README command is live and correct in practice.
