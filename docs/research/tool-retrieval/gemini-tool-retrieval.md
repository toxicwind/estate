# Gemini API Tool Retrieval EAP — integration brief

Status: SPEC + BLOCKER. 2026-09-17. Chris asked for "the geminiapi text" and "the ecp docs".
ECP has no existence anywhere in the stack or in public Gemini docs — the email trail shows
it is the **EAP** (Early Access Program): Gemini API **Tool Retrieval** (also called Tool Search).
Source: ai.google.dev/gemini-api/docs/tool-retrieval (EAP-gated; Chris pasted the page 2026-09-17).
Confidential, under embargo until Google says otherwise.

## What it is

- EAP run by Guillaume Vernade (giom@google.com), Gemini API team.
- Our project is enrolled. Google (2026-09-07): "We haven't seen API requests from your project yet."
- Lets the model dynamically search for and load tool schemas on demand instead of receiving
  all tool definitions upfront. Designed for 30+ tool catalogs: reduces context usage,
  lowers cost, improves model accuracy — exactly shep's shape (30 upstream MCP servers).
- Also noted on the EAP page: **Gemini 3.8 Flash is now available.**

## The real API surface (this is what I got wrong on the first two audits)

- **Endpoint: `POST /v1beta/interactions`** — the Interactions API. `generateContent`
  does NOT support tool retrieval. That was the wrong-endpoint mistake.
- **Model: `gemini-flash-tool-retrieval`**.
- **Key: GEMINI_API_KEY_2** in /home/toxic/.secrets (project/654595778272, eap=1).
  GOOGLE_API_KEY is a different, non-EAP project — wrong key. 5 GEMINI_API_KEY_N keys
  exist on the box; only #2 is EAP-enrolled.

### Server-side mode (default)

```json
POST https://generativelanguage.googleapis.com/v1beta/interactions
{
  "model": "gemini-flash-tool-retrieval",
  "input": "Check the temperature in London and convert 100 USD to EUR.",
  "tools": [
    {"type": "tool_search"},
    {"type": "function", "name": "convert_currency",
     "description": "Convert currency amount.", "defer_loading": true,
     "parameters": {"type": "object", "properties": {"amount": {"type": "number"}, "to": {"type": "string"}}, "required": ["amount", "to"]}},
    {"type": "mcp_server", "name": "weather_service",
     "url": "https://gemini-api-demos.uc.r.appspot.com/mcp", "defer_loading": true}
  ]
}
```

- Tools marked `defer_loading: true` send only name + description in initial context;
  full schemas load on demand through an automatic server-side loop.
- `defer_loading` without a `tool_search` entry in tools → 400.
- Optional `short_description` on declarations overrides the retrieval summary.
- **MCP servers are first-class**: `{"type": "mcp_server", "name", "url", "defer_loading": true}`
  defers ALL tools on that server. This is the direct shape for shep's 30-server union.
- Response steps: `tool_search_call` → `tool_search_result` → `function_call` /
  `mcp_server_tool_call`; you handle the calls and return results as usual.

### Client-side mode

- `{"type": "tool_search", "execution": "client", "name", "description", "parameters": {...}}`
  — model emits a standard `function_call` for YOUR search tool; you return matching
  complete FunctionDeclaration objects inline inside `function_result.result`.
- Supports dynamic tool injection: tools don't need pre-registration.
- Server-side and client-side are mutually exclusive in one request.

### SDKs

Preview build 2.16.0 (EAP-only): Python `google_genai-2.16.0-py3-none-any.whl`,
TS `google-genai-2.16.0.tgz` — both at gs://gemini-api-eap-sdks/toolRetrieval/ (or Drive).

## BLOCKER — action needed by Chris

Fully corrected audit 2026-09-17 (~04:30 MDT): right key (GEMINI_API_KEY_2, eap=1),
right model (gemini-flash-tool-retrieval), right endpoint (v1beta/interactions),
right tool shapes (tool_search + defer_loading function) → **429
"Your prepayment credits are depleted."** Same 429 on generateContent/gemini-2.5-flash
with the same key, so it's project billing, not the endpoint or model.
Top up at https://ai.studio/projects and this lane unblocks immediately.

## Integration design (for when billing is fixed)

1. Run `tools/probe_gemini_eap.py` (exit 0 = EAP_OK on the interactions endpoint).
2. In sovereign-router-ts, add a NATIVE Gemini path: POST /v1beta/interactions on
   `gemini-flash-tool-retrieval` — NOT the OpenAI-compat `/v1beta/openai` path the router
   uses for the google provider, which has no EAP semantics.
3. Server-side mode first: pass shep's 30-server union as `mcp_server` entries with
   `defer_loading: true` + `{"type": "tool_search"}`; handle `mcp_server_tool_call`
   steps by executing through shep and returning results.
4. Client-side mode as the advanced lane: implement our own retrieval over the tool
   registry (vector search / ffs-style symbol lookup) and inject schemas dynamically.
5. Gate behind a strategy flag; keep the compat path default until proven.

## Deliberately NOT done

- Forcing this into nim-proxy: nim-proxy is an NVIDIA NIM rate-limit proxy; the EAP is a
  Gemini API feature. No shared surface — would be fake integration.
- Client-side pre-filtering in the router: speculative, breaks prompt caching, not asked for.
