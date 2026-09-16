# Kimi transport for collab-web — contract map & design notes

**Status:** implemented, additive. `src/transports/` is a new module; the only
touch to existing code is an *optional* 3rd constructor parameter on
`GuestClient` (behavior-preserving for all existing callers).

**Goal:** make Tau's *existing* collab-web UI drive Moonshot's kimi-code
backend (kap-server) instead of a pi-coding-agent collab relay — no parallel
WebUI, no iframe shell. The loopback gateway (`tau-extensions@omp-kimi-webui`)
remains a valid deployment target: this adapter speaks the kap-server protocol
at a configurable `baseUrl`, so it works against kap-server directly
(`http://127.0.0.1:58627`) *or* through the gateway proxy, which exposes the
same paths with token-swap auth.

Sources: `kimi-code/packages/kap-server/src` (read-only, MIT),
`tau/engine/packages/collab-web/src`, `tau/engine/packages/wire/src/index.ts`
(`@oh-my-pi/pi-wire`).

## 1. kap-server contract (concrete)

**Base:** `http://127.0.0.1:58627` (default), everything under `/api/v1`.
**REST auth:** `Authorization: Bearer <token>` (`middleware/auth.ts`).
Bypassed only for `OPTIONS`, `GET /api/v1/healthz`, and non-`/api/` web assets.
**REST envelope:** `{code: 0, msg: "success", data, request_id}`
(`protocol/envelope.ts`).
**WS:** `/api/v1/ws`, subprotocol `kimi-code.bearer.<token>`
(`transport/ws/bearerProtocol.ts`, `transport/ws/v1/registerWsV1.ts`).
Client→server JSON frames `{type, id?, payload?}`; server→client
`EventEnvelope` `{type, seq, epoch?, session_id?, timestamp, payload}` whose
`payload` is the agent event (`protocol/events-zod.ts`).

| Operation | Method & path |
|---|---|
| Create session | `POST /api/v1/sessions` `{title?, workspace_id?}` |
| Get session | `GET /api/v1/sessions/{session_id}` |
| List/get messages | `GET /api/v1/sessions/{session_id}/messages?before_id=&after_id=&page_size=&role=` → `{items: Message[], has_more}` |
| Submit prompt | `POST /api/v1/sessions/{session_id}/prompts` `{content: [{type:"text",text}…], …}` |
| Abort prompt | `POST /api/v1/sessions/{session_id}/prompts/{prompt_id}:abort` |
| Steer queued prompts | `POST /api/v1/sessions/{session_id}/prompts::steer` `{prompt_ids}` |
| Pending approvals | `GET /api/v1/sessions/{session_id}/approvals?status=pending` → `{items: ApprovalRequest[]}` |
| Resolve approval | `POST /api/v1/sessions/{session_id}/approvals/{approval_id}` `{decision: approved\|rejected\|cancelled, scope?, feedback?}` |
| Pending questions | `GET /api/v1/sessions/{session_id}/questions?status=pending` |
| Transcript | `GET /api/v1/sessions/{session_id}/transcript` (agent-scoped ops, not byte ranges) |
| Workspace | `GET /api/v1/workspaces/{workspace_id}` → `{id, root, name, …}` |
| WS subscribe | send `{type:"subscribe", id, payload:{session_ids:[…]}}` → `ack` |

**Session** (`protocol/session.ts`): `{id, workspace_id, title, created_at,
busy, main_turn_active?, pending_interaction?: none|approval|question,
last_turn_reason?, current_prompt_id?, …}`.

**Message** (`protocol/message.ts`): `{id, session_id, role:
user|assistant|tool|system, content: […], created_at, prompt_id?}`; content
blocks: `text{text}`, `tool_use{tool_call_id, tool_name, input}`,
`tool_result{tool_call_id, output, is_error?}`, `image{source:
{kind: base64|url|file|…}}`, …

**Streaming events** (`protocol/events-zod.ts`, delivered via WS when subscribed):
`assistant.delta{delta}`, `thinking.delta{delta}`, `tool.call.started
{toolCallId, name, args}`, `tool.call.delta{argumentsPart}`,
`tool.progress{toolCallId, update}`, `tool.result{toolCallId, output, isError}`,
`turn.started{origin, prompt?}`, `turn.ended{reason}`, `prompt.submitted /
completed / aborted`, `event.session.work_changed{busy, pending_interaction}`,
`compaction.*`, `subagent.spawned/started/completed/failed`, …

## 2. collab-web contract (what the UI consumes)

`GuestClient` (`src/lib/client.ts`) owns a `CollabSocket`
(`src/lib/socket.ts`) — an AES-GCM encrypted relay socket speaking
`@oh-my-pi/pi-wire` frames — and folds `HostFrame`s into an immutable
`GuestSnapshot` (transcript `entries`, streaming ghost `stream`,
`activeTools`, `uiRequest`, `agents`, …).

**HostFrame** (`@oh-my-pi/pi-wire`): `welcome{header, state, agents,
entryCount, readOnly}` → `snapshot-chunk{entries, final}` → live
`entry{entry}` / `event{event}` / `state{state}` / `agents{agents}` /
`ui-request{request}` / `ui-request-end{reqId}` / `transcript{…}` /
`bye{reason}` / `error{message}`.

**AgentEvent** (handled subset): `message_start/update/end` — *update carries
the FULL accumulating message*; `tool_execution_start/update/end`;
`agent_start/agent_end`; `notice`; `auto_compaction_*`; `auto_retry_*`.

**GuestFrame**: `hello`, `prompt{text, images?}`, `ui-response{reqId, value}`,
`abort`, `agent-cmd{chat|kill|revive}`, `fetch-transcript{reqId, agentId,
fromByte}`.

## 3. Mapping (kap-server → pi-wire)

| kap-server | pi-wire | notes |
|---|---|---|
| `GET session` + `GET workspace` | `welcome{header, state, agents, entryCount}` | `SessionHeader{id, title, timestamp, cwd: workspace.root}`; `SessionState{isStreaming: session.busy, cwd, …}`; one `main` `AgentSnapshot` |
| `GET messages` (paged, sorted oldest-first) | `snapshot-chunk{entries, final:true}` | `user`→`UserMessage`; `assistant`→`AssistantMessage` (`tool_use`→`ToolCallContent`); `tool`→one `ToolResultMessage` entry per `tool_result` block; `system`→dropped |
| `assistant.delta` + `thinking.delta` | `message_start` → `message_update`* | adapter accumulates deltas; every `message_update` carries the **full** message (text + thinking blocks), matching pi-wire semantics |
| `turn.started` / `prompt.submitted` | `agent_start` (+ `state{isStreaming:true}`) | |
| `turn.ended` / `prompt.completed` / `prompt.aborted` | `message_end` (if streaming) → `agent_end` → `state{isStreaming:false}` → fresh `entry` frames | final messages are re-read via `GET messages?after_id=` — no delta-reconstruction drift |
| `tool.call.started{name, args}` | `tool_execution_start{toolCallId, toolName, args}` | adapter keeps a `toolCallId → {name, args}` map for the update/end frames |
| `tool.progress{update}` | `tool_execution_update{partialResult: update}` | |
| `tool.result{output, isError}` | `tool_execution_end{result: output, isError}` | |
| `event.session.work_changed{busy, pending_interaction}` | `state{isStreaming: busy}`; `approval`→ approval poll | |
| `GET approvals?status=pending` item | `ui-request{kind:"select", title: "<tool> — <action>", options:[approved,rejected,cancelled]}` | `ui-response{value}` → `POST approvals/{id} {decision: value}` → `ui-request-end` |
| `compaction.started/completed` | `auto_compaction_start/end` | |
| `error` | `notice{level:"error"}` | |

Guest → kap-server:

| GuestFrame | kap-server call |
|---|---|
| `prompt{text, images?}` | `POST prompts` `{content:[{type:"text",text}, {type:"image",source:{kind:"base64",…}}…]}` |
| `abort` | `POST prompts/{current_prompt_id}:abort` |
| `ui-response{reqId, value}` | `POST approvals/{approval_id} {decision}` (reqId→approval_id map) |
| `agent-cmd` | unsupported → `notice` info frame |
| `fetch-transcript` | unsupported → `transcript` frame with `error` (kap-server transcript is agent-scoped ops, not byte ranges) |
| `hello` | no-op (bootstrap already ran) |

## 4. Mismatches & how they're handled

1. **Auth.** Relay uses AES-GCM room keys; kap-server uses bearer tokens
   (REST header, WS subprotocol `kimi-code.bearer.<token>`). The token is a
   constructor option; never logged. When running behind the loopback
   gateway, the same code path works — the gateway does the token swap.
2. **Streaming protocol.** pi-wire `message_update` carries the full message;
   kap-server sends delta strings. `KimiStreamAccumulator` bridges this.
   Thinking arrives as a separate event stream and is merged into the
   assistant message as `thinking` content blocks.
3. **Approval UX.** kap-server approvals are per-tool-call server state with
   expiry; pi-wire `ui-request` is a transient select/editor prompt. Mapped to
   `select` with the three kap-server decisions as options. The adapter polls
   `GET approvals?status=pending` on `work_changed` *and* on a 2s timer while
   `pending_interaction === "approval"` (covers approvals already pending at
   attach time); resolved/expired approvals yield `ui-request-end`.
4. **Questions.** kap-server questions (`single`/`multi`/`other` answers,
   `protocol/question.ts`) have no direct pi-wire shape; currently surfaced
   only via `pending_interaction` state. **Gap:** map to `select`/`editor`
   `ui-request`s (needs answer-schema round-trip design).
5. **Subagents.** kap-server `subagent.*` events exist but are not yet mapped
   to `agents` frames / `bus` channels. **Gap:** subagent panel will show only
   the main agent.
6. **Transcript fetch.** `fetch-transcript` (byte-range JSONL) has no
   kap-server equivalent; returns an error frame. **Gap** if the AgentsPanel
   transcript view is needed for kimi sessions.
7. **Frame transport.** No encryption layer — kap-server is loopback (or the
   gateway), unlike the relay's AES-GCM. Fine for local use; do not point at
   an untrusted remote kap-server.
8. **Reconnect.** `KimiTransport` retries WS with exponential backoff like
   `CollabSocket`, but bootstrap is REST (session/messages re-fetched);
   in-flight deltas across a reconnect are lost and recovered via the
   `after_id` message refresh on the next `turn.ended`.

## 5. What was implemented

- `src/transports/types.ts` — `CollabTransport` interface (structural; `CollabSocket` conforms).
- `src/transports/kimi-map.ts` — pure mapping functions + `KimiStreamAccumulator` + WS/REST request builders.
- `src/transports/kimi.ts` — `KimiTransport implements CollabTransport`
  (REST bootstrap → `welcome`/`snapshot-chunk`; WS subscribe → live frames;
  guest actions → kap-server calls; approval polling).
- `src/transports/index.ts` — re-exports.
- `src/lib/client.ts` — **one additive change**: `GuestClient` constructor
  takes an optional 3rd `transport?: CollabTransport` (defaults to
  `CollabSocket`; existing call sites and tests unchanged).
- `test/transports/kimi-map.test.ts` — 15 unit tests over the mapping layer.
- This doc (`KIMI_TRANSPORT.md`).

Not wired into any UI entry point yet (`app.tsx`/`ConnectScreen` still build
`GuestClient` from collab links) — that's the deliberate next step: add a
"connect to kimi" screen that constructs `new GuestClient("", name,
new KimiTransport({baseUrl, token, sessionId}))`.

## 6. Verification

- `bun test test/transports/kimi-map.test.ts` — 15 pass.
- `bun test --parallel` (full package) — run before push.
- `tsgo -p tsconfig.json --noEmit` — run before push.
- Live kap-server round-trip (create session, stream deltas, resolve an
  approval) is **not** covered — needs a running kap-server + token; flagged
  as the first integration test to write.
