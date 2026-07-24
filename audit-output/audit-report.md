# Sovereign Log Audit Report
**Log File:** `2026-07-22T00:07:28-06:00.log` (1000 lines)
**Generated:** 2026-07-22T06:19:38.186Z

---

## 📈 Summary Statistics

| Metric | Value |
|--------|-------|
| Total Log Lines | 1000 |
| Parsed Entries | 1000 |
| ERROR Level | 954 |
| WARN Level | 3 |
| INFO Level | 43 |
| Unique Error Patterns | 13 |
| Total Error Occurrences | 955 |

---

## 📊 By Module
| `worktree` | 952 |
| `git::repository` | 38 |
| `fs` | 3 |
| `crates/task/src/vscode_format.rs:158` | 2 |
| `zed::reliability` | 2 |
| `node_runtime` | 1 |
| `agent` | 1 |
| `agent::thread` | 1 |

---

## 🔴 Top 10 Problematic Repositories
| Repository | Error Count |
|------------|-------------|
| SketchyStunts_Cachy-Hyprland-Tweaked | 844 |
| samonide_Cachy-dots | 58 |
| highercomve_hyprdotfiles | 17 |
| unknown | 13 |
| ZanzyTHEbar_dragonarchy | 6 |
| bgibson72_yahr-quickshell | 4 |
| JaKooLit_Hyprland-Dots | 3 |
| LinuxBeginnings_Hyprland-Dots | 3 |
| HyDE-Project_hyde | 2 |
| bryanwills_HyDE-arch | 2 |

---

## 🏷️ Error Categories
| Category | Count |
|----------|-------|
| broken_symlink | 949 |
| symlink_loop | 6 |

---

## 📋 Detailed Error Breakdown
### SketchyStunts_Cachy-Hyprland-Tweaked (broken_symlink)
- **Error:** `No such file or directory`
- **Occurrences:** 844
- **Example Path:** `/home/toxic/projects/dotfiles_pull/repos/SketchyStunts_Cachy-Hyprland-Tweaked/dotfiles/.config/Kvantum/pywal/pywal.kvconfig`

### samonide_Cachy-dots (broken_symlink)
- **Error:** `No such file or directory`
- **Occurrences:** 58
- **Example Path:** `/home/toxic/projects/dotfiles_pull/repos/samonide_Cachy-dots/.config/hyde/themes/AbyssGreen/wall.set`

### highercomve_hyprdotfiles (broken_symlink)
- **Error:** `No such file or directory`
- **Occurrences:** 17
- **Example Path:** `/home/toxic/projects/dotfiles_pull/repos/highercomve_hyprdotfiles/dotfiles/waypaper/config.ini`

### unknown (broken_symlink)
- **Error:** `No such file or directory`
- **Occurrences:** 13
- **Example Path:** `/home/toxic/projects/ide-test/zed-fang/.devenv/gc/shell`

### bgibson72_yahr-quickshell (broken_symlink)
- **Error:** `No such file or directory`
- **Occurrences:** 4
- **Example Path:** `/home/toxic/projects/dotfiles_pull/repos/bgibson72_yahr-quickshell/fastfetch/current-theme-logo.png`

### ZanzyTHEbar_dragonarchy (broken_symlink)
- **Error:** `No such file or directory`
- **Occurrences:** 4
- **Example Path:** `/home/toxic/projects/dotfiles_pull/repos/ZanzyTHEbar_dragonarchy/packages/kitty/.config/kitty/colors.conf`

### JaKooLit_Hyprland-Dots (broken_symlink)
- **Error:** `No such file or directory`
- **Occurrences:** 3
- **Example Path:** `/home/toxic/projects/dotfiles_pull/repos/JaKooLit_Hyprland-Dots/config/rofi/.current_wallpaper`

### LinuxBeginnings_Hyprland-Dots (broken_symlink)
- **Error:** `No such file or directory`
- **Occurrences:** 3
- **Example Path:** `/home/toxic/projects/dotfiles_pull/repos/LinuxBeginnings_Hyprland-Dots/config/waybar/config`

### HyDE-Project_hyde (symlink_loop)
- **Error:** `Too many levels of symbolic links`
- **Occurrences:** 2
- **Example Path:** `/home/toxic/projects/dotfiles_pull/repos/HyDE-Project_hyde/Source/assets/hyde.png`

### bryanwills_HyDE-arch (symlink_loop)
- **Error:** `Too many levels of symbolic links`
- **Occurrences:** 2
- **Example Path:** `/home/toxic/projects/dotfiles_pull/repos/bryanwills_HyDE-arch/Source/assets/hyde.png`

### rohankid1_cachy-dotfiles (broken_symlink)
- **Error:** `No such file or directory`
- **Occurrences:** 2
- **Example Path:** `/home/toxic/projects/dotfiles_pull/repos/rohankid1_cachy-dotfiles/ags/.config/ags/types`

### ZanzyTHEbar_dragonarchy (symlink_loop)
- **Error:** `Too many levels of symbolic links`
- **Occurrences:** 2
- **Example Path:** `/home/toxic/projects/dotfiles_pull/repos/ZanzyTHEbar_dragonarchy/packages/hardware/.config/systemd/user/timers.target.wants/fprintd-watchdog.timer`

### celesrenata_end-4-flakes (broken_symlink)
- **Error:** `No such file or directory`
- **Occurrences:** 1
- **Example Path:** `/home/toxic/projects/dotfiles_pull/repos/celesrenata_end-4-flakes/configs/quickshell/ii/modules/settings/transparency-config.json`

---

## 🎯 Fix Plan for Subagents

### Subagent A: Symlink Cleanup (Broken Symlinks)
**Scope:** All `broken_symlink` errors (10 patterns, 949 occurrences)

**Repos to fix:**
- SketchyStunts_Cachy-Hyprland-Tweaked: 844 occurrences
- samonide_Cachy-dots: 58 occurrences
- highercomve_hyprdotfiles: 17 occurrences
- unknown: 13 occurrences
- bgibson72_yahr-quickshell: 4 occurrences
- ZanzyTHEbar_dragonarchy: 4 occurrences
- JaKooLit_Hyprland-Dots: 3 occurrences
- LinuxBeginnings_Hyprland-Dots: 3 occurrences
- rohankid1_cachy-dotfiles: 2 occurrences
- celesrenata_end-4-flakes: 1 occurrences

**Action:** Remove or fix dangling symlinks in dotfiles_pull/repos/* directories.

### Subagent B: Symlink Loop Resolution
**Scope:** All `symlink_loop` errors (3 patterns, 6 occurrences)

**Repos to fix:**
- HyDE-Project_hyde: 2 occurrences
- bryanwills_HyDE-arch: 2 occurrences
- ZanzyTHEbar_dragonarchy: 2 occurrences

**Action:** Resolve circular symlink chains (likely HyDE assets).

---

## 💾 Machine-Readable Outputs
- `audit-data.json` — Full parsed data
- `audit-fixes.json` — Structured fix list for subagents
