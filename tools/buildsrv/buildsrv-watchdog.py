#!/usr/bin/env python3
"""buildsrv-watchdog -- external liveness guard for the buildsrv daemon.

Polls http://127.0.0.1:$BUILDSRV_PORT/health every INTERVAL_S (default 20).
After MAX_FAILS (default 3) consecutive failures (timeout, connection
refused, non-200, ok!=true) it restarts the daemon: first via
`pitchfork restart buildsrv`, and if the daemon is still unhealthy, via a
direct kill + detached start (2026-09-17: the pitchfork supervisor no
longer manages buildsrv -- it reports the daemon as stopped/unavailable,
so the pitchfork route is a no-op).

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
import re
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
    if _pitchfork_restart():
        return True
    log("pitchfork route did not restore health; falling back to direct restart")
    return _direct_restart()


def _pitchfork_restart():
    """Try the supervisor route. Returns True if the daemon is healthy after."""
    log("restarting buildsrv via pitchfork")
    try:
        r = subprocess.run(
            ["bash", "-lc", "pitchfork restart buildsrv"],
            capture_output=True, text=True, timeout=90,
        )
        out = (r.stdout or "") + (r.stderr or "")
        log(f"pitchfork restart exit={r.returncode}: {out.strip()[:300]}")
    except Exception as e:
        log(f"pitchfork restart failed to run: {type(e).__name__}: {e}")
    time.sleep(8)
    ok, detail = healthy()
    log(f"post-pitchfork health: {ok} ({detail})")
    return ok


DAEMON_PY = "/home/toxic/sovereign/tools/buildsrv/buildsrvd.py"
DAEMON_LOG = "/home/toxic/sovereign/logs/buildsrv-watchdog-restarts.log"


def _port_holders(port):
    """PIDs currently LISTENing on TCP port (127.0.0.1 or any iface).

    Ground truth for "who owns the port", independent of process names.
    Excludes this watchdog itself.
    """
    try:
        r = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, timeout=10)
    except Exception:
        return []
    holders = set()
    for line in (r.stdout or "").splitlines():
        cols = line.split()
        if len(cols) < 4:
            continue
        local = cols[3]
        if not re.search(rf":{port}([^0-9]|$)", local):
            continue
        for m in re.finditer(r"pid=(\d+)", line):
            holders.add(int(m.group(1)))
    holders.discard(os.getpid())
    return sorted(holders)


def _wait_port_free(port, timeout_s):
    """Poll until nothing listens on port; True if freed within timeout."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if not _port_holders(port):
            return True
        time.sleep(0.5)
    return not _port_holders(port)


def _direct_restart():
    """Supervisor route is a no-op for buildsrv (2026-09-17: pitchfork
    reports it stopped/unavailable, `pitchfork start` says not found).
    Kill any stray buildsrvd.py and start the daemon directly, detached,
    with the same env the pitchfork stanza would have given it.

    2026-09-20 (port-hunter): the old daemon is usually WEDGED at this
    point (that is why we are restarting it) and the old fixed 2s sleep
    after pkill was not enough for it to release the port -- the fresh
    instance then died with EADDRINUSE (see the 03:40 entry in
    buildsrv-watchdog-restarts.log). Now we SIGTERM whoever actually
    holds the port, WAIT for the port to free, SIGKILL stragglers, and
    abort the start loudly if the port never frees. We never start a new
    instance into an occupied port.
    """
    log("direct restart: killing stray buildsrvd.py processes")
    try:
        subprocess.run(["pkill", "-f", r"buildsrvd\.py"], timeout=10,
                       capture_output=True)
    except Exception as e:
        log(f"pkill: {type(e).__name__}: {e}")
    holders = _port_holders(PORT)
    if holders:
        log(f"port {PORT} held by {holders}; SIGTERM")
        for pid in holders:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    if not _wait_port_free(PORT, 10):
        holders = _port_holders(PORT)
        log(f"port {PORT} still held by {holders} after SIGTERM; SIGKILL")
        for pid in holders:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    if not _wait_port_free(PORT, 5):
        log(f"port {PORT} STILL held by {_port_holders(PORT)}; "
            f"refusing to start into EADDRINUSE")
        return False
    log(f"port {PORT} free; launching {DAEMON_PY}")
    env = dict(os.environ)
    env.update({
        "BUILDSRV_ROOT": "/home/toxic/buildsrv",
        "BUILDSRV_PORT": str(PORT),
        "BUILDSRV_WORKERS": "2",
    })
    try:
        fh = open(DAEMON_LOG, "a")
        subprocess.Popen(
            [sys.executable, DAEMON_PY],
            stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT,
            start_new_session=True, env=env,
        )
    except Exception as e:
        log(f"direct start failed: {type(e).__name__}: {e}")
        return False
    time.sleep(8)
    ok, detail = healthy()
    log(f"post-direct-start health: {ok} ({detail})")
    return ok


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
