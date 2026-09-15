#!/usr/bin/env python3
"""buildsrv-watchdog -- external liveness guard for the buildsrv daemon.

Polls http://127.0.0.1:$BUILDSRV_PORT/health every INTERVAL_S (default 20).
After MAX_FAILS (default 3) consecutive failures (timeout, connection
refused, non-200, ok!=true) it runs `pitchfork restart buildsrv` and keeps
watching.

Why this exists (2026-09-14): pitchfork `retry = true` only fires when the
daemon PROCESS dies. A wedged-but-alive daemon -- e.g. the 18:03 deploy
where a non-reentrant lock parked every thread (health dead, process
"running", zero syscalls, no traceback, no OOM) -- is invisible to the
supervisor. This watchdog converts "silent wedge" into "restart".

Scope: buildsrv ONLY. Sibling lanes own their own watchdogs (squawk-ws /
squawk-feed have theirs). Additive: never touches the supervisor itself,
never disables anything.

Env: BUILDSRV_PORT (default 25148), WATCHDOG_INTERVAL_S (default 20),
     WATCHDOG_MAX_FAILS (default 3).
"""
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

PORT = int(os.environ.get("BUILDSRV_PORT", "25148"))
INTERVAL_S = float(os.environ.get("WATCHDOG_INTERVAL_S", "20"))
MAX_FAILS = int(os.environ.get("WATCHDOG_MAX_FAILS", "3"))
HEALTH_URL = f"http://127.0.0.1:{PORT}/health"

stop = False


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[buildsrv-watchdog {ts}] {msg}", flush=True)


def on_term(signum, frame):
    global stop
    log("SIGTERM/SIGINT -- stopping")
    stop = True


def healthy():
    """True if the daemon answers /health with ok=true."""
    try:
        req = urllib.request.Request(HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as r:
            if r.status != 200:
                return False, f"http={r.status}"
            body = json.loads(r.read(4096).decode())
            if body.get("ok") is True:
                return True, "ok"
            return False, f"ok!={body.get(ok)}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def restart_daemon():
    log("restarting buildsrv via pitchfork")
    try:
        r = subprocess.run(
            ["bash", "-lc", "pitchfork restart buildsrv"],
            capture_output=True, text=True, timeout=90,
        )
        out = (r.stdout or "") + (r.stderr or "")
        log(f"pitchfork restart exit={r.returncode}: {out.strip()[:300]}")
        return r.returncode == 0
    except Exception as e:
        log(f"pitchfork restart failed to run: {type(e).__name__}: {e}")
        return False


def main():
    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)
    log(f"watching {HEALTH_URL} every {INTERVAL_S}s, restart after {MAX_FAILS} fails")
    fails = 0
    checks = 0
    while not stop:
        checks += 1
        ok, detail = healthy()
        if ok:
            if fails:
                log(f"health recovered ({detail}); fail counter reset")
            fails = 0
        else:
            fails += 1
            log(f"health check FAILED ({fails}/{MAX_FAILS}): {detail}")
            if fails >= MAX_FAILS:
                restart_daemon()
                fails = 0
                # grace: let the fresh daemon bind before judging it
                for _ in range(3):
                    if stop:
                        break
                    time.sleep(10)
                continue
        if checks % 30 == 0:
            log(f"heartbeat: {checks} checks, daemon healthy")
        for _ in range(int(INTERVAL_S)):
            if stop:
                break
            time.sleep(1)
    log("watchdog stopped")


if __name__ == "__main__":
    main()
