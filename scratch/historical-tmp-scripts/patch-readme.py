#!/usr/bin/env python3
"""Append the kernel-audit section to kernel-profiles README.md. Idempotent."""
import os

p = os.path.expanduser("~/sovereign/projects/shell/ii/system-tuning/limine/"
                       "kernel-profiles/README.md")
with open(p) as f:
    src = f.read()

if "## Kernel audit:" in src:
    print("ALREADY-PRESENT")
    raise SystemExit

section = '''
## Kernel audit: bore vs server comparison

`audit.py` (stdlib-only python3) snapshots the running kernel's config plus a
~60-90s benchmark suite, so a future boot into another profile can be
compared side-by-side. The tool only observes — it never reboots or edits
config.

```bash
./ui/kernel-profiles-cli.sh audit snapshot        # -> baselines/<uname -r>-<YYYYMMDD>.json
./ui/kernel-profiles-cli.sh audit snapshot bore   # named snapshot instead
./ui/kernel-profiles-cli.sh audit compare <a>.json <b>.json
```

Snapshot contents: `uname -r`, full cmdline, scheduler identity (BORE vs
stock EEVDF — layered: `kernel.sched_bore` sysctl, then dmesg, then the
release string), CPU model/threads, per-CPU governors, every
`/proc/sys/kernel/sched_*` and `/proc/sys/vm/*` tunable, meminfo, NVIDIA
driver version, loadavg, uptime. Benchmarks: socketpair context-switch
latency, fork+exec spawn latency (1000x /bin/true), memcpy bandwidth
(4x 256MB, best of), integer-loop throughput (20M iters), numpy matmul
(skipped gracefully when numpy is absent). `compare` prints config diffs
and benchmark deltas with a better/tie verdict per metric.

Baseline on file: `baselines/7.2.6-1-cachyos-bore-20260921.json` (bore,
2026-09-21). To complete the comparison: boot the server profile, run
`audit snapshot server`, then `audit compare` the two.
'''

with open(p, "a") as f:
    f.write(section)
print("APPENDED")
