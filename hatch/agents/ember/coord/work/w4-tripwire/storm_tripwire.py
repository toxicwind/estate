#!/usr/bin/env python3
import json, sys
p, thr = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10
d = json.load(open(p))
if d.get("storm_active") and int(d.get("chat_hits", 0)) >= thr:
    print(f"TRIPPED storm_active=true chat_hits={d['chat_hits']} thr={thr}")
    sys.exit(2)
print(f"CLEAR storm_active={d.get('storm_active')} chat_hits={d.get('chat_hits')}")
