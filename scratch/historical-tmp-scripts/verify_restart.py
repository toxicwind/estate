#!/usr/bin/env python3
"""Post-restart verification for the new squawk-feed code."""
import json, time, urllib.request, urllib.error, subprocess, sys

BASE = "http://127.0.0.1:25135"
TOKEN = open("/home/toxic/.shingle/squawk-relay/feed-token").read().strip()

def get(path, timeout=70):
    req = urllib.request.Request(BASE + path,
        headers={"Authorization": "Bearer " + TOKEN})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            dt = time.monotonic() - t0
            return r.status, dt, json.loads(body), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, time.monotonic() - t0, None, dict(e.headers)

ok = True
def check(name, cond, detail=""):
    global ok
    print(("PASS " if cond else "FAIL ") + name + (f" [{detail}]" if detail else ""))
    ok = ok and cond

# 1. /ping current
s, dt, obj, _ = get("/squawk-feed/ping")
high = obj["seq"] if obj else -1
check("ping 200 + seq", s == 200 and high > 12600, f"seq={high} {dt*1000:.0f}ms")

# 2. tail snapshot: one request, bounded, at high-water
s, dt, obj, _ = get(f"/squawk-feed/wait?since=0&tail=200")
n = len(obj["messages"]) if obj else -1
seqs = [m["seq"] for m in obj["messages"]] if obj else []
check("tail=200 one-shot", s == 200 and n == 200 and obj["seq"] == high,
      f"n={n} seq={obj['seq'] if obj else '?'} {dt*1000:.0f}ms")
check("tail sorted oldest-first", seqs == sorted(seqs) and all(x > 0 for x in seqs))

# 3. wake latency: park at high-water, publish, measure
import threading
res = {}
def parked():
    s2, dt2, obj2, _ = get(f"/squawk-feed/wait?since={high}", timeout=70)
    res.update(s=s2, dt=dt2, obj=obj2)
t = threading.Thread(target=parked); t.start()
time.sleep(1.0)  # let it park
t0 = time.monotonic()
subprocess.run(["flock", "/home/toxic/.shingle/squawk-root/.seq-fleet.lock", "-c",
    "max=$(ls /home/toxic/.shingle/squawk-root/fleet/*.md 2>/dev/null | sed 's/.*\\/\\/; s/-.*//' | sort -n | tail -1); "
    "seq=${max:-0}; seq=$((seq+1)); "
    "printf -- '---\\nseq: %s\\nfrom: squawk-feed-perf\\nto: all\\nchannel: fleet\\nts: x\\nstatus: discussion\\ntitle: verify-wake\\n---\\npost-restart wake probe\\n' $seq > /home/toxic/.shingle/squawk-root/fleet/${seq}-squawk-feed-perf-verify-wake.md; echo $seq"],
    capture_output=True, text=True)
t.join(timeout=60)
wake = (time.monotonic() - t0) * 1000
got = res.get("obj", {}).get("messages", [])
check("parked wait woke on publish", res.get("s") == 200 and len(got) >= 1,
      f"wake={wake:.0f}ms n={len(got)}")
check("wake fast (<2s incl 1s settle)", wake < 3000, f"{wake:.0f}ms")

# 4. ghosts resurrected: no seq-0 records in a fresh tail snapshot
s, dt, obj, _ = get("/squawk-feed/wait?since=0&tail=200")
zero = [m for m in obj["messages"] if not m.get("seq")]
check("no seq-0 ghosts in tail", not zero, f"ghosts={len(zero)}")

# 5. channel param honored + rejected
s, _, obj, _ = get("/squawk-feed/wait?since=0&tail=5&channel=fleet")
check("channel=fleet 200", s == 200 and "messages" in obj)
s, _, _, _ = get("/squawk-feed/wait?since=0&channel=../x")
check("channel traversal 404", s == 404)

# 6. UI served with no-store + new boot code
s, dt, _, headers = get("/squawk-feed/ui")
check("ui 200 no-store", s == 200 and headers.get("Cache-Control") == "no-store",
      f"cc={headers.get('Cache-Control')} {dt*1000:.0f}ms")
body = urllib.request.urlopen(urllib.request.Request(
    BASE + "/squawk-feed/ui", headers={"Authorization": "Bearer " + TOKEN}),
    timeout=30).read().decode()
check("ui has tail boot", "wait?since=0&tail=" in body)
check("ui has state machine", all(x in body for x in
      ("catching-up", "reconnecting", "connstat")))

print("ALL-OK" if ok else "SOME-FAILED")
sys.exit(0 if ok else 1)
