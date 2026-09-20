# whatsapp-mcp

WhatsApp Cloud API as an MCP server + inbound webhook, running on awrawr-pc
under pitchfork (mise sovereign) as daemon `whatsapp-mcp`.

- **MCP (StreamableHTTP)** on `127.0.0.1:25146/mcp` — local only, never exposed.
- **Webhook** `/webhook` — the only public path, via Tailscale funnel:
  `https://github-mcp-host.tailc9ac71.ts.net/whatsapp-webhook`
- **Health** `http://127.0.0.1:25146/health` (pitchfork `ready_http`).

## MCP tools

| Tool | Args | Notes |
|---|---|---|
| `send_text_message` | `to`, `body` | `to` = E.164 digits, e.g. `13035550100` |
| `send_template_message` | `to`, `template_name`, `language_code="en_US"`, `body_params=[...]` | approved templates; works outside the 24h window |
| `send_media_message` | `to`, `media`, `kind="image"`, `caption=""` | `kind`: image\|video\|audio\|document; `media` = https URL or uploaded media ID |
| `mark_message_read` | `message_id` | marks an inbound message read |

Free-form (non-template) messages only deliver inside the **24h customer-service
window** (opened when the user messages the business number). Outside it, use an
approved template.

## Inbound messages

Meta POSTs notifications to `/webhook`. Each inbound message is appended as one
JSON line to `/home/toxic/.shingle/whatsapp-inbox/YYYYMMDD.jsonl`:

```json
{"received_at": "...", "from": "13035550100", "type": "text",
 "message_id": "wamid....", "timestamp": "...", "message": {...}}
```

The fleet polls these files. `GET /webhook` answers Meta's verification handshake
(`hub.mode=subscribe`, constant-time verify-token compare).

## Setup (Meta side)

1. developers.facebook.com → create a Business app → add the **WhatsApp** product.
2. **API Setup / Getting Started**: note the **Phone number ID** and generate a
   **System User access token** with scopes `whatsapp_business_messaging`
   (+ `whatsapp_business_management`, `business_management` for admin).
   Use a permanent token, not the 24h test token.
3. **Configuration → Webhook**: Callback URL
   `https://github-mcp-host.tailc9ac71.ts.net/whatsapp-webhook`,
   Verify Token = the `WHATSAPP_VERIFY_TOKEN` value from the pitchfork env
   (see below). Subscribe to the **messages** field, then Verify & Save.
4. Message the business number once from your phone to open the 24h window for
   free-form test messages.

## Setup (awrawr-pc side)

Secrets live **only** in the pitchfork daemon env
(`/home/toxic/sovereign/pitchfork.toml`, `[daemons.whatsapp-mcp]`).
Nothing secret is committed to this repo.

```toml
[daemons.whatsapp-mcp]
run = "exec /home/toxic/.whatsapp-mcp-venv/bin/python /home/toxic/whatsapp-mcp/server.py"
dir = "/home/toxic/whatsapp-mcp"
mise = false
retry = true
ready_http = "http://127.0.0.1:25146/health"
auto = ["start"]
env = { WHATSAPP_API_TOKEN = "<paste system-user token>",
        WHATSAPP_PHONE_NUMBER_ID = "<phone number id>",
        WHATSAPP_VERIFY_TOKEN = "<generated>",
        WHATSAPP_MCP_PORT = "25146" }
```

Then reload pitchfork so it picks up the daemon. Funnel route (already added):

```
tailscale serve --https=443 /whatsapp-webhook http://127.0.0.1:25146/webhook
```

(`tailscale serve status` shows it; the existing `/` and `/mcp` routes are untouched.)

## Local test (no live key)

```bash
/home/toxic/.whatsapp-mcp-venv/bin/python -m pytest test_server.py -q
```

All tool handlers are unit-tested against a mocked Graph layer; the webhook
verification handshake is tested with good/bad tokens. Tools raise a clear
`RuntimeError` naming the missing env vars when the key isn't placed yet.

## Layout

- `server.py` — FastMCP tools + Starlette webhook/health/MCP app
- `test_server.py` — pytest suite (mocked HTTP)
- venv: `/home/toxic/.whatsapp-mcp-venv` (pinned `mcp<2` for the FastMCP v1 API)

Graph API: `https://graph.facebook.com/v23.0` (current per Meta's Get Started guide).
