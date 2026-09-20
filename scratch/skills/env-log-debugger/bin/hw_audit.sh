#!/usr/bin/env bash
# hw-audit v2 — physical hardware inventory as VALID jsonl (one record per line).
# Fixes vs v1:
#   * every jq invocation uses -c (v1 used bare `jq -Rs` which pretty-prints,
#     producing 295 physical lines for 147 logical records — not JSONL)
#   * nvidia per-GPU fields parsed with python csv (v1 used IFS=', ' which
#     split GPU names on spaces and misaligned every field)
#   * assumes cpuid / msr-tools / nvme-cli installed (pacman -S cpuid msr-tools nvme-cli)
# Usage: ./hw_audit.sh [out.jsonl]
set -uo pipefail
OUT="${1:-$HOME/hw-audit.jsonl}"
: > "$OUT"
emit() { jq -c -n "$@" >> "$OUT"; }
have() { command -v "$1" >/dev/null 2>&1; }

# ── 0. environment ───────────────────────────────────────────────────────
emit --arg kernel "$(uname -r)" \
     --arg distro "$(grep -E '^(NAME|VERSION)=' /etc/os-release 2>/dev/null | tr '\n' ' ')" \
     --arg arch "$(uname -m)" \
     --arg host "$(hostnamectl --json=short 2>/dev/null || echo '{}')" \
     '{section:"env",kernel:$kernel,distro:$distro,arch:$arch,host:$host}'

# ── 1. DMI/SMBIOS ────────────────────────────────────────────────────────
if have dmidecode; then
  dmidecode -q 2>/dev/null | base64 -w0 | jq -c -Rs '{section:"dmi",kind:"dmi_raw_b64",data:.}' >> "$OUT"
  for t in system baseboard chassis processor memory cache slot connector bios; do
    dmidecode -t "$t" 2>/dev/null | base64 -w0 | jq -c -Rs --arg t "$t" \
      '{section:"dmi_type",type:$t,data:.}' >> "$OUT"
  done
  emit --arg mfr  "$(dmidecode -s system-manufacturer 2>/dev/null)" \
       --arg prod "$(dmidecode -s system-product-name 2>/dev/null)" \
       --arg ver  "$(dmidecode -s system-version 2>/dev/null)" \
       --arg sn   "$(dmidecode -s system-serial-number 2>/dev/null)" \
       --arg uuid "$(dmidecode -s system-uuid 2>/dev/null)" \
       --arg sku  "$(dmidecode -s system-sku-number 2>/dev/null)" \
       --arg fam  "$(dmidecode -s system-family 2>/dev/null)" \
       '{section:"dmi",sub:"system",mfr:$mfr,product:$prod,version:$ver,serial:$sn,uuid:$uuid,sku:$sku,family:$fam}'
  emit --arg mfr  "$(dmidecode -s baseboard-manufacturer 2>/dev/null)" \
       --arg prod "$(dmidecode -s baseboard-product-name 2>/dev/null)" \
       --arg ver  "$(dmidecode -s baseboard-version 2>/dev/null)" \
       --arg sn   "$(dmidecode -s baseboard-serial-number 2>/dev/null)" \
       --arg atag "$(dmidecode -s baseboard-asset-tag 2>/dev/null)" \
       '{section:"dmi",sub:"board",mfr:$mfr,product:$prod,version:$ver,serial:$sn,asset:$atag}'
  emit --arg vendor "$(dmidecode -s bios-vendor 2>/dev/null)" \
       --arg ver    "$(dmidecode -s bios-version 2>/dev/null)" \
       --arg date   "$(dmidecode -s bios-release-date 2>/dev/null)" \
       --arg rev    "$(dmidecode -s bios-revision 2>/dev/null)" \
       --arg fw     "$(dmidecode -s bios-firmware-revision 2>/dev/null)" \
       '{section:"dmi",sub:"bios",vendor:$vendor,version:$ver,date:$date,revision:$rev,firmware:$fw}'
  # decoded DIMM inventory — one record per populated slot (human-readable)
  dmidecode -t memory 2>/dev/null | awk '
    /^Memory Device/ { dev=""; size=""; type=""; speed=""; mfr=""; part=""; sn=""; loc=""; cfg="" }
    /^\tSize: / && $2 != "No" { size=$2" "$3 }
    /^\tType: / && $2 != "Unknown" { type=$2 }
    /^\tSpeed: / { speed=$2" "$3 }
    /^\tManufacturer: / { mfr=$0; sub(/^\tManufacturer: */,"",mfr) }
    /^\tPart Number: / { part=$0; sub(/^\tPart Number: */,"",part) }
    /^\tSerial Number: / { sn=$3 }
    /^\tLocator: / { loc=$2 }
    /^\tConfigured Memory Speed: / { cfg=$4" "$5 }
    /^$/ && size != "" { printf "%s|%s|%s|%s|%s|%s|%s|%s\n", loc, size, type, speed, mfr, part, sn, cfg; size="" }
  ' | while IFS='|' read -r loc size type speed mfr part sn cfg; do
      emit --arg loc "$loc" --arg size "$size" --arg type "$type" --arg speed "$speed" \
           --arg mfr "$mfr" --arg part "$part" --arg sn "$sn" --arg cfg "$cfg" \
           '{section:"dimm",locator:$loc,size:$size,type:$type,speed:$speed,mfr:$mfr,part:$part,serial:$sn,configured:$cfg}'
    done
fi

# ── 2. CPUID ─────────────────────────────────────────────────────────────
# Arch ships the kernel's kcpuid (no classic `cpuid` package in repos)
if have kcpuid; then
  kcpuid -r 2>/dev/null | base64 -w0 | jq -c -Rs '{section:"cpuid",sub:"raw_b64",data:.}' >> "$OUT"
fi
# Classic cpuid per-leaf dumps: only when the binary really supports -1/-l.
# Arch's minimal /usr/bin/cpuid prints usage to stderr otherwise, yielding empty records.
if have cpuid && cpuid -1 -l 0 2>/dev/null | grep -q .; then
  cpuid -1 2>/dev/null | base64 -w0 | jq -c -Rs '{section:"cpuid",sub:"raw_b64",data:.}' >> "$OUT"
  for leaf in 0 1 7 0x80000000 0x80000001 0x80000002 0x80000003 0x80000004 0x80000006 0x80000007 0x80000008 0x8000001E 0x8000001F; do
    cpuid -1 -l "$leaf" 2>/dev/null | base64 -w0 | jq -c -Rs --arg leaf "$leaf" \
      '{section:"cpuid_leaf",leaf:$leaf,data:.}' >> "$OUT"
  done
fi

# ── 3. MSR ───────────────────────────────────────────────────────────────
if have rdmsr; then
  modprobe msr 2>/dev/null || true
  if [ -e /dev/cpu/0/msr ]; then
    while IFS='=' read -r reg name; do
      v=$(rdmsr -p 0 "$reg" 2>/dev/null) || v=""
      [ -n "$v" ] && emit --arg name "$name" --arg reg "$reg" --arg val "$v" \
        '{section:"msr",name:$name,reg:$reg,value:$val}'
    done <<'MSRS'
0xCE=IA32_PLATFORM_ID
0x198=IA32_PERF_STATUS
0x199=IA32_PERF_CTL
0x19C=IA32_THERM_STATUS
0x1A2=MSR_TEMPERATURE_TARGET
0x1B1=IA32_PACKAGE_THERM_STATUS
0xC0000080=EFER
0xC0010010=SYSCFG
0xC0010015=HWCR
0xC0010064=PStateDef0
0xC0010293=CStateCfg
0xC0010299=HWPCap
MSRS
    ncpu=$(nproc 2>/dev/null || echo 1)
    for ((i=0;i<ncpu;i++)); do
      for reg in 0x198 0x19C 0xC0010064 0xC0010293; do
        v=$(rdmsr -p "$i" "$reg" 2>/dev/null) || continue
        emit --arg cpu "$i" --arg reg "$reg" --arg val "$v" \
          '{section:"msr_per_cpu",cpu:$cpu,reg:$reg,value:$val}'
      done
    done
  fi
fi

# ── 4. CPU topology / cpuinfo ────────────────────────────────────────────
for f in /sys/devices/system/cpu/cpu0/topology/core_id \
         /sys/devices/system/cpu/cpu0/topology/physical_package_id \
         /sys/devices/system/cpu/cpu0/cache/index0/size \
         /sys/devices/system/cpu/cpu0/cache/index1/size \
         /sys/devices/system/cpu/cpu0/cache/index2/size \
         /sys/devices/system/cpu/cpu0/cache/index3/size; do
  [ -r "$f" ] && emit --arg p "$f" --arg v "$(cat "$f" 2>/dev/null)" \
    '{section:"sysfs_cpu",path:$p,value:$v}'
done
if [ -r /proc/cpuinfo ]; then
  awk -F: '/^(vendor_id|model name|cpu family|model|stepping|microcode)/ {gsub(/^[ \t]+/,"",$2); print $1"="$2}' /proc/cpuinfo \
    | sort -u | while IFS='=' read -r k v; do
        emit --arg k "$k" --arg v "$v" '{section:"cpuinfo",key:$k,value:$v}'
      done
fi

# ── 5. NVIDIA ────────────────────────────────────────────────────────────
if have nvidia-smi; then
  all_q=$(nvidia-smi --help-query-gpu 2>/dev/null \
    | grep -E '^\s+"[a-z0-9._]+"' | tr -d ' "' | tr '\n' ',' | sed 's/,$//')
  [ -n "$all_q" ] && nvidia-smi --query-gpu="$all_q" --format=csv,noheader,nounits 2>/dev/null \
    | base64 -w0 | jq -c -Rs --arg q "$all_q" \
      '{section:"nvidia",sub:"all_query_gpu",queries:$q,data:.}' >> "$OUT"
  nvidia-smi -q 2>/dev/null | base64 -w0 \
    | jq -c -Rs '{section:"nvidia",sub:"full_q_b64",data:.}' >> "$OUT"
  nvidia-smi -q -x 2>/dev/null | base64 -w0 \
    | jq -c -Rs '{section:"nvidia",sub:"q_xml_b64",data:.}' >> "$OUT"
  nvidia-smi topo -m 2>/dev/null | base64 -w0 \
    | jq -c -Rs '{section:"nvidia",sub:"topo_b64",data:.}' >> "$OUT"
  # per-GPU key fields — parsed with python csv (GPU names contain spaces)
  nvidia-smi --query-gpu=index,name,uuid,serial,pci.bus_id,vbios_version,driver_version,memory.total \
    --format=csv,noheader,nounits 2>/dev/null | python3 -c '
import csv, json, sys
fields = ["idx","name","uuid","serial","bus","vbios","driver","mem_total"]
for row in csv.reader(sys.stdin):
    row = [c.strip() for c in row]
    if len(row) < len(fields):
        continue
    d = dict(zip(fields, row))
    d["section"] = "nvidia_gpu"
    print(json.dumps(d))
' >> "$OUT"
fi
if have nvidia-debugdump; then
  nvidia-debugdump -l 2>/dev/null | base64 -w0 \
    | jq -c -Rs '{section:"nvidia",sub:"debugdump_list_b64",data:.}' >> "$OUT"
fi

# ── 6. PCI ───────────────────────────────────────────────────────────────
if have lspci; then
  lspci -nnvvv 2>/dev/null | base64 -w0 \
    | jq -c -Rs '{section:"pci",sub:"full_dump_b64",data:.}' >> "$OUT"
  lspci -t 2>/dev/null | base64 -w0 \
    | jq -c -Rs '{section:"pci",sub:"tree_b64",data:.}' >> "$OUT"
  lspci -nnmm 2>/dev/null | while IFS= read -r line; do
    emit --arg line "$line" '{section:"pci_device",raw:$line}'
  done
fi

# ── 7. Storage ───────────────────────────────────────────────────────────
if have lsblk; then
  lsblk -O -J 2>/dev/null | base64 -w0 \
    | jq -c -Rs '{section:"storage",sub:"lsblk_json_b64",data:.}' >> "$OUT"
  # human-readable disk inventory, one record per physical disk
  lsblk -d -n -o NAME,SIZE,MODEL,SERIAL,TRAN,ROTA --json 2>/dev/null \
    | jq -c -r '.blockdevices[] | {section:"disk",name:.name,size:.size,model:.model,serial:.serial,tran:.tran,rotational:.rota}' >> "$OUT"
fi
if have nvme; then
  for dev in /dev/nvme?; do
    [ -e "$dev" ] || continue
    nvme id-ctrl "$dev" 2>/dev/null | base64 -w0 \
      | jq -c -Rs --arg d "$dev" '{section:"nvme_ctrl",dev:$d,data:.}' >> "$OUT"
    nvme smart-log "$dev" 2>/dev/null | base64 -w0 \
      | jq -c -Rs --arg d "$dev" '{section:"nvme_smart",dev:$d,data:.}' >> "$OUT"
    nvme fw-log "$dev" 2>/dev/null | base64 -w0 \
      | jq -c -Rs --arg d "$dev" '{section:"nvme_fw",dev:$d,data:.}' >> "$OUT"
  done
fi
if have smartctl; then
  for dev in /dev/sd? /dev/nvme?; do
    [ -e "$dev" ] || continue
    smartctl -a -j "$dev" 2>/dev/null | base64 -w0 \
      | jq -c -Rs --arg d "$dev" '{section:"smart",dev:$d,data:.}' >> "$OUT"
    # flat health fields (no base64 needed to read these)
    smartctl -a -j "$dev" 2>/dev/null | jq -c --arg d "$dev" '{
      section:"disk_health", dev:$d,
      model:.model_name, serial:.serial_number, fw:.firmware_version,
      passed:.smart_status.passed, temp_c:.temperature.current,
      power_on_hours:(.power_on_time.hours // .nvme_smart_health_information_log.power_on_hours),
      pct_used:.nvme_smart_health_information_log.percentage_used
    }' >> "$OUT"
  done
fi

# ── 8. Memory summary ────────────────────────────────────────────────────
if [ -r /proc/meminfo ]; then
  awk '/^(MemTotal|MemFree|MemAvailable|SwapTotal)/ {gsub(/ /,"");print}' /proc/meminfo \
    | while IFS=':' read -r k v; do
        emit --arg k "$k" --arg v "$v" '{section:"meminfo",key:$k,value:$v}'
      done
fi
if have decode-dimms; then
  decode-dimms 2>/dev/null | base64 -w0 \
    | jq -c -Rs '{section:"memory",sub:"decode_dimms_b64",data:.}' >> "$OUT"
fi

# ── 9. USB ───────────────────────────────────────────────────────────────
if have lsusb; then
  lsusb -t 2>/dev/null | base64 -w0 \
    | jq -c -Rs '{section:"usb",sub:"tree_b64",data:.}' >> "$OUT"
fi

# ── 10. Network ──────────────────────────────────────────────────────────
if have ip; then
  ip -j link 2>/dev/null | jq -c -r '.[] | {section:"net_iface",ifname:.ifname,mac:.address,mtu:.mtu,state:.operstate}' >> "$OUT"
fi
if have ethtool; then
  for iface in $(ip -o link show 2>/dev/null | awk -F': ' '{print $2}' | cut -d@ -f1 | grep -v '^lo$'); do
    ethtool -i "$iface" 2>/dev/null | jq -c -Rs --arg i "$iface" \
      '{section:"net_driver",iface:$i,data:.}' >> "$OUT"
  done
fi

# ── 11. Power / thermal ──────────────────────────────────────────────────
[ -r /sys/class/thermal/thermal_zone0/temp ] && \
  emit --arg v "$(cat /sys/class/thermal/thermal_zone0/temp)" \
    '{section:"thermal",zone:"0",raw:$v}'
for f in scaling_driver scaling_governor energy_performance_preference scaling_cur_freq cpuinfo_max_freq cpuinfo_min_freq; do
  [ -r "/sys/devices/system/cpu/cpu0/cpufreq/$f" ] && \
    emit --arg p "$f" --arg v "$(cat "/sys/devices/system/cpu/cpu0/cpufreq/$f")" \
      '{section:"cpufreq",path:$p,value:$v}'
done

# ── 12. Firmware / UEFI ──────────────────────────────────────────────────
if have efibootmgr; then
  efibootmgr -v 2>/dev/null | base64 -w0 \
    | jq -c -Rs '{section:"firmware",sub:"efibootmgr_b64",data:.}' >> "$OUT"
fi

# ── 13. Tool availability ────────────────────────────────────────────────
for t in dmidecode cpuid rdmsr nvme nvidia-smi nvidia-debugdump lspci lsusb lsblk smartctl decode-dimms ethtool efibootmgr; do
  if p=$(command -v "$t" 2>/dev/null); then
    emit --arg t "$t" --arg p "$p" '{section:"tool",name:$t,path:$p,present:true}'
  else
    emit --arg t "$t" '{section:"tool",name:$t,present:false}'
  fi
done

# ── validate: physical lines must equal logical records ──────────────────
phys=$(wc -l < "$OUT")
logic=$(jq -s 'length' "$OUT" 2>/dev/null || echo 0)
printf '{"validation":{"physical_lines":%s,"logical_records":%s,"valid_jsonl":%s}}\n' \
  "$phys" "$logic" "$([ "$phys" = "$logic" ] && [ "$phys" -gt 0 ] && echo true || echo false)"
