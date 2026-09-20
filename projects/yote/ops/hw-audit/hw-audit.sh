#!/usr/bin/env bash
# hw-audit.sh — nightly hardware inventory audit (JSONL).
#
# MASTER: toxicwind/sovereign-projects projects/yote/ops/hw-audit/
# Live copy deployed to /home/toxic/hw-audit.sh (see hw-audit.service).
#
# Usage: hw-audit.sh <output.jsonl>
# Runs as root (hw-audit.timer, 03:17 MDT). Emits one JSON object per line,
# each with a "section" key. Schema mirrors hw-audit v2 (2026-09-14).
#
# Fixes incorporated from docs/HARDWARE_AUDIT_20260914.md:
#   - classic `cpuid` on Arch is a minimal tool, not classic-cpuid: the cpuid
#     branch is guarded on real capability (cpuid -1 -l 0 | grep -q .)
#     so it never emits header-only / empty records. kcpuid -r is the real dump.
set -uo pipefail

OUT="${1:?usage: hw-audit.sh <output.jsonl>}"
: > "$OUT" || { echo "cannot write $OUT" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

# emit <section> <key=value ...> — values are passed through python for JSON safety.
# Special values: @b64:<file> -> base64 of file contents; @raw:<file> -> file text.
emit() {
  local section="$1"; shift
  python3 - "$section" "$OUT" "$@" <<'EOF'
import json, sys, base64
section, out = sys.argv[1], sys.argv[2]
rec = {"section": section}
for kv in sys.argv[3:]:
    k, v = kv.split("=", 1)
    if v.startswith("@b64:"):
        try:
            rec[k] = base64.b64encode(open(v[5:], "rb").read()).decode()
            rec["kind"] = "b64"
        except OSError:
            rec[k] = None
    elif v.startswith("@raw:"):
        try:
            rec[k] = open(v[5:]).read()
        except OSError:
            rec[k] = None
    else:
        rec[k] = v
with open(out, "a") as f:
    f.write(json.dumps(rec) + "\n")
EOF
}

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# --- env --------------------------------------------------------------------
kernel="$(uname -r)"; arch="$(uname -m)"
distro="$(grep -m1 '^NAME=' /etc/os-release 2>/dev/null || echo unknown)"
hostjson="$(hostnamectl --json=short 2>/dev/null || echo '{}')"
emit env kernel="$kernel" distro="$distro" arch="$arch" host="$hostjson"

# --- dmi --------------------------------------------------------------------
if have dmidecode; then
  dmidecode >"$tmp/dmi.txt" 2>/dev/null
  emit dmi data="@b64:$tmp/dmi.txt"
  dmidecode -t system    >"$tmp/dmi_system.txt" 2>/dev/null;    emit dmi sub=system    data="@b64:$tmp/dmi_system.txt"
  dmidecode -t baseboard >"$tmp/dmi_board.txt" 2>/dev/null;     emit dmi sub=board     data="@b64:$tmp/dmi_board.txt"
  dmidecode -t bios      >"$tmp/dmi_bios.txt" 2>/dev/null;      emit dmi sub=bios      data="@b64:$tmp/dmi_bios.txt"
  for t in 0 1 2 3 4 7 8 9 17; do
    dmidecode -t "$t" >"$tmp/dmi_type_$t.txt" 2>/dev/null
    emit dmi_type type="$t" data="@b64:$tmp/dmi_type_$t.txt"
  done
  dmidecode -t 17 >"$tmp/dimm.txt" 2>/dev/null
  emit dimm data="@b64:$tmp/dimm.txt"
fi

# --- memory -----------------------------------------------------------------
if have decode-dimms; then
  decode-dimms >"$tmp/decode-dimms.txt" 2>&1
  emit memory sub=decode-dimms data="@b64:$tmp/decode-dimms.txt"
else
  emit memory sub=decode-dimms data=""
fi
for k in MemTotal MemAvailable SwapTotal HugePages_Total; do
  v="$(awk -v k="$k" '$1==k":" {print $2" "$3}' /proc/meminfo)"
  emit meminfo key="$k" value="$v"
done

# --- cpu --------------------------------------------------------------------
if have kcpuid; then
  kcpuid -r >"$tmp/kcpuid.txt" 2>/dev/null
  emit cpuid tool=kcpuid data="@b64:$tmp/kcpuid.txt"
fi
if have cpuid && cpuid -1 -l 0 2>/dev/null | grep -q .; then
  # capability-guarded: Arch's cpuid is minimal; skip if it can't do classic flags
  cpuid -1 -r >"$tmp/cpuid.txt" 2>/dev/null
  emit cpuid tool=cpuid data="@b64:$tmp/cpuid.txt"
fi
if have lscpu; then
  lscpu >"$tmp/lscpu.txt" 2>/dev/null
  emit cpuinfo sub=lscpu data="@b64:$tmp/lscpu.txt"
fi
grep -m1 'model name' /proc/cpuinfo | sed 's/.*: *//' >"$tmp/cpu_model.txt"
emit cpuinfo sub=model data="@raw:$tmp/cpu_model.txt"
grep -c '^processor' /proc/cpuinfo >"$tmp/cpu_count.txt"
emit cpuinfo sub=thread_count data="@raw:$tmp/cpu_count.txt"
# sysfs topology: distinct cache sizes + core/thread counts
for f in /sys/devices/system/cpu/cpu0/cache/index*/size; do
  [ -f "$f" ] && emit sysfs_cpu path="${f#/sys/devices/system/cpu/cpu0/cache/}" value="$(cat "$f")"
done
emit sysfs_cpu path=core_count value="$(lscpu -p=core 2>/dev/null | grep -v '^#' | sort -u | wc -l)"
emit sysfs_cpu path=thread_count value="$(nproc)"

# --- cpufreq ----------------------------------------------------------------
for f in /sys/devices/system/cpu/cpufreq/policy0/scaling_driver \
         /sys/devices/system/cpu/cpufreq/policy0/scaling_governor \
         /sys/devices/system/cpu/cpufreq/policy0/energy_performance_preference \
         /sys/devices/system/cpu/cpufreq/policy0/cpuinfo_max_freq \
         /sys/devices/system/cpu/cpufreq/policy0/cpuinfo_min_freq \
         /sys/devices/system/cpu/amd_pstate/status; do
  [ -f "$f" ] && emit cpufreq path="${f##*/}" value="$(cat "$f")"
done

# --- msr --------------------------------------------------------------------
if have rdmsr; then
  for reg in 0xc0010010 0xc0010015 0xc0010016 0xc0010064 0xc0011020 0xc0011021; do
    v="$(rdmsr -0 "$reg" 2>/dev/null || echo ERR)"
    emit msr reg="$reg" value="$v"
  done
  # per-cpu: 16 threads x 2 regs
  for cpu in $(seq 0 $(( $(nproc) - 1 ))); do
    for reg in 0xc0010064 0xc0011021; do
      v="$(rdmsr -p "$cpu" -0 "$reg" 2>/dev/null || echo ERR)"
      emit msr_per_cpu cpu="$cpu" reg="$reg" value="$v"
    done
  done
fi

# --- pci / usb --------------------------------------------------------------
if have lspci; then
  lspci -nn >"$tmp/lspci.txt" 2>/dev/null;      emit pci sub=full data="@b64:$tmp/lspci.txt"
  lspci -t  >"$tmp/lspci_t.txt" 2>/dev/null;    emit pci sub=tree data="@b64:$tmp/lspci_t.txt"
  lspci -nn | while IFS= read -r line; do
    emit pci_device slot="${line%% *}" desc="${line#* }"
  done
fi
if have lsusb; then
  lsusb >"$tmp/lsusb.txt" 2>/dev/null
  emit usb sub=lsusb data="@b64:$tmp/lsusb.txt"
fi

# --- net --------------------------------------------------------------------
for iface in /sys/class/net/*; do
  ifname="${iface##*/}"
  mac="$(cat "$iface/address" 2>/dev/null)"; mtu="$(cat "$iface/mtu" 2>/dev/null)"
  state="$(cat "$iface/operstate" 2>/dev/null)"
  emit net_iface ifname="$ifname" mac="$mac" mtu="$mtu" state="$state"
  if have ethtool; then
    ethtool -i "$ifname" >"$tmp/ethtool_$ifname.txt" 2>/dev/null \
      && emit net_driver iface="$ifname" data="@b64:$tmp/ethtool_$ifname.txt"
  fi
done

# --- disks ------------------------------------------------------------------
if have lsblk; then
  lsblk -J -o NAME,SIZE,MODEL,SERIAL,TRAN,ROTA >"$tmp/lsblk.json" 2>/dev/null
  emit storage sub=lsblk_json data="@b64:$tmp/lsblk.json"
  lsblk -dn -o NAME,SIZE,MODEL,SERIAL,TRAN,ROTA 2>/dev/null | while read -r name size model serial tran rota; do
    emit disk name="$name" size="$size" model="$model" serial="$serial" tran="$tran" rotational="$rota"
  done
fi
if have smartctl; then
  for dev in /dev/sd? /dev/nvme?n1; do
    [ -b "$dev" ] || continue
    smartctl -a -j "$dev" >"$tmp/smart_$(basename "$dev").json" 2>/dev/null
    emit smart dev="$dev" data="@b64:$tmp/smart_$(basename "$dev").json"
    # parsed health summary (what hw-watchdog.py consumes)
    parsed="$(python3 - "$tmp/smart_$(basename "$dev").json" "$dev" <<'EOF'
import json, sys, re
p, dev = sys.argv[1], sys.argv[2]
# v2 convention: strip the NVMe namespace suffix (/dev/nvme0n1 -> /dev/nvme0)
short = re.sub(r"^(.*/nvme\d+)n\d+$", r"\1", dev)
try:
    d = json.load(open(p))
except Exception:
    sys.exit(1)
model = d.get("model_name") or d.get("model_family") or ""
serial = d.get("serial_number", "")
fw = d.get("firmware_version", "")
passed = str(d.get("smart_status", {}).get("passed", "")).lower() == "true"
temp = d.get("temperature", {}).get("current", "")
poh = d.get("power_on_time", {}).get("hours", "")
pct = ""
for a in d.get("ata_smart_attributes", {}).get("table", []):
    if a.get("id") == 177 or "wear" in a.get("name", "").lower():
        pct = a.get("value", "")
nvw = d.get("nvme_smart_health_information_log", {})
if nvw:
    temp = nvw.get("temperature", temp)
    poh = nvw.get("power_on_hours", poh)
    pct = nvw.get("percentage_used", pct)
print(json.dumps({"dev": short, "model": model, "serial": serial, "fw": fw,
                  "passed": passed, "temp_c": temp, "power_on_hours": poh,
                  "pct_used": pct}))
EOF
)"
    [ -n "$parsed" ] && python3 - "$OUT" "$parsed" <<'EOF'
import json, sys
out, parsed = sys.argv[1], json.loads(sys.argv[2])
rec = {"section": "disk_health", **parsed}
open(out, "a").write(json.dumps(rec) + "\n")
EOF
  done
fi

# --- nvme -------------------------------------------------------------------
if have nvme; then
  for dev in /dev/nvme?n1; do
    [ -c "$dev" ] || [ -b "$dev" ] || continue
    nvme id-ctrl "$dev" >"$tmp/nvme_ctrl_$(basename "$dev").txt" 2>/dev/null
    emit nvme_ctrl dev="$dev" data="@b64:$tmp/nvme_ctrl_$(basename "$dev").txt"
    nvme smart-log "$dev" >"$tmp/nvme_smart_$(basename "$dev").txt" 2>/dev/null
    emit nvme_smart dev="$dev" data="@b64:$tmp/nvme_smart_$(basename "$dev").txt"
    nvme fw-log "$dev" >"$tmp/nvme_fw_$(basename "$dev").txt" 2>/dev/null
    emit nvme_fw dev="$dev" data="@b64:$tmp/nvme_fw_$(basename "$dev").txt"
  done
fi

# --- nvidia -----------------------------------------------------------------
if have nvidia-smi; then
  nvidia-smi -q >"$tmp/nvidia_q.txt" 2>/dev/null;        emit nvidia sub=full_q_b64 data="@b64:$tmp/nvidia_q.txt"
  nvidia-smi -q -x >"$tmp/nvidia_x.xml" 2>/dev/null;      emit nvidia sub=xml data="@b64:$tmp/nvidia_x.xml"
  nvidia-smi topo -m >"$tmp/nvidia_topo.txt" 2>/dev/null; emit nvidia sub=topo data="@b64:$tmp/nvidia_topo.txt"
  nvidia-debugdump -l >"$tmp/nvidia_dbg.txt" 2>&1;        emit nvidia sub=debugdump data="@b64:$tmp/nvidia_dbg.txt"
  gpu="$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null | head -1)"
  emit nvidia_gpu summary="$gpu"
fi

# --- firmware ---------------------------------------------------------------
if have efibootmgr; then
  efibootmgr >"$tmp/efibootmgr.txt" 2>/dev/null
  emit firmware sub=efibootmgr data="@b64:$tmp/efibootmgr.txt"
fi

# --- tool presence ----------------------------------------------------------
for t in dmidecode smartctl nvme lspci lsusb ethtool cpuid kcpuid nvidia-smi efibootmgr rdmsr decode-dimms lscpu; do
  if have "$t"; then
    emit tool name="$t" path="$(command -v "$t")" present=true
  else
    emit tool name="$t" path="" present=false
  fi
done

echo "audit complete: $(wc -l < "$OUT") records -> $OUT"
