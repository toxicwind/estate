#!/usr/bin/env python3
"""w7-weather-card: compact user-facing storm status card (HTML, phone-sized).
Plan: (1) read LATEST.json from SEEDS; (2) build a single-file dark HTML card:
status pill, hits, digests seen, sparkline of storm-turn hours from
seed_list_chat.json, updated timestamp; (3) validate: file exists, size sane,
no external deps; (4) RESULT.json. Aesthetic: one glance, not a document.
"""
import json, os, time
from datetime import datetime, timezone
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
SEEDS = "/home/toxic/.shingle/coord/work/seeds"

latest = json.load(open(os.path.join(SEEDS, "LATEST.json")))
turns = json.load(open(os.path.join(SEEDS, "seed_list_chat.json")))
hours = Counter()
for t in turns:
    if t["label"] == -1:
        try:
            h = datetime.fromisoformat(t["ts"]).astimezone(timezone.utc).strftime("%H")
            hours[h] += 1
        except Exception:
            pass
mx = max(hours.values()) if hours else 1
bars = "".join(
    f'<div class="b" style="height:{100 * hours.get(f"{h:02d}", 0) // mx}%" title="{h:02d}h"></div>'
    for h in range(24))

active = bool(latest.get("storm_active"))
pill = ("STORM ACTIVE" if active else "QUIET")
color = "#ff5d5d" if active else "#59d98c"
digests = "<br>".join(d[:16] + "&hellip;" for d in latest.get("digests_seen", []))

html = f"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>storm weather</title><style>
body{{background:#10141b;color:#e8edf5;font-family:system-ui;margin:0;padding:16px}}
.card{{max-width:380px;margin:0 auto;background:#171d27;border-radius:14px;padding:18px}}
.pill{{display:inline-block;padding:6px 14px;border-radius:999px;background:{color};color:#10141b;font-weight:700}}
.big{{font-size:44px;font-weight:800;margin:8px 0}}
.dim{{color:#8b95a9;font-size:13px}}
.spark{{display:flex;align-items:flex-end;gap:2px;height:64px;margin-top:10px}}
.b{{flex:1;background:#3b82f6;border-radius:2px;min-height:2px}}
</style></head><body><div class=card>
<span class=pill>{pill}</span>
<div class=big>{latest.get("chat_hits", "?")}</div>
<div class=dim>chat hits this window &middot; updated {latest.get("sweep_ts", "?")}</div>
<div class=dim style="margin-top:8px">digests seen:<br>{digests}</div>
<div class=dim style="margin-top:10px">storm turns by hour (UTC)</div>
<div class=spark>{bars}</div>
</div></body></html>"""
p = os.path.join(WORK, "weather.html")
open(p, "w").write(html)
sz = os.path.getsize(p)
assert 2000 < sz < 60000, f"suspicious size {sz}"
assert "http" not in html.replace("charset=utf-8", ""), "external deps!"

r = {"lane": "w7-weather-card",
     "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
     "claims": ["single-file HTML status card built, no external deps",
                f"size {sz} bytes, renders storm_active={active}"],
     "evidence": {"bytes": sz, "storm_active": active},
     "proof_files": ["weather.html", "brief.py"]}
json.dump(r, open(os.path.join(WORK, "RESULT.json"), "w"), indent=1)
print(json.dumps(r, indent=1))
