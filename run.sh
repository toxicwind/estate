#!/bin/bash
# MAXIMAL HARDWARE EXTRACTION
# Run as root. Output goes to ./hw_dump_$(date +%s)/

OUTDIR="./hw_dump_$(date +%s)"
mkdir -p $OUTDIR
cd $OUTDIR

echo "[*] Starting maximal extraction..."

# === GPU ===
echo "[*] GPU dump..."
nvidia-smi -q -x > nvidia_full.xml 2>/dev/null
nvidia-smi --query-gpu=timestamp,driver_version,count,name,serial,uuid,pci.bus_id,pci.domain,pci.bus,pci.device,pci.sub_device_id,pcie.link.gen.max,pcie.link.gen.current,pcie.link.width.max,pcie.link.width.current,index,display_mode,display_active,persistence_mode,accounting.mode,accounting.buffer_size,driver_model.current,driver_model.pending,vbios_version,inforom.img,inforom.oem,inforom.ecc,inforom.pwr,gom.current,gom.pending,fan.speed,pstate,clocks_throttle_reasons.supported,clocks_throttle_reasons.active,clocks_throttle_reasons.gpu_idle,clocks_throttle_reasons.applications_clocks_setting,clocks_throttle_reasons.sw_power_cap,clocks_throttle_reasons.hw_slowdown,clocks_throttle_reasons.hw_thermal_slowdown,clocks_throttle_reasons.hw_power_brake_slowdown,clocks_throttle_reasons.sw_thermal_slowdown,clocks_throttle_reasons.sync_boost,memory.total,memory.used,memory.free,memory.reserved,compute_mode,utilization.gpu,utilization.memory,encoder.stats.sessionCount,encoder.stats.averageFps,encoder.stats.averageLatency,ecc.mode.current,ecc.mode.pending,ecc.errors.corrected.volatile.device_memory,ecc.errors.corrected.volatile.dram,ecc.errors.corrected.volatile.register_file,ecc.errors.corrected.volatile.l1_cache,ecc.errors.corrected.volatile.l2_cache,ecc.errors.corrected.volatile.texture_memory,ecc.errors.corrected.volatile.total,ecc.errors.corrected.aggregate.device_memory,ecc.errors.corrected.aggregate.dram,ecc.errors.corrected.aggregate.register_file,ecc.errors.corrected.aggregate.l1_cache,ecc.errors.corrected.aggregate.l2_cache,ecc.errors.corrected.aggregate.texture_memory,ecc.errors.corrected.aggregate.total,ecc.errors.uncorrected.volatile.device_memory,ecc.errors.uncorrected.volatile.dram,ecc.errors.uncorrected.volatile.register_file,ecc.errors.uncorrected.volatile.l1_cache,ecc.errors.uncorrected.volatile.l2_cache,ecc.errors.uncorrected.volatile.texture_memory,ecc.errors.uncorrected.volatile.total,ecc.errors.uncorrected.aggregate.device_memory,ecc.errors.uncorrected.aggregate.dram,ecc.errors.uncorrected.aggregate.register_file,ecc.errors.uncorrected.aggregate.l1_cache,ecc.errors.uncorrected.aggregate.l2_cache,ecc.errors.uncorrected.aggregate.texture_memory,ecc.errors.uncorrected.aggregate.total,retired_pages.single_bit_ecc.count,retired_pages.double_bit_ecc.count,retired_pages.pending,temperature.gpu,temperature.memory,power.draw,power.limit,power.max_limit,power.min_limit,power.default_limit,enforced.power.limit,power.management,clocks.current.graphics,clocks.current.sm,clocks.current.memory,clocks.current.video,clocks.applications.graphics,clocks.applications.memory,clocks.default_applications.graphics,clocks.default_applications.memory,clocks.max.graphics,clocks.max.sm,clocks.max.memory,clocks.offset,clocks.offset.sm,clocks.offset.memory,mig.mode.current,mig.mode.pending --format=csv > nvidia_query.csv 2>/dev/null

for f in /proc/driver/nvidia/gpus/0000:*/{information,registry,power,thermal,clocks,status}; do
    [ -f "$f" ] && cp "$f" "gpu_$(basename $f).txt"
done

lspci -s 01:00.0 -vvvxxx > gpu_pci_full.txt 2>/dev/null
cat /sys/bus/pci/devices/0000:01:00.0/config > gpu_config_space.bin 2>/dev/null
cat /sys/bus/pci/devices/0000:01:00.0/resource > gpu_bars.txt 2>/dev/null

# VBIOS
echo 1 > /sys/bus/pci/devices/0000:01:00.0/rom 2>/dev/null
cat /sys/bus/pci/devices/0000:01:00.0/rom > gpu_vbios.rom 2>/dev/null
echo 0 > /sys/bus/pci/devices/0000:01:00.0/rom 2>/dev/null

# === CPU ===
echo "[*] CPU dump..."
cpuid -1 > cpuid_full.txt 2>/dev/null
cpuid -r > cpuid_raw.txt 2>/dev/null
cat /proc/cpuinfo > cpuinfo.txt

modprobe msr 2>/dev/null
for msr in 0xC0010000 0xC0010015 0xC001001A 0xC0010061 0xC0010062 0xC0010063 0xC0010064 0xC0011020 0xC0011021 0xC0011022 0xC0011023 0xC0011028 0xC0011029 0xC001102A 0xC001102B; do
    rdmsr -a $msr > "msr_${msr}.txt" 2>/dev/null
done

# === MOTHERBOARD ===
echo "[*] Motherboard dump..."
dmidecode > dmi_full.txt 2>/dev/null
for t in 0 1 2 3 4 7 11 17 22 32 41; do
    dmidecode -t $t > "dmi_type_${t}.txt" 2>/dev/null
done

# ACPI
cp /sys/firmware/acpi/tables/DSDT dsdt.dat 2>/dev/null
cp /sys/firmware/acpi/tables/SSDT* . 2>/dev/null

# === RAM ===
echo "[*] RAM dump..."
decode-dimms > dimm_decode.txt 2>/dev/null
for i in $(seq 0 7); do
    i2cdump -y 0 0x5$i > "spd_dimm_${i}.txt" 2>/dev/null || true
done

# === NVMe ===
echo "[*] NVMe dump..."
for dev in /dev/nvme0 /dev/nvme1; do
    [ -e "$dev" ] || continue
    base=$(basename $dev)
    nvme id-ctrl $dev > "${base}_id_ctrl.txt" 2>/dev/null
    nvme id-ns ${dev}n1 > "${base}_id_ns.txt" 2>/dev/null
    nvme smart-log $dev > "${base}_smart.txt" 2>/dev/null
    nvme error-log $dev > "${base}_errors.txt" 2>/dev/null
    nvme fw-log $dev > "${base}_fw.txt" 2>/dev/null
done

# === PCIe ===
echo "[*] PCIe dump..."
lspci -vvvxxx > pcie_full.txt 2>/dev/null
lspci -vvvk > pcie_drivers.txt 2>/dev/null

# === Kernel ===
echo "[*] Kernel state..."
cat /proc/modules > kernel_modules.txt
cat /proc/iomem > iomem.txt
cat /proc/ioports > ioports.txt
cat /proc/interrupts > interrupts.txt
cat /proc/dma > dma.txt

echo "[*] Done. Output in $OUTDIR"
ls -la