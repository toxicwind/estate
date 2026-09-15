#!/usr/bin/env python3
"""buildsrvd — the fleet's continuous-modification engine.

A pitchfork-managed build daemon (stdlib-only Python). It watches a
disk-backed job queue, runs builds through the user's login shell
(`bash -lc`, so mise toolchains resolve exactly as they do for Chris),
streams logs to per-job files, and caches artifacts keyed by content hash
of the job spec.

Job semantics (forward-only):
  * The daemon NEVER touches the working tree — no git checkout, stash,
    or revert. The build command sees the tree exactly as it is.
  * Jobs iterate forward on the tree; re-submitting an identical job is
    a cache-hit no-op that returns the previous result.
  * Interrupted jobs (daemon restart mid-run) are re-queued cleanly;
    nothing is ever half-applied because nothing is applied at all —
    only the build command runs.

Layout under $BUILDSRV_ROOT (default /home/toxic/buildsrv):
  queue/      pending job specs: <id>.json
  active/     claimed by this daemon (moved back to queue/ on boot)
  logs/       <id>.log — streamed while the build runs, tail-able
  results/    <id>.json — terminal result record
  artifacts/  <jobhash>/ — copied build outputs + manifest.json
  state.json  job ledger (status, attempts, hashes, timings)

Health: http://127.0.0.1:$BUILDSRV_PORT/health
"""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(os.environ.get("BUILDSRV_ROOT", "/home/toxic/buildsrv"))
QUEUE = ROOT / "queue"
ACTIVE = ROOT / "active"
LOGS = ROOT / "logs"
RESULTS = ROOT / "results"
ARTIFACTS = ROOT / "artifacts"
STATE_FILE = ROOT / "state.json"
PID_FILE = ROOT / "buildsrvd.pid"

PORT = int(os.environ.get("BUILDSRV_PORT", "25148"))
MAX_WORKERS = int(os.environ.get("BUILDSRV_WORKERS", "2"))
POLL_INTERVAL = float(os.environ.get("BUILDSRV_POLL", "2"))

# toolchain -> primary binary the daemon preflights via the login shell
# (mise shims live on the login PATH, so this also proves mise resolution).
TOOLCHAIN_BINS = {
    "rust": "cargo", "cargo": "cargo",
    "go": "go",
    "bun": "bun",
    "node": "node",
    "python": "python3", "python3": "python3",
    "tsc": "bun",
}

TERMINAL = {"succeeded", "failed", "cached"}


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(msg):
    print(f"[buildsrvd {time.strftime('%H:%M:%S')}] {msg}", flush=True)


for d in (QUEUE, ACTIVE, LOGS, RESULTS, ARTIFACTS):
    d.mkdir(parents=True, exist_ok=True)

state_lock = threading.RLock()  # reentrant: claim_next()/save_state() re-acquire under one thread; plain Lock deadlocks the daemon (2026-09-14)
state = {"jobs": {}, "counters": {"succeeded": 0, "failed": 0}}
shutdown = threading.Event()
active_threads = 0
boot_time = time.time()


def load_state():
    global state
    try:
        with open(STATE_FILE) as f:
            loaded = json.load(f)
        if isinstance(loaded, dict) and "jobs" in loaded:
            state = loaded
            log(f"loaded state: {len(state['jobs'])} jobs on record")
    except FileNotFoundError:
        log("no state file yet — starting fresh")
    except Exception as e:
        log(f"WARN: state file unreadable ({e}) — starting fresh")


def save_state():
    tmp = STATE_FILE.with_suffix(".tmp")
    with state_lock:
        payload = json.dumps(state, indent=1, sort_keys=True)
    tmp.write_text(payload)
    tmp.replace(STATE_FILE)


def job_hash(job):
    canon = {
        "repo": job.get("repo"),
        "workdir": job.get("workdir"),
        "toolchain": job.get("toolchain"),
        "cmd": job.get("cmd"),
        "env": job.get("env") or {},
        "artifacts": job.get("artifacts") or [],
    }
    return hashlib.sha256(
        json.dumps(canon, sort_keys=True).encode()
    ).hexdigest()


def preflight(job):
    """Fail fast with a clear message if the toolchain is missing."""
    tc = (job.get("toolchain") or "").lower()
    binary = TOOLCHAIN_BINS.get(tc)
    if not binary:
        return False, (
            f"unknown toolchain {tc!r}; known: {sorted(TOOLCHAIN_BINS)} "
            "(the daemon orchestrates mise toolchains, it never installs them)"
        )
    try:
        r = subprocess.run(
            ["bash", "-lc", f"command -v {binary}"],
            capture_output=True, text=True, timeout=20,
        )
    except Exception as e:
        return False, f"toolchain preflight failed to run: {e}"
    path = (r.stdout or "").strip().splitlines()
    if r.returncode != 0 or not path:
        return False, (
            f"toolchain {tc!r} not on login PATH (looked for {binary!r}); "
            f"install/enable it via mise, then resubmit"
        )
    repo = Path(job.get("repo") or "")
    if not repo.is_dir():
        return False, f"repo dir does not exist: {repo}"
    wd = Path(job.get("workdir") or str(repo))
    if not wd.is_dir():
        return False, f"workdir does not exist: {wd}"
    if not job.get("cmd"):
        return False, "job has no cmd"
    return True, path[0]


def find_cached(job):
    """Return a succeeded job record with the same spec hash, if any."""
    h = job_hash(job)
    with state_lock:
        for rec in state["jobs"].values():
            if rec.get("job_hash") == h and rec.get("status") == "succeeded":
                return rec
    return None


def copy_artifacts(job, jhash, logf):
    dest = ARTIFACTS / jhash
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    wd = Path(job.get("workdir") or job["repo"])
    manifest = {"job_hash": jhash, "files": []}
    for rel in job.get("artifacts") or []:
        src = wd / rel
        if not src.exists():
            logf.write(f"[buildsrv] artifact declared but missing: {rel}\n")
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, target, symlinks=True)
        else:
            shutil.copy2(src, target)
        manifest["files"].append(rel)
        logf.write(f"[buildsrv] cached artifact: {rel}\n")
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return str(dest) if manifest["files"] else None


def run_job(job, jid):
    rec_update = {}
    started = time.time()
    log_path = LOGS / f"{jid}.log"
    logf = open(log_path, "a", encoding="utf-8", errors="replace")
    logf.write(f"\n===== buildsrv job {jid} started {now_iso()} =====\n")
    logf.write(f"name={job.get('name')} toolchain={job.get('toolchain')} repo={job.get('repo')}\n")
    logf.write(f"cmd: {job.get('cmd')}\n")
    logf.flush()

    ok, detail = preflight(job)
    status, exit_code = "failed", 98
    duration = 0.0
    artifact_dir = None
    jhash = job_hash(job)

    if not ok:
        logf.write(f"[buildsrv] PREFLIGHT FAILED: {detail}\n")
        log(f"job {jid} preflight failed: {detail}")
    else:
        logf.write(f"[buildsrv] toolchain ok: {detail}\n")
        env = dict(os.environ)
        # Never inherit a stale GOROOT supervisor env leaks
        # GOROOT=<mise go 1.23.1> while login PATH resolves go to the
        # system 1.26.5 binary -> wrong std tree, go builds break.
        # A go binary always knows its own GOROOT. (2026-09-14)
        env.pop("GOROOT", None)
        env.update(job.get("env") or {})
        env["BUILDSRV_JOB_ID"] = jid
        wd = job.get("workdir") or job.get("repo")
        timeout = int(job.get("timeout_s", 1200))
        log(f"job {jid} running (timeout {timeout}s): {job['cmd'][:100]}")
        try:
            proc = subprocess.Popen(
                ["bash", "-lc", job["cmd"]],
                cwd=wd, env=env,
                stdout=logf, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                exit_code = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                import signal as _sig
                try:
                    os.killpg(proc.pid, _sig.SIGKILL)
                except ProcessLookupError:
                    pass
                exit_code = proc.wait()
                logf.write(f"\n[buildsrv] TIMEOUT after {timeout}s — killed\n")
                log(f"job {jid} timed out after {timeout}s")
            duration = time.time() - started
            if exit_code == 0:
                status = "succeeded"
                artifact_dir = copy_artifacts(job, jhash, logf)
            else:
                status = "failed"
            logf.write(f"\n[buildsrv] {status} exit={exit_code} duration={duration:.1f}s\n")
        except Exception as e:
            duration = time.time() - started
            logf.write(f"\n[buildsrv] launcher error: {e}\n")
            log(f"job {jid} launcher error: {e}")
    logf.write(f"===== buildsrv job {jid} finished {now_iso()} =====\n")
    logf.close()

    result = {
        "id": jid,
        "name": job.get("name"),
        "status": status,
        "exit_code": exit_code,
        "duration_s": round(duration, 1),
        "job_hash": jhash,
        "artifact_dir": artifact_dir,
        "finished_at": now_iso(),
        "log": str(log_path),
    }
    (RESULTS / f"{jid}.json").write_text(json.dumps(result, indent=1))
    with state_lock:
        rec = state["jobs"].get(jid, {})
        rec.update(
            status=status, exit_code=exit_code,
            duration_s=round(duration, 1), job_hash=jhash,
            artifact_dir=artifact_dir, finished_at=now_iso(),
        )
        state["jobs"][jid] = rec
        state["counters"][status] = state["counters"].get(status, 0) + 1
    save_state()
    log(f"job {jid}: {status} exit={exit_code} {duration:.1f}s")
    return result


def claim_next():
    """Atomically claim one pending job file. Returns (jid, job) or None."""
    global active_threads
    with state_lock:
        if active_threads >= MAX_WORKERS:
            return None
        pending = sorted(QUEUE.glob("*.json"), key=lambda p: p.stat().st_mtime)
        for spec in pending:
            jid = spec.stem
            try:
                job = json.loads(spec.read_text())
            except Exception as e:
                log(f"WARN: unreadable job file {spec.name}: {e}")
                continue
            with state_lock:
                rec = state["jobs"].get(jid)
                if rec and rec.get("status") in TERMINAL:
                    spec.unlink()  # terminal but file lingered — archive it
                    continue
                if rec and rec.get("status") == "running":
                    continue  # boot reap covers this; stay safe
                active_threads += 1
                state["jobs"][jid] = {
                    "status": "running",
                    "name": job.get("name"),
                    "job_hash": job_hash(job),
                    "started_at": now_iso(),
                    "attempt": (rec.get("attempt", 0) + 1) if rec else 1,
                    "submitted_at": job.get("submitted_at"),
                }
            save_state()
            dest = ACTIVE / spec.name
            try:
                spec.replace(dest)
            except FileNotFoundError:
                with state_lock:
                    active_threads -= 1
                continue
            log(f"claimed job {jid} ({job.get('name')})")
            return jid, job
        with state_lock:
            # nothing claimable; undo the optimistic reservation check
            pass
        return None


def run_one(jid, job):
    global active_threads
    try:
        run_job(job, jid)
    except Exception as e:
        log(f"job {jid} crashed: {e}")
        with state_lock:
            state["jobs"][jid] = {
                "status": "failed", "exit_code": 97,
                "finished_at": now_iso(), "name": job.get("name"),
            }
        save_state()
    finally:
        (ACTIVE / f"{jid}.json").unlink(missing_ok=True)
        with state_lock:
            active_threads -= 1


def worker_loop():
    while not shutdown.is_set():
        claimed = claim_next()
        if claimed is None:
            shutdown.wait(POLL_INTERVAL)
            continue
        jid, job = claimed
        threading.Thread(target=run_one, args=(jid, job), daemon=True).start()
    # drain: wait for in-flight jobs (bounded; boot-reap covers the rest)
    deadline = time.time() + 120
    while time.time() < deadline:
        with state_lock:
            if active_threads == 0:
                break
        time.sleep(1)


class HealthHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            with state_lock:
                running = [jid for jid, r in state["jobs"].items()
                           if r.get("status") == "running"]
                counters = dict(state["counters"])
            depth = sum(1 for _ in QUEUE.glob("*.json"))
            self._send({
                "ok": True,
                "uptime_s": round(time.time() - boot_time, 1),
                "queue_depth": depth,
                "running": running,
                "workers": MAX_WORKERS,
                "active_threads": active_threads,
                "counters": counters,
            })
        elif self.path == "/jobs":
            with state_lock:
                jobs = {jid: {"status": r.get("status"), "name": r.get("name"),
                              "exit_code": r.get("exit_code"),
                              "duration_s": r.get("duration_s")}
                        for jid, r in state["jobs"].items()}
            self._send({"jobs": jobs})
        else:
            self._send({"error": "not found"}, 404)


def reap_orphans():
    """Jobs claimed (active/) by a dead daemon go back to pending."""
    moved = 0
    for spec in ACTIVE.glob("*.json"):
        try:
            (QUEUE / spec.name).write_bytes(spec.read_bytes())
            spec.unlink()
            moved += 1
        except Exception as e:
            log(f"WARN: could not reap {spec.name}: {e}")
    with state_lock:
        for rec in state["jobs"].values():
            if rec.get("status") == "running":
                rec["status"] = "pending"
    if moved:
        log(f"reaped {moved} orphaned active job(s) back to queue")
    save_state()


def on_term(signum, frame):
    log("SIGTERM/SIGINT — draining (no new jobs), waiting for workers")
    shutdown.set()


def main():
    PID_FILE.write_text(str(os.getpid()))
    load_state()
    reap_orphans()
    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)
    server = HTTPServer(("127.0.0.1", PORT), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log(f"buildsrvd up: root={ROOT} port={PORT} workers={MAX_WORKERS}")
    try:
        worker_loop()
    finally:
        server.shutdown()
        log("buildsrvd down")


if __name__ == "__main__":
    main()
