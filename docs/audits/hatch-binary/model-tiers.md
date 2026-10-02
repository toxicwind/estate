# Hatch binary — model tiers

Findings on the "pro" tier and tier labels from `/opt/hatch/bin/hatch`
strings (2026-10-02). See the [index](README.md) for the full decompose.

## `avocado-pro-max`

Exists as a route string in the binary. Listed among dormant candidate routes
in [route findings](../avocado-model-routes-2026-09-30.md) — authd has never
served it per the DB (`agent.agents.model` GROUP BY shows only `5.16-v4`
and legacy `5.14`).

**Unknown:** whether pro-max is larger, differently tuned, or a different
purpose tier. The binary does not label it.

## Tier labels

Concatenated tier strings found in the binary (2026-10-02):

- `avocadolow`, `avocadomedium` — seen as `avocadolowmedium` in strings output
- `avocadointernal` — internal tier label
- `avocadovoice` — voice modality tier

These appear to be telemetry/model-selection labels, not standalone routes.
No `avocadohigh` string was observed in the sampled output.

## Tier-related knobs

- `JARVIS_VOICE_TIER_BYPASS` — env var, voice tier control
- `JARVIS_MODEL_ID_OVERRIDE` — model route override ("using model override
  because authd selection is not aligned with requested target")
- Selection is per-purpose (`SYSTEM_PURPOSES` rows: main, compaction, memory
  flush, telemetry judging, voice, ...). Unknown purpose → "using the default
  model at Main tier".

## See also

- [Model routes](../avocado-model-family-2026-09-30.md) — full version map
- [Route findings](../avocado-model-routes-2026-09-30.md) — override mechanism
- [Index](README.md)
