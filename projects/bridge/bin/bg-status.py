#!/usr/bin/env python3
"""bg-status.py — query a detached bridge-bg job with reap-on-read.

Usage: bg-status.py <handle>

Reads /home/toxic/.cache/bridge-bg/<handle>/status.json. If it claims
"running" but the recorded pid is dead (or no longer our bg-run.py for
this handle — guards against pid reuse), the job is atomically reaped
to "stale" and reported as such. No polling daemons: reaping happens
exactly when someone asks, which is the only moment the answer matters.

Prints one JSON doc: the status fields plus stdout_tail/stderr_tail
(last 4000 bytes each) and pid_alive.

Canonical source: projects/bridge/bin/bg-status.py in
toxicwind/sovereign-projects (bridge-max, 2026-09-20).
"""
import json
import os
import re
import sys
import time

BASE = "/home/toxic/.cache/bridge-bg"
HANDLE_RX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
TAIL_BYTES = 4000


def _wjson(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def _tail(path, n=TAIL_BYTES):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            sz = f.tell()
            f.seek(max(0, sz - n))
            return f.read().decode("utf-8", "replace")
    except Exception:
        return ""


def _pid_is_ours(pid, handle):
    """True iff /proc/<pid>/cmdline shows our bg-run.py for this handle."""
    try:
        with open("/proc/%d/cmdline" % pid, "rb") as f:
            cl = f.read().decode("utf-8", "replace").replace("\x00", " ")
        return "bg-run.py" in cl and handle in cl
    except Exception:
        return False


def main():
    if len(sys.argv) != 2 or not HANDLE_RX.match(sys.argv[1]):
        print(json.dumps({"handle": sys.argv[1] if len(sys.argv) > 1 else None,
                          "state": "bad-handle"}))
        return 2
    handle = sys.argv[1]
    d = os.path.join(BASE, handle)
    st_path = os.path.join(d, "status.json")
    try:
        with open(st_path) as f:
            st = json.load(f)
    except Exception as e:
        print(json.dumps({"handle": handle, "state": "unknown",
                          "error": "no status.json: %s" % e}))
        return 0
    pid = st.get("pid")
    alive = isinstance(pid, int) and _pid_is_ours(pid, handle)
    if st.get("state") == "running" and not alive:
        st = dict(st)
        st["state"] = "stale"
        st["finished"] = time.time()
        st["note"] = ("runner pid %s dead or reused; reaped by status query"
                      % pid)
        try:
            _wjson(st_path, st)
        except Exception as e:
            st["reap_error"] = "%s: %s" % (type(e).__name__, e)
    out = dict(st)
    out["handle"] = handle
    out["pid_alive"] = alive
    out["stdout_tail"] = _tail(os.path.join(d, "stdout.log"))
    out["stderr_tail"] = _tail(os.path.join(d, "stderr.log"))
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
