# README audit — toxicwind/openfang @ 31a166b3 — 2026-09-14

**Verdict:** NEEDS UPDATE

Private mirror of RightNow-AI/openfang (open-source Agent OS, Rust) plus 4 local
commits from 2026-09-14 (Chris: hal-substrate agent registry work, rename to
coyote). Audited via GitHub trees API (tarball endpoint 404'd under the
surrogate; full tree of 711 entries / 541 blobs reconstructed, key files fetched
as real content). Note: the repo's own CHANGELOG.md is stale — top entry is
[0.5.10] 2026-04-17 while Cargo.toml says 0.6.9.

## Mechanical (bin/audit.py)

- readme-exists: PASS (20,639 chars, 520 lines)
- mentioned-paths-exist: PASS (2 paths, none missing)
- relative-links-resolve: PASS
- versions-match-manifests: WARN — `['0.5.10', '0.6.9-green', '127.0.0']` not
  matched (mostly badge-syntax false positives; manual check: badge v0.6.9 =
  Cargo.toml `version = "0.6.9"` line 21 → matches)
- badge-workflows-exist: PASS
- quickstart-entrypoints-exist: PASS
- external-links-alive: WARN — `https://openfang.sh/docs/channels/whatsapp`
  → HTTPError (dead)

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| Open-source Agent OS, built in Rust (header) | Cargo.toml workspace; 15 Cargo.toml manifests in tree | VERIFIED |
| 137K LOC / 137,728 lines (header, Architecture) | No full source available to count | UNVERIFIED |
| 14 crates (header, Architecture table) | 14 crate dirs in `crates/` + xtask; table lists exactly those 14 | VERIFIED |
| 1,767+ tests (header) vs 2,696+ passing (badge) | Self-contradictory numbers in same README | WRONG (at least one) |
| Zero clippy warnings (header) | Can't verify from tree | UNVERIFIED |
| v0.6.9 badge | Cargo.toml:21 `version = "0.6.9"` | VERIFIED |
| Single ~32MB binary, `openfang init/start` (Quick Start) | `Commands::Init` (cli main.rs:110), `Commands::Start` (:116), install path external | VERIFIED (commands) / UNVERIFIED (binary size) |
| Dashboard at http://localhost:4200 (Quick Start) | cli main.rs:85 `Dashboard: http://127.0.0.1:4200/` | VERIFIED |
| `openfang hand activate researcher` (Quick Start) | `Commands::Hand` (main.rs:142), `HandCommands` incl. activate (:405) | VERIFIED |
| `openfang chat researcher` (Quick Start) | `Commands::Chat` (main.rs:147) | VERIFIED |
| `openfang agent spawn coder` (Quick Start) | `AgentCommands::Spawn` (main.rs:514); `agents/coder/` exists | VERIFIED |
| "The 7 Bundled Hands" + per-hand table | 9 HAND.toml in `crates/openfang-hands/bundled/`: browser, clip, collector, **infisical-sync**, lead, predictor, researcher, **trader**, twitter | STALE (7 → 9) |
| "40 Channel Adapters" | ~48 subdirs under `crates/openfang-channels/src/` | VERIFIED (conservative) |
| "60 bundled skills" | 62 files under openfang-skills bundled paths | VERIFIED |
| "27 LLM Providers, 123+ Models" | Only 5 provider-named .rs files found; catalog not verified | UNVERIFIED |
| "140+ REST/WS/SSE endpoints" (openfang-api row) | Not counted | UNVERIFIED |
| "16 Security Systems" table | Named systems not mapped to code | UNVERIFIED |
| "25 MCP templates" (openfang-extensions row) | No template files matched in tree | UNVERIFIED |
| WhatsApp QR gateway section | Docs link dead (see mechanical) | STALE (link) |

## Missing from README

- **agents/coyote** — 4 commits today (31a166b3 `[agents] Rename hal-substrate -> coyote`;
  231b505f, 03c01905, 23748244 `[HAL] …hal-substrate…`): agent registry,
  system prompt, first-class dynamic agent registration. Zero README coverage.
  This is the mirror's actual delta vs upstream.
- **infisical-sync and trader hands** — real bundled hands with HAND.toml, not
  in the "7 Bundled Hands" table.

## Quickstart check

- [x] Commands exist (`init`, `start`, `hand`, `chat`, `agent spawn`, `dashboard` all in CLI source)
- [x] Ports/config keys match code (4200 in main.rs:85)
- [x] A fresh user could follow it end to end (install script itself is external/unverified)

## Recent commits vs README

Last 20 commits: 4× today (coyote/hal-substrate — ours, uncovered), then
2026-08-21 HAL agent work (uncovered), 2026-06-08 Alpine 0.6.9 bump, 2026-05-12
audit/clippy/fmt hardening. README matches upstream v0.6.9; the uncovered delta
is ours (coyote) plus the two undocumented hands.

## Action taken

- None — report only, per task rules. Suggested: update hand count to 9 and
  document infisical-sync/trader; reconcile the 1,767 vs 2,696 test figures;
  fix the WhatsApp docs link; add a section on the coyote dynamic agent.
