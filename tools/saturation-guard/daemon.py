#!/usr/bin/env python3
"""saturation-guard: cell-side supervisor/reaper daemon for the hatch cell.

First-class patch for debate 2c7ca733 (converged: lane-1 pro seq 2, lane-3 pro
seq 4, lane-6 synthesis seq 3, lane-7 synthesis seq 5; lane-4 con seq 6
addressed via forensics leases + iowait gating).

What it does:
  - Tracks every process's disk I/O rate via /proc/PID/io and D-state time.
  - Watches system iowait via /proc/stat. Actions are GATED on sustained
    iowait (default: 60s avg wa% > 30) -- the crash was 50-80% iowait, NOT
    compute, so caps are iowait-aware, not CPU-load-aware.
  - Violation ladder per process (oracle 2c7ca733, winner seq 7):
    flag (attribution) -> throttle (ionice idle + nice 19, unleased only)
    -> page (structured JSONL event; leased violators are page-only).
    The SIGTERM/SIGKILL ladder from the pre-verdict build exists in code
    but is DEFAULT-OFF (kill_enabled=false): the standing verdict says
    "ionice plus page, never kill". Enabling it contradicts the verdict.
  - Orphaned processes (PPID 1) are the prime suspect class (the killer grep
    was orphaned) but actions are driven by measured I/O, not names.
  - Forensics leases (lane-4 con + lane-7 io-lease registry): a declared
    forensics job drops a lease (guard-local leases/<pid>.json or the
    shared ~/workspace/bin/.io-leases/<pid>) and gets 4x I/O headroom and
    page-only treatment -- never throttled, never killed.
    The guard cannot fratricide declared work.
  - Self-protection: never touches PID 1, kernel threads, itself, or
    processes matching never_touch (hatch daemon, squawk, pitchfork...).

This is a DAEMON, not a cron job: it runs its own tick loop. Idempotent
start via pidfile + fcntl lock.

CPU caps: the cell grants no cgroup delegation (/sys/fs/cgroup is root-owned),
so the CPU lever is nice-deprioritization; the I/O lever (ionice idle class +
kill ladder) is the primary one, which matches the measured failure mode.

Usage:
  daemon.py start [--foreground] [--config PATH]
  daemon.py stop
  daemon.py status
  daemon.py lease --pid N --minutes M --reason "..." [--by NAME]
  daemon.py release --pid N
"""

import argparse
import errno
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
from collections import deque

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(STATE_DIR, "config.toml")

SIGTERM = signal.SIGTERM
SIGKILL = signal.SIGKILL


# ---------------------------------------------------------------- config

DEFAULTS = {
    "daemon": {"tick_secs": 5, "pidfile": "saturation-guard.pid",
               "log_dir": "logs", "lease_dir": "leases",
               "metrics_file": "metrics.json", "max_log_mb": 10},
    "iowait": {"gate_enabled": True, "window_secs": 60, "threshold_pct": 30.0},
    "io": {"read_mbps": 50.0, "write_mbps": 20.0, "sustain_secs": 60,
           "dstate_ticks": 12},
    "actions": {"throttle_first": True,
                # Oracle verdict 2c7ca733 (seq 7, 2026-09-19): ionice +
                # attribution + paging, NEVER killing. The SIGTERM/SIGKILL
                # ladder exists in code but is default-OFF; kill_enabled=true
                # is an explicit operator opt-in that contradicts the
                # standing verdict and must never be the default.
                "kill_enabled": False,
                "kill_grace_secs": 120, "term_grace_secs": 15},
    "protect": {"never_touch_comm": ["^hatch(-execd)?$", "^sshd$",
                                     "^systemd$"],
                # cmdline tokens: distinctive daemon script/binary names only.
                # NEVER a bare path substring like "hatch" -- /home/hatch
                # appears in nearly every cmdline and would protect everything.
                "never_touch_cmdline": ["squawk-ws-client", "squawk-push",
                                        "ws_daemon", "pitchfork",
                                        "saturation-guard"],
                "lease_io_multiplier": 4.0},
}


def load_config(path):
    cfg = {k: dict(v) for k, v in DEFAULTS.items()}
    if tomllib and os.path.exists(path):
        with open(path, "rb") as f:
            user = tomllib.load(f)
        for section, vals in user.items():
            if section in cfg and isinstance(vals, dict):
                cfg[section].update(vals)
    # resolve relative paths against STATE_DIR
    d = cfg["daemon"]
    for key in ("pidfile", "log_dir", "lease_dir", "metrics_file"):
        if not os.path.isabs(d[key]):
            d[key] = os.path.join(STATE_DIR, d[key])
    return cfg


# ---------------------------------------------------------------- logging

class JsonLog:
    def __init__(self, path, max_mb):
        self.path = path
        self.max_bytes = int(max_mb * 1024 * 1024)
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def emit(self, event, level="info", **fields):
        rec = {"ts": time.time(), "ts_iso": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "level": level, "event": event}
        rec.update(fields)
        line = json.dumps(rec, default=str)
        try:
            if os.path.exists(self.path) and \
                    os.path.getsize(self.path) > self.max_bytes:
                os.replace(self.path, self.path + ".1")
            with open(self.path, "a") as f:
                f.write(line + "\n")
        except OSError:
            pass
        if level in ("warning", "error", "critical"):
            print(line, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- /proc helpers

def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except (OSError, IOError):
        return None


def parse_stat(pid):
    """Return (comm, state, ppid) or None."""
    data = read_file(f"/proc/{pid}/stat")
    if not data:
        return None
    try:
        lparen = data.index("(")
        rparen = data.rindex(")")
        comm = data[lparen + 1:rparen]
        rest = data[rparen + 2:].split()
        return comm, rest[0], int(rest[1])
    except (ValueError, IndexError):
        return None


def read_io(pid):
    """Return (read_bytes, write_bytes) or None."""
    data = read_file(f"/proc/{pid}/io")
    if not data:
        return None
    rb = wb = None
    for line in data.splitlines():
        if line.startswith("read_bytes:"):
            rb = int(line.split(":")[1].strip())
        elif line.startswith("write_bytes:"):
            wb = int(line.split(":")[1].strip())
    if rb is None:
        return None
    return rb, wb


def read_cmdline(pid):
    data = read_file(f"/proc/{pid}/cmdline")
    if data is None:
        return ""
    return data.replace("\x00", " ").strip()


def sample_cpu():
    """Return (iowait_ticks, total_ticks) from /proc/stat aggregate line."""
    data = read_file("/proc/stat")
    if not data:
        return None
    for line in data.splitlines():
        if line.startswith("cpu "):
            parts = line.split()
            vals = [int(x) for x in parts[1:8]]  # u,n,s,idle,iowait,irq,soft
            return vals[4], sum(vals)
    return None


# ---------------------------------------------------------------- daemon

class Reaper:
    def __init__(self, cfg):
        self.cfg = cfg
        self.log = JsonLog(os.path.join(cfg["daemon"]["log_dir"], "reaper.log"),
                           cfg["daemon"]["max_log_mb"])
        self.me = os.getpid()
        self.procs = {}          # pid -> tracking dict
        self.cpu_samples = deque()  # (ts, iowait, total)
        self.metrics = {"violations": 0, "throttles": 0, "terms": 0,
                        "kills": 0, "pages": 0, "lease_skips": 0,
                        "scans": 0, "gate_closed_ticks": 0}
        self.start_ts = time.time()
        self.running = True
        self.patterns_comm = [re.compile(p) for p in
                              cfg["protect"]["never_touch_comm"]]
        self.patterns_cmd = [re.compile(p) for p in
                             cfg["protect"]["never_touch_cmdline"]]
        os.makedirs(cfg["daemon"]["lease_dir"], exist_ok=True)

    # -- protection -------------------------------------------------
    def protected(self, pid, comm, cmdline):
        if pid in (1, self.me):
            return True
        st = parse_stat(pid)
        if st and st[2] == 0:      # kernel thread
            return True
        if any(p.search(comm) for p in self.patterns_comm):
            return True
        return any(p.search(cmdline) for p in self.patterns_cmd)

    # -- leases (lane-4 con: declared forensics work is never killed;
    #           verdict 2c7ca733 seq 7: leased violators are page-only) --
    # Two sources: guard-local leases/<pid>.json and lane-7's shared
    # fleet registry ~/workspace/bin/.io-leases/<pid> ("<expiry> <reason>").
    # The verdict's implementation notes say to fold the io-lease registry
    # into the watchdog bundle; both are honored here.
    SHARED_LEASE_DIR = os.path.expanduser("~/workspace/bin/.io-leases")

    def get_lease(self, pid):
        now = time.time()
        path = os.path.join(self.cfg["daemon"]["lease_dir"], f"{pid}.json")
        try:
            with open(path) as f:
                lease = json.load(f)
            if lease.get("pid") == pid and \
                    lease.get("expires", 0) >= now:
                return lease
        except (OSError, ValueError):
            pass
        else:
            try:  # stale local lease: clean up
                os.unlink(path)
            except OSError:
                pass
        try:
            with open(os.path.join(self.SHARED_LEASE_DIR,
                                   str(pid))) as f:
                parts = f.read().strip().split(None, 1)
            if parts and float(parts[0]) >= now:
                return {"pid": pid, "expires": float(parts[0]),
                        "reason": parts[1] if len(parts) > 1 else "",
                        "by": "io-lease", "shared": True}
        except (OSError, ValueError):
            pass
        return None

    # -- iowait gate --------------------------------------------------
    def iowait_pct(self):
        now = time.time()
        s = sample_cpu()
        if s:
            self.cpu_samples.append((now, s[0], s[1]))
        window = self.cfg["iowait"]["window_secs"]
        while self.cpu_samples and now - self.cpu_samples[0][0] > window:
            self.cpu_samples.popleft()
        if len(self.cpu_samples) < 2:
            return 0.0
        t0, io0, tot0 = self.cpu_samples[0]
        t1, io1, tot1 = self.cpu_samples[-1]
        dtot = tot1 - tot0
        if dtot <= 0:
            return 0.0
        return 100.0 * (io1 - io0) / dtot

    # -- actions ------------------------------------------------------
    def throttle(self, pid, info):
        ok = True
        try:
            subprocess.run(["ionice", "-c3", "-p", str(pid)],
                           capture_output=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            ok = False
        try:
            subprocess.run(["renice", "-n", "19", "-p", str(pid)],
                           capture_output=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            ok = False
        self.metrics["throttles"] += 1
        self.log.emit("throttle", pid=pid, comm=info["comm"],
                      read_mbps=round(info["rate_r"], 1),
                      write_mbps=round(info["rate_w"], 1),
                      orphan=info["ppid"] == 1, ionice_idle=ok)

    def terminate(self, pid, info):
        try:
            os.kill(pid, SIGTERM)
            self.metrics["terms"] += 1
            self.log.emit("sigterm", pid=pid, comm=info["comm"],
                          read_mbps=round(info["rate_r"], 1),
                          write_mbps=round(info["rate_w"], 1),
                          orphan=info["ppid"] == 1)
            return True
        except ProcessLookupError:
            return False
        except OSError as e:
            self.log.emit("sigterm_failed", level="warning", pid=pid,
                          error=str(e))
            return False

    def kill(self, pid, info):
        try:
            os.kill(pid, SIGKILL)
            self.metrics["kills"] += 1
            self.log.emit("sigkill", level="warning", pid=pid,
                          comm=info["comm"],
                          read_mbps=round(info["rate_r"], 1),
                          write_mbps=round(info["rate_w"], 1),
                          orphan=info["ppid"] == 1)
            return True
        except ProcessLookupError:
            return False
        except OSError as e:
            self.log.emit("sigkill_failed", level="error", pid=pid,
                          error=str(e))
            return False

    def page(self, pid, info, lease, reason):
        """Verdict 2c7ca733 (seq 7) paging: structured attribution event.

        The page path is logs/reaper.log JSONL + metrics.json flags,
        consumed by the 2m saturation-watchdog cron / fleet channel.
        A page never throttles, never signals -- it attributes."""
        self.metrics["pages"] += 1
        self.log.emit("page", level="warning", pid=pid, comm=info["comm"],
                      read_mbps=round(info["rate_r"], 1),
                      write_mbps=round(info["rate_w"], 1),
                      orphan=info["ppid"] == 1, leased=bool(lease),
                      lease_reason=(lease or {}).get("reason", ""),
                      reason=reason)
        info["page_ts"] = time.time()

    # -- main tick ----------------------------------------------------
    def tick(self):
        now = time.time()
        wa = self.iowait_pct()
        gate_open = (not self.cfg["iowait"]["gate_enabled"] or
                     wa >= self.cfg["iowait"]["threshold_pct"])
        if not gate_open:
            self.metrics["gate_closed_ticks"] += 1
        self.metrics["scans"] += 1

        io_cfg = self.cfg["io"]
        act_cfg = self.cfg["actions"]
        mult = self.cfg["protect"]["lease_io_multiplier"]
        seen = set()
        flags = []

        for pid_str in os.listdir("/proc"):
            if not pid_str.isdigit():
                continue
            pid = int(pid_str)
            st = parse_stat(pid)
            io = read_io(pid)
            if not st or not io:
                continue
            comm, state, ppid = st
            cmdline = read_cmdline(pid)
            if self.protected(pid, comm, cmdline):
                self.procs.pop(pid, None)
                continue
            seen.add(pid)

            prev = self.procs.get(pid)
            if prev is None:
                self.procs[pid] = prev = {
                    "comm": comm, "ppid": ppid, "last_r": io[0],
                    "last_w": io[1], "last_t": now, "rate_r": 0.0,
                    "rate_w": 0.0, "viol_since": None, "dstreak": 0,
                    "stage": "new", "throttle_ts": 0, "term_ts": 0,
                }
            dt = now - prev["last_t"]
            if dt > 0:
                prev["rate_r"] = (io[0] - prev["last_r"]) / dt / 1e6
                prev["rate_w"] = (io[1] - prev["last_w"]) / dt / 1e6
                prev["last_r"], prev["last_w"], prev["last_t"] = \
                    io[0], io[1], now
            prev["comm"], prev["ppid"] = comm, ppid
            prev["dstreak"] = prev["dstreak"] + 1 if state == "D" else 0

            lease = self.get_lease(pid)
            r_thr = io_cfg["read_mbps"] * (mult if lease else 1.0)
            w_thr = io_cfg["write_mbps"] * (mult if lease else 1.0)
            violating = (prev["rate_r"] > r_thr or
                         prev["rate_w"] > w_thr or
                         prev["dstreak"] >= io_cfg["dstate_ticks"])
            if violating and prev["viol_since"] is None:
                prev["viol_since"] = now
                self.metrics["violations"] += 1
                self.log.emit("flag", pid=pid, comm=comm, ppid=ppid,
                              read_mbps=round(prev["rate_r"], 1),
                              write_mbps=round(prev["rate_w"], 1),
                              dstate_ticks=prev["dstreak"],
                              iowait_pct=round(wa, 1), leased=bool(lease),
                              orphan=ppid == 1, gate_open=gate_open)
            elif not violating:
                if prev["stage"] != "new":
                    self.log.emit("recovered", pid=pid, comm=comm)
                prev["viol_since"] = None
                prev["stage"] = "new"

            if violating:
                flags.append({"pid": pid, "comm": comm,
                              "read_mbps": round(prev["rate_r"], 1),
                              "write_mbps": round(prev["rate_w"], 1),
                              "stage": prev["stage"],
                              "leased": bool(lease), "orphan": ppid == 1,
                              "viol_secs": round(now - prev["viol_since"], 1)})
                if not gate_open:
                    continue  # observe only; iowait gate closed
                age = now - prev["viol_since"]
                kill_enabled = bool(act_cfg.get("kill_enabled", False))
                if prev["stage"] == "new" and \
                        age >= io_cfg["sustain_secs"]:
                    if lease:
                        # Verdict seq 7: leased -> page only, never throttle.
                        self.page(pid, prev, lease, reason="leased")
                        self.metrics["lease_skips"] += 1
                        prev["stage"] = "paged"
                    elif act_cfg["throttle_first"]:
                        self.throttle(pid, prev)
                        prev["stage"] = "throttled"
                        prev["throttle_ts"] = now
                    else:
                        prev["stage"] = "throttled"
                        prev["throttle_ts"] = now - \
                            act_cfg["kill_grace_secs"]
                elif prev["stage"] == "paged" and \
                        now - prev.get("page_ts", 0) >= \
                        act_cfg["kill_grace_secs"]:
                    # leased violator persists: keep paging, never act
                    self.page(pid, prev, lease, reason="leased_persist")
                    self.metrics["lease_skips"] += 1
                elif prev["stage"] == "throttled" and \
                        now - prev["throttle_ts"] >= \
                        act_cfg["kill_grace_secs"]:
                    if kill_enabled:
                        if self.terminate(pid, prev):
                            prev["stage"] = "termed"
                            prev["term_ts"] = now
                    else:
                        # kill ladder disabled per verdict: re-throttle is a
                        # no-op (already idle-class); re-page instead.
                        self.page(pid, prev, None,
                                  reason="escalation_kill_disabled")
                        prev["throttle_ts"] = now  # re-page later
                elif prev["stage"] == "termed" and \
                        now - prev["term_ts"] >= act_cfg["term_grace_secs"]:
                    if kill_enabled and not lease:
                        self.kill(pid, prev)
                        prev["stage"] = "killed"
                    elif not kill_enabled:
                        self.page(pid, prev, None,
                                  reason="escalation_kill_disabled")
                        prev["term_ts"] = now

        for pid in [p for p in self.procs if p not in seen]:
            del self.procs[pid]

        # top I/O consumers for metrics
        top = sorted(
            ((p, v["comm"], v["rate_r"], v["rate_w"]) for p, v in
             self.procs.items()),
            key=lambda t: t[2] + t[3], reverse=True)[:5]
        self.write_metrics(wa, gate_open, flags, top)

    def write_metrics(self, wa, gate_open, flags, top):
        m = {
            "ts": time.time(),
            "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "daemon_pid": self.me,
            "uptime_secs": round(time.time() - self.start_ts, 1),
            "iowait_pct": round(wa, 1),
            "iowait_gate_open": gate_open,
            "tracked_pids": len(self.procs),
            "flags": flags,
            "top_io": [{"pid": p, "comm": c,
                        "read_mbps": round(r, 1),
                        "write_mbps": round(w, 1)} for p, c, r, w in top],
        }
        m.update(self.metrics)
        path = self.cfg["daemon"]["metrics_file"]
        tmp = path + ".tmp"
        try:
            with open(tmp, "w") as f:
                json.dump(m, f, indent=1)
            os.replace(tmp, path)
        except OSError:
            pass

    def run(self):
        self.log.emit("start", pid=self.me,
                      config={s: self.cfg[s] for s in
                              ("iowait", "io", "actions")})
        tick = self.cfg["daemon"]["tick_secs"]

        def handle(sig, frm):
            self.running = False

        signal.signal(SIGTERM, handle)
        signal.signal(signal.SIGINT, handle)
        while self.running:
            try:
                self.tick()
            except Exception as e:  # never die on a bad tick
                self.log.emit("tick_error", level="error", error=str(e))
            # poll-await in small slices so shutdown is prompt
            end = time.time() + tick
            while self.running and time.time() < end:
                time.sleep(0.2)
        self.log.emit("stop", pid=self.me)


# ---------------------------------------------------------------- CLI

def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def cmd_start(args):
    cfg = load_config(args.config)
    pidfile = cfg["daemon"]["pidfile"]
    # The pidfile itself is the mutex: the live daemon holds LOCK_EX on it
    # for its whole lifetime. A second start fails the lock -> reports the
    # live pid and exits 0 (idempotent).
    lockf = open(pidfile, "a+")
    try:
        fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lockf.seek(0)
        try:
            old = int((lockf.read() or "0").strip())
        except ValueError:
            old = 0
        if old and pid_alive(old):
            print(f"saturation-guard: already running (pid {old})")
            return 0
        # lock held but pid dead: previous holder crashed; steal it
        try:
            fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("saturation-guard: cannot acquire pidfile lock; aborting")
            return 1
    if not args.foreground:
        # double fork; the grandchild inherits lockf and keeps the lock
        if os.fork() > 0:
            sys.exit(0)
        os.setsid()
        if os.fork() > 0:
            sys.exit(0)
        sys.stdout.flush()
        sys.stderr.flush()
        with open(os.devnull, "r") as dn:
            os.dup2(dn.fileno(), 0)
        with open(os.devnull, "a+") as dn:
            os.dup2(dn.fileno(), 1)
            os.dup2(dn.fileno(), 2)
    lockf.seek(0)
    lockf.truncate()
    lockf.write(str(os.getpid()))
    lockf.flush()
    try:
        Reaper(cfg).run()
    finally:
        try:
            os.unlink(pidfile)
        except OSError:
            pass
    return 0


def cmd_stop(args):
    cfg = load_config(args.config)
    pidfile = cfg["daemon"]["pidfile"]
    try:
        with open(pidfile) as f:
            pid = int(f.read().strip())
    except (OSError, ValueError):
        print("saturation-guard: not running (no pidfile)")
        return 0
    if not pid_alive(pid):
        print("saturation-guard: stale pidfile; cleaning")
        try:
            os.unlink(pidfile)
        except OSError:
            pass
        return 0
    os.kill(pid, SIGTERM)
    for _ in range(50):  # 10s
        if not pid_alive(pid):
            break
        time.sleep(0.2)
    else:
        os.kill(pid, SIGKILL)
    print(f"saturation-guard: stopped (pid {pid})")
    return 0


def cmd_status(args):
    cfg = load_config(args.config)
    pidfile = cfg["daemon"]["pidfile"]
    running, pid = False, None
    try:
        with open(pidfile) as f:
            pid = int(f.read().strip())
        running = pid_alive(pid)
    except (OSError, ValueError):
        pass
    print(f"running: {running}" + (f" (pid {pid})" if running else ""))
    mpath = cfg["daemon"]["metrics_file"]
    if os.path.exists(mpath):
        with open(mpath) as f:
            m = json.load(f)
        for k in ("ts_iso", "uptime_secs", "iowait_pct", "iowait_gate_open",
                  "tracked_pids", "scans", "violations", "throttles",
                  "terms", "kills", "pages", "lease_skips",
                  "gate_closed_ticks"):
            print(f"{k}: {m.get(k)}")
        if m.get("flags"):
            print("flags:")
            for fl in m["flags"]:
                print(f"  pid={fl['pid']} comm={fl['comm']} "
                      f"r={fl['read_mbps']}MB/s w={fl['write_mbps']}MB/s "
                      f"stage={fl['stage']} leased={fl['leased']} "
                      f"orphan={fl['orphan']}")
    else:
        print("metrics: none yet")
    return 0


def cmd_lease(args):
    cfg = load_config(args.config)
    lease = {"pid": args.pid,
             "expires": time.time() + args.minutes * 60,
             "reason": args.reason, "by": args.by,
             "created_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime())}
    path = os.path.join(cfg["daemon"]["lease_dir"], f"{args.pid}.json")
    with open(path, "w") as f:
        json.dump(lease, f, indent=1)
    print(f"lease granted: pid {args.pid} for {args.minutes} min "
          f"({args.reason})")
    return 0


def cmd_release(args):
    cfg = load_config(args.config)
    path = os.path.join(cfg["daemon"]["lease_dir"], f"{args.pid}.json")
    try:
        os.unlink(path)
        print(f"lease released: pid {args.pid}")
    except OSError as e:
        if e.errno == errno.ENOENT:
            print(f"no lease for pid {args.pid}")
        else:
            raise
    return 0


def main():
    ap = argparse.ArgumentParser(prog="saturation-guard")
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("--foreground", action="store_true")
    sub.add_parser("stop")
    sub.add_parser("status")
    lz = sub.add_parser("lease")
    lz.add_argument("--pid", type=int, required=True)
    lz.add_argument("--minutes", type=int, required=True)
    lz.add_argument("--reason", required=True)
    lz.add_argument("--by", default="fleet")
    rel = sub.add_parser("release")
    rel.add_argument("--pid", type=int, required=True)
    args = ap.parse_args()
    return {"start": cmd_start, "stop": cmd_stop, "status": cmd_status,
            "lease": cmd_lease, "release": cmd_release}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
