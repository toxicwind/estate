# RTX 3090 cooling · LACT · undervolt notes

## What was wrong
`lactd` was active with an **aggressive fan curve**:
- ~40–55% duty around 40–50°C idle
- Observed: **~46% / ~1700 RPM at 41–44°C** → jet-engine idle noise

Also `power_cap: 350` (max) with no soft undervolt, so load ramps heat/fans hard.

## Current control plane
| Piece | Role |
|--------|------|
| **`lactd`** (`systemctl status lactd`) | Primary GPU fan + power control |
| Config | `/etc/lact/config.yaml` |
| CLI | `lact cli stats`, `lact cli power-limit get\|set` |
| Backup script | `sovereign/bin/nvidia-fan-curve.py` (exits if lactd active) |

## Applied quiet profile
- **Fan curve**: hold **30%** (hardware minimum on this 3090) until ~50°C, then gentle ramp
- **Hysteresis**: `change_threshold: 4`, `spindown_delay_ms: 12000` (less hunting)
- **Power cap**: **300 W** (range 100–365) — practical “undervolt” for LLM
- **Clock offset**: `gpu_clock_offsets: {0: -80}` MHz on P0 (mild)
- **Thermal target**: 80°C (`nvidia_thermal_options`)

After apply (measured): **42–44°C, 30% fan (~1190 RPM), 300 W limit**.

## Undervolting reality (NVIDIA + Linux)
Full curve undervolt (mV vs MHz) is **first-class on AMD** in LACT; on NVIDIA:

1. **Power limit** (best lever) — `lact cli power-limit set 280..300`
2. **Clock offset** — LACT `gpu_clock_offsets` / NvAPI
3. **PowerMizer** — `PreferConsistentPerformance` vs max boost

True per-MHz undervolt like Afterburner is limited; don’t expect MSI Afterburner UV tables.

### Performance profile (when you need max)
```bash
# temporary full power
lact cli power-limit set 350
# edit /etc/lact/config.yaml → power_cap: 350.0 and gpu_clock_offsets: {0: 0}
sudo systemctl restart lactd
```

### Quieter still under load
Lower power further if models still fit:
```bash
lact cli power-limit set 280
```

## GHAS / ecosystem references
- [ilya-zlobintsev/LACT](https://github.com/ilya-zlobintsev/LACT) — daemon we use
- [nan0s7/nfancurve](https://github.com/nan0s7/nfancurve) — quiet POSIX curves
- [infinirc/nvfd](https://github.com/infinirc/nvfd) — NVML fan daemon (X11/Wayland/headless)
- [foucault/nvfancontrol](https://github.com/foucault/nvfancontrol) — Rust dynamic fan control

## Other noise sources
- **PCIe link** currently reported as Gen1 x8 at times — not fan, but hurts bandwidth; check cable/slot if LLM tokens/s look wrong.
- Case / CPU fans are separate from GPU duty.

## Ops
```bash
lact cli stats
nvidia-smi --query-gpu=temperature.gpu,fan.speed,power.draw,power.limit --format=csv
sudo systemctl status lactd
# after editing config:
sudo systemctl restart lactd
```
