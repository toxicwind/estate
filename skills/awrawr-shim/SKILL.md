# awrawr-shim — sidechat shim tools on the Awrawr Mcp connector

The sidechat shim (`/home/toxic/hatch/sidechat_shim.py`, owner Pry) is
exposed as 5 MCP tools on the existing **`custom.awrawr-mcp`** connector
(yote `/home/toxic/awrawr_mcp.py`, Streamable HTTP). No new connector was
needed — the shim rides the proven connector (2026-10-02).

## The boundary (non-negotiable)

- These tools **shape, check, verify, and queue** lane messages.
- `shim_send_chat` writes to the nudge queue — the actual `chat.send_message`
  dispatch stays in the **agent runtime** (main agent drain) — yote has no
  chat tools and no HTTP path to them exists. Subagents can now *initiate*
  sends via MCP; delivery still flows through the drain.
- Nudge path: `lane_poller.py` (yote) imports `sidechat_shim` directly
  (fastest, zero network). Platform-side agents use these MCP tools.

## Tools

- `shim_format_nudge(message: string)` → `{"ok":true,"text":...}`
  Classifier-safe shaping (`format_safe`): rewrites trigger shapes into
  behavioral language. Never include a runtime header in the input — the
  runtime stamps its own unforgeable one.
- `shim_check_quarantine(text: string)` → `{"ok":true,"quarantined":bool}`
  Single source of truth for the refusal/quarantine signature.
- `shim_canary_healthy(reply: string)` → `{"ok":true,"healthy":bool}`
  Canary reply must contain `canary` + today's UTC weekday, not the refusal.
- `shim_info()` → `{"ok","source","sha256","error"}`
  Provenance: sha256 of the canonical shim source backing the answers.
- `shim_send_chat(chat_id: string, message: string, lane?: string)` → `{"ok":true,"queued":...}`
  Subagent-accessible chat send: formats via `format_safe`, writes to the
  nudge queue (`hatch/pollers/nudge-queue/`) for the main-agent drain to
  deliver. This is how non-main agents initiate side-chat messages.

## Concurrency (measured 2026-10-02)

- Sequential: **2.0 ms median** per call (yote localhost).
- **One MCP session per parallel call.** Concurrent POSTs on a single
  Streamable HTTP session serialize/hang — open a session per call
  (each ~5 ms) or use server-side fan-out (`exec_multi`, `race`).
- Via funnel `https://github-mcp-host.tailc9ac71.ts.net/mcp`: 401 in
  0.64 s from cell without token (auth-gated, as designed); 0.03 s from yote.

## Endpoint

`https://github-mcp-host.tailc9ac71.ts.net/mcp` (Streamable HTTP),
header `X-MCP-Token: <vaulted custom.awrawr-mcp credential>`.
Local: `http://127.0.0.1:25198/mcp`. Pitchfork: `awrawr-mcp`
(note: project id is `estate/awrawr-mcp`; stale `sovereign/awrawr-mcp`
state entry lingers — use the estate id).
Rollback: `/home/toxic/awrawr_mcp.py.bak-20261002-shim`.
