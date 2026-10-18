---
crew: 'flock-consolidation'
scope: 'router consolidation wave: hodos flock maximal merge — nim-proxy core absorbed (FEATURE_PARITY), Anthropic /v1/messages surface (Claude Code), headless env seeding, verified-model catalog, docker nim-proxy retired, herd + cuttinggate repaired'
owner: 'kappa-session (flock lane)'
status: 'DONE (2026-10-17) -- hodos proxy v0.6.6 (441 tests green, clippy clean); flock live :25193 (OpenAI + Anthropic, 28 verified models); docker nim-proxy container stopped; kappa custom provider wired and e2e-verified (KAPPA-FLOCK-OK)'
order: 91
registered: '2026-10-17'
updated: '2026-10-17'
---

# flock-consolidation

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.

2026-10-17 wave. Deliverables:

- `ranch/hodos/proxy/` — the preserved nim-proxy Rust core (v0.6.6) moved from
  `ranch/forge/router/flock-proxy/` into the hodos tree (`FEATURE_PARITY.md`
  promised the merge; this landed it). 28 Rust sources, 441 tests green,
  nightly toolchain pinned (`rust-toolchain.toml`), estate rustfmt config
  repaired (`format_strings = false` — it corrupted string literals).
- **Anthropic Messages surface** — `src/anthropic.rs`: `/v1/messages` +
  `/v1/messages/count_tokens` with full request/response/SSE translation
  (content blocks, tool use → tool_calls + input_json_delta, stop_reason
  mapping). Claude Code works against flock with `ANTHROPIC_BASE_URL`.
- **Headless bootstrap** — `settings::apply_env_seeds`: NIM keys, client
  keys (hashed), superuser, limits and base URL seed the store at boot,
  additively; the dashboard stays the day-2 surface. 6 regression tests.
- **Honest catalog** — `NIM_VERIFIED_MODELS` refreshed from the 2026-10-17
  full audit (81 models probed end-to-end at 10s: 14 pass, 55 404, 11
  deadline-exceeded twice, 1 non-text modality).
- **Daemon cutover** — `[daemons.flock]` in `pitchfork.toml` now runs the
  hodos binary on :25193 (the registered SSOT port; :8000 was absurd and is
  dead). The docker `nim-proxy` container is stopped (Lane A doctrine).
- **Router repairs** — herd launcher finds the relocated `llama-swap` binary
  (52 models live), cuttinggate reads its relocated source dir + the
  regenerated Roost catalog contract (94/94 tests), catalog-audit
  `audit`/`renderReport` implemented, `bin/catalog-sync.ts` quarantines
  unservable ids with receipts.
- **Kilo/kappa** — `provider.flock` custom provider in the dots config
  (key from env, never in-file) verified end-to-end through kappa.

Follow-ups: estate-router-ts and the pre-rename `e2e-agent-stack.ts` naming
rot remain; old `ranch/flock/bin/flock-run.sh` launcher is superseded.
