---
title: "Gemini API Tool Retrieval (EAP) — API Reference"
source: "https://ai.google.dev/gemini-api/docs/tool-retrieval (EAP-gated; captured 2026-09-17)"
page_last_updated: "2026-08-21 UTC"
status: "EAP — confidential, under embargo until Google authorizes"
enrolled_project_number: "654595778272"
our_key: "GEMINI_API_KEY_2 in /home/toxic/.secrets (eap=1)"
see_also: "docs/gemini-tool-retrieval.md (integration brief + blocker)"
---

# Purpose
Let the model dynamically search for and load tool schemas on demand instead of
receiving all tool definitions upfront. Targets 30+ tool catalogs: less context,
lower cost, better accuracy.

# Endpoint
- `POST https://generativelanguage.googleapis.com/v1beta/interactions`
- Auth: header `x-goog-api-key: $GEMINI_API_KEY`
- **generateContent does NOT support tool retrieval.** Only the Interactions API
  (Gemini API and Vertex AI).
- Model: `gemini-flash-tool-retrieval`

# Modes
Two mutually exclusive modes. Cannot mix server-side and client-side `tool_search`
in one request.

## 1. Server-side (default)
API server retrieves tool schemas automatically in a loop.

Request:
```json
{
  "model": "gemini-flash-tool-retrieval",
  "input": "Check the temperature in London and convert 100 USD to EUR.",
  "tools": [
    {"type": "tool_search"},
    {
      "type": "function",
      "name": "convert_currency",
      "description": "Convert currency amount.",
      "defer_loading": true,
      "parameters": {
        "type": "object",
        "properties": {
          "amount": {"type": "number"},
          "to": {"type": "string"}
        },
        "required": ["amount", "to"]
      }
    },
    {
      "type": "mcp_server",
      "name": "weather_service",
      "url": "https://gemini-api-demos.uc.r.appspot.com/mcp",
      "defer_loading": true
    }
  ]
}
```

Flow:
1. Define tools with `defer_loading: true`, include `{"type": "tool_search"}` in tools.
2. Model receives only tool names + short descriptions (compact summaries).
3. Model issues a `tool_search_call` step automatically when it needs a tool.
4. Server resolves the full schema, returns it as `tool_search_result`.
5. Model issues the actual `function_call` with correct arguments.
6. Developer handles `function_call` / `mcp_server_tool_call`, returns results normally.

Server-side response steps example:
```json
{
  "id": "int_server_111",
  "status": "requires_action",
  "steps": [
    {"type": "tool_search_call", "id": "tsc_abc123",
     "arguments": {"function_names": ["weather_service:get_weather", "convert_currency"]}},
    {"type": "tool_search_result", "call_id": "tsc_abc123",
     "result": [
       {"type": "function", "name": "weather_service:get_weather",
        "parameters": {"type": "object",
          "properties": {"location": {"type": "string"}}, "required": ["location"]}},
       {"type": "function", "name": "convert_currency",
        "parameters": {"type": "object",
          "properties": {"amount": {"type": "number"}, "to": {"type": "string"}},
          "required": ["amount", "to"]}}
     ]},
    {"type": "mcp_server_tool_call", "id": "mcp_call_111",
     "name": "get_weather", "server_name": "weather_service",
     "arguments": {"location": "London"}},
    {"type": "mcp_server_tool_result", "call_id": "mcp_call_111",
     "name": "get_weather", "server_name": "weather_service",
     "result": {"temp_celsius": 15}},
    {"type": "function_call", "id": "fc_xyz789",
     "name": "convert_currency", "arguments": {"amount": 15, "to": "EUR"}}
  ]
}
```

## 2. Client-side
Developer implements custom retrieval; tools can be injected dynamically without
pre-registration.

Turn 1 — declare the search tool:
```json
{
  "model": "gemini-flash-tool-retrieval",
  "input": "Search my billing database for user 123.",
  "tools": [
    {
      "type": "tool_search",
      "execution": "client",
      "name": "db_tool_search",
      "description": "Search the billing tool registry.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {"type": "string", "description": "The tool name or purpose to search for."},
          "namespace": {"type": "string", "description": "Namespace filter."},
          "limit": {"type": "integer", "description": "Maximum number of tools to return."}
        },
        "required": ["query"]
      }
    }
  ]
}
```
Response: `function_call` for `db_tool_search` with e.g.
`{"query": "get_billing_history", "namespace": "billing"}`.

Turn 2 — return discovered schemas inline in `function_result.result`
(tools array stays unchanged; do not append schemas to the tools block):
```json
{
  "model": "gemini-flash-tool-retrieval",
  "previous_interaction_id": "INTERACTION_ID",
  "tools": [ {"type": "tool_search", "execution": "client", "name": "db_tool_search",
               "description": "Search the billing tool registry.",
               "parameters": {"type": "object",
                 "properties": {"query": {"type": "string"},
                                "namespace": {"type": "string"},
                                "limit": {"type": "integer"}},
                 "required": ["query"]}} ],
  "input": [
    {
      "type": "function_result",
      "name": "db_tool_search",
      "call_id": "CALL_ID",
      "result": [
        {
          "type": "function",
          "name": "get_billing_history",
          "description": "Retrieve billing history for a given user.",
          "parameters": {"type": "object",
            "properties": {"user_id": {"type": "integer"}},
            "required": ["user_id"]}
        }
      ]
    }
  ]
}
```
The model then issues sequential `function_call` steps using the injected definitions;
execute and return results normally.

# Field reference

## tool_search tool type
| Form | Meaning |
|---|---|
| `{"type": "tool_search"}` | Server-side retrieval (default) |
| `{"type": "tool_search", "execution": "client", "name": ..., "description": ..., "parameters": {...}}` | Client-side retrieval with custom search tool |

## execution field
| Value | Behavior |
|---|---|
| `"server"` (default) | Server retrieves tool schemas automatically from deferred tools |
| `"client"` | Model emits `function_call` for the search tool; developer returns function definitions |

## defer_loading (server-side only)
- Set `defer_loading: true` on any function declaration or MCP server to exclude its
  full schema from the initial model context. Name + description remain as summaries.
- `defer_loading` on any tool WITHOUT `tool_search` in the tools array → **400 error**.
- If `execution: "client"` is set on tool_search, the API **ignores** any tools marked
  `defer_loading: true` (single-field switch between modes).

## short_description (server-side only)
- Optional on function declarations. When set, the model uses it (not the full
  `description`) as the compact retrieval summary.

## mcp_server tool type (server-side)
```json
{"type": "mcp_server", "name": "weather_service",
 "url": "https://gemini-api-demos.uc.r.appspot.com/mcp", "defer_loading": true}
```
- When `defer_loading: true`, ALL tools exposed by that server are deferred and load
  only when the model needs them.
- Step types: `mcp_server_tool_call` / `mcp_server_tool_result` (include `server_name`).

# Step types (interactions response)
| Step | Direction | Notes |
|---|---|---|
| `tool_search_call` | model → server (auto) | `arguments.function_names[]` |
| `tool_search_result` | server → model (auto) | full schemas for requested tools |
| `function_call` | model → developer | execute and return `function_result` |
| `mcp_server_tool_call` | model → developer | includes `server_name` |
| `mcp_server_tool_result` | developer → model | tool execution result |

# Limitations
- Only the Interactions API supports tool retrieval; `generateContent` does not.
- Server-side and client-side `tool_search` are mutually exclusive per request.
- `execution: "client"` ignores `defer_loading` tools (mode switch, not additive).
- Model may issue multiple search calls in a single turn when it needs several tools.
- Client-side mode requires complete function definitions as an array in
  `function_result.result`.

# SDKs (EAP preview build 2.16.0)
- Python: `gs://gemini-api-eap-sdks/toolRetrieval/google_genai-2.16.0-py3-none-any.whl`
  (or Google Drive link)
- TypeScript/JavaScript: `gs://gemini-api-eap-sdks/toolRetrieval/google-genai-2.16.0.tgz`
  (or Google Drive link); install via `npm install gs://...` (needs gcloud auth) or
  `npm install ./google-genai-2.16.0.tgz` after downloading.

# Enrollment (from giom@google.com)
- 2026-08-31: EAP invite — Tool Retrieval / Tool Search; SDK special builds 2.16.0;
  model `models/gemini-flash-tool-retrieval`; project 654595778272 enabled.
- 2026-09-01: EAP invite repeat — "Hey Contractor/Effusion Labs"; feedback requested by EOD Sept 3.
- 2026-09-07: "Platform issues fixed — ready for testing." HTTP 400 on deferred
  parameterized tools fixed fleet-wide; token-accounting correction for uncalled
  deferred tools rolling out. "We haven't seen API requests from your project yet."
