"""Task executor: runs shell/python tasks with a hard timeout.

Real execution on yote. Optional heartbeat callback for long tasks
(deadline-driven, not a poll loop). Output truncated to 4KB.

run_task(task, heartbeat_cb=None) ->
    (success: bool, output: str, duration_s: float, error: str)
"""

import subprocess
import tempfile
import threading
import time
from pathlib import Path

OUTPUT_CAP = 4096


def run_task(task, heartbeat_cb=None):
    kind = task.get("kind", "shell")
    payload = task.get("payload", "")
    timeout_s = max(1.0, float(task.get("deadline_s", 300)))
    stop = threading.Event()

    def _beats():
        # heartbeat every 20s while the task runs (only matters for long ones)
        while not stop.wait(20.0):
            try:
                heartbeat_cb()
            except Exception:
                break

    hb = None
    if heartbeat_cb is not None and timeout_s > 40:
        hb = threading.Thread(target=_beats, daemon=True)
        hb.start()
    t0 = time.time()
    try:
        if kind == "python":
            return _run_python(payload, timeout_s, t0)
        return _run_shell(payload, timeout_s, t0)
    except subprocess.TimeoutExpired:
        return False, "", time.time() - t0, "timeout after %.1fs" % timeout_s
    except Exception as e:  # noqa: BLE001 -- surface anything as failure
        return False, "", time.time() - t0, "executor error: %s" % e
    finally:
        stop.set()


def _run_shell(payload, timeout_s, t0):
    p = subprocess.run(["bash", "-c", payload], capture_output=True, text=True,
                       timeout=timeout_s)
    out = (p.stdout or "") + (p.stderr or "")
    err = "" if p.returncode == 0 else "exit code %d" % p.returncode
    return p.returncode == 0, out[:OUTPUT_CAP], time.time() - t0, err


def _run_python(payload, timeout_s, t0):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     dir="/tmp") as f:
        f.write(payload)
        tmp = f.name
    try:
        p = subprocess.run(["python3", tmp], capture_output=True, text=True,
                           timeout=timeout_s, cwd="/tmp")
    finally:
        try:
            Path(tmp).unlink()
        except OSError:
            pass
    out = (p.stdout or "") + (p.stderr or "")
    err = "" if p.returncode == 0 else "exit code %d" % p.returncode
    return p.returncode == 0, out[:OUTPUT_CAP], time.time() - t0, err
