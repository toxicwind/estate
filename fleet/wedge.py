#!/usr/bin/env python3
"""fleet/wedge.py — lazy wedge classifier for fleet dispatch (e3918e04).

Default mode: trigger the server's lazy classification over all live claims
(POST /v1/dispatch/wedge-scan) and report signal transitions. The server is
the canonical classifier and the single writer; this tool is the trigger +
reporter. Wedge-signal frames go out on :25120 (topic fleet-claims) with a
durable copy in dispatch.db, a room message, and a JSONL mirror line.

--local mode: read-only forensic classification straight from dispatch.db
(short-lived handle; never writes). Same rules, for triage without the server.

Signal levels (merged spec §1, binding):
  alive | wedge-suspect (silent 2x cadence, heartbeats fresh)
  | wedged (silent 3x cadence OR 50% of lease, whichever first)
  | dead (heartbeats stale past threshold or owner gone)
WEDGED is flagged, NEVER auto-requeued. BLOCKED extends the lease.
"""
import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone

TOKEN_FILE = "/home/toxic/.config/sovereign-chat-token"
DEFAULT_STATE_DIR = "/home/toxic/sovereign/tools/sovereign-chat/state"
HEARTBEAT_DEAD_S = 300


def token():
    with open(TOKEN_FILE) as f:
        return f.read().strip()


def api(port, path, method="GET", payload=None):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def classify_local(lease, heartbeat_ts, now):
    """Python port of the canonical classifier (dispatch.ts). Read-only."""
    state = lease["state"] or "progressing"
    if state == "blocked" or state.startswith("blocked:"):
        return ("blocked", f"state={state}; lease extended, never expires")
    hb_age = (now - heartbeat_ts).total_seconds() if heartbeat_ts else float("inf")
    if heartbeat_ts is None or hb_age > HEARTBEAT_DEAD_S:
        basis = (f"holder {lease['claimed_by']} unknown/gone" if heartbeat_ts is None
                 else f"holder heartbeat stale {hb_age:.0f}s > {HEARTBEAT_DEAD_S}s")
        return ("dead", basis)
    wedge_ts = datetime.fromisoformat(lease["wedge_ts"].replace("Z", "+00:00"))
    silent = (now - wedge_ts).total_seconds()
    wedged_at = min(3 * lease["cadence_secs"], 0.5 * lease["lease_secs"])
    if silent >= wedged_at:
        return ("wedged", f"no progress for {silent:.0f}s (wedged at {wedged_at:.0f}s = min(3x cadence, 50% lease)); heartbeats fresh")
    if silent >= 2 * lease["cadence_secs"]:
        return ("wedge-suspect", f"no progress for {silent:.0f}s >= 2x cadence ({lease['cadence_secs']}s); heartbeats fresh")
    return ("alive", f"progress {silent:.0f}s ago within cadence {lease['cadence_secs']}s")


def local_scan(state_dir, as_json):
    now = datetime.now(timezone.utc)
    db = sqlite3.connect(f"file:{state_dir}/dispatch.db?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    chat = sqlite3.connect(f"file:{state_dir}/chat.db?mode=ro", uri=True)
    chat.row_factory = sqlite3.Row
    out = []
    for lease in db.execute("SELECT * FROM dispatch_leases WHERE status='live'"):
        l = dict(lease)
        hb = chat.execute("SELECT last_heartbeat FROM agents WHERE agent_id=?",
                          (l["claimed_by"],)).fetchone()
        hb_ts = None
        if hb and hb["last_heartbeat"]:
            hb_ts = datetime.fromisoformat(hb["last_heartbeat"].replace("Z", "+00:00"))
        signal, basis = classify_local(l, hb_ts, now)
        out.append({"lease_id": l["lease_id"], "task_id": l["task_id"],
                    "claimed_by": l["claimed_by"], "signal": signal, "basis": basis})
    db.close()
    chat.close()
    if as_json:
        print(json.dumps({"ts": now.isoformat(), "live_claims": out}, indent=1))
    else:
        for o in out:
            print(f"lease {o['lease_id']} task {o['task_id']} by {o['claimed_by']}: {o['signal']}\n  {o['basis']}")
        if not out:
            print("no live claims")
    return 0


def main():
    ap = argparse.ArgumentParser(description="fleet dispatch wedge classifier trigger")
    ap.add_argument("--port", type=int, default=25120)
    ap.add_argument("--local", action="store_true",
                    help="read-only forensic classification from dispatch.db (no server write)")
    ap.add_argument("--state-dir", default=os.environ.get("SOVEREIGN_CHAT_STATE_DIR", DEFAULT_STATE_DIR))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.local:
        return local_scan(args.state_dir, args.json)
    try:
        res = api(args.port, "/v1/dispatch/wedge-scan", "POST", {})
    except Exception as e:
        print(f"wedge-scan failed: {e}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(res, indent=1))
        return 0
    print(f"scanned {res.get('scanned', 0)} live claims @ {res.get('ts', '')}")
    for t in res.get("transitions", []):
        print(f"  lease {t['lease_id']} task {t['task_id']}: {t['from']} -> {t['to']}\n    {t['basis']}")
    if not res.get("transitions"):
        print("  no signal transitions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
