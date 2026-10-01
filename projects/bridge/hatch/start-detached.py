#!/usr/bin/env python3
"""Detached launcher for the yote-connector supervisor (127.0.0.1:18301).

Replaces the retired shell pattern:
    cd DIR && setsid nohup python3 supervise-connector.py >>supervisor.log 2>&1 < /dev/null &
In that pattern `&` backgrounds the whole `cd && ...` chain, so the daemon
ends up in a subshell tied to the launching exec session and gets reaped
between watchdog runs.

This launcher uses no shell backgrounding at all: subprocess.Popen with
start_new_session=True puts the supervisor in its own session; when this
launcher exits, the supervisor is reparented to PID 1. Truly detached =
PPID 1 and its own SID (verified below with ps).

Guards:
  - refuses to start if 127.0.0.1:18301 is already bound (no EADDRINUSE race;
    kill the stale holder with exact-PID discipline first, never pkill -f)
  - appends to supervisor.log (never truncates); the connector child keeps
    writing connector.log and its own connector.pid on startup
  - waits for /health and exits nonzero if ok:true never arrives

Usage: python3 start-detached.py [--wait SECS]   (default 8)
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SUPERVISOR = os.path.join(HERE, "supervise-connector.py")
SUP_LOG = os.path.join(HERE, "supervisor.log")
HOST, PORT = "127.0.0.1", 18301
HEALTH_URL = "http://%s:%d/health" % (HOST, PORT)


def port_serving():
    """True if something is actually listening on HOST:PORT.

    Connect-based, not bind-based: a bind probe without SO_REUSE_ADDRESS
    reports "bound" for a port lingering in TIME_WAIT, even though a real
    server (SO_REUSE_ADDRESS) binds it fine. A connect succeeds only when
    a live listener answers.
    """
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect((HOST, PORT))
        return True
    except OSError:
        return False
    finally:
        s.close()


def proc_rows():
    """ps lines for the supervisor and its connector child."""
    try:
        out = subprocess.run(
            ["ps", "-eo", "pid,ppid,sid,args"],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except Exception:
        return []
    rows = []
    for line in out.splitlines():
        if "supervise-connector" in line or "yote-connector/connector.py" in line:
            if "start-detached.py" not in line:
                rows.append(line.strip())
    return rows


def main():
    wait = 8
    args = sys.argv[1:]
    if "--wait" in args:
        try:
            wait = int(args[args.index("--wait") + 1])
        except (IndexError, ValueError):
            print("bad --wait value", file=sys.stderr)
            return 2
    if port_serving():
        print(
            "REFUSE: %s:%d is serving — a live holder owns the slot. "
            "Kill it with exact-PID discipline (verify /proc/<pid>/cmdline "
            "names connector.py and cwd is the connector dir), never pkill -f. "
            "Refusing to race into EADDRINUSE." % (HOST, PORT),
            file=sys.stderr,
        )
        return 2
    log_fd = os.open(SUP_LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    devnull = os.open(os.devnull, os.O_RDONLY)
    try:
        p = subprocess.Popen(
            [sys.executable, SUPERVISOR],
            cwd=HERE,
            stdout=log_fd,
            stderr=subprocess.STDOUT,
            stdin=devnull,
            start_new_session=True,  # new SID; reparented to PID 1 on our exit
            close_fds=True,
        )
    finally:
        os.close(log_fd)
        os.close(devnull)
    print("supervisor launched pid=%d; waiting up to %ds for /health ..." % (p.pid, wait))
    deadline = time.time() + wait
    last_err = "timeout"
    ok, body = False, ""
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=3) as r:
                body = r.read().decode(errors="replace")
            ok = bool(json.loads(body).get("ok"))
            break
        except Exception as e:  # noqa: BLE001 - health poll, any failure means retry
            last_err = e
            time.sleep(0.5)
    if body:
        print("/health -> %r" % body[:160])
    else:
        print("/health never answered: %s" % last_err, file=sys.stderr)
    print("process table (supervisor + connector child; want PPID 1, own SID):")
    rows = proc_rows()
    for row in rows:
        print("  " + row)
    if not rows:
        print("  (no matching processes found)", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
