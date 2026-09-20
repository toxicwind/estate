#!/usr/bin/env python3
import os
import sys

os.environ.setdefault("FLEET_KEYS_DIR", "/home/toxic/.shingle/squawk-root/keys")
with open("/home/toxic/.shingle/squawk-relay/feed-token") as f:
    os.environ["SQUAWK_FEED_TOKEN"] = f.read().strip()

root = os.environ.get("SQUAWK_CHAT_ROOT", "/home/toxic/.shingle/squawk-root")
port = os.environ.get("SQUAWK_FEED_PORT", "25135")
os.execvpe("python3", ["python3", "/home/toxic/squawk/squawk_feed.py",
    "--root", root, "--channel", "fleet",
    "--bind", "127.0.0.1", "--port", port,
    "--identity", "relay"], os.environ)
