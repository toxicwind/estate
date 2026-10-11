---
name: system-audit
description: >
  System context capture before any latency or packet-trace audit. Records what the box is, what normal looks like for it, and what is competing for CPU, GPU, memory and IO at that moment, so a profile is never read without context. Triggers on: "system audit", "latency audit", "pcap", "system context".
---

# system-audit

Run BEFORE any perf/latency audit on awrawr-pc. A packet trace or profile
without system context is dumb — this captures the context first: what the
box IS, what "normal" looks like for it, and what's competing for resources
right now.

## When to use

- Before any streaming/latency/slowness investigation on awrawr-pc.
- When Chris says something "makes no sense" / "slows down for NO reason" —
  the cause is often build contention, a saturated box, or hardware drift,
  not the code being audited.
- As a pre-flight for pcap/tcpdump captures: run it at capture start and end
  so the trace has a system-context bracket.

## Usage (on awrawr-pc, passive only — reads procfs/sysfs, never attaches)

```
bin/sys_audit.sh [--pid <pid>] [--target <ip>]... [--path <path>]...
```

- `--pid`: profile a target process (%CPU, RSS, threads, fds, io, children).
- `--target`: show the route to a provider IP (confirms direct vs proxied path).
- `--path`: report mtime of a watched file (e.g. a rebuilt binary — catches
  build contention overlapping the slow window).

## hardware-baseline

`hardware-baseline.json` is this box's known-good profile, seeded from
`sovereign/docs/HARDWARE_AUDIT_20260914.md` and the nightly
`/var/lib/hw-audit/` audits (hw-audit.timer 03:17 MDT, root).
`sys_audit.sh` diffs live readings against it and prints PASS/FAIL per item.

Known hardware (awrawr-pc):
- MSI PRO B650-VC WIFI (MS-7D78), BIOS AMI 1.L5 10/22/2025
- AMD Ryzen 7 8700F 8C/16T, 2.6–5.05 GHz, amd-pstate-epp powersave
- 64 GiB DDR5-6000 in A2/B2 (2×32 GiB)
- NVIDIA RTX 3090 24 GB (sm_86), driver 610.43.03
- Realtek RTL8125 2.5GbE wired primary; MT7922 wifi DOWN is expected
- 4 disks, all SMART-passed: Samsung 870 QVO 1 TB (wear 090),
  Seagate ST8000NT001 8 TB, WD SN850X 1 TB, Crucial E100 1 TB
- Swap 200 GiB = zram0 62.4G + nvme0n1p4 138.3G (CachyOS default)

Intentional quirks — do NOT flag these as problems:
- `mitigations=off`, zram over zswap, cpufreq powersave/balance_performance,
  nvidia-smi deprecation banner (cosmetic), DIMM mfr "Unknown" (BIOS reports
  generic UD5-6000), decode-dimms empty (kernel lacks eeprom modules).

## What it checks

1. Hardware vs baseline (PASS/FAIL per item: cpu, threads, mem, gpu, disks,
   mitigations, zram, primary NIC).
2. Load average + PSI (cpu/memory/io pressure — `some`/`full` avg10).
3. Top CPU and top RSS consumers system-wide (names the actual hogs).
4. Target PID profile: %CPU, RSS, thread count, fd count, context switches,
   /proc/io deltas, children (catches broker-child churn).
5. Build contention: running compilers (bun/rustc/gcc/go) + mtimes of
   watched paths (a fresh 184 MB `dist/omp` at the slow window = the build,
   not the app).
6. Network path: interface errors, route to each `--target`, resolver.
7. Running fleet jobs (`/home/toxic/fleet/jobs/bin/job list`).

## Borrowed from

- `/home/toxic/hw-audit.sh` (nightly hardware audit — do not modify it;
  this skill only reads its output format).
- pattern-forge latency doctrine: measure everything, fail-fast, keep the fast path hot.

## Precedent

2026-09-15: Chris's live tau "slowed for NO reason" at 03:13:33 UTC.
System-context sweep showed a `bun scripts/build-binary.ts` (184 MB dist/omp)
started 03:13:27 UTC — 6 seconds before his complaint — saturating the 16-core
box. The tau engine was innocent; the build was the slowdown. A pcap alone
would never have shown that.
