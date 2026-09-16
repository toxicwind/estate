# Hardware Audit Classification — awrawr-pc — 2026-09-14

Source: `/tmp/hw-audit-v2.jsonl` — **205 records, all classified below.** No record fabricated.
Audit script: `/home/toxic/hw-audit.sh` (hw-audit v2). Nightly via `hw-audit.timer` (03:17 MDT, root).

## Machine

| Item | Value |
|---|---|
| Host | awrawr-pc |
| Board | MSI PRO B650-VC WIFI (MS-7D78), serial 07D7812_P71E071687 |
| BIOS | AMI 1.L5, 10/22/2025, rev 5.35 |
| CPU | AMD Ryzen 7 8700F 8-Core (Family 19h, Model 75h, Stepping 2, microcode 0xa70520a) |
| RAM | 64 GiB — 2×32 GiB DDR5-6000 in A2/B2, configured 6000 MT/s |
| GPU | NVIDIA GeForce RTX 3090 24 GB, driver 610.43.03, vBIOS 94.02.42.00.A7 |
| NIC (wired) | Realtek RTL8125 2.5GbE (enp12s0, r8169, fw rtl8125b-2_0.0.2) — UP |
| NIC (wifi) | MediaTek MT7922 802.11ax (wlan0, mt7921e) — DOWN (expected, wired primary) |
| OS | CachyOS Linux, kernel 7.1.5-1-cachyos-server, x86_64 |
| cpufreq | amd-pstate-epp, governor powersave, EPP balance_performance (2.6–5.05 GHz) |

The "Phoenix Root Complex" in lspci is **correct**: the 8700F is Phoenix-silicon (Ryzen 8000, no iGPU — PCI shows "Dummy Function (absent graphics controller)").

## Record inventory (205/205)

| Section | N | Verdict |
|---|---|---|
| `env` | 1 | Healthy — kernel/distro/arch/host all expected |
| `dmi` | 4 | Healthy — raw SMBIOS + system + board + bios |
| `dmi_type` | 9 | Healthy — system/baseboard/chassis/processor/memory/cache/slot/connector/bios |
| `dmi` system serial | — | Informational — "To be filled by O.E.M." (normal for MSI retail) |
| `dimm` | 2 | Healthy — both 32 GiB DDR5-6000 @ 6000 MT/s; mfr "Unknown" is BIOS reporting generic `UD5-6000` sticks (see limitations) |
| `memory` | 1 | Collection limitation — decode-dimms empty (no EEPROM; see below) |
| `meminfo` | 4 | Healthy — 64 GiB RAM; SwapTotal 200 GiB = 62.4 G zram0 + 138.3 G nvme0n1p4 partition (CachyOS default, intentional) |
| `cpuid` | 2 | **Fixed** — 1 real (kcpuid -r) + 1 header-only from broken classic-cpuid branch |
| `cpuid_leaf` | 13 | **Fixed** — all 13 had empty data (same root cause) |
| `cpuinfo` | 6 | Healthy — 8700F identity confirmed |
| `sysfs_cpu` | 6 | Healthy — topology + L1/L2/L3 (32K/32K/1024K/16384K) |
| `cpufreq` | 6 | Intentional — amd-pstate-epp powersave/balance_performance |
| `msr` | 6 | Healthy — EFER/SYSCFG/HWCR/PStateDef0/CStateCfg/HWPCap readable |
| `msr_per_cpu` | 32 | Healthy — 16 threads × 2 regs, values consistent across CPUs |
| `pci` | 2 | Healthy — full dump + tree |
| `pci_device` | 54 | Healthy — all devices expected for this board (see PCI notes) |
| `usb` | 1 | Healthy — 2 xHCI buses, HID kbd/mouse, hub, BT (btusb) |
| `net_iface` | 9 | Healthy — lo, enp12s0 UP, wlan0 DOWN, tailscale0, docker0 + 2 bridges + 2 veths |
| `net_driver` | 8 | Healthy — r8169/mt7921e/tun/bridge/veth all bound correctly |
| `disk` | 5 | Healthy — sda/sdb/zram0/nvme0n1/nvme1n1 |
| `smart` | 4 | Healthy — all 4 drives SMART passed, full JSON captured |
| `disk_health` | 4 | Healthy — see drive table |
| `nvme_ctrl` | 2 | Healthy — WD SN850X (fw 620361WD), Crucial E100 (fw VDCR4014) |
| `nvme_smart` | 2 | Healthy — 0 critical warnings on both |
| `nvme_fw` | 2 | Healthy |
| `storage` | 1 | Healthy — lsblk JSON |
| `nvidia` | 4 | Healthy — smi full/xml/topo/debugdump; note driver-version deprecation banner (cosmetic) |
| `nvidia_gpu` | 1 | Healthy — RTX 3090 24 GB |
| `firmware` | 1 | Healthy — efibootmgr (BootCurrent 0003, shim) |
| `tool` | 13 | Healthy — all 13 audit tools present |

## Drive health (all SMART passed)

| Drive | Model | Temp | POH | Wear/Used | Written | Notes |
|---|---|---|---|---|---|---|
| sda | Samsung 870 QVO 1 TB | 27 °C | 46,417 h | Wear 090 (~10% consumed) | 76.3 TB of 360 TBW | 0 realloc, 0 rsvd-used — healthy |
| sdb | Seagate ST8000NT001 8 TB | 31 °C | 22,995 h | n/a (HDD) | — | healthy |
| nvme0 | WD Black SN850X 1 TB | 29 °C | 15,556 h | 11% used | 205.9 TB | 0 crit warnings — healthy |
| nvme1 | Crucial CT1000E100SSD8 1 TB | 34 °C | 4,980 h | 3% used | 52.7 TB | 0 crit warnings — healthy |

## PCI notes (54 devices, all expected)

- `01:00.0` NVIDIA GA102 RTX 3090 (PNY subvendor) + `01:00.1` HD audio
- `02:00.0` Micron/Crucial E100 NVMe (DRAM-less) — nvme1
- `10:00.0` SanDisk WD Black SN850X — nvme0
- `0c:00.0` Realtek RTL8125 2.5GbE; `0d:00.0` MediaTek MT7922 WiFi/BT
- SATA: ASMedia ASM1064 + AMD 600-series; USB: AMD 600-series + Phoenix xHCI
- Kernel log: **zero** err/crit/alert/emerg; **zero** PCIe AER errors

## Fixes applied (maximal — found and fixed, not just reported)

1. **cpuid/cpuid_leaf empty records — FIXED in `/home/toxic/hw-audit.sh`.**
   Root cause: Arch's `/usr/bin/cpuid` is a minimal tool (usage: `cpuid [processor #]`),
   not the classic cpuid. The script's `if have cpuid` branch used classic flags
   (`-1`, `-l`), which print usage to stderr → 1 header-only + 13 empty records.
   Fix: guard the branch on real capability (`cpuid -1 -l 0 | grep -q .`); kcpuid -r
   already captures the full dump. Validated: re-run yields `cpuid:1, cpuid_leaf:0`,
   zero empty records, valid JSONL. Tonight's 03:17 root run picks this up.
2. **Stale `nanocoder-daemon-cd0002d8cc.service` — RESOLVED (already gone).**
   Zero hits in all 205 audit records. Verified on host: no unit file in
   /etc/systemd, /usr/lib/systemd, user units, or /run; `journalctl -u` → "No entries".
   Nothing to disable/remove — fully stale history only.
3. **Pacman orphans (fltk flxmlrpc hamradio-menus kcat-docs) — already removed** by earlier work; `pacman -Qtdq` is clean.

## Data-quality / collection limitations (not fixable from userspace)

- **SPD via decode-dimms**: `No EEPROM found` — kernel 7.1.5-1-cachyos-server has no
  `eeprom`/`at24`/`ee1004` modules, so DIMM SPD is unreadable. DMI Type 17 still gives
  full inventory (2×32 GiB DDR5-6000, serials 01046DE8/01046DF1). DIMM *manufacturer*
  string "Unknown" is the BIOS reporting generic `UD5-6000` part numbers, not a tool failure.
- **nvidia-smi deprecation banner**: `610.43.03 [Deprecated; will be removed in CUDA 14.0.
  Use KMD version instead]` refers to the *version-reporting field*, not the driver itself. Cosmetic.
- **net_iface count varies run to run** (9 in v2, 7 in test): docker bridges/veths are
  ephemeral. Expected.

## Intentional configuration (do not "fix")

- `mitigations=off`, zram-over-zswap, `comfyui-offload` on the QVO (Chris's call),
  200 GiB total swap (zram + disk partition), wlan0 DOWN (wired primary).

## Anomalies: none actionable

No failing drives, no reallocations, no PCIe errors, no kernel errors, no unknown PCI/USB
devices, no unexpected network interfaces, no MSR inconsistencies. The only true defects
found (empty cpuid_leaf records) are fixed in the audit script.

## Decisions needed from Chris

None. Hardware is healthy; the one script bug is fixed and validated.
