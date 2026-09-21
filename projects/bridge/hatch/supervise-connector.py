#!/usr/bin/env python3
"""Supervisor wrapper for the yote-connector daemon.

Why this exists: the connector died silently 4x in one night (2026-09-21
~23:51, ~01:1x, ~04:28, ~04:31 MDT) with no traceback and no error in its
log. A bare log cannot distinguish "killed from outside" from "crashed
inside". This supervisor wait()s on the child and records HOW it died:

  - killed by signal N  -> external killer (SIGKILL=9: OOM or kill -9;
                          SIGTERM=15: someone/something asked it to stop)
  - exited with code N  -> the connector process itself ended (internal)

The supervisor does NOT respawn the child itself: the 5-minute
yote-connector-watch cron owns restarts. After logging the death it exits,
so a stale supervisor can never shadow a fresh one.

Launch (log-preserving, detached):
  cd /home/hatch/workspace/yote-connector && \
  setsid nohup python3 supervise-connector.py >>supervisor.log 2>&1 < /dev/null &

The connector child still writes its own connector.pid (see connector.py
main()), so watchdog pid checks keep working against the child process.
"""

import datetime
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUP_LOG = os.path.join(HERE, "supervisor.log")
CHILD = os.path.join(HERE, "connector.py")

SIGNAMES = {9: "SIGKILL", 15: "SIGTERM", 1: "SIGHUP", 2: "SIGINT"}


def slog(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[supervisor %s] %s\n" % (ts, msg)
    try:
        with open(SUP_LOG, "a") as f:
            f.write(line)
    except OSError:
        sys.stderr.write(line)  # file unwritable: stderr only (also lands in SUP_LOG via 2>&1)


def main():
    env = dict(os.environ)  # child inherits YOTE_CONNECTOR_PORT etc.
    proc = subprocess.Popen(
        [sys.executable, CHILD],
        cwd=HERE,
        env=env,
        stdin=subprocess.DEVNULL,
        start_new_session=True,  # child in its own session; we only wait()
    )
    slog("child started pid=%d cmd=%s" % (proc.pid, CHILD))
    rc = proc.wait()
    if rc < 0:
        signum = -rc
        slog(
            "child pid=%d KILLED by signal %d (%s) — external killer, not an internal crash"
            % (proc.pid, signum, SIGNAMES.get(signum, "?"))
        )
    else:
        slog("child pid=%d exited with status %d" % (proc.pid, rc))
    # Do not respawn; the watchdog cron owns restarts. Exit so a stale
    # supervisor can never hold the slot.
    sys.exit(0)


if __name__ == "__main__":
    main()
