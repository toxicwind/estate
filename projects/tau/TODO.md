# Endless TODO — Tau Sovereign Loop (never finite, always next wave)

> This file is the infinite loop. Do not close. Each wave appends, never replaces.
> Previous waves remain for archaeology. Next wave always open.

## Wave Groq Maximal 2026-09-03
- [x] groq registry login via createApiKeyLogin (gsk_...) — `packages/ai/src/registry/groq.ts` + engine mirror
- [x] catalogDiscovery Groq + default llama-3.3-70b-versatile — `packages/catalog/src/provider-models/descriptors.ts` + `openai-compat.ts` (groqModelManagerOptions -> https://api.groq.com/openai/v1) + hosts/api.groq.com + engine/packages/ai/src/providers/data/groq.json mirrored
- [x] groq streaming/tool/JSON parity tests (4 pass) — `packages/ai/test/groq-streaming.test.ts` (compat supportsToolChoice/Forced/Named, supportsMultipleSystemMessages via isGroqHost, SSE tool-call delta/reasoning_content/[DONE], response_format json_object via onPayload) + `packages/catalog/test/groq-provider.test.ts` (4 pass)
- [ ] next: live generate with GROQ_API_KEY nightly, whisper audio filter audit, mixtral deprecation watch

## Next Wave (open)
- [ ] nightly `GROQ_API_KEY` live discovery against https://api.groq.com/openai/v1/models — assert catalog drift <7d
- [ ] whisper audio filter audit — ensure groq whisper/tts prefixes excluded from chat catalog (OPENAI_NON_RESPONSES_PREFIXES parity)
- [ ] mixtral deprecation watch — remove 8x7B if upstream 410
- [ ] engine ↔ packages byte-ident flush script — `packages/catalog/scripts/generate-models.ts` canonical, delete stale data/ duplicates
- [ ] herd nightly model-rank refresh

---
*Loop rule: append-only, never finite, always next.*
