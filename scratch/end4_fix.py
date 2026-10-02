#!/usr/bin/env python3
"""Bruteforce README fix for toxicwind/sovereign-end4. Every replacement
asserts its match count — any failure aborts with a clear message."""
import sys

R = '/home/toxic/readmefix-end4-4223/repo'
P = R + '/README.md'
t = open(P).read()
changes = []

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f'REP FAIL ({n}x, want {count}x): {old[:90]!r}'
    t = t.replace(old, new)
    changes.append('rep: ' + old[:60].replace('\n', '\\n'))

def delline(substr):
    global t
    lines = t.split('\n')
    hits = [i for i, l in enumerate(lines) if substr in l]
    assert len(hits) == 1, f'DELLINE FAIL ({len(hits)}x): {substr!r}'
    del lines[hits[0]]
    t = '\n'.join(lines)
    changes.append('del line: ' + substr[:60])

def insert_after(anchor_frag, new_text):
    global t
    lines = t.split('\n')
    hits = [i for i, l in enumerate(lines) if anchor_frag in l]
    assert len(hits) == 1, f'INSERT_AFTER FAIL ({len(hits)}x): {anchor_frag!r}'
    lines.insert(hits[0] + 1, new_text)
    t = '\n'.join(lines)
    changes.append('insert_after: ' + anchor_frag[:50])

def append_after_line_with(frag, new_text):
    global t
    lines = t.split('\n')
    hits = [i for i, l in enumerate(lines) if frag in l]
    assert len(hits) == 1, f'APPEND_AFTER FAIL ({len(hits)}x): {frag!r}'
    lines.insert(hits[0] + 1, new_text)
    t = '\n'.join(lines)
    changes.append('append_after: ' + frag[:50])

def banner_fix(old_frag, new_frag):
    """Replace text inside an ASCII-banner line, re-pad to original width."""
    global t
    lines = t.split('\n')
    for i, l in enumerate(lines):
        if old_frag in l and l.rstrip().endswith('║'):
            nl = l.replace(old_frag, new_frag)
            assert len(nl) <= len(l), f'banner frag too long: {new_frag!r}'
            nl = nl[:-1] + ' ' * (len(l) - len(nl)) + '║'
            lines[i] = nl
            t = '\n'.join(lines)
            changes.append('banner: ' + old_frag[:40])
            return
    raise AssertionError('banner frag not found: ' + old_frag)

# ---- 1. Rebrand leftovers ----
rep('# toxicwind/sovereign-hypr // ii — Iterative Instinct',
    '# toxicwind/sovereign-end4 // ii — Iterative Instinct')
rep('║  sovereign-hypr // ii — Iterative Instinct',
    '║  sovereign-end4 // ii — Iterative Instinct')
banner_fix('(Haar cascades)', '(Canny edges)')
banner_fix('Exponential backoff with full jitter (AWS SRE spec)',
           'Crash-proof grim+slurp screenshot pipeline')
banner_fix('804-app Launchpad', '114-app Launchpad')

# ---- 2. Path convention note ----
rep("## 🎯 What's Different from Upstream\n",
    "## 🎯 What's Different from Upstream\n\n"
    "> **Path convention:** `hypr/...`, `modules/...`, and `scripts/...` below are relative to their "
    "*installed* locations (`~/.config/hypr/`, `~/.config/quickshell/ii/`); in this repo they live under "
    "`dots/.config/...` (see `install.conf.yaml`).\n")

# ---- 3. Hyprland Core table fixes ----
rep('`hypr/custom/keybinds.lua`', '`hypr/hyprland/keybinds.lua`')
rep('`SUPER+Return` → **wezterm** (keycode `36` fallback)',
    '`SUPER+Return` → **wezterm** (keycode `36` fallback); `SUPER` → Quickshell search overview; `SUPER+D` → Fuzzel')
rep('rgba(3f484b77)', 'rgba(4a464677)')
rep('rgba(171c1e33)', 'rgba(1e1b1b33)')
rep('rgba(0f1416FF)', 'rgba(161313FF)')

# ---- 4. QuickShell detail fixes ----
rep('Split `middleFraction` → `middleFractionX` + `middleFractionY` for **vertical + horizontal parallax**',
    'Single `middleFraction` (0.5 default) — no X/Y split; parallax via `parallaxTotalPixelsX/Y`')
rep('Dynamic Python venv resolution (was hardcoded), returns both **X and Y** focus points',
    'Prints `width height focus` (single 0–1 focal value, 0.5 fallback); plain `python3`, no venv resolution')
rep('**Art/Anime/Furry-aware** — Haar cascade face/eye detection, warm/cool color analysis, Laplacian detail map',
    '**Art/Anime/Furry-aware** — Canny edge map + saturation/hue masking for focal-point detection (no Haar cascades, no Laplacian)')

# ---- 5. Screenshot section: document reality (block swap) ----
shot_start = '#### Screenshot / Region Capture — Exponential Backoff + Circuit Breaker'
shot_end = '#### Booru / Wallpaper Sources'
si = t.find(shot_start)
ei = t.find(shot_end)
assert si != -1 and ei != -1 and ei > si, 'screenshot block anchors not found'
shot_new = '''#### Screenshot / Region Capture — Crash-Proof grim+slurp

| File | Change |
| ---- | ------ |
| `scripts/screenshot-region.sh` | **New** — crash-proof grim+slurp pipeline: duplicate-`slurp` guard (`pidof`), `slurp` region select, `grim` capture, `wl-copy` to clipboard; actions `copy` / `edit` (`swappy`) / `ocr` (`tesseract`); `notify-send` feedback; exits cleanly on cancel |
| `modules/common/utils/RecursiveFallback.qml` | Generic recursive fallback engine — each strategy runs in its own nested try/catch with self-heal and watchdog escalation (ReAct/Reflexion-inspired); no exponential backoff, no circuit breaker |
| `modules/common/models/quickToggles/ScreenSnipToggle.qml` | Shells out to `scripts/screenshot-region.sh` directly (does not use `RecursiveFallback`) |
| `modules/ii/bar/UtilButtons.qml` | Wires new screenshot toggle |

> **History:** the July exponential-backoff experiment (`70b7758`) was superseded — the Sep desktop syncs restored upstream's non-backoff `RecursiveFallback.qml`, and `42f4f58` replaced the screenshot design with the grim+slurp pipeline above. `PrintScreen` is bound (`787ef91`).

'''
t = t[:si] + shot_new + t[ei:]
changes.append('screenshot section block swap')

# ---- 6. Mac Launcher count ----
rep('**804 apps** — static database: categories, colors, icons, exec commands',
    '**114 apps** — static database (`"name":` entries in `AppDatabase.qml`): categories, colors, icons, exec commands')

# ---- 7. Meta-packages block ----
rep('Installed via `makepkg -si` from the repo root:',
    'Installed automatically by `./setup install` — routed through `sdata/subcmd-install/1.deps-router.sh` → '
    '`sdata/dist-arch/install-deps.sh` (runs a full `pacman -Syu` first; there is no flag to skip the system update):')
rep('cd /home/toxic/projects/dots-hyprland\n./setup install-deps -f --skip-sysupdate',
    'cd sovereign-end4\n./setup install -y')

# ---- 8. Installation section: real setup CLI ----
rep('# 2. Install deps (non-interactive, skip system update)\n./setup install-deps -f --skip-sysupdate',
    '# 2. Install everything: pacman -Syu + AUR deps, dotfile symlinks, system setups\n./setup install -y')
rep('# 4. Install configs\n./setup install-files -f\n\n# 5. Reboot or restart SDDM + Hyprland',
    '# 4. Reboot or restart SDDM + Hyprland')
rep('# 4. Reboot or restart SDDM + Hyprland\n```',
    '# 4. Reboot or restart SDDM + Hyprland\n```\n\n'
    '> **Selective phases:** `./setup install --skip-deps`, `--skip-links`, or `--skip-setups`. '
    'Preview with `./setup install -n` (dry run).')

# ---- 9. Upstream Sync note (line surgery on unique fragment) ----
def rep_line_containing(frag, new_line):
    global t
    lines = t.split('\n')
    hits = [i for i, l in enumerate(lines) if frag in l]
    assert len(hits) == 1, f'LINE_REP FAIL ({len(hits)}x): {frag!r}'
    lines[hits[0]] = new_line
    t = '\n'.join(lines)
    changes.append('line rep: ' + frag[:50])

rep_line_containing('exp-merge',
    '> **Note:** `sdata/subcmd-exp-merge/` is a legacy leftover — `./setup` has no `exp-merge` subcommand. Rebase manually as above.')

# ---- 10. mise comment: rust-web is dead ----
rep('mise run up        # starts llama-swap:25100, rust-web:25101, openfang:25103, etc.',
    'mise run up        # starts llama-swap:25100, openfang:25103, etc.')

# ---- 11. Structure diagram ----
rep('sovereign-hypr/', 'sovereign-end4/')
insert_after('├── diagnose                   # Health check script',
             '├── docs/                      # System-tuning audit + CachyOS kernel/limine notes')
rep('├── dots/                      # ~/.config/* symlinks',
    '├── dots/                      # ~/ dotfiles + .config/* symlinks\n'
    '│   ├── .bashrc                # Canonical bash dotfiles (.bashrc.env, .bash_profile)')
insert_after('├── install.conf.yaml          # Declarative symlink & provisioning manifest',
             '├── dots-extra/                # Distro-specific extras (emacs, fcitx5, fedora, fontsets, swaylock, via-nix)\n'
             '├── licenses/                  # Third-party license notices (LGPL-3.0, MIT)')
rep('├── scripts/                   # Utility and wallpaper scripts',
    '├── scripts/                   # Repo-level utilities (keyring PAM fix)')
rep('└── setup                      # Streamlined bootstrap runner',
    '├── setup                      # Main entry point (install/sync/check/checkbins/checkdeps/help)\n'
    '├── sdata/                     # Install phases: deps router, meta-package PKGBUILDs, setups, file linking\n'
    '├── system-tuning/             # apply-system-tuning.sh, limine, sysctl (zswap), udev\n'
    '└── README.md                  # This file')

# ---- 12. Related repos: drop dead, fix mcpproxy ----
delline('toxicwind/byte-vision-proxy')
delline('toxicwind/rust-web')
rep('toxicwind/mcpproxy](https://github.com/toxicwind/mcpproxy)',
    'toxicwind/mcpproxy-go](https://github.com/toxicwind/mcpproxy-go)')

# ---- 13. Recent Changes section ----
recent = """## 📝 Recent Changes

- **Super key** is dedicated to the native Quickshell search overview; Fuzzel moved to `SUPER+D` (`347077e`).
- **Mac Launcher** filters `hidden`/`noDisplay` desktop entries and dedupes identical entries (`1179bfc`).
- **Screenshot engine** is a crash-proof grim+slurp pipeline; the July exponential-backoff experiment was reverted during the Sep desktop syncs (`42f4f58`).
- **Keyring popup eliminated** — PAM unlock on SDDM login + hyprlock unlock, bar screen-snip button restored (`787ef91`).
- **PrintScreen** dispatch fixed and bound (`42f4f58`, `787ef91`).
- **Bash dotfiles** consolidated from live home: `dots/.bashrc`, `.bashrc.env`, `.bash_profile` (`f4694c1`).
- **System tuning** lives in `system-tuning/` (`apply-system-tuning.sh`, limine, sysctl/zswap, udev); background docs in `docs/` (`AUDIT_SYSTEM_TUNING_AND_OPTIMIZATIONS.md`, `cachyos-kernel-limine-tuning.md`).
- **Extras & licenses:** `dots-extra/` (emacs, fcitx5, fedora, fontsets, swaylock, via-nix), `licenses/` (third-party notices). Run `./diagnose` after install for a health check.

---

"""
rep('## 📁 Repository Structure', recent + '## 📁 Repository Structure')

open(P, 'w').write(t)

# ---- install.conf.yaml header ----
IP = R + '/install.conf.yaml'
it = open(IP).read()
n = it.count('# sovereign-hypr // ii — Iterative Instinct')
assert n == 1, f'install.conf.yaml header count: {n}'
it = it.replace('# sovereign-hypr // ii — Iterative Instinct',
                '# sovereign-end4 // ii — Iterative Instinct')
open(IP, 'w').write(it)
changes.append('install.conf.yaml header')

print(f'OK: {len(changes)} edits, README {len(t)} chars')
for c in changes:
    print('  -', c)
