#!/usr/bin/env python3
"""Supervisor wrapper for the yote-connector daemon.

Why this exists: the connector died silently 4x in one night (2026-09-21
~23:51, ~01:1x, ~04:28, ~04:31 MDT) with no traceback and no error in its
log. A bare log cannot distinguish "killed from outside" from "crashed
inside". This supervisor wait()s on the child and records HOW it died:

  - killed by signal N  -> external killer (SIGKILL=9: OOM or kill -9;
                          SIGTERM=15: someone/something asked it to stop)
  - exited with code N  -> the connector process itself ended (internal)

SELF-HEALING (2026-10-01): the supervisor now RESPAWNS the child with
exponential backoff (5s -> 60s cap, reset after the child survives 300s).
Rationale: the previous design exited after one death and depended on the
5-minute progress-watchdog for restarts -- but on 2026-09-30 the watchdog
scheduler itself died silently at 22:52 UTC and the connector then sat
dead for hours with nobody restarting it. Depending on an external
restarter is a single point of failure; the supervisor is the process
closest to the child and must own the respawn.

No-shadow guarantees (so a stale supervisor can never fight a fresh one):
  - before every (re)spawn, the supervisor probes 127.0.0.1:18301. If the
    port is bound, it logs and exits -- someone else owns the slot.
  - start-detached.py refuses to launch when the port is bound.
  - SIGTERM to the supervisor is honored promptly: it stops the child
    (if still ours) and exits without respawning. The deploy path
    (deploy-yote-connector / stop_connector_exact) SIGTERMs supervisor +
    child, so deploys never race a respawn.

MUTUAL WATCH (2026-10-01): every 10 minutes the supervisor best-effort
runs `watchdog-scheduler ensure` (idempotent). The scheduler's
progress-watchdog is the second layer: its restart_local_connector()
relaunches THIS supervisor if the supervisor itself is killed. Each side
keeps the other alive; a simultaneous kill of both is the residual risk
and is reported, not silently absorbed.

Launch (log-preserving, detached) -- use the dedicated launcher:
  python3 /home/hatch/workspace/yote-connector/start-detached.py --wait 8
The old `cd DIR && setsid nohup ... &` shell pattern is RETIRED: the `&`
bound the whole `cd && ...` chain, leaving the daemon in a subshell tied
to the launching exec session (reaped between watchdog runs). The launcher
uses Popen(start_new_session=True) with no shell backgrounding, guards
against EADDRINUSE, and verifies /health plus PPID 1 / own SID.

The connector child still writes its own connector.pid (see connector.py
main()), so watchdog pid checks keep working against the child process.
"""

import datetime
import os
import signal
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SUP_LOG = os.path.join(HERE, "supervisor.log")
CHILD = os.path.join(HERE, "connector.py")
HOST, PORT = "127.0.0.1", 18301
SCHEDULER = os.path.join(os.path.expanduser("~"), "workspace", "bin",
                         "watchdog-scheduler")
ENSURE_INTERVAL = 600      # mutual-watch tick: scheduler ensure, seconds
BACKOFF_START = 5
BACKOFF_MAX = 60
BACKOFF_RESET_AFTER = 300  # child surviving this long resets the backoff

SIGNAMES = {9: "SIGKILL", 15: "SIGTERM", 1: "SIGHUP", 2: "SIGINT"}

_shutdown = False


def slog(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[supervisor %s] %s\n" % (ts, msg)
    try:
        with open(SUP_LOG, "a") as f:
            f.write(line)
    except OSError:
        sys.stderr.write(line)  # file unwritable: stderr only


def _on_sigterm(signum, frame):
    global _shutdown
    _shutdown = True


def port_serving():
    """True if something is actually listening on HOST:PORT.

    Connect-based, not bind-based: a bind probe without SO_REUSE_ADDRESS
    reports "bound" for a port lingering in TIME_WAIT after a SIGKILLed
    child, even though a real server (SO_REUSE_ADDRESS) binds it fine.
    That false positive made the supervisor exit instead of respawning
    (observed 2026-10-01). A connect succeeds only when a live listener
    answers.
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


def ensure_scheduler():
    """Best-effort mutual watch: keep the watchdog scheduler alive.

    Never raises; never blocks the supervisor for long. A failure here is
    logged, not fatal -- the respawn loop must survive it.
    """
    try:
        if not (os.path.isfile(SCHEDULER) and os.access(SCHEDULER, os.X_OK)):
            return
        subprocess.run([sys.executable, SCHEDULER, "ensure"],
                       stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       timeout=30)
    except Exception as e:  # noqa: BLE001 - best-effort only
        slog("scheduler ensure failed (best-effort): %r" % e)


def spawn_child():
    env = dict(os.environ)  # child inherits YOTE_CONNECTOR_PORT etc.
    return subprocess.Popen(
        [sys.executable, CHILD],
        cwd=HERE,
        env=env,
        stdin=subprocess.DEVNULL,
        start_new_session=True,  # child in its own session; we only wait()
    )


def wait_with_watch(proc, last_ensure):
    """Wait for the child; run the mutual-watch tick every ENSURE_INTERVAL.

    Returns (returncode_or_None, last_ensure). rc None means we were asked
    to shut down (SIGTERM) while the child was still alive.
    """
    while True:
        if _shutdown:
            return None, last_ensure
        try:
            rc = proc.wait(timeout=30)
            return rc, last_ensure
        except subprocess.TimeoutExpired:
            pass
        now = time.time()
        if now - last_ensure >= ENSURE_INTERVAL:
            ensure_scheduler()
            last_ensure = now


def main():
    signal.signal(signal.SIGTERM, _on_sigterm)
    backoff = BACKOFF_START
    last_ensure = 0.0
    first = True
    while True:
        if _shutdown:
            slog("received SIGTERM -- exiting without respawn")
            return 0
        if port_serving():
            # Someone else owns the slot (fresh deploy, manual start).
            # Exit rather than shadow it.
            slog("port %s:%d is serving -- another owner holds the slot, "
                 "exiting without respawn" % (HOST, PORT))
            return 0
        proc = spawn_child()
        slog("child started pid=%d cmd=%s" % (proc.pid, CHILD))
        started = time.time()
        # Mutual-watch tick also runs while the child is healthy.
        if first or time.time() - last_ensure >= ENSURE_INTERVAL:
            ensure_scheduler()
            last_ensure = time.time()
            first = False
        rc, last_ensure = wait_with_watch(proc, last_ensure)
        if rc is None:  # SIGTERM arrived while waiting
            slog("received SIGTERM -- stopping child pid=%d and exiting" % proc.pid)
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proc.kill()
            except Exception:
                pass
            return 0
        lived = time.time() - started
        if rc < 0:
            signum = -rc
            slog("child pid=%d KILLED by signal %d (%s) -- external killer, "
                 "not an internal crash" % (proc.pid, signum,
                                            SIGNAMES.get(signum, "?")))
        else:
            slog("child pid=%d exited with status %d" % (proc.pid, rc))
        if rc == 0:
            slog("child exited cleanly (status 0) -- intentional stop, "
                 "not respawning")
            return 0
        # Abnormal death: respawn with backoff.
        if lived >= BACKOFF_RESET_AFTER:
            backoff = BACKOFF_START
        else:
            backoff = min(backoff * 2, BACKOFF_MAX)
        slog("respawning child in %ds (lived %.0fs)" % (backoff, lived))
        deadline = time.time() + backoff
        while time.time() < deadline:
            if _shutdown:
                slog("received SIGTERM during backoff -- exiting")
                return 0
            time.sleep(0.5)


if __name__ == "__main__":
    sys.exit(main())
