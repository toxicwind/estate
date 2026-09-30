#!/usr/bin/env python3
"""Wake-latency probe: park at high-water, publish a real message, time the wake."""
import json, time, urllib.request, threading, subprocess, sys

BASE = "http://127.0.0.1:25135"
TOKEN = open("/home/toxic/.shingle/squawk-relay/feed-token").read().strip()
ROOT = "/home/toxic/.shingle/squawk-root/fleet"

def api(path, timeout=70):
    req = urllib.request.Request(BASE + path,
        headers={"Authorization": "Bearer " + TOKEN})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, time.monotonic() - t0, json.loads(r.read())

_, _, ping = api("/squawk-feed/ping")
high = ping["seq"]
print(f"high-water seq={high}", flush=True)

res = {}
def parked():
    try:
        s, dt, obj = api(f"/squawk-feed/wait?since={high}")
        res.update(s=s, dt=dt, obj=obj)
    except Exception as e:
        res.update(err=repr(e))
t = threading.Thread(target=parked); t.start()
time.sleep(1.5)  # ensure parked

new_seq = high + 1
body = ("---\nseq: %d\nfrom: squawk-feed-perf\nto: all\nchannel: fleet\n"
        "ts: 2026-09-21T19:55:00Z\nstatus: discussion\ntitle: wake-probe-2\n---\n"
        "post-restart wake probe two\n" % new_seq)
p = subprocess.run(
    ["flock", ROOT + "/../.seq-fleet.lock", "-c",
     f"printf %s {json.dumps(body)!r} > {ROOT}/{new_seq}-squawk-feed-perf-wake-probe-2.md && "
     f"[ -s {ROOT}/{new_seq}-squawk-feed-perf-wake-probe-2.md ] && echo WROTE"],
    capture_output=True, text=True)
t0 = time.monotonic()
print("publish:", p.stdout.strip() or p.stderr.strip(), flush=True)
if "WROTE" not in p.stdout:
    print("PUBLISH FAILED"); sys.exit(2)
t.join(timeout=60)
wake_ms = (time.monotonic() - t0) * 1000
msgs = res.get("obj", {}).get("messages", []) if "obj" in res else []
print(f"waiter status={res.get('s')} err={res.get('err')} "
      f"wake={wake_ms:.0f}ms n={len(msgs)}", flush=True)
print("WAKE-OK" if (wake_ms < 5000 and any(m.get("seq") == new_seq for m in msgs))
      else "WAKE-FAIL")
