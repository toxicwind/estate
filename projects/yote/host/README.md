<div align="right">

[![license: MIT](https://img.shields.io/badge/license-MIT%20%2B%20upstream-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects#license)
[![sovereign-projects](https://img.shields.io/badge/sovereign--projects-1f6feb?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects)

</div>

# yote host provisioning

> Source of truth for host-level `/etc` config on the yote box.

> **Why care? Hand-tuned box config rots — vendor packages silently override it (ask the swappiness=150 incident). This directory mirrors `/etc` paths exactly and `apply.sh` re-asserts the intended state, so the box is reproducible and drift is a diff, not a mystery.**

- **`etc/` mirrors `/etc` paths exactly — deploy with `./apply.sh` (runs on yote, needs sudo)**
- **zram mask — comment-only udev rule masks the vendor `30-zram.rules` that trampled `vm.swappiness=60`**
- **nvidia-persistenced self-heal — `Restart=on-failure` drop-in for the early-start race**
- **Drift-proof — live `/etc` files carry a comment naming their repo source; re-running `apply.sh` re-asserts state**
- **Proven live — every artifact documents its root cause, fix, and no-reboot verification**

```mermaid
flowchart LR
    REPO[host/etc/...] --> APPLY[apply.sh on yote]
    APPLY --> ETC[live /etc]
    ETC -->|comment names repo source| SYNC[keep in sync]
    DRIFT[vendor upgrade / drift] --> APPLY
    APPLY --> VERIFY[checklist: swappiness=60, zswap=Y, persistenced active]
```

## Quick start

```bash
cd projects/yote/host && ./apply.sh   # runs on yote, needs sudo
cat /proc/sys/vm/swappiness           # -> 60
cat /sys/module/zswap/parameters/enabled  # -> Y
```

## License & security

- **License:** [MIT](https://github.com/toxicwind/sovereign-projects#license)
- **Security:** `apply.sh` needs sudo and writes host `/etc` — review the diff before applying on a live box. The zram mask survives `cachyos-settings` upgrades precisely because it doesn't edit `/usr/lib` directly.

---

<div align="right">

![sovereign](https://img.shields.io/badge/sovereign--projects-blue?style=for-the-badge)
![bash](https://img.shields.io/badge/bash-4EAA25?style=for-the-badge)
![systemd](https://img.shields.io/badge/systemd-2D2D2D?style=for-the-badge)
![arch-linux](https://img.shields.io/badge/arch--linux-1793D1?style=for-the-badge)

</div>

**This directory is the canonical source of truth for host-level `/etc` config on yote (the CachyOS/Arch bridge box).** Vendor packages silently override hand-tuned kernel and daemon settings — twice, in ways that took real hunts to find. The fix isn't "remember to re-tune after every upgrade"; it's this tree: files under `etc/` mirror their `/etc` paths exactly, and one script re-asserts them. Drift is a deploy away from fixed, not a mystery away from noticed.

## Quick Start

```bash
cd projects/yote/host && ./apply.sh
cat /proc/sys/vm/swappiness
systemctl is-active nvidia-persistenced
```

`apply.sh` runs on yote and needs sudo for the `etc/` side; `home/` files install as the invoking user (no sudo). Re-running after package upgrades or drift re-asserts the intended state. The live `/etc` files carry a comment naming their repo source — keep both sides in sync.

## Architecture

```mermaid
flowchart LR
    ETC["etc/\nmirrors /etc paths"] --> APPLY["apply.sh\nidempotent"]
    HOME["home/\nmirrors $HOME paths"] --> APPLY
    APPLY -->|sudo| LIVE_ETC["/etc on yote\nudev rules · sysctl · systemd drop-ins"]
    APPLY -->|as user| LIVE_HOME["$HOME on yote\n.cargo/config.toml · ccache.conf"]
    LIVE_ETC -.->|verified by| CHECK["deploy checklist\nswappiness=60 · zswap=Y\npersistenced active"]
```

## Artifacts

### `etc/udev/rules.d/30-zram.rules` — zswap + swappiness=60 mask

**Root cause (found 2026-09-21):** the `cachyos-settings` package ships `/usr/lib/udev/rules.d/30-zram.rules`, which fires on every `zram0` init and writes `vm.swappiness=150` and `N > /sys/module/zswap/parameters/enabled`. That silently trampled Chris's hand-tuned dual setup:

- `/etc/sysctl.d/99-zswap-vm.conf` → `vm.swappiness=60`
  (lexically wins over `99-znver4-llm.conf`=10 and `/usr/lib/sysctl.d/70-cachyos-settings.conf`=100;
  `vm.dirty_ratio=10` from the same file is the correct expected value)
- kernel cmdline `zswap.enabled=1` + `CONFIG_ZSWAP_DEFAULT_ON=y`

The vendor rule's zram-only policy is defensible for pure-zram setups, but the bug is the silent override of explicit tuning — plus it contributed to the 2026-09-21 11:21:54 MDT ffs order-0 allocation warning by routing reclaim pressure 3:1 toward anon/zswap at maximum volume.

**Fix:** a same-named, comment-only file in `/etc/udev/rules.d` masks the vendor file by precedence (verified: udev reports `Skipping overridden file '/usr/lib/udev/rules.d/30-zram.rules'`) and survives `cachyos-settings` upgrades — unlike editing `/usr/lib` directly.

**Proven live (no reboot):** `udevadm control --reload-rules` + `udevadm trigger --action=change --sysname-match=zram0` leaves `vm.swappiness=60` and zswap `Y` untouched.

### `etc/systemd/system/nvidia-persistenced.service.d/override.conf` — persistenced self-heal

**Root cause (found 2026-09-21):** on the 2026-09-20 bore-kernel repair boot, `nvidia-persistenced` started at 21:39:11 MDT, ~7 minutes before `/dev/nvidia*` existed (the bore nvidia driver was installed mid-boot; initramfs rebuilt 21:46:34). The stock NVIDIA unit has no restart policy, so it stayed `failed` until noticed. Daemon and driver were healthy — verified by running it as root manually.

**Fix:** drop-in adds `Restart=on-failure` + `RestartSec=15` so future early-start races self-heal, plus start-limit settings.

**Important:** `StartLimitBurst`/`StartLimitIntervalSec` belong under `[Unit]` on systemd ≥ 230 (verified 261.3 on yote). Under `[Service]`, `systemd-analyze verify` warns `Unknown key ... ignoring` and they have no effect. An earlier version of this drop-in had them misplaced; corrected 2026-09-21.

**Proven live (no reboot):** `systemctl restart` → active, `nvidia-smi` persistence mode `Enabled`; `kill -9` on the daemon → systemd reborns it within seconds (`NRestarts=1`).

## Build-cache home configs

`home/` mirrors `$HOME` paths (installed as the invoking user by `apply.sh` via `install_home_file`). These are the canonical sources for the build-cache environment that buildsrv injects into every job (pitchfork.toml `daemons.buildsrv` env):

- `home/.cargo/config.toml` — `[build] rustc-wrapper = sccache`. Routes all Cargo rustc invocations through sccache (10 GiB at `~/.cache/sccache`). Requires `CARGO_INCREMENTAL=0` in the daemon env: sccache refuses incremental compilation outright.
- `home/.config/ccache/ccache.conf` — `max_size = 10.0G`, `compression = true`. Backs CC/CXX/CMAKE compiler launchers in the buildsrv env (10 GiB at `~/.cache/ccache`).

Proven 2026-09-21: real buildsrv job, `cargo clean` between builds, second build showed nonzero sccache hits (2 hits, 50% hit rate).

## Config

The full investigation record (4 lanes: swappiness provenance, page-alloc failure, zswap/persistenced/hardware, btrfs audit) lives at `~/workspace/kernel-anomaly-hunt/2026-09-21-findings.md` on the hatch cell. Snapshot pressure resolved itself (275.98 GiB free on 2026-09-21; no btrfs balance needed). Hardware healthy (NVMe 11% used, 0 media errors; RTX 3090 34°C).

### Deploy checklist after `apply.sh`

- `cat /proc/sys/vm/swappiness` → `60`
- `cat /sys/module/zswap/parameters/enabled` → `Y`
- `systemctl is-active nvidia-persistenced` → `active`
- `nvidia-smi --query-gpu=persistence_mode --format=csv,noheader` → `Enabled`
- `systemd-analyze verify nvidia-persistenced.service` → clean

## Dev / Contributing

- New host-level config lands here first, then deploys via `apply.sh` — never hand-edit `/etc` on the box and call it done; the next upgrade will eat it.
- Vendor files under `/usr/lib` are never edited directly — mask by precedence (`/etc` wins over `/usr/lib` in udev and systemd) so upgrades can't silently revert you.
- When a tuning value's provenance is unclear, hunt it like the 2026-09-21 swappiness case: grep the vendor packages, check lexical precedence, verify live — then encode the fix in this tree.

## License + Security

- This directory ships **no standalone LICENSE file**; it is declarative host config in the sovereign-projects tree.
- **Security posture:** no secrets live here — only tuning values, masks, and drop-ins. `apply.sh` is idempotent and re-runnable; the live `/etc` files name their repo source in a comment so any drift is attributable. Review the diff before applying after major package upgrades.
