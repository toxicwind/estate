#!/usr/bin/env bash
# sys_audit.sh — system-context sweep for perf/latency audits on awrawr-pc.
# Passive only: reads procfs/sysfs, never attaches to processes.
# Usage: sys_audit.sh [--pid <pid>] [--target <ip>]... [--path <path>]...
# Part of the system-audit skill. Borrows from /home/toxic/hw-audit.sh (do not modify it).
set -u
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
BASELINE="$SCRIPT_DIR/../hardware-baseline.json"
PID=""; TARGETS=(); PATHS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --pid) PID="$2"; shift 2;;
    --target) TARGETS+=("$2"); shift 2;;
    --path) PATHS+=("$2"); shift 2;;
    *) shift;;
  esac
done
sec() { echo "=== $1 ==="; }
sec "HOST $(hostname) $(date -u '+%F %T UTC')"

sec "HARDWARE vs BASELINE"
if [ -f "$BASELINE" ] && command -v python3 >/dev/null; then
  BASELINE="$BASELINE" python3 - <<'PYEOF'
import json, os, re, subprocess
def sh(cmd):
    try: return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15).stdout.strip()
    except Exception: return ""
b = json.load(open(os.environ["BASELINE"]))
def check(name, expected, actual, ok=None):
    good = ok if ok is not None else (str(expected).lower() in str(actual).lower() or str(actual).lower() in str(expected).lower())
    print(("PASS " if good else "FAIL ") + name + " | expected: " + str(expected) + " | actual: " + str(actual))
cpu = sh("awk -F': ' '/model name/{print $2; exit}' /proc/cpuinfo")
check("cpu.model", b["machine"]["cpu"], cpu)
check("cpu.threads", b["cpu"]["threads"], sh("nproc"), ok=int(sh("nproc") or 0) == b["cpu"]["threads"])
mem_kb = int((sh("awk '/MemTotal/{print $2}' /proc/meminfo") or "0"))
check("mem.total_gib", b["memory"]["total_gib"], round(mem_kb/1048576, 1), ok=abs(mem_kb/1048576 - b["memory"]["total_gib"]) < 2)
gpu = sh("nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null")
check("gpu.model", b["gpu"]["model"], gpu.split(",")[0] if gpu else "nvidia-smi missing/failed")
check("gpu.driver", b["gpu"]["driver"], gpu.split(",")[1].strip() if "," in gpu else (gpu or "missing"),
      ok=(b["gpu"]["driver"] in gpu) if gpu else False)
mit = sh("cat /proc/cmdline")
check("mitigations=off (intentional)", "mitigations=off", "present" if "mitigations=off" in mit else "ABSENT",
      ok="mitigations=off" in mit)
zram = sh("ls /dev/zram0 2>/dev/null")
check("zram present (intentional over zswap)", "/dev/zram0", zram or "missing")
lsblk = sh("lsblk -dn -o NAME,MODEL 2>/dev/null")
for d in b["disks"]:
    present = d["dev"] in lsblk
    check("disk." + d["dev"], d["model"], "present" if present else "MISSING", ok=present)
iface = sh("ip -o link show enp12s0 2>/dev/null")
check("net.primary_iface", b["net"]["primary_iface"] + " UP", "UP" if ",UP" in iface else iface or "missing")
PYEOF
else
  echo "baseline file or python3 missing — skipping diff"
fi

sec "LOAD + PSI"
cat /proc/loadavg
for f in cpu memory io; do echo "-- pressure/$f:"; cat "/proc/pressure/$f" 2>/dev/null || echo missing; done

sec "TOP CPU"
ps -eo pid,pcpu,pmem,etime,comm --sort=-pcpu 2>/dev/null | head -11
sec "TOP RSS"
ps -eo pid,rss,pmem,comm --sort=-rss 2>/dev/null | head -11

if [ -n "$PID" ] && [ -d "/proc/$PID" ]; then
  sec "TARGET PID $PID"
  ps -o pid,pcpu,pmem,etime,args -p "$PID" 2>/dev/null
  echo "threads: $(awk '/^Threads/{print $2}' "/proc/$PID/status" 2>/dev/null)"
  echo "fds: $(ls "/proc/$PID/fd" 2>/dev/null | wc -l)"
  echo "ctxt_switches: $(grep -E 'voluntary|nonvoluntary' "/proc/$PID/status" 2>/dev/null | tr '\n' ' ')"
  echo "io: $(tr '\n' ' ' < "/proc/$PID/io" 2>/dev/null)"
  echo "children:"; ps --ppid "$PID" -o pid,pcpu,pmem,etime,args 2>/dev/null
fi

sec "BUILD CONTENTION"
ps -eo pid,etime,pcpu,args 2>/dev/null | grep -iE "bun build|rustc|cargo|gcc|g\\+\\+|go build|tsc --|esbuild" | grep -v grep | head -6 || true
echo "-- watched paths:"; for p in "${PATHS[@]}"; do [ -e "$p" ] && stat -c "%y %n" "$p"; done

sec "NET PATH"
ip -s link 2>/dev/null | grep -E "^[0-9]+: " | head -12
for t in "${TARGETS[@]}"; do echo "-- route to $t:"; ip route get "$t" 2>&1 | head -1; done
echo "-- resolver:"; grep "^nameserver" /etc/resolv.conf 2>/dev/null | head -3

sec "FLEET JOBS (running)"
/home/toxic/fleet/jobs/bin/job list 2>/dev/null | head -10
echo "=== END sys_audit ==="
