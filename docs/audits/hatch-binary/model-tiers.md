# Hatch binary — model tiers

Verified findings on the "pro" tier and tier labels from `/opt/hatch/bin/hatch`
strings (2026-10-02). See the [index](README.md) for the full decompose.

## `ipnext/avocado-pro-max` — VERIFIED REAL

**Display name:** "Avocado Pro Max" (verbatim from the binary display-name catalog).

**Source:** binary strings, model wire-format catalog (verbatim order):
`ipnext/avocado-5.16-v4`, `ipnext/avocado-5-16-vibe`, `ipnext/avocado-pro-max`,
`ipnext/avocado-9b-voice-staging`, ...

The earlier investigation missed it because it only matched the `5.x` version
pattern — pro-max does not follow version numbering.

## How model selection works (verified from binary strings)

1. **Purpose-based routing.** Each purpose (`BrowserMain`, `BackgroundAgent`,
   `CronWorker`, `CompactionBackground`, etc.) has a `primary_model` /
   `fallback_model`. Code path:
   `hatch-engine/crates/hatch-inference/src/model_resolver/resolve_pipeline.rs`
2. **authd decides.** Verbatim: "system-pinned purpose reached selection
   routing with no SYSTEM_PURPOSES row; using the default model at Main tier"
3. **Tiered fallbacks.** Verbatim: "authd selected a model with no setup;
   falling back to avocadolow" and "falling back to avocadomedium"

## Tier labels

- `avocadolow`, `avocadomedium` — fallback tiers (the "avocadolowmedium" blob
  is two adjacent strings)
- `avocadointernal` — internal tier label
- `avocadovoice` — voice modality tier
- Tier names in binary: `main`, `basic`, `free`, `standard`, `Plus`, `MAIN`
- TrainingTier values: `green`, `yellow`, `red`

## The override knob (verified in binary, not live-tested)

- `JARVIS_MODEL_ID_OVERRIDE` — env var that forces a model route. Verbatim:
  "using model override because authd selection is not aligned with requested
  target"
- `JARVIS_MAX_TRAINING_TIER` — injected into tool subprocesses by the daemon
- Neither is settable from inside the cell for the daemon own selection —
  authd reads them at request time, host-side.

## DB reality check (2026-10-02)

`SELECT model, count(*) FROM agent.agents GROUP BY model`:
- `ipnext/avocado-5.16-v4`: **18,278 agents**
- `ipnext/avocado-5.14`: 2 agents
- `ipnext/avocado-pro-max`: **0 agents — nobody has ever run on it**

## What we cannot verify from here

- How to get authd to select pro-max for a purpose (no `SYSTEM_PURPOSES`
  config on disk; host-side behind authd)
- Whether pro-max is subscription-gated (binary has a full subscription
  system but no visible tier → pro-max mapping)
- Whether `JARVIS_MODEL_ID_OVERRIDE=ipnext/avocado-pro-max` would actually
  route (code path exists; requires daemon-level env control to test)

## See also

- [Model routes](../avocado-model-family-2026-09-30.md) — full version map
- [Route findings](../avocado-model-routes-2026-09-30.md) — override mechanism
- [Index](README.md)
