#!/usr/bin/env python3
"""whatsapp-mcp — WhatsApp Cloud API MCP server + inbound webhook.

Runs on awrawr-pc under pitchfork (mise sovereign) as daemon `whatsapp-mcp`.

Topology:
  * MCP (StreamableHTTP) and /health bind 127.0.0.1 only — never funneled.
  * /webhook is the ONLY public path, via Tailscale funnel
    https://github-mcp-host.tailc9ac71.ts.net/whatsapp-webhook -> 127.0.0.1:PORT/webhook

Environment (pitchfork daemon env; never committed to git):
  WHATSAPP_API_TOKEN        Meta System User token (whatsapp_business_messaging scope)
  WHATSAPP_PHONE_NUMBER_ID  WhatsApp Business phone number ID
  WHATSAPP_VERIFY_TOKEN     Webhook verify token (self-generated; entered in Meta dashboard)
  WHATSAPP_MCP_PORT         Local port (default 25146)

Inbound messages are appended as JSONL to
/home/toxic/.shingle/whatsapp-inbox/YYYYMMDD.jsonl for the fleet to poll.
"""

import hashlib  # noqa: F401  (kept for future X-Hub-Signature-256 support)
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import anyio
import httpx
import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route

GRAPH_VERSION = "v23.0"  # current per Meta Get Started guide, 2026-09
GRAPH_HOST = "https://graph.facebook.com"
INBOX_DIR = Path(os.environ.get("WHATSAPP_INBOX_DIR", "/home/toxic/.shingle/whatsapp-inbox"))
PORT = int(os.environ.get("WHATSAPP_MCP_PORT", "25146"))
SERVICE = "whatsapp-mcp"

log = logging.getLogger(SERVICE)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _config() -> tuple[str, str]:
    """Read live credentials. Raises a clear error when Chris hasn't placed them yet."""
    token = os.environ.get("WHATSAPP_API_TOKEN", "").strip()
    phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    if not token or not phone_id:
        raise RuntimeError(
            "WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID are not set. "
            "Place them in the pitchfork env for daemon 'whatsapp-mcp' "
            "(/home/toxic/sovereign/pitchfork.toml) and reload pitchfork."
        )
    return token, phone_id


async def _graph_post(payload: dict) -> dict:
    """POST one message payload to the Cloud API. Single HTTP seam — mocked in tests."""
    token, phone_id = _config()
    url = f"{GRAPH_HOST}/{GRAPH_VERSION}/{phone_id}/messages"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
        )
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text[:2000]}
    if resp.status_code >= 400:
        raise RuntimeError(f"Graph API HTTP {resp.status_code}: {json.dumps(data)[:500]}")
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(f"Graph API error: {json.dumps(data['error'])[:500]}")
    return data


mcp = FastMCP(
    SERVICE,
    host="127.0.0.1",
    port=PORT,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
    ),
)


@mcp.tool()
async def send_text_message(to: str, body: str) -> str:
    """Send a WhatsApp text message. `to`: E.164 digits, e.g. 13035550100
    (no '+', no spaces). Outside the 24h customer-service window only
    approved template messages go through."""
    data = await _graph_post(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": body[:4096], "preview_url": False},
        }
    )
    return json.dumps(data)


@mcp.tool()
async def send_template_message(
    to: str,
    template_name: str,
    language_code: str = "en_US",
    body_params: list[str] | None = None,
) -> str:
    """Send an approved WhatsApp template message (works outside the 24h window).
    `body_params` fills the template's {{1}}, {{2}}, ... body placeholders in order."""
    parameters = [{"type": "text", "text": p} for p in (body_params or [])]
    data = await _graph_post(
        {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": [{"type": "body", "parameters": parameters}] if parameters else [],
            },
        }
    )
    return json.dumps(data)


@mcp.tool()
async def send_media_message(
    to: str, media: str, kind: str = "image", caption: str = ""
) -> str:
    """Send a WhatsApp media message. `kind`: image|video|audio|document.
    `media`: an https URL (sent as link) or an uploaded media object ID."""
    if kind not in ("image", "video", "audio", "document"):
        raise ValueError("kind must be one of: image, video, audio, document")
    media_obj = {"link": media} if media.startswith("https://") else {"id": media}
    if caption:
        media_obj["caption"] = caption[:1024]
    data = await _graph_post(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": kind,
            kind: media_obj,
        }
    )
    return json.dumps(data)


@mcp.tool()
async def mark_message_read(message_id: str) -> str:
    """Mark an inbound WhatsApp message as read (message_id from the webhook inbox)."""
    data = await _graph_post(
        {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
    )
    return json.dumps(data)


# --- inbound webhook (Meta -> us) -------------------------------------------


async def webhook_verify(request: Request) -> PlainTextResponse:
    """Meta's verification handshake: GET with hub.mode=subscribe."""
    q = request.query_params
    expected = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")
    if (
        q.get("hub.mode") == "subscribe"
        and expected
        and hmac.compare_digest(q.get("hub.verify_token", ""), expected)
    ):
        return PlainTextResponse(q.get("hub.challenge", ""))
    return PlainTextResponse("forbidden", status_code=403)


async def webhook_receive(request: Request) -> PlainTextResponse:
    """Receive message notifications; append to the fleet-pollable JSONL inbox."""
    try:
        body = await request.json()
    except Exception:
        return PlainTextResponse("bad request", status_code=400)
    if body.get("object") != "whatsapp_business_account":
        return PlainTextResponse("ignored")  # 200: don't make Meta retry junk
    received_at = datetime.now(timezone.utc).isoformat()
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    count = 0
    try:
        with open(INBOX_DIR / f"{day}.jsonl", "a") as f:
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for msg in value.get("messages", []):
                        rec = {
                            "received_at": received_at,
                            "from": msg.get("from"),
                            "type": msg.get("type"),
                            "message_id": msg.get("id"),
                            "timestamp": msg.get("timestamp"),
                            "message": msg,
                        }
                        f.write(json.dumps(rec) + "\n")
                        count += 1
    except Exception as e:
        log.exception("inbox write failed: %s", e)
        return PlainTextResponse("error", status_code=500)
    log.info("webhook: stored %d message(s)", count)
    return PlainTextResponse("ok")


async def health(_request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "service": SERVICE,
            "port": PORT,
            "graph": f"{GRAPH_HOST}/{GRAPH_VERSION}",
            "configured": bool(os.environ.get("WHATSAPP_API_TOKEN", "").strip())
            and bool(os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "").strip()),
            "time": datetime.now(timezone.utc).isoformat(),
        }
    )


async def _serve() -> None:
    mcp_app = mcp.streamable_http_app()
    app = Starlette(
        routes=[
            Route("/health", health),
            Route("/webhook", webhook_verify, methods=["GET"]),
            Route("/webhook", webhook_receive, methods=["POST"]),
            Mount("/mcp", app=mcp_app),
        ]
    )
    await uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="info")
    ).serve()


if __name__ == "__main__":
    anyio.run(_serve)
