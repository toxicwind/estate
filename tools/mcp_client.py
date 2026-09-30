"""Minimal MCP client for gatehouse (:25127).

Session flow (2024-11-05 spec):
  1. POST initialize       → server returns Mcp-Session-Id header
  2. POST notifications/initialized  (optional)
  3. POST tools/list       with Mcp-Session-Id header
  4. POST tools/call       with Mcp-Session-Id header
"""
import json, urllib.request, urllib.error, uuid
from typing import Any

ENDPOINT = "http://127.0.0.1:25127/mcp"

class Session:
    def __init__(self, endpoint: str = ENDPOINT):
        self.endpoint = endpoint
        self.sid = None

    def _post(self, method: str, params: dict | None = None, notif: bool = False) -> dict:
        body = {"jsonrpc":"2.0", "method": method}
        if not notif:
            body["id"] = str(uuid.uuid4())
        if params is not None:
            body["params"] = params
        req = urllib.request.Request(self.endpoint,
            data=json.dumps(body).encode(), method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        if self.sid:
            req.add_header("Mcp-Session-Id", self.sid)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                if not self.sid:
                    self.sid = r.headers.get("Mcp-Session-Id")
                raw = r.read().decode()
                if not raw.strip(): return {}
                try: return json.loads(raw)
                except Exception: return {"_raw": raw}
        except urllib.error.HTTPError as e:
            return {"_error": e.code, "_body": e.read().decode(errors="replace")[:300]}

    def initialize(self) -> dict:
        return self._post("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "sovereign-tools", "version": "0.1.0"},
        })

    def initialized(self):
        return self._post("notifications/initialized", notif=True)

    def list_tools(self) -> list[dict]:
        r = self._post("tools/list", {})
        return ((r.get("result") or {}).get("tools") or [])

    def call(self, name: str, arguments: dict) -> dict:
        return self._post("tools/call", {"name": name, "arguments": arguments})

def connect() -> Session:
    s = Session()
    s.initialize()
    s.initialized()
    return s

if __name__ == "__main__":
    s = connect()
    tools = s.list_tools()
    print(f"session={s.sid}  tools={len(tools)}")
    for t in tools:
        print(f"  {t.get('name')}")
