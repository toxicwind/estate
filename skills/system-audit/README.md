![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/system-audit?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/system-audit?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/system-audit?style=for-the-badge)

# system-audit
Run BEFORE any perf/latency audit on awrawr-pc. Captures system context first: what the box IS, what "normal" looks like, and what's competing for resources right now.

## What it does
Pre-flight system auditing tool that captures hardware baseline, system load, top resource consumers, target process profiles, build contention indicators, network path information, and running fleet jobs to provide context for performance investigations.

## Why it matters
Prevents misleading performance investigations by establishing system context first - ensuring that perceived code slowness isn't actually caused by resource contention, hardware issues, or competing processes on the audit machine.

## Who it's for
Performance engineers, SREs, and developers investigating latency or throughput issues on the awrawr-pc machine who need to rule out system-level causes before diving into application code.

## Features
- **Hardware Baseline Comparison** - Diffs live readings against `hardware-baseline.json` (PASS/FAIL per item: cpu, threads, mem, gpu, disks, mitigations, zram, primary NIC)
- **Load & Pressure Analysis** - Reports load average + PSI (cpu/memory/io pressure - `some`/`full` avg10)
- **Top Resource Consumers** - Names actual system-wide CPU and RSS hogs
- **Target PID Profiling** - %CPU, RSS, thread count, fd count, context switches, /proc/io deltas, and children (catches broker-child churn)
- **Build Contention Detection** - Running compilers (bun/rustc/gcc/go) + mtimes of watched paths (fresh dist/omp = build, not app)
- **Network Path Analysis** - Interface errors, route to each `--target`, and DNS resolver information
- **Fleet Job Monitoring** - Lists running fleet jobs via `/home/toxic/fleet/jobs/bin/job list`
- **Passive Operation** - Reads procfs/sysfs only; never attaches to or instruments targets

## Quick Start
```bash
# Basic system audit
bin/sys_audit.sh

# Profile a target process
bin/sys_audit.sh --pid 1234

# Show route to provider IPs
bin/sys_audit.sh --target 8.8.8.8 --target 1.1.1.1

# Watch file mtime for build contention
bin/sys_audit.sh --path /home/toxic/sovereign/dist/omp

# Combine multiple options
bin/sys_audit.sh --pid 5678 --target 10.0.0.1 --path /tmp/build.log
```

## Configuration
- **Hardware Baseline**: `hardware-baseline.json` - Seeded from:
  - `sovereign/docs/HARDWARE_AUDIT_20260914.md`
  - Nightly `/var/lib/hw-audit/` audits (hw-audit.timer 03:17 MDT, root)
- **Known Hardware (awrawr-pc)**:
  - MSI PRO B650-VC WIFI (MS-7D78), BIOS AMI 1.L5 10/22/2025
  - AMD Ryzen 7 8700F 8C/16T, 2.6–5.05 GHz, amd-pstate-epp powersave
  - 64 GiB DDR5-6000 in A2/B2 (2×32 GiB)
  - NVIDIA RTX 3090 24 GB (sm_86), driver 610.43.03
  - Realtek RTL8125 2.5GbE wired primary; MT7922 wifi DOWN is expected
  - 4 disks, all SMART-passed: Samsung 870 QVO 1 TB, Seagate ST8000NT001 8 TB, WD SN850X 1 TB, Crucial E100 1 TB
  - Swap 200 GiB = zram0 62.4G + nvme0n1p4 138.3G (CachyOS default)
- **Intentional Quirks** (do NOT flag as problems):
  - `mitigations=off`, zram over zswap, cpufreq powersave/balance_performance,
  - nvidia-smi deprecation banner (cosmetic), DIMM mfr "Unknown" (BIOS reports generic UD5-6000),
  - decode-dimms empty (kernel lacks eeprom modules)

## Development
Modify the bash script at `/home/toxic/estate/skills/system-audit/bin/sys_audit.sh` to adjust auditing behavior. The script:
- Reads `/proc` and `/sys` filesystems for system information
- Compares against `hardware-baseline.json` for PASS/FAIL determinations
- Integrates with `/home/toxic/hw-audit.sh` (nightly hardware audit - read only)
- Follows pattern-forge latency doctrine: measure everything, fail-fast, keep the fast path hot

## License
Internal tool - refer to sovereign estate licensing

## Security
- **Passive Observation** - Reads procfs/sysfs only; never attaches, injects, or instruments targets
- **Read-Only Access** - All information gathered through standard system interfaces
- **Context-Only Purpose** - Designed to provide context for other audits, not to modify or interfere with systems
- **Baseline Comparison** - Uses known-good hardware profile for anomaly detection, not absolute thresholds