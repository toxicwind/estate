#!/usr/bin/env python3
"""bg-ctl.py — extended control plane for detached bridge-bg jobs (bridge-max).

Complements the sibling scripts in this directory (same JSON/base64 idioms,
same /proc/<pid>/cmdline ownership checks):

    bin/bg-status.py   live status of one handle + tails (reap-on-read)
    bin/bg-kill.py     SIGTERM a job's process group (pid-reuse safe)
    bin/bg-ctl.py      this file: offset-based output attach + job listing

Commands:
    tail <handle> [soff] [eoff]   incremental stdout/stderr deltas
    list                          every job dir with live state

    tail reads stdout.log / stderr.log from byte offsets soff/eoff and
    returns base64 chunks plus the new offsets to resume from. A negative
    offset means "last N bytes" (e.g. -4000 = tail the last 4 KiB). Pass
    the returned offsets back on the next call for event-style reattach:
    no polling loops, just resume-from-offset fetches. status.json is
    included so the caller knows when the job is terminal.

    list enumerates every state dir, applies the same reap-on-read rule as
    bg-status.py (state "running" but runner pid dead or reused ->
    atomically rewritten to "stale"), and returns one row per job.

Output is always a single JSON document on stdout. Errors exit non-zero
with {"error": ...} on stdout (so exec-lane callers can parse it).
"""

import base64
import json
import os
import re
import sys

BASE = "/home/toxic/.cache/bridge-bg"
HANDLE_RX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _err(msg, code=1):
    sys.stdout.write(json.dumps({"error": msg}) + "\n")
    sys.stdout.flush()
    sys.exit(code)


def _read_status(d):
    try:
        with open(os.path.join(d, "status.json")) as f:
            st = json.load(f)
        return st if isinstance(st, dict) else {}
    except Exception:
        return {}


def _write_status(d, st):
    tmp = os.path.join(d, "status.json.tmp")
    with open(tmp, "w") as f:
        json.dump(st, f)
    os.replace(tmp, os.path.join(d, "status.json"))


def _pid_is_ours(pid, handle):
    """True iff /proc/<pid>/cmdline still shows our bg-run.py for handle."""
    try:
        with open("/proc/%d/cmdline" % pid, "rb") as f:
            cl = f.read().replace(b"\x00", b" ").decode("utf-8", "replace")
    except OSError:
        return False
    return "bg-run.py" in cl and handle in cl


def _reap_if_stale(handle, d, st):
    """Reap-on-read: a "running" job whose runner pid is dead or reused
    (verified via /proc cmdline) is atomically rewritten to "stale".
    Returns the (possibly updated) status dict."""
    if st.get("state") != "running":
        return st
    pid = st.get("pid")
    if isinstance(pid, int) and pid > 0 and _pid_is_ours(pid, handle):
        return st
    st = dict(st)
    st["state"] = "stale"
    st["finished"] = st.get("finished")
    try:
        _write_status(d, st)
    except OSError:
        pass
    return st


def _delta(path, off):
    """Read bytes from off (>=0 absolute, <0 last -off bytes). Returns
    (b64_chunk, new_offset). Missing file -> ("", off)."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return "", off
    start = size + off if off < 0 else off
    start = max(0, min(start, size))
    with open(path, "rb") as f:
        f.seek(start)
        chunk = f.read()
    return base64.b64encode(chunk).decode(), size


def cmd_tail(handle, soff=0, eoff=0):
    d = os.path.join(BASE, handle)
    st = _reap_if_stale(handle, d, _read_status(d))
    so_b64, so_new = _delta(os.path.join(d, "stdout.log"), soff)
    eo_b64, eo_new = _delta(os.path.join(d, "stderr.log"), eoff)
    sys.stdout.write(json.dumps({
        "handle": handle,
        "state": st.get("state", "unknown"),
        "code": st.get("code"),
        "pid": st.get("pid"),
        "pgid": st.get("pgid"),
        "started": st.get("started"),
        "finished": st.get("finished"),
        "stdout_b64": so_b64,
        "stdout_soff": so_new,
        "stderr_b64": eo_b64,
        "stderr_eoff": eo_new,
    }) + "\n")


def cmd_list():
    jobs = []
    try:
        names = sorted(os.listdir(BASE))
    except OSError:
        names = []
    for handle in names:
        if not HANDLE_RX.match(handle):
            continue
        d = os.path.join(BASE, handle)
        if not os.path.isdir(d):
            continue
        st = _reap_if_stale(handle, d, _read_status(d))
        jobs.append({
            "handle": handle,
            "state": st.get("state", "unknown"),
            "code": st.get("code"),
            "cmd": (st.get("cmd") or "")[:120],
            "started": st.get("started"),
            "finished": st.get("finished"),
            "pid": st.get("pid"),
        })
    sys.stdout.write(json.dumps({"jobs": jobs, "count": len(jobs)}) + "\n")


def main():
    if len(sys.argv) < 2:
        _err("usage: bg-ctl.py tail <handle> [soff] [eoff] | list")
    op = sys.argv[1]
    if op == "tail":
        if len(sys.argv) < 3:
            _err("usage: bg-ctl.py tail <handle> [soff] [eoff]")
        handle = sys.argv[2]
        if not HANDLE_RX.match(handle):
            _err("bad handle")
        try:
            soff = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            eoff = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        except ValueError:
            _err("bad offset")
        cmd_tail(handle, soff, eoff)
    elif op == "list":
        cmd_list()
    else:
        _err("unknown op %r (want tail|list)" % op)


if __name__ == "__main__":
    main()
