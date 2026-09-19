#!/usr/bin/env python3
"""fleet/dispatch_fallback.py — directives-file fallback for fleet dispatch (e3918e04 §3).

When :25120 is unreachable, dispatch frames are appended to the directives
file (/home/toxic/.shingle/directives.md) instead of being dropped. On
reconnect, `replay` re-POSTs the queued frames in order and advances the
cursor. Push latency of successful sends is logged for p50/p99 reporting.

Wire format in the directives file is human-readable markdown; the actual
frames live in a JSONL sidecar (<directives>.fallback.jsonl) so replay is
exact. The cursor is the count of replayed sidecar lines, kept in
<directives>.fallback.cursor.

This is the CLIENT side of §3. The server side is snapshot()
(GET /v1/dispatch/snapshot) plus since_seq replay on the rooms.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

TOKEN_FILE = "/home/toxic/.config/sovereign-chat-token"
DEFAULT_DIRECTIVES = "/home/toxic/.shingle/directives.md"


def token():
    with open(TOKEN_FILE) as f:
        return f.read().strip()


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def try_post(url, payload, timeout=10):
    """POST payload; return (ok, latency_s, error)."""
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(), method="POST",
            headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode()[:500]
        return True, time.monotonic() - t0, body
    except Exception as e:
        return False, time.monotonic() - t0, f"{type(e).__name__}: {e}"[:300]


def sidecar_paths(directives):
    return directives + ".fallback.jsonl", directives + ".fallback.cursor"


def read_cursor(cursor_path):
    try:
        with open(cursor_path) as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def write_cursor(cursor_path, n):
    with open(cursor_path, "w") as f:
        f.write(str(n))


def log_latency(directives, latency_s):
    with open(directives + ".fallback.lat", "a") as f:
        f.write(f"{now_iso()} {latency_s:.3f}\n")


def cmd_push(args):
    payload = json.loads(args.payload)
    ok, lat, info = try_post(args.url, payload, timeout=args.timeout)
    if ok:
        log_latency(args.directives, lat)
        print(json.dumps({"ok": True, "latency_s": round(lat, 3), "response": info}))
        return 0
    # fallback engaged: queue to directives file + sidecar
    jl, cur = sidecar_paths(args.directives)
    with open(jl, "a") as f:
        f.write(json.dumps({"ts": now_iso(), "url": args.url, "payload": payload}) + "\n")
    nlines = sum(1 for _ in open(jl))
    with open(args.directives, "a") as f:
        f.write(f"\n<!-- dispatch-fallback {now_iso()} ENGAGED: {args.url} unreachable "
                f"({info}); frame queued as cursor {nlines} -->\n")
        f.write(f"- [ ] `dispatch-fallback` queued POST {args.url} @ {now_iso()} (cursor {nlines})\n")
    print(json.dumps({"ok": False, "fallback": "engaged", "cursor": nlines,
                      "latency_s": round(lat, 3), "error": info}))
    return 0


def cmd_replay(args):
    jl, cur_path = sidecar_paths(args.directives)
    cursor = read_cursor(cur_path)
    try:
        with open(jl) as f:
            queued = [json.loads(l) for l in f if l.strip()]
    except OSError:
        queued = []
    pending = queued[cursor:]
    if not pending:
        print(json.dumps({"ok": True, "replayed": 0, "cursor": cursor}))
        return 0
    done = 0
    for q in pending:
        url = args.url_override or q["url"]
        ok, lat, info = try_post(url, q["payload"], timeout=args.timeout)
        if not ok:
            print(json.dumps({"ok": False, "replayed": done, "cursor": cursor + done,
                              "error": info, "note": "server still unreachable; cursor held"}))
            return 1
        log_latency(args.directives, lat)
        done += 1
    write_cursor(cur_path, cursor + done)
    with open(args.directives, "a") as f:
        f.write(f"\n<!-- dispatch-fallback {now_iso()} DISENGAGED: replayed {done} queued frames -->\n")
    print(json.dumps({"ok": True, "replayed": done, "cursor": cursor + done}))
    return 0


def cmd_latencies(args):
    try:
        with open(args.directives + ".fallback.lat") as f:
            lat = sorted(float(l.split()[-1]) for l in f if l.strip())
    except OSError:
        lat = []
    if not lat:
        print(json.dumps({"n": 0}))
        return 0
    import statistics
    print(json.dumps({"n": len(lat), "p50": round(statistics.median(lat), 3),
                      "p99": round(lat[min(len(lat) - 1, int(0.99 * len(lat)))], 3),
                      "unit": "s"}))
    return 0


def main():
    ap = argparse.ArgumentParser(description="dispatch directives-file fallback")
    ap.add_argument("--directives", default=os.environ.get("DISPATCH_DIRECTIVES", DEFAULT_DIRECTIVES))
    ap.add_argument("--timeout", type=int, default=10)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("push", help="POST a frame; queue to directives file if unreachable")
    p.add_argument("--url", required=True)
    p.add_argument("--payload", required=True, help="JSON payload")
    r = sub.add_parser("replay", help="re-POST queued frames in order")
    r.add_argument("--url-override", default=None, help="replay to this URL instead of the queued one")
    l = sub.add_parser("latencies", help="p50/p99 of successful push latency")
    # Accept --directives/--timeout after the subcommand too (argparse only
    # takes main-parser opts before the subcommand). SUPPRESS lets the main
    # value survive when the subcommand doesn't override it.
    for sp in (p, r, l):
        sp.add_argument("--directives", default=argparse.SUPPRESS)
        sp.add_argument("--timeout", type=int, default=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.cmd == "push":
        return cmd_push(args)
    if args.cmd == "replay":
        return cmd_replay(args)
    return cmd_latencies(args)


if __name__ == "__main__":
    sys.exit(main())
