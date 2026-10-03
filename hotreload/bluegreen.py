#!/usr/bin/env python3
"""Blue-green deploy orchestrator with automatic rollback.

Given a service spec (JSON), deploys a new version with zero downtime:
  1. Start GREEN on the idle port.
  2. Poll /health until healthy or timeout -> on timeout, kill GREEN, BLUE stays. ROLLBACK.
  3. Cut proxy to GREEN (write backend file + SIGHUP).
  4. Gracefully drain BLUE (SIGTERM, wait, SIGKILL after timeout).
  5. GREEN becomes BLUE. Deploy complete.

At every step, at least one healthy backend serves the stable port.
A failed deploy NEVER takes the service down — that is the "impossible break" guarantee.

Usage:
  bluegreen.py deploy <spec.json>
  bluegreen.py status <spec.json>     # show current blue/green state
  bluegreen.py rollback <spec.json>   # manually cut back to blue (if green is live)

Spec format: see DESIGN.md.
"""
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error


def load_spec(path):
    with open(path) as f:
        return json.load(f)


def state_dir(spec):
    base = os.environ.get("HOTRELOAD_STATE_BASE",
                           "/home/toxic/estate/hotreload/state")
    d = os.path.join(base, spec["name"])
    os.makedirs(d, exist_ok=True)
    return d


def backend_file(spec):
    return os.path.join(state_dir(spec), "backend")


def pid_file(spec, color):
    return os.path.join(state_dir(spec), f"{color}.pid")


def current_backend(spec):
    """Returns (host, port) of the currently active backend, or None."""
    try:
        with open(backend_file(spec)) as f:
            host, port = f.read().strip().split(":")
            return (host.strip(), int(port.strip()))
    except Exception:
        return None


def which_color(spec, port):
    """Determine if a port is the blue or green port."""
    if port == spec["blue_port"]:
        return "blue"
    if port == spec["green_port"]:
        return "green"
    return "unknown"


def health_ok(spec, port, timeout_s=5):
    """Poll the health endpoint. Returns True if 200."""
    url = f"http://127.0.0.1:{port}{spec.get('health_path', '/health')}"
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as r:
            return r.status == 200
    except Exception:
        return False


def wait_healthy(spec, port, timeout_s):
    """Wait for a backend to become healthy. Returns True/False."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if health_ok(spec, port):
            return True
        time.sleep(1)
    return False


def start_backend(spec, color, port):
    """Start a backend process. Returns Popen. Writes pid file."""
    cmd = spec["start_cmd"]
    # Allow port override via env
    env = dict(os.environ)
    env["PORT"] = str(port)
    env["BACKEND_COLOR"] = color
    # Spec-defined extra env (e.g. BACKEND_VERSION for testing)
    env.update(spec.get("env", {}))
    log_path = os.path.join(state_dir(spec), f"{color}.log")
    log = open(log_path, "a")
    proc = subprocess.Popen(
        cmd, env=env, stdout=log, stderr=subprocess.STDOUT,
        start_new_session=True,  # detach so we can SIGTERM the group
    )
    with open(pid_file(spec, color), "w") as f:
        f.write(str(proc.pid))
    print(f"bluegreen: started {color} on :{port} (pid {proc.pid})", flush=True)
    return proc


def stop_backend(spec, color, port, drain_timeout_s=15):
    """Gracefully stop a backend: SIGTERM, wait, SIGKILL."""
    pf = pid_file(spec, color)
    try:
        with open(pf) as f:
            pid = int(f.read().strip())
    except Exception:
        print(f"bluegreen: no pid file for {color}, skipping stop", flush=True)
        return
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"bluegreen: SIGTERM -> {color} (pid {pid}), draining...",
              flush=True)
    except ProcessLookupError:
        print(f"bluegreen: {color} (pid {pid}) already gone", flush=True)
        return

    # Wait for the port to close (drain)
    deadline = time.time() + drain_timeout_s
    while time.time() < deadline:
        s = socket.socket()
        s.settimeout(1)
        try:
            s.connect(("127.0.0.1", port))
            s.close()
        except OSError:
            print(f"bluegreen: {color} drained", flush=True)
            break
        time.sleep(0.5)
    else:
        # Still listening after drain timeout — force kill
        try:
            os.kill(pid, signal.SIGKILL)
            print(f"bluegreen: SIGKILL -> {color} (pid {pid})", flush=True)
        except ProcessLookupError:
            pass

    try:
        os.remove(pf)
    except OSError:
        pass


def cutover(spec, port):
    """Point the proxy at a new backend port."""
    with open(backend_file(spec), "w") as f:
        f.write(f"127.0.0.1:{port}\n")
    # Nudge the proxy via SIGHUP (it also polls, this is faster)
    # Find proxy pid via pidfile if we manage it, else rely on polling.
    proxy_pid_file = os.path.join(state_dir(spec), "proxy.pid")
    try:
        with open(proxy_pid_file) as f:
            os.kill(int(f.read().strip()), signal.SIGHUP)
    except Exception:
        pass  # proxy polls the file anyway
    print(f"bluegreen: proxy -> :{port}", flush=True)


def do_deploy(spec_path):
    spec = load_spec(spec_path)
    name = spec["name"]
    health_timeout = spec.get("health_timeout_s", 30)
    drain_timeout = spec.get("drain_timeout_s", 15)

    print(f"bluegreen: deploying {name}", flush=True)

    cur = current_backend(spec)
    if cur is None:
        print("bluegreen: no current backend — fresh deploy, starting BLUE",
              flush=True)
        cutover(spec, spec["blue_port"])
        start_backend(spec, "blue", spec["blue_port"])
        if not wait_healthy(spec, spec["blue_port"], health_timeout):
            print("bluegreen: FRESH DEPLOY FAILED — no healthy backend",
                  flush=True)
            sys.exit(1)
        print("bluegreen: fresh deploy complete", flush=True)
        return

    cur_port = cur[1]
    cur_color = which_color(spec, cur_port)
    if cur_color == "blue":
        new_color, new_port = "green", spec["green_port"]
        old_color, old_port = "blue", spec["blue_port"]
    elif cur_color == "green":
        new_color, new_port = "blue", spec["blue_port"]
        old_color, old_port = "green", spec["green_port"]
    else:
        print(f"bluegreen: current backend :{cur_port} matches neither "
              f"blue (:{spec['blue_port']}) nor green (:{spec['green_port']})",
              flush=True)
        sys.exit(1)

    print(f"bluegreen: live is {old_color} (:{old_port}), "
          f"deploying {new_color} (:{new_port})", flush=True)

    # 1. Start GREEN
    green_proc = start_backend(spec, new_color, new_port)

    # 2. Health gate
    if not wait_healthy(spec, new_port, health_timeout):
        print(f"bluegreen: {new_color} FAILED health check — ROLLBACK "
              f"(killing :{new_port}, {old_color} still live)", flush=True)
        green_proc.terminate()
        try:
            green_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            green_proc.kill()
        try:
            os.remove(pid_file(spec, new_color))
        except OSError:
            pass
        print("bluegreen: rollback complete, service never went down",
              flush=True)
        sys.exit(1)

    # 3. Cut over
    print(f"bluegreen: {new_color} healthy, cutting over", flush=True)
    cutover(spec, new_port)
    time.sleep(2)  # let the proxy settle

    # 4. Verify the cutover serves
    if not health_ok(spec, spec["stable_port"]):
        print("bluegreen: CUTOVER FAILED — proxy not serving, rolling back",
              flush=True)
        cutover(spec, old_port)
        stop_backend(spec, new_color, new_port, drain_timeout)
        print("bluegreen: rolled back to :%d" % old_port, flush=True)
        sys.exit(1)

    # 5. Drain old
    print(f"bluegreen: cutover verified, draining {old_color}", flush=True)
    stop_backend(spec, old_color, old_port, drain_timeout)

    print(f"bluegreen: deploy complete — {new_color} (:{new_port}) is live",
          flush=True)


def do_status(spec_path):
    spec = load_spec(spec_path)
    cur = current_backend(spec)
    print(json.dumps({
        "service": spec["name"],
        "stable_port": spec["stable_port"],
        "current_backend": f"{cur[0]}:{cur[1]}" if cur else None,
        "current_color": which_color(spec, cur[1]) if cur else None,
        "blue_port": spec["blue_port"],
        "green_port": spec["green_port"],
        "blue_healthy": health_ok(spec, spec["blue_port"]),
        "green_healthy": health_ok(spec, spec["green_port"]),
    }, indent=2))


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("deploy", "status", "rollback"):
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == "deploy":
        do_deploy(sys.argv[2])
    elif sys.argv[1] == "status":
        do_status(sys.argv[2])
    elif sys.argv[1] == "rollback":
        spec = load_spec(sys.argv[2])
        cur = current_backend(spec)
        if not cur:
            print("bluegreen: no current backend", flush=True)
            sys.exit(1)
        # Roll back to whichever port is NOT current
        other = (spec["blue_port"] if cur[1] == spec["green_port"]
                 else spec["green_port"])
        if health_ok(spec, other):
            cutover(spec, other)
            print(f"bluegreen: rolled back to :{other}", flush=True)
        else:
            print(f"bluegreen: cannot rollback — :{other} not healthy",
                  flush=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
