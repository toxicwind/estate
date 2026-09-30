import json, urllib.request
tok = open("/home/toxic/.shingle/squawk-relay/feed-token").read().strip()
base = json.loads(urllib.request.urlopen(
    "http://127.0.0.1:25135/squawk-feed/seq?channel=fleet",
    timeout=10).read().decode())["seq"]
body = ("<div style=\"color:red\">vex html proof</div>\n"
        "<style>.vx{color:blue}</style>\n"
        "<script>window.__vex_live=1</script>\n"
        "**bold** and <i>ital</i>")
req = urllib.request.Request(
    "http://127.0.0.1:25135/squawk-feed/send",
    data=json.dumps({"channel": "fleet", "text": body,
                     "from": "vex"}).encode(),
    headers={"Authorization": "Bearer " + tok,
             "Content-Type": "application/json"})
posted = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
req2 = urllib.request.Request(
    "http://127.0.0.1:25135/squawk-feed/wait?since=%d&tail=3" % base,
    headers={"Authorization": "Bearer " + tok})
msgs = json.loads(urllib.request.urlopen(req2, timeout=10).read()
                  .decode())["messages"]
last = msgs[-1]["body"]
print("posted seq:", posted["seq"], "channel:", posted["channel"])
print("byte-identical:", last == body)
print("len:", len(last))
