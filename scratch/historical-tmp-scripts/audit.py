#!/usr/bin/env python3
"""kernel-profiles/audit.py — snapshot and compare kernel profiles (bore vs server).

Part of the kernel-profiles tree (system-tuning/limine/kernel-profiles/).
The audit tool that makes a bore-vs-server comparison easy: snapshot the
currently-booted kernel now, boot the other profile later, snapshot again,
then `compare` the two JSONs. No reboots, no config edits — observe only.

Subcommands:
  snapshot [--out PATH] [name]   capture config + run the benchmark suite
  compare <a.json> <b.json>      side-by-side table of config + benchmark deltas
  schema                         print the snapshot JSON schema (documentation)

Default snapshot path: baselines/<kernel-release>-<YYYYMMDD>.json
next to this script.

stdlib-only python3. numpy is optional (matmul benchmark is skipped if absent).
The benchmark suite is a one-shot ~60-90s load on the box — not a daemon.
"""
import argparse
import datetime
import json
import math
import os
import platform
import socket
import statistics
import subprocess
import sys
import time

TOOL = "kernel-audit"
VERSION = 1
KP_ROOT = os.path.dirname(os.path.abspath(__file__))


def _run(cmd, timeout=15):
    """Run cmd, return (rc, stdout_str). Never raises."""
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           timeout=timeout, check=False)
        return p.returncode, p.stdout.decode("utf-8", "replace")
    except Exception:
        return -1, ""


def _read(path):
    """Read a file, return stripped str, or None."""
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return None


def _read_lines(path):
    try:
        with open(path) as f:
            return [l.rstrip("\n") for l in f]
    except Exception:
        return []


# ---------------------------------------------------------------- config ---

def detect_scheduler():
    """BORE vs stock EEVDF/CFS, layered detection. Returns (name, evidence)."""
    rel = platform.uname().release
    # 1. BORE exposes kernel.sched_bore on CachyOS bore kernels
    v = _read("/proc/sys/kernel/sched_bore")
    if v is not None and v != "":
        return ("BORE", "kernel.sched_bore=%s" % v)
    # 2. dmesg boot lines
    rc, out = _run(["dmesg"], timeout=10)
    low = out.lower()
    if "bore" in low:
        for line in out.splitlines():
            if "bore" in line.lower():
                return ("BORE", line.strip()[:120])
    # 3. release string convention
    if "bore" in rel:
        return ("BORE?", "release string contains 'bore' but no sched_bore sysctl / dmesg line")
    return ("EEVDF", "no BORE markers; stock CachyOS scheduler assumed")


def cpu_info():
    model, cores, threads = None, 0, 0
    for line in _read_lines("/proc/cpuinfo"):
        if line.startswith("model name"):
            if model is None:
                model = line.split(":", 1)[1].strip()
        if line.startswith("processor"):
            threads += 1
    rc, out = _run(["lscpu"], timeout=10)
    for line in out.splitlines():
        if line.startswith("Core(s) per socket"):
            try:
                cores = int(line.split(":")[1])
            except Exception:
                pass
    return {"model": model, "threads": threads, "cores": cores or None}


def governors():
    g = {}
    base = "/sys/devices/system/cpu"
    try:
        cpus = [d for d in os.listdir(base) if d.startswith("cpu") and d[3:].isdigit()]
    except Exception:
        return g
    for c in sorted(cpus, key=lambda x: int(x[3:])):
        g[c] = _read(os.path.join(base, c, "cpufreq", "scaling_governor"))
    return g


def sysctl_dir(path, prefix_filter=None):
    """Read every readable scalar file directly under path."""
    out = {}
    try:
        names = os.listdir(path)
    except Exception:
        return out
    for n in sorted(names):
        if prefix_filter and not n.startswith(prefix_filter):
            continue
        p = os.path.join(path, n)
        if not os.path.isfile(p):
            continue
        v = _read(p)
        if v is not None and "\n" not in v and len(v) < 128:
            out[n] = v
    return out


def meminfo(keys=("MemTotal", "MemFree", "MemAvailable", "Buffers", "Cached",
                  "SwapTotal", "SwapFree", "HugePages_Total", "Hugepagesize",
                  "Shmem", "SReclaimable")):
    out = {}
    for line in _read_lines("/proc/meminfo"):
        parts = line.split(":")
        if len(parts) == 2 and parts[0] in keys:
            out[parts[0]] = parts[1].strip()
    return out


def nvidia_driver():
    rc, out = _run(["nvidia-smi", "--query-gpu=driver_version",
                    "--format=csv,noheader"], timeout=15)
    if rc == 0 and out.strip():
        return out.strip().splitlines()[0]
    return None


def booted_profile():
    """Best-effort profile slug from the kernel-profiles monitor script."""
    mon = os.path.join(KP_ROOT, "ui", "kernel-profiles-monitor.sh")
    if not os.access(mon, os.X_OK):
        return None
    rc, out = _run([mon], timeout=15)
    for line in out.splitlines():
        if line.startswith("booted_profile="):
            return line.split("=", 1)[1] or None
    return None


def collect_config():
    sched_name, sched_evidence = detect_scheduler()
    up = _read("/proc/uptime")
    uptime_s = None
    if up:
        try:
            uptime_s = float(up.split()[0])
        except Exception:
            pass
    cfg = {
        "kernel_release": platform.uname().release,
        "kernel_version": platform.uname().version,
        "machine": platform.uname().machine,
        "cmdline": _read("/proc/cmdline"),
        "profile": booted_profile(),
        "scheduler": {"name": sched_name, "evidence": sched_evidence},
        "cpu": cpu_info(),
        "governors": governors(),
        "sched_tunables": sysctl_dir("/proc/sys/kernel", "sched_"),
        "vm_tunables": sysctl_dir("/proc/sys/vm"),
        "meminfo": meminfo(),
        "nvidia_driver": nvidia_driver(),
        "loadavg": list(os.getloadavg()),
        "uptime_s": uptime_s,
    }
    return cfg


# ------------------------------------------------------------ benchmarks ---

def bench_ctx_switch(iters=10000):
    """socketpair ping-pong across fork(): 2 ctx switches per round-trip."""
    a, b = socket.socketpair()
    pid = os.fork()
    if pid == 0:  # child: echo
        a.close()
        try:
            while True:
                data = b.recv(1)
                if not data:
                    break
                b.sendall(b"X")
        except Exception:
            pass
        os._exit(0)
    b.close()
    try:
        # warmup
        for _ in range(200):
            a.sendall(b"X")
            a.recv(1)
        t0 = time.perf_counter()
        for _ in range(iters):
            a.sendall(b"X")
            a.recv(1)
        dt = time.perf_counter() - t0
    finally:
        try:
            a.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        a.close()
        os.waitpid(pid, 0)
    return {"us_per_switch": dt / iters / 2 * 1e6, "iters": iters}


def bench_fork_exec(iters=1000):
    """Wall time per fork+exec of /bin/true."""
    devnull = open(os.devnull, "w")
    try:
        t0 = time.perf_counter()
        for _ in range(iters):
            subprocess.run(["/bin/true"], stdout=devnull, stderr=devnull,
                           check=True)
        dt = time.perf_counter() - t0
    finally:
        devnull.close()
    return {"ms_per_spawn": dt / iters * 1e3, "iters": iters}


def bench_memcpy(mb=256, iters=4):
    """Single-threaded bytearray copy bandwidth, best of N."""
    n = mb * 1024 * 1024
    src = bytearray(n)
    dst = bytearray(n)
    for i in range(0, n, 4096):  # touch pages so we measure copy, not faults
        src[i] = i & 0xFF
    best = None
    for _ in range(iters):
        t0 = time.perf_counter()
        dst[:] = src
        dt = time.perf_counter() - t0
        if best is None or dt < best:
            best = dt
    return {"gb_per_s": n / best / 1e9, "mb": mb, "iters": iters,
            "best_of": True}


def bench_int_loop(iters=20_000_000):
    """Tight integer loop: ns per iteration (single thread, CPython)."""
    acc = 0
    t0 = time.perf_counter()
    for i in range(iters):
        acc += (i * 2654435761) & 0xFFFFFFFF
    dt = time.perf_counter() - t0
    return {"ns_per_iter": dt / iters * 1e9, "iters": iters,
            "checksum": acc & 0xFFFFFFFF}


def bench_matmul(n=1024, iters=5):
    """numpy matmul GFLOPS, best of N. None if numpy is absent."""
    try:
        import numpy as np
    except Exception:
        return None
    rng = np.random.default_rng(42)
    a = rng.random((n, n))
    b = rng.random((n, n))
    _ = a @ b  # warmup (BLAS thread-pool spin-up)
    best = None
    for _ in range(iters):
        t0 = time.perf_counter()
        c = a @ b
        dt = time.perf_counter() - t0
        if best is None or dt < best:
            best = dt
    flops = 2 * n ** 3
    return {"gflops": flops / best / 1e9, "n": n, "iters": iters,
            "best_of": True}


def run_benchmarks(progress=None):
    def say(msg):
        if progress:
            print(msg, flush=True)
    benches = {}
    say("[bench 1/5] context-switch latency (socketpair ping-pong)...")
    benches["ctx_switch"] = bench_ctx_switch()
    say("[bench 2/5] fork+exec spawn latency (1000x /bin/true)...")
    benches["fork_exec"] = bench_fork_exec()
    say("[bench 3/5] memory copy bandwidth (4x 256MB)...")
    benches["memcpy"] = bench_memcpy()
    say("[bench 4/5] integer-loop throughput (20M iters)...")
    benches["int_loop"] = bench_int_loop()
    say("[bench 5/5] numpy matmul (optional)...")
    mm = bench_matmul()
    benches["matmul"] = mm if mm is not None else {"skipped": "numpy not available"}
    return benches


# --------------------------------------------------------------- snapshot ---

def default_snapshot_path(name=None):
    d = os.path.join(KP_ROOT, "baselines")
    if name:
        fname = name if name.endswith(".json") else name + ".json"
    else:
        rel = platform.uname().release
        day = datetime.date.today().strftime("%Y%m%d")
        fname = "%s-%s.json" % (rel, day)
    return os.path.join(d, fname)


def cmd_snapshot(args):
    out = args.out or default_snapshot_path(args.name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print("collecting config...", flush=True)
    snap = {
        "meta": {
            "tool": TOOL,
            "version": VERSION,
            "taken_at": datetime.datetime.now(
                datetime.timezone.utc).isoformat(),
        },
        "config": collect_config(),
    }
    print("running benchmarks (~60-90s)...", flush=True)
    snap["benchmarks"] = run_benchmarks(progress=True)
    with open(out, "w") as f:
        json.dump(snap, f, indent=2, sort_keys=True)
        f.write("\n")
    print("snapshot -> %s" % out, flush=True)
    return out


# ---------------------------------------------------------------- compare ---

def _fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return "%.4g" % v
    return str(v)


def _changed(a, b):
    return "" if a == b else "  <--"


def cmd_compare(args):
    with open(args.a) as f:
        A = json.load(f)
    with open(args.b) as f:
        B = json.load(f)
    la = A["meta"].get("taken_at", "?")[:10]
    lb = B["meta"].get("taken_at", "?")[:10]
    ka = A["config"].get("kernel_release", "?")
    kb = B["config"].get("kernel_release", "?")
    print("kernel-audit compare")
    print("  A: %s (%s)" % (ka, la))
    print("  B: %s (%s)" % (kb, lb))
    print()
    print("== config ==")
    rows = []
    ca, cb = A["config"], B["config"]
    simple = ["kernel_release", "profile", "nvidia_driver", "machine"]
    for k in simple:
        rows.append((k, _fmt(ca.get(k)), _fmt(cb.get(k))))
    s, t = ca.get("scheduler", {}), cb.get("scheduler", {})
    rows.append(("scheduler", _fmt(s.get("name")), _fmt(t.get("name"))))
    for k in ("model",):
        rows.append(("cpu." + k, _fmt(ca.get("cpu", {}).get(k)),
                     _fmt(cb.get("cpu", {}).get(k))))
    rows.append(("cpu.threads",
                 _fmt(ca.get("cpu", {}).get("threads")),
                 _fmt(cb.get("cpu", {}).get("threads"))))
    # governors: collapse to unique set
    ga = sorted(set(str(v) for v in ca.get("governors", {}).values()))
    gb = sorted(set(str(v) for v in cb.get("governors", {}).values()))
    rows.append(("governors", ",".join(ga), ",".join(gb)))
    rows.append(("cmdline", _fmt(ca.get("cmdline")), _fmt(cb.get("cmdline"))))
    # tunables: union of keys, show only differing ones
    for section in ("sched_tunables", "vm_tunables"):
        sa, sb = ca.get(section, {}), cb.get(section, {})
        for k in sorted(set(sa) | set(sb)):
            va, vb = sa.get(k), sb.get(k)
            if va != vb:
                rows.append((section + "." + k, _fmt(va), _fmt(vb)))
    w = max(len(r[0]) for r in rows)
    wa = max(len(r[1]) for r in rows)
    for name, va, vb in rows:
        mark = _changed(va, vb)
        print("  %-*s  %-*s  %s%s" % (w, name, wa, va, vb, mark))
    print()
    print("== benchmarks (B vs A: + means B slower/bigger for latency, faster for throughput) ==")
    ba, bb = A.get("benchmarks", {}), B.get("benchmarks", {})
    metrics = [
        ("ctx_switch", "us_per_switch", "us/switch", "lower"),
        ("fork_exec", "ms_per_spawn", "ms/spawn", "lower"),
        ("memcpy", "gb_per_s", "GB/s", "higher"),
        ("int_loop", "ns_per_iter", "ns/iter", "lower"),
        ("matmul", "gflops", "GFLOPS", "higher"),
    ]
    for bench, key, unit, better in metrics:
        da = ba.get(bench, {})
        db = bb.get(bench, {})
        va = da.get(key)
        vb = db.get(key)
        if va is None or vb is None:
            print("  %-10s  A=%-12s B=%-12s (missing data)" %
                  (bench, _fmt(va), _fmt(vb)))
            continue
        if va == 0:
            delta = float("nan")
        else:
            delta = (vb - va) / abs(va) * 100.0
        if better == "lower":
            verdict = "B better" if delta < -1 else ("A better" if delta > 1 else "tie")
        else:
            verdict = "B better" if delta > 1 else ("A better" if delta < -1 else "tie")
        print("  %-10s  A=%-10s B=%-10s  %+7.1f%%  [%s]  (%s)" %
              (bench, _fmt(va) + " " + unit, _fmt(vb) + " " + unit,
               delta, verdict, key))
    print()
    print("done.")


def cmd_schema(_args):
    print(json.dumps({
        "meta": {"tool": TOOL, "version": VERSION,
                 "taken_at": "ISO-8601 UTC"},
        "config": {
            "kernel_release": "str (uname -r)",
            "kernel_version": "str", "machine": "str",
            "cmdline": "str (/proc/cmdline)",
            "profile": "str|null (kernel-profiles slug, best effort)",
            "scheduler": {"name": "BORE|EEVDF|BORE?",
                          "evidence": "str"},
            "cpu": {"model": "str", "threads": "int",
                    "cores": "int|null"},
            "governors": {"cpu0": "str|null", "...": "..."},
            "sched_tunables": {"/proc/sys/kernel/sched_*": "str"},
            "vm_tunables": {"/proc/sys/vm/*": "str"},
            "meminfo": {"MemTotal": "str", "...": "..."},
            "nvidia_driver": "str|null",
            "loadavg": [1, 5, 15],
            "uptime_s": "float|null",
        },
        "benchmarks": {
            "ctx_switch": {"us_per_switch": "float", "iters": "int"},
            "fork_exec": {"ms_per_spawn": "float", "iters": "int"},
            "memcpy": {"gb_per_s": "float", "mb": "int", "iters": "int",
                       "best_of": True},
            "int_loop": {"ns_per_iter": "float", "iters": "int",
                         "checksum": "int"},
            "matmul": {"gflops": "float", "n": "int", "iters": "int",
                       "best_of": True,
                       "or": {"skipped": "numpy not available"}},
        },
    }, indent=2))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="audit.py",
                                 description="kernel profile snapshot + compare")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot", help="capture config + run benchmarks")
    s.add_argument("--out", default=None, help="output JSON path")
    s.add_argument("name", nargs="?", default=None,
                   help="snapshot name (default: <uname -r>-<YYYYMMDD>)")
    s.set_defaults(fn=cmd_snapshot)
    c = sub.add_parser("compare", help="side-by-side table of two snapshots")
    c.add_argument("a"); c.add_argument("b")
    c.set_defaults(fn=cmd_compare)
    sc = sub.add_parser("schema", help="print the snapshot JSON schema")
    sc.set_defaults(fn=cmd_schema)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
