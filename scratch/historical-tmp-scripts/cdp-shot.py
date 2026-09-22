#!/usr/bin/env python3
"""CDP screenshot of the squawk UI in the isolated agent browser."""
import json, time, urllib.parse, urllib.request, base64, sys
import websocket

CDP = "http://127.0.0.1:9223"
token = open("/home/toxic/.shingle/squawk-relay/feed-token").read().strip()
url = f"http://127.0.0.1:25135/squawk-feed/ui?token={token}"
enc = urllib.parse.urlencode({"url": url})
req = urllib.request.Request(f"{CDP}/json/new?{enc}", method="PUT")
tab = json.load(urllib.request.urlopen(req, timeout=15))
ws_url = tab["webSocketDebuggerUrl"]
print("tab:", tab["url"], file=sys.stderr)

ws = websocket.create_connection(ws_url, timeout=20)
mid = [0]
def send(method, params=None):
    mid[0] += 1
    ws.send(json.dumps({"id": mid[0], "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == mid[0]:
            return msg

send("Page.enable")
time.sleep(4)  # let the page load + long-poll render
comp = send("Runtime.evaluate", {"expression": "JSON.stringify({composer: !!document.getElementById('composer'), msg: !!document.getElementById('msg'), send: !!document.getElementById('send'), msgs: document.querySelectorAll('.msg').length})"})
print("dom:", comp["result"]["result"]["value"], file=sys.stderr)
shot = send("Page.captureScreenshot", {"format": "png"})
data = base64.b64decode(shot["result"]["data"])
open("/tmp/squawk-ui-check.png", "wb").write(data)
print(f"screenshot: {len(data)} bytes -> /tmp/squawk-ui-check.png")
ws.close()
