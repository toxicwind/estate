# Avocado model family — what we can verify (2026-09-30)

**Bottom line:** there is no GGUF and no downloadable weight file. Avocado is
Meta's internal model family served from Meta's inference substrate
(`ipnext/*` routes); the weights do not live on the cell or on yote. This doc
is the backup that *is* possible: the full route/version map, variants, and
knobs extracted from the runtime binary, plus honest notes on what we don't know.

## What it is

- 
-  — model route override; binary log text indicates it is
  *applied* when "authd selection is not aligned with requested target"
  (system-pinned purposes fall back when no SYSTEM_PURPOSES row exists).
  Launch-time env; not settable live from inside the cell.`ipnext/avocado-5.16-v4` is the model route observed on the README-crew agent
  records on 2026-09-30 — it's what powers this runtime's agents (including this
  session). Not a public model; not on OpenRouter/HF; no public API.
- `ipnext` = Meta's internal inference provider route. `avocado` = the model family.
- Versioning: `5.16-v4` = family generation 5.16, 4th revision.

## Version map (from `/opt/hatch/bin/hatch` strings, 2026-09-30)

Chat/agent routes:
`ipnext/avocado`, `ipnext/avocado-5.11`, `ipnext/avocado-5.12`,
`ipnext/avocado-5.13`, `ipnext/avocado-5.13b`, `ipnext/avocado-5.14`,
`ipnext/avocado-5.14-load-test`, `ipnext/avocado-5.14-sglang`,
`ipnext/avocado-5.14.1.v1`, `ipnext/avocado-5.14.1.v2`, `ipnext/avocado-5.14.1.v3`,
`ipnext/avocado-5.14.1.cm1`, `ipnext/avocado-5.14.1.cm2`, `ipnext/avocado-5.14.2`,
`ipnext/avocado-5.14.3.b`, `ipnext/avocado-5.15`,
`ipnext/avocado-5.16-v0` … `ipnext/avocado-5.16-v4`,
`ipnext/avocado-pro-max`

Responses-API variants:
`ipnext_responses/avocado-5.11`, `ipnext_responses/avocado-5.14`,
`ipnext_responses/avocado-5.14-load-test`

Agent-profile variants (per-generation agent configs):
`avocado_5p13_agent`, `avocado_5p14_agent`, `avocado_5p15_agent`

Compaction (context management):
`azure/avocado-compaction-v1`, `azure/avocado-memory-flush-v1`,
env `JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS` (default 150000/200000 window)

Cron/background:
`avocado-cron`, `avocrono-5.13`, `avocrono-5.13-load-test`,
`avocrono-5.14`, `avocrono-5.14-load-test`, `avocado-5.14-agent`, `avocado-5.15-agent`

Voice/TTS (same family, different modality):
`ipnext/avocado-9b-voice`, `ipnext/avocado-9b-voice-staging`,
`avocado_v2_*` voice catalog entries (TTS voices, not the chat model)

Notable neighbor on the same provider: `ipnext/glm-5.2`

## Knobs visible in the binary

- `JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS` — compaction trigger (150000 default
  of 200000 window; staged 170000 override was wiped by host re-provision —
  see TOOLS.md).
- `JARVIS_AVOCADO_CONTEXT_WINDOW_TOKENS`
- `avocado_compaction_272k` experiment flag.

## Quality — what we can honestly say

No public benchmarks exist for this family (it's internal). Observed 2026-09-30:
it ran the full README rollout — 50 repos landed with verified pushes, multi-step
audits, honest license corrections, byte-exact transfers. Strong tool use,
long-context coherence, follows complex multi-constraint briefs. That's
operational evidence, not a benchmark score.

## What we don't know (not inventing)

- Parameter count, architecture, training data, context-window size in tokens.
- Whether `pro-max` is larger or just differently tuned.
- What `cm` / `b` suffixes denote.

## Method note

Extracted via `strings` on the runtime binary plus the fleet knowledgebase.
Re-extract after runtime updates — the route list changes with new builds.
