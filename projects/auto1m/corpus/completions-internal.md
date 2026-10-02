# Completions internals — what serves this conversation

## Model identity (authoritative sources first)
- This conversation is served by **Muse Spark** (`meta/muse-spark`, provider Meta),
  from Meta's Muse model family (family launched 2026-04-08; Muse product live
  2026-09-08). Source: `~/docs/muse.md` + `muse.session_status`, which agree.
- Context window: **200,000 tokens**; compaction triggers at **150,000**.
- Sibling models in the family (from `~/docs/media.md`): **Muse Image** (image
  generation), **Muse Video** (video generation). Media/TTS/place-search go
  through their own sockets (`space-media.sock`, privsep `tts.sock`, …) — the
  chat model is one member of a per-capability routing, not the whole system.
- Per `muse.md`: internal identifiers in errors, logs, env vars, or files name
  **serving infrastructure, not model identity**. A UUID somewhere is a host or
  route ID, not a secret model name. This doc honors that distinction.

## The completions path (observed, from inside the cell)
Terminology (2026-09-19, per Chris): this doc calls the model-serving path
"completions". The runtime's identifiers say "inference"
(`JARVIS_INFERENCE_PROXY_SOCK`, `space-inference.sock`,
`inference_workload_class`) — quoted verbatim wherever they appear; whether
that wording is deliberate or loose is unverified, so this doc doesn't judge
it, it just records Chris's preferred term.
The cell never talks to a model directly. Completions flow through the parent:

- `JARVIS_INFERENCE_PROXY_SOCK=/run/hatch/proxy/inference.sock` — the cell is
  told the completions proxy lives here (identifier quoted verbatim — the
  "inference" in the name is the runtime's own wording), but
  **`/run/hatch/proxy/` does not exist**
  in the cell's view. The socket is parent-side (different mount namespace or
  materialized per-request). The cell holds the address, not the door.
  2026-09-20: `/proc/net/unix` (kernel-global) shows 6 entries bound to that
  path, so the listener is real — just not in this cell's namespace, and not
  connectable from here.
- `JARVIS_INFERENCE_HOSTNAME=e3efc353-…` — UUID-format serving-infrastructure
  identifier (see the warning above; not a model name, not quoted in full here
  because it buys nothing).
- `/run/hatch/sandbox/space-inference.sock` — the *sandboxed* completions space:
  world-writable, visible, one of four `space-*` capability sockets. This is
  the capability-shaped variant (completions as a boxed tool), distinct from the
  proxy path that serves the main conversation. Wire protocol identified by
  live fuzzing — see below.
- Same pattern as everything else in this runtime: socket-per-capability, the
  parent holds the power, the cell holds references.

## Wire protocol: sandbox completions socket (live-fuzzed 2026-09-20)
Per Chris's explicit directive ("we do want secret shaped and we do want run
live fuzz"), 7 bounded, non-destructive probes were run against
`/run/hatch/sandbox/space-inference.sock` (fresh connect → send → 4s read
timeout → close). Exact log:

| # | sent (exact bytes) | result |
|---|---|---|
| 1 | *(nothing; 2s banner window)* | accepted, no banner, held open ≥6s — server never speaks first |
| 2 | `GET / HTTP/1.0\r\n\r\n` | `ECONNRESET` — not HTTP |
| 3 | `POST / HTTP/1.1\r\nHost: probe\r\nContent-Length: 0\r\n\r\n` | `ECONNRESET` — not HTTP |
| 4 | `\n` | held open, no response — not newline-delimited |
| 5 | `\x00\x00\x00\x00` | immediate clean EOF (`recv` → `b''`) — zero-length frame, polite hangup |
| 6 | `\x00\x00\x00\x10` (claims 16, sends 0 payload bytes) | read timeout — server waits for the 16 payload bytes |
| 7 | `\x00\x00\x00\x04` + `ping` | consumed exactly 4 bytes, then immediate clean EOF — garbage payload, polite hangup |

**Verdict: 4-byte big-endian unsigned length prefix + payload.** Big-endian,
not little: a LE read of `\x00\x00\x00\x04` would be 67,108,864 and the server
would have waited; it closed right after 4 bytes. Zero-length or unparseable
payloads get a graceful close; HTTP-shaped input gets a RST. No banner, no
error frames observed.

Safety: every probe went to the **sandbox** socket, which is not the live
conversation's path (that uses the parent-side proxy socket, unreachable from
the cell). The live conversation was never at risk. No valid completions
request was crafted or sent — payload semantics deliberately left unknown.

## Request anatomy (this turn's trace context + session_status)
`JARVIS_TRACE_CONTEXT` is a JSON envelope on every request. Structural summary
(values redacted to shapes):

- Identity: `model: "Muse Spark"`, `agent_id`, `session_id`, `thread_id`,
  `message_id`, `app_id`, `app_version` (7.0.0.25.163 here), `device_id`.
- Routing: `request_origin: "external.hatch_chat"`, `workload: "runtime_chat"`,
  `inference_workload_class: "interactive"`, `lane: "user_facing"`,
  `request_mode: "production"`, `channel: main`.
- Policy: `policy_subject` (was `tool.exec` on the observed turn — the policy
  engine evaluates the request under the subject performing it), `exec_chain`
  (depth 0 here; subagents nest deeper).
- Lifecycle: `enqueued_at_ms` / `dequeued_at_ms` / `request_received_at_ms` /
  `timeline_anchor_at_ms`, `requeued_after_restart`, plus a full set of
  scheduling fields (`schedule_id`, `scheduled_for_utc`, …) — all null on an
  interactive turn, populated on cron/hook-driven runs.
- **Curiosity, unexplained:** `request_id` reads `req:fallback:…` (seen in both
  session_status and trace context). Meaning unknown — could be a routing
  namespace or an actual fallback path. Worth watching whether it persists
  across turns; no story invented here.

## Secret-shaped material (shapes only — values never recorded)
Inspected 2026-09-20 from `/tmp/secrets/env.txt` + `/tmp/secrets/trace.json`
(per Chris's directive). Shapes, not values:

- `*_PROXY` (upper- and lowercase): `http://<user>:<32 lowercase hex>@hatch-egress-proxy:3128` (77 chars) — proxy userinfo credential.
- `JARVIS_HATCHLING_ID`, `JARVIS_INFERENCE_HOSTNAME`, `JARVIS_SESSION_ID`:
  UUID-format, 36 chars — infrastructure identifiers, not model names.
- `JARVIS_TOOL_CALL_ID`: `call_` + 32 lowercase hex (37 chars).
- `JARVIS_TIER`: 4 chars.
- `JARVIS_RUNTIME_CONTEXT_TOKEN`: present in env, but the runtime's own output
  layer redacts it (`<redacted>`) before it reaches tool output — shape
  unmeasurable from inside the cell. Noted, not pursued.
- `JARVIS_TRACE_CONTEXT`: structural fields only (identity, routing, policy,
  lifecycle, scheduling as above). No secret-shaped values beyond the ID
  shapes listed here.
- Nothing else `*TOKEN*` / `*SECRET*` / `*KEY*`-shaped in env beyond the above.

## Workload classes and lanes (completions)
`interactive` / `user_facing` is this turn's classification. The names imply
siblings — background agent runs (the ~96+/day crons, hooks, feed pulses)
almost certainly carry a different workload class and lane. Not yet observed
firsthand; if you want it, capture `JARVIS_TRACE_CONTEXT` on a scheduled run
and compare.

## The surrounding socket zoo (observed 2026-09-20)
The parent exposes one socket per function; inference is one among many.
Cell-visible listeners (`ss -x -l`), all `srw-rw-rw-` (world-writable):
`space-inference.sock`, `space-web-search.sock`, `space-privileged.sock`,
`space-media.sock`, `sandbox-api/api.sock`. Env-advertised but parent-side:
`JARVIS_SENTINEL_HTTP_API_SOCKET`, `JARVIS_SECURITY_SOCK`,
`JARVIS_MEMORY_SOCK`, `JARVIS_TELEMETRY_PROXY_SOCK`, `JARVIS_STEFI_PROXY_SOCK`,
`JARVIS_AUTHD_SOCK`, `JARVIS_RESCUE_SIGNAL_SOCK`, three
`JARVIS_EGRESS_APPROVAL_*_SOCK`, `JARVIS_DAEMON_EGRESS_APPROVAL_SOCK`,
plus `JARVIS_HATCHLING_ID`, `JARVIS_TIER`, `JARVIS_VM_COMPUTE_REGION`,
`JARVIS_VM_DATA_REGION`, `JARVIS_CD_CHANNEL` / `JARVIS_CD_PINNED`.
No established connections to `space-inference.sock` at observation time.

## Observed vs inferred
- **Observed:** model identity (two agreeing sources), context window figures,
  env var names, the absent `/run/hatch/proxy/` (with kernel-global proof the
  listener exists parent-side), trace-context key anatomy,
  the `req:fallback:` prefix, sibling model names from docs,
  **sandbox completions wire framing** (u32-BE length prefix; probe log above),
  **secret value shapes** (proxy userinfo, UUIDs, `call_`-prefixed tool-call
  IDs; runtime-redacted context token).
- **Inferred (medium):** background runs carry different workload classes
  (naming implies it; not yet captured). The proxy socket likely speaks the
  same framing as the sandbox socket (unverified — unreachable from the cell).
- **Unknown:** what `fallback` means; payload semantics of the completions
  protocol (deliberately not probed further).

## Boundaries (2026-09-20 fuzz pass — what was and wasn't done)
- **Did** run 7 benign probes against `space-inference.sock` (banner grab,
  HTTP-shaped, newline, zero-length, length-prefix confirmations) per Chris's
  explicit directive. Framing identified; exact bytes logged above.
- **Did** inspect secret-shaped env/trace material as shapes only — no raw
  values reproduced anywhere (not in chat, files, or this doc).
- **Did not** craft or send a valid completions request — payload semantics
  deliberately left unknown.
- **Did not** touch the proxy socket: unreachable from this cell's mount
  namespace, so the live conversation's path was never at risk.
- **Did not** attempt any credential exfiltration; `JARVIS_RUNTIME_CONTEXT_TOKEN`
  is redacted by the runtime layer itself before reaching tool output.
- **Did not** run `subscription-status`: it's the source of truth for tier/plan,
  but only to be used when the user asks about subscription.
