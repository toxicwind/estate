"""Launches the REAL bidder.py processes for the market run.

5 concurrent OS processes (mirrors real_pool.POOL):
  bidder-flash, bidder-flash-2, bidder-mule,
  bidder-specialist, bidder-specialist-2
Each is a genuine bidder daemon: inotify watch, real bid heuristics,
real execution, HMAC-signed posts. Logs under <run_dir>/bidder-logs/.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import real_pool  # noqa: E402

BIDDER_PY = str(HERE.parent / "bidder.py")


def launch(run_dir, log_dir=None):
    """Spawn the 5 real bidder processes. Returns {worker_name: Popen}."""
    if not os.path.isfile(BIDDER_PY):
        raise RuntimeError("bidder.py not found: %s" % BIDDER_PY)
    os.makedirs(run_dir, exist_ok=True)
    log_dir = log_dir or os.path.join(run_dir, "bidder-logs")
    os.makedirs(log_dir, exist_ok=True)
    procs = {}
    for worker_name, profile in real_pool.POOL:
        instance = 2 if worker_name.split("-")[-1] == "2" else 1
        cmd = [sys.executable, BIDDER_PY, "--profile", profile,
               "--instance", str(instance), "--channel", "bid-market"]
        logf = open(os.path.join(log_dir, "bidder-%s.log" % worker_name), "w")
        procs[worker_name] = subprocess.Popen(
            cmd, stdout=logf, stderr=subprocess.STDOUT)
    time.sleep(3)  # one-time boot; bidders print "up |" when ready
    dead = [n for n, p in procs.items() if p.poll() is not None]
    if dead:
        stop(procs)
        raise RuntimeError("bidders died on boot: %s (see %s)" %
                           (dead, log_dir))
    # confirm every bidder logged its ready line (real readiness, not hope)
    for worker_name in procs:
        logp = os.path.join(log_dir, "bidder-%s.log" % worker_name)
        try:
            txt = open(logp).read()
        except OSError:
            txt = ""
        if "up |" not in txt:
            stop(procs)
            raise RuntimeError("bidder %s never came up (see %s)" %
                               (worker_name, logp))
    return procs


def stop(procs, timeout=10):
    for p in procs.values():
        try:
            p.terminate()
        except OSError:
            pass
    for p in procs.values():
        try:
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
