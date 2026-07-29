# Swap Architecture Quick Reference

> **Live config** for AMD Ryzen 7 8700F + 62 GiB DDR5 + RTX 3090 + WD_BLACK SN850X

---

## Current Tiering (Active)

| Tier | Technology     | Size                | Priority | Role                 |
| ---- | -------------- | ------------------- | -------- | -------------------- |
| L1   | **zswap pool** | 25% RAM = 15.5 GiB  | Highest  | Hot compressed cache |
| L2   | **NVMe swap**  | 138 GiB (SN850X p4) | Medium   | Warm spillover       |
| L3   | HDD/QVO        | 8+ TB               | Lowest   | Cold archive         |

**zram: DISABLED** — LRU inversion proven harmful (Chris Down, Meta, 2026)

---

## Kernel Command Line (limine, all entries)

```bash
zswap.enabled=1 zswap.compressor=zstd zswap.max_pool_percent=25 \
zswap.shrinker_enabled=1 zswap.accept_threshold_percent=90 \
amd_pstate=guided cpufreq.default_governor=schedutil \
transparent_hugepage=madvise nvme_core.default_ps_max_latency_us=0
```

---

## Sysctl (`/etc/sysctl.d/99-swap-vm.conf`)

```ini
vm.swappiness = 60
vm.page-cluster = 0
vm.vfs_cache_pressure = 50
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10
vm.dirty_writeback_centisecs = 1500
vm.watermark_scale_factor = 10
vm.watermark_boost_factor = 0
vm.compaction_proactiveness = 0
vm.extfrag_threshold = 500
```

---

## Cgroup Overrides (llama-swap)

```bash
systemctl set-property llama-swap.slice \
  MemoryZSwapWriteback=0 \
  MemoryZSwapMax=8G \
  MemoryHigh=48G \
  MemoryMax=56G \
  CPUWeight=200 \
  IOWeight=200
```

---

## Live Tuning (No Reboot)

```bash
# zswap
echo zstd | sudo tee /sys/module/zswap/parameters/compressor
echo 25 | sudo tee /sys/module/zswap/parameters/max_pool_percent
echo Y | sudo tee /sys/module/zswap/parameters/shrinker_enabled
echo 90 | sudo tee /sys/module/zswap/parameters/accept_threshold_percent

# AMD P-state
echo guided | sudo tee /sys/devices/system/cpu/amd_pstate/status

# Verify
cat /sys/kernel/debug/zswap/pool_total_size
cat /sys/kernel/debug/zswap/stored_pages
cat /sys/kernel/debug/zswap/written_back_pages
```

---

## Key Thresholds

| Metric                  | Warning  | Critical |
| ----------------------- | -------- | -------- |
| zswap pool usage        | > 85%    | > 95%    |
| `pool_limit_hit`        | > 0/min  | > 10/min |
| PSI `some` avg10        | > 20%    | > 50%    |
| Swap read latency (p99) | > 500 µs | > 2 ms   |
| Compression ratio       | < 2.5:1  | < 2.0:1  |

---

## Rollback (Emergency)

```bash
echo 0 | sudo tee /sys/module/zswap/parameters/enabled
systemctl enable --now systemd-zram-setup@zram0
# Edit /etc/default/limine → remove zswap params
# limine-install
reboot
```
