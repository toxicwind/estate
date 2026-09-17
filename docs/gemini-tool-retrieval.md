# Gemini API Tool Retrieval EAP — integration brief

Status: SPEC + BLOCKER. 2026-09-17. Chris asked for "the geminiapi text" and "the ecp docs".
ECP has no existence anywhere in the stack or in public Gemini docs — the email trail shows
it is the **EAP** (Early Access Program): Gemini API **Tool Retrieval** (also called Tool Search).

## What it is

- EAP run by Guillaume Vernade (giom@google.com), Gemini API team. Confidential, under embargo.
- Our project is enrolled. Google (2026-09-07): "We haven't seen API requests from your project yet."
- Feature: `defer_loading: true` on tool declarations offloads tool schemas server-side;
  a retrieval meta-tool lets the model search the tool catalog dynamically at call time.
- Designed for large catalogs (30+ tools) where context-window management matters —
  exactly shep's shape (30 upstream MCP servers federated, tools/list served as a
  provenance-namespaced union).
- Docs: https://ai.google.dev/gemini-api/docs/tool-retrieval (EAP-gated, login required)
- Platform state per Google 2026-09-07: HTTP 400 on deferred tools with parameters fixed
  fleet-wide; token-accounting fix for uncalled deferred tools rolling out.

## Enrollment (from the EAP invite, giom@google.com 2026-09-01)

- Model: `models/gemini-flash-tool-retrieval` (NOT gemini-2.5-flash)
- Project number with access: **654595778272**
- SDKs: special EAP builds (google-genai 2.18.0 TS tgz / 2.19.0 Python whl via
  gs://gemini-api-eap-sdks/toolRetrieval/); REST also supported per the invite.
- Our key: **GEMINI_API_KEY_2** (project/654595778272, eap=1) in /home/toxic/.secrets.
  (GOOGLE_API_KEY is a different, non-EAP project — wrong key for this. There are 5
  GEMINI_API_KEY_N keys on the box; only #2 is EAP-enrolled.)

## Why it matters for the stack

- Context bloat: a 30-server MCP union can eat 50k+ tokens in tool schemas before any work.
- Tool-selection accuracy degrades past ~30-50 tools.
- Server-side deferral keeps the `tools` parameter stable, preserving prompt cache —
  client-side pre-filtering would break it.
- Public API parity note (googleapis/js-genai#1416): Anthropic and OpenAI already ship
  defer_loading + tool_search; Gemini only has it behind this EAP.

## BLOCKER — action needed by Chris

Corrected audit 2026-09-17 (right key + right model + right endpoint):
native generateContent on `models/gemini-flash-tool-retrieval` with GEMINI_API_KEY_2
and deferLoading declarations returns **429 RESOURCE_EXHAUSTED —
"Your prepayment credits are depleted."** Same 429 on GA gemini-2.5-flash with the
same key, so this is project billing, not the endpoint or model.
The EAP cannot be exercised until billing is topped up at https://ai.studio/projects.
Key, model, and endpoint are all correct — only money is missing.

## Integration design (for when billing is fixed)

Target path: **native** `generativelanguage.googleapis.com/v1beta/models/...:generateContent`
with `functionDeclarations[].deferLoading` on `models/gemini-flash-tool-retrieval` —
NOT the OpenAI-compat `/v1beta/openai` path the router currently uses for the google
provider. The compat path has no EAP semantics.

1. Run `tools/probe_gemini_eap.py` (re-runnable, prints shapes not keys; uses the EAP key
   GEMINI_API_KEY_2 against `models/gemini-flash-tool-retrieval`) — exit 0 means the
   enrolled project accepts deferred declarations and the lane is unblocked.
2. In sovereign-router-ts, add a native Gemini path for tool-heavy requests:
   assemble the tool catalog (shep union), mark declarations deferred, let the model
   pull schemas via the retrieval meta-tool, execute calls through shep, loop.
3. Gate behind a strategy flag; keep the compat path as default until proven.

## Deliberately NOT done

- Forcing this into nim-proxy: nim-proxy is an NVIDIA NIM rate-limit proxy; the EAP is a
  Gemini API feature. No shared surface — would be fake integration.
- Client-side pre-filtering in the router: speculative, breaks prompt caching, not asked for.
