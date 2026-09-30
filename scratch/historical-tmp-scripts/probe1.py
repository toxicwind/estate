#!/usr/bin/env python3
"""Squawk feed pre-fix measurement probe (runs on yote, token stays local)."""
import fcntl, json, os, sys, threading, time, urllib.request

BASE = "http://127.0.0.1:25135/squawk-feed"
ROOT = "/home/toxic/.shingle/squawk-root"
CHAN = "fleet"

tok = open("/home/toxic/.shingle/squawk-relay/feed-token").read().strip()
HDR = {"Authorization": "Bearer " + tok}

def get(path, timeout=70):
    req = urllib.request.Request(BASE + path, headers=HDR)
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
    return time.monotonic() - t0, json.loads(body)

def ping():
    req = urllib.request.Request(BASE + "/ping")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())["seq"]

high = ping()
print("high seq:", high, flush=True)

# 1) single since=0 batch latency
dt, d1 = get("/wait?since=0")
print(f"single_batch_since0: {dt*1000:.1f}ms msgs={len(d1['messages'])} seq={d1['seq']}", flush=True)

# 2) full drain since=0 -> high
t0 = time.monotonic(); since = 0; nreq = 0; nmsg = 0
while True:
    dt, d = get(f"/wait?since={since}")
    nreq += 1; nmsg += len(d["messages"]); since = d["seq"]
    if since >= high or not d["messages"]:
        break
    if nreq > 2000:
        print("DRAIN RUNAWAY"); break
tot = time.monotonic() - t0
print(f"full_drain: reqs={nreq} msgs={nmsg} total={tot:.2f}s avg_per_req={tot/max(nreq,1)*1000:.1f}ms", flush=True)

# 3) parked-wait wake latency: park at since=high, publish, time to response
res = {}
def parked():
    dt, d = get(f"/wait?since={high}")
    res["dt"] = dt; res["msgs"] = len(d["messages"]); res["seq"] = d["seq"]
th = threading.Thread(target=parked, daemon=True)
th.start()
time.sleep(1.0)  # let the long-poll park
nxt = ping() + 1
t_write = time.monotonic()
lockp = os.path.join(ROOT, f".seq-{CHAN}.lock")
with open(lockp, "a+") as lf:
    fcntl.flock(lf, fcntl.LOCK_EX)
    body = ("---\nseq: %d\nfrom: probe\nto: all\nchannel: fleet\n"
            "ts: %s\nstatus: discussion\ntitle: probe\n---\nwake-probe\n" % (nxt, time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())))
    tmp = os.path.join(ROOT, CHAN, f".{nxt}-probe-wake.tmp")
    fn = os.path.join(ROOT, CHAN, f"{nxt}-probe-wake-msg.md")
    open(tmp, "w").write(body)
    os.rename(tmp, fn)
    fcntl.flock(lf, fcntl.LOCK_UN)
th.join(timeout=70)
wake = (res.get("dt", 0))
print(f"wake: parked_wait_returned_in={wake*1000:.1f}ms msgs={res.get('msgs')} seq={res.get('seq')} (includes ~1s pre-park settle)", flush=True)
# inotify->response: subtract nothing; the park was already established, so dt ~= wake latency
print("DONE", flush=True)
