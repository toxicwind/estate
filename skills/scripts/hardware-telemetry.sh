#!/usr/bin/env bash
# ==============================================================================
# Sovereign Hardware & Performance Telemetry Helper
# Inspects CPU cores, frequency governor, L3 cache, swappiness, and GPU memory.
# ==============================================================================
set -euo pipefail

echo "=== CPU & Architecture ==="
lscpu | grep -E 'Model name|CPU\(s\):|Thread|Core|L1|L2|L3|NUMA' || true

echo "=== CPU Scaling Governor ==="
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "governor unreadable"

echo "=== Memory & Swappiness ==="
free -h
echo "swappiness: $(cat /proc/sys/vm/swappiness 2>/dev/null || echo 'N/A')"
echo "vfs_cache_pressure: $(cat /proc/sys/vm/vfs_cache_pressure 2>/dev/null || echo 'N/A')"

echo "=== NVMe I/O Scheduler ==="
cat /sys/block/nvme0n1/queue/scheduler 2>/dev/null || echo "scheduler unreadable"

echo "=== GPU Telemetry (NVIDIA RTX 3090) ==="
nvidia-smi --query-gpu=name,driver_version,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu --format=csv || echo "nvidia-smi unavailable"

echo "=== System Load Average ==="
cat /proc/loadavg
