#!/usr/bin/env python3
"""Open the squawk UI in the isolated agent browser via CDP HTTP."""
import json, urllib.parse, urllib.request

token = open("/home/toxic/.shingle/squawk-relay/feed-token").read().strip()
target = "http://127.0.0.1:25135/squawk-feed/ui?token=" + token
enc = urllib.parse.urlencode({"url": target})
req = urllib.request.Request("http://127.0.0.1:9223/json/new?" + enc, method="PUT")
tab = json.load(urllib.request.urlopen(req, timeout=15))
print("opened tab:", tab["url"][:70])
