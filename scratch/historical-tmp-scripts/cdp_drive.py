#!/usr/bin/env python3
"""CDP driver: navigate keeper page, dump safe metadata only. Never prints secrets."""
import json, sys, time, urllib.request

CDP = "http://127.0.0.1:9223"

def cdp_get(path):
    with urllib.request.urlopen(CDP + path, timeout=10) as r:
        return json.load(r)

def main():
    action = sys.argv[1]
    targets = cdp_get("/json/list")
    page = next((t for t in targets if t.get("type") == "page"), None)
    if not page:
        print("NO_PAGE"); return 1
    ws_url = page["webSocketDebuggerUrl"]

    try:
        import websocket  # websocket-client
        has_ws = True
    except ImportError:
        has_ws = False

    if action == "info":
        print(json.dumps({"id": page["id"], "title": page.get("title"), "url": page.get("url")}))
        return 0

    if not has_ws:
        print("NO_WS_LIB"); return 2

    ws = websocket.create_connection(ws_url, timeout=15)
    mid = [0]
    def send(method, params=None):
        mid[0] += 1
        ws.send(json.dumps({"id": mid[0], "method": method, "params": params or {}}))
        deadline = time.time() + 20
        while time.time() < deadline:
            msg = json.loads(ws.recv())
            if msg.get("id") == mid[0]:
                return msg
        raise TimeoutError(method)

    if action == "navigate":
        url = sys.argv[2]
        send("Page.navigate", {"url": url})
        print("NAVIGATED")
    elif action == "text":
        r = send("Runtime.evaluate", {"expression": "document.documentElement ? document.documentElement.innerText.slice(0,4000) : 'NO_DOC'", "returnByValue": True})
        txt = (r.get("result", {}).get("result", {}) or {}).get("value", "")
        print(txt)
    elif action == "url":
        r = send("Runtime.evaluate", {"expression": "location.href", "returnByValue": True})
        print((r.get("result", {}).get("result", {}) or {}).get("value", ""))
    ws.close()
    return 0

sys.exit(main())
