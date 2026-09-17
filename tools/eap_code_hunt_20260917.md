# Gemini Tool Retrieval EAP — real-code hunt (2026-09-17)

Read-only hunt for actual client code implementing the Gemini Tool Retrieval EAP
(defer_loading + tool_search meta-tool + gemini-flash-tool-retrieval model).
Ground truth per verified spec: endpoint `POST
https://generativelanguage.googleapis.com/v1beta/interactions`, model
`gemini-flash-tool-retrieval`, key var `GEMINI_API_KEY_2` (project
654595778272), tool shapes `{"type":"tool_search"}` + function declarations with
`defer_loading:true` (defer_loading without tool_search = 400), MCP servers as
`{"type":"mcp_server","name","url","defer_loading":true}`, response steps
`tool_search_call` / `tool_search_result` / `function_call` /
`mcp_server_tool_call` / `mcp_server_tool_result`.

## Verdict

**No public EAP client code exists anywhere reachable.** The Interactions API
*transport* (`/v1beta/interactions`, create/get/cancel/delete, agents,
environments, even `mcp_server_tool_call` step types) is fully public in
googleapis/js-genai and googleapis/python-genai. The *tool-retrieval deferral
layer* (`defer_loading`, `tool_search`, `ToolRetrieval`,
`gemini-flash-tool-retrieval`) exists only in the EAP-gated preview builds
(`google_genai-2.16.0` wheel / `google-genai-2.16.0.tgz` at
`gs://gemini-api-eap-sdks/toolRetrieval/`), which are a private fork sharing
the version number with a public release that lacks the feature. Real code
options: (a) fetch the preview builds from the EAP bucket (needs Google-issued
access; gsutil not installed on awrawr-pc), or (b) hand-roll the wire shapes in
sovereign-router-ts against `/v1beta/interactions` from the verified spec.
Live verification remains blocked only by billing (429, project prepay
depleted).

## 1. Public GitHub repos (fresh clones, 2026-09-17)

All three Apache-2.0. Zero hits for `defer_loading`, `deferLoading`,
`tool_search`, `ToolRetrieval`, `tool_search_call`, `gemini-flash-tool-retrieval`
in any of them.

### googleapis/js-genai @ e85d189 (2026-09-16)

- `src/types.ts:2662` — `export declare interface McpServer {` (public Live API
  surface, not EAP).
- `src/types.ts:2799` — `mcpServers?: McpServer[];` on Tool (public Live API).
- `src/gaos/sdk/interactions.ts` — Interactions client (create/get/cancel/
  delete) exists; no EAP terms inside.
- `src/interactions-private/**`, `src/interactions-deprecated/**` — present in
  tsconfig but contain none of the EAP terms.
- Public, no EAP.

### googleapis/python-genai @ 6669bb6 (2026-09-16)

Public Interactions API surface in `_gaos/` (Speakeasy-generated):

- `google/genai/client.py:100-105` — `def interactions(self) ->
  AsyncGeminiNextGenInteractions` (sync variant at :484-489).
- `google/genai/_gaos/interactions.py:534,554,574,594,614,634,654,674,694`
  (sync) and `:1992,:2012,:2032,:2052,:2072,:2092,:2112,:2132` (async) — doc
  examples POSTing `https://generativelanguage.googleapis.com/v1beta/interactions`
  with shapes:
  `{"model": "gemini-3.6-flash", "input": "Hello, how are you?"}`,
  `{"model": ..., "input": [{"type": "user_input", "content": [{"type": "text",
  "text": ...}]}]}`,
  `{"model": ..., "tools": [{"type": "function", "name": "get_weather",
  "description": ..., "parameters": {...}}], "input": "What is the weather like
  in Boston, MA?"}`,
  `{"agent": "antigravity-preview-05-2026", "input": "...", "environment":
  "remote"}`.
- `google/genai/_gaos/types/interactions/mcpservertoolcallstep.py:40,60-64` —
  `type: Literal["mcp_server_tool_call"]` (matches EAP step vocabulary).
- `google/genai/_gaos/types/interactions/mcpservertoolcalldelta.py:33,45-49` —
  same for streaming deltas.
- `google/genai/_gaos/google_genai.py:1456,1464` — `'mcp_server_tool_call'`,
  `'mcp_server_tool_result'` in step-type unions.
- `google/genai/_gaos/types/agents/agenttool.py:64` —
  `"mcp_server": interactions_mcpserver.MCPServer` (MCP server as agent tool).
- `google/genai/types.py:5241` — `class McpServer(_common.BaseModel)` (public
  generateContent/Live surface).
- `retrievalConfig` hits (e.g. `models.py:4011,4043`, `caches.py:865,894`) are
  the public `ToolConfig.retrieval_config` (unrelated legacy field), not EAP.
- `interactions` hits outside `_gaos` are replay-client/test plumbing.
- Transport public; tool-retrieval deferral absent. License Apache-2.0.

### google-gemini/gemini-cli @ 6a466a7 (2026-09-15)

- No EAP terms in code. Only prose mentions of "interactions" in docs
  (`docs/resources/quota-and-pricing.md`, keyboard-shortcuts, configuration).
- Apache-2.0. Nothing to use.

## 2. PyPI `google_genai-2.16.0` (public wheel, 532 files)

- Downloaded from PyPI (latest public is 2.24.0; 2.16.0 exists publicly).
- Contains `_gaos` Interactions API including `mcp_server_tool_call` step types
  (`google/genai/_gaos/types/interactions/mcpservertoolcallstep.py` etc.).
- Zero `defer_loading`, zero `tool_search`, zero `ToolRetrieval`, zero
  `gemini-flash-tool-retrieval` in any of the 532 files.
- Proves the EAP preview build at
  `gs://gemini-api-eap-sdks/toolRetrieval/google_genai-2.16.0-py3-none-any.whl`
  is a private fork: same filename/version, different bytes. The deferral
  feature has not been merged to public even in 2.24.0-era HEAD.

## 3. Local corpus near-misses (documented so nobody re-hunts them)

All unrelated to the Gemini EAP:

- `/home/toxic/sovereign/projects/tau-occupied-20260916/engine/vendor/oh-my-pi/packages/ai/src/providers/anthropic.ts:3552,3723,3756,3796,5068`
  and `anthropic-wire.ts:220` — `defer_loading` is Anthropic's own tool
  deferral in the vendored oh-my-pi provider. Same field name, different API.
- `/home/toxic/sovereign/bench-wt-tau/tau/...`, `/home/toxic/sovereign/projects/tau/...`
  (multiple copies) — same vendored Anthropic `deferLoading` ↔ `defer_loading`
  mapping; tests at `test/auth-gateway-anthropic-messages.test.ts:212`.
- `/home/toxic/projects/pi-upstream/packages/ai/src/api/openai-responses-shared.ts:131,344,376,389`
  and `anthropic-messages.ts:1311,1338` — `deferLoading` in OpenAI-Responses /
  Anthropic flavors.
- `/home/toxic/projects/openrouter_recon/typescript-sdk/src/models/namespacefunctiontool.ts:25,57,79,89`
  and `messagesrequest.ts:340,1163,1172` — OpenRouter SDK field alias
  `deferLoading` ↔ `"defer_loading"`.
- `/home/toxic/projects/experimental-crisis-2026/vllm-kernel/vllm/entrypoints/openai/engine/protocol.py:290,298-299`
  and `chat_completion/protocol.py:186` — vLLM OpenAI-engine field.
- `/home/toxic/projects/emergent-august/venv/lib/python3.12/site-packages/openai/types/responses/tool_search_tool.py:14-15`,
  `response_tool_search_call.py:27-28`, `response_input_param.py:203-204`, etc.
  — OpenAI's **public** Responses API `tool_search` / `tool_search_call`
  types. Same vocabulary, different vendor; not Gemini EAP.
- `/home/toxic/projects/antigravity-gateway-master/.../strings_all.txt:260910`
  — `retrievalConfig` in a protobuf strings dump; unrelated.
- Tau branch `wt-kimi-free-20260914` (`/home/toxic/sovereign/projects/tau`):
  `git grep` for all terms → zero hits.
- `/home/toxic/super-ralph`: zero hits for all terms.
- `~/Downloads`: zero hits (only legacy `[mcp_servers.*]` TOML in old
  monolith scripts).
- `gemini-api-dev` / `gemini-api-integration` skill dirs: empty stubs.

## 4. Our own artifacts (not upstream code)

- `/home/toxic/sovereign/docs/gemini-tool-retrieval.md`,
  `docs/gemini-tool-retrieval-reference.md` — request/response shapes transcribed
  from the EAP material Chris supplied, plus the 429 billing probe result.
- `/home/toxic/sovereign/tools/probe_gemini_eap.py` — probe built from that
  spec (exit 2 = billing blocked).

## Bottom line for the router work

The native Gemini Interactions path in sovereign-router-ts must be hand-rolled
from the verified spec: `POST /v1beta/interactions` with
`{"model": "gemini-flash-tool-retrieval", "input": ..., "tools":
[{"type": "tool_search"}, {"type": "function", "name": ..., "defer_loading":
true}, {"type": "mcp_server", "name": ..., "url": ..., "defer_loading":
true}]}`. No public SDK or CLI contains these shapes; the public python-genai
`_gaos` layer is useful only as a reference for the transport envelope
(create/get/cancel/delete, agent+environment fields, `mcp_server_tool_call`
step parsing). EAP preview builds remain the only source of real client code
and are bucket-gated.
