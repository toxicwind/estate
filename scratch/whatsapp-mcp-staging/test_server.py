"""Unit tests for whatsapp-mcp — HTTP layer is mocked, no live key needed."""
import json
import os
import sys

import anyio
import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.dirname(__file__))
import server  # noqa: E402

captured = {}


async def fake_graph_post(payload: dict) -> dict:
    captured["payload"] = payload
    return {"messages": [{"id": "wamid.TEST123"}]}


@pytest.fixture(autouse=True)
def _patch(monkeypatch):
    monkeypatch.setattr(server, "_graph_post", fake_graph_post)
    monkeypatch.setenv("WHATSAPP_API_TOKEN", "test-token")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123456789")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "verify-secret")
    captured.clear()


def run(coro):
    return anyio.run(lambda: coro)


def test_send_text_message():
    out = run(server.send_text_message("13035550100", "hello"))
    p = captured["payload"]
    assert p["to"] == "13035550100"
    assert p["type"] == "text"
    assert p["text"]["body"] == "hello"
    assert p["messaging_product"] == "whatsapp"
    assert json.loads(out)["messages"][0]["id"] == "wamid.TEST123"


def test_send_template_message():
    run(server.send_template_message("13035550100", "hello_world", "en_US", ["Chris", "42"]))
    p = captured["payload"]
    assert p["type"] == "template"
    assert p["template"]["name"] == "hello_world"
    assert p["template"]["language"] == {"code": "en_US"}
    comps = p["template"]["components"]
    assert comps[0]["parameters"] == [
        {"type": "text", "text": "Chris"},
        {"type": "text", "text": "42"},
    ]


def test_send_media_message_url_and_id():
    run(server.send_media_message("13035550100", "https://example.com/a.jpg", "image", "cap"))
    p = captured["payload"]
    assert p["type"] == "image"
    assert p["image"] == {"link": "https://example.com/a.jpg", "caption": "cap"}
    run(server.send_media_message("13035550100", "987654321", "document"))
    p = captured["payload"]
    assert p["type"] == "document"
    assert p["document"] == {"id": "987654321"}
    with pytest.raises(ValueError):
        run(server.send_media_message("13035550100", "x", "sticker"))


def test_mark_message_read():
    run(server.mark_message_read("wamid.INBOUND1"))
    p = captured["payload"]
    assert p["status"] == "read"
    assert p["message_id"] == "wamid.INBOUND1"
    assert p["messaging_product"] == "whatsapp"


def test_missing_config_errors(monkeypatch):
    monkeypatch.delenv("WHATSAPP_API_TOKEN", raising=False)

    async def go():
        return await server._config()

    with pytest.raises(RuntimeError, match="WHATSAPP_API_TOKEN"):
        anyio.run(go)


def _client(tmp_path, monkeypatch):
    monkeypatch.setenv("WHATSAPP_INBOX_DIR", str(tmp_path / "inbox"))
    import importlib

    importlib.reload(server)
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "verify-secret")
    app = server.Starlette(
        routes=[
            server.Route("/webhook", server.webhook_verify, methods=["GET"]),
            server.Route("/webhook", server.webhook_receive, methods=["POST"]),
        ]
    )
    return TestClient(app)


def test_webhook_verify_ok(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    r = c.get(
        "/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "verify-secret",
                "hub.challenge": "CHALLENGE123"},
    )
    assert r.status_code == 200
    assert r.text == "CHALLENGE123"


def test_webhook_verify_bad_token(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    r = c.get(
        "/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "wrong",
                "hub.challenge": "CHALLENGE123"},
    )
    assert r.status_code == 403


def test_webhook_receive_stores_jsonl(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    body = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "13035550100",
                                    "id": "wamid.IN1",
                                    "timestamp": "1726000000",
                                    "type": "text",
                                    "text": {"body": "ping"},
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }
    r = c.post("/webhook", json=body)
    assert r.status_code == 200
    inbox = tmp_path / "inbox"
    files = list(inbox.glob("*.jsonl"))
    assert len(files) == 1
    rec = json.loads(files[0].read_text().strip().splitlines()[0])
    assert rec["from"] == "13035550100"
    assert rec["message_id"] == "wamid.IN1"
    assert rec["message"]["text"]["body"] == "ping"
    assert "received_at" in rec


def test_webhook_receive_ignores_non_whatsapp(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    r = c.post("/webhook", json={"object": "page"})
    assert r.status_code == 200
