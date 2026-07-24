#!/usr/bin/env bash
# Fix broken symlinks in dotfiles_pull/repos/
# Run from /home/toxic/sovereign

set -euo pipefail

LOG_FILE="/home/toxic/sovereign/audit-output/fix-broken-symlinks.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Fixing broken symlinks started at $(date) ==="

# Function to remove broken symlinks in a directory
fix_broken_symlinks() {
    local dir="$1"
    if [[ -d "$dir" ]]; then
        local count=0
        while IFS= read -r -d '' link; do
            if [[ -L "$link" && ! -e "$link" ]]; then
                rm -f "$link"
                ((count++))
            fi
        done < <(find "$dir" -type l -print0 2>/dev/null)
        if [[ $count -gt 0 ]]; then
            echo "  Fixed $count broken symlinks in $dir"
        fi
        return $count
    fi
    return 0
}

total_fixed=0

# Subagent A: Broken Symlinks
echo "--- Subagent A: Broken Symlinks ---"

# 1. SketchyStunts_Cachy-Hyprland-Tweaked (844 broken symlinks - Tela-circle icons)
dir="/home/toxic/projects/dotfiles_pull/repos/SketchyStunts_Cachy-Hyprland-Tweaked/home_backup/.icons"
if [[ -d "$dir" ]]; then
    echo "Processing: $dir"
    fix_broken_symlinks "$dir"
    total_fixed=$((total_fixed + $?))
fi

# 2. samonide_Cachy-dots (58 broken symlinks - hyde themes)
dir="/home/toxic/projects/dotfiles_pull/repos/samonide_Cachy-dots"
if [[ -d "$dir" ]]; then
    echo "Processing: $dir"
    fix_broken_symlinks "$dir"
    total_fixed=$((total_fixed + $?))
fi

# 3. highercomve_hyprdotfiles (17 broken symlinks - waypaper/waybar configs)
dir="/home/toxic/projects/dotfiles_pull/repos/highercomve_hyprdotfiles"
if [[ -d "$dir" ]]; then
    echo "Processing: $dir"
    fix_broken_symlinks "$dir"
    total_fixed=$((total_fixed + $?))
fi

# 4. unknown (zed-fang/zerofang/omnifang/lapce-sovereign/void-fang - devenv gc)
for subdir in zed-fang zerofang omnifang lapce-sovereign void-fang; do
    dir="/home/toxic/projects/ide-test/$subdir/.devenv/gc"
    if [[ -d "$dir" ]]; then
        echo "Processing: $dir"
        fix_broken_symlinks "$dir"
        total_fixed=$((total_fixed + $?))
    fi
done

# 5. bgibson72_yahr-quickshell (4 broken symlinks)
dir="/home/toxic/projects/dotfiles_pull/repos/bgibson72_yahr-quickshell"
if [[ -d "$dir" ]]; then
    echo "Processing: $dir"
    fix_broken_symlinks "$dir"
    total_fixed=$((total_fixed + $?))
fi

# 6. ZanzyTHEbar_dragonarchy (4 broken symlinks - kitty colors)
dir="/home/toxic/projects/dotfiles_pull/repos/ZanzyTHEbar_dragonarchy"
if [[ -d "$dir" ]]; then
    echo "Processing: $dir"
    fix_broken_symlinks "$dir"
    total_fixed=$((total_fixed + $?))
fi

# 7. JaKooLit_Hyprland-Dots (3 broken symlinks)
dir="/home/toxic/projects/dotfiles_pull/repos/JaKooLit_Hyprland-Dots"
if [[ -d "$dir" ]]; then
    echo "Processing: $dir"
    fix_broken_symlinks "$dir"
    total_fixed=$((total_fixed + $?))
fi

# 8. LinuxBeginnings_Hyprland-Dots (3 broken symlinks)
dir="/home/toxic/projects/dotfiles_pull/repos/LinuxBeginnings_Hyprland-Dots"
if [[ -d "$dir" ]]; then
    echo "Processing: $dir"
    fix_broken_symlinks "$dir"
    total_fixed=$((total_fixed + $?))
fi

# 9. rohankid1_cachy-dotfiles (2 broken symlinks)
dir="/home/toxic/projects/dotfiles_pull/repos/rohankid1_cachy-dotfiles"
if [[ -d "$dir" ]]; then
    echo "Processing: $dir"
    fix_broken_symlinks "$dir"
    total_fixed=$((total_fixed + $?))
fi

# 10. celesrenata_end-4-flakes (1 broken symlink)
dir="/home/toxic/projects/dotfiles_pull/repos/celesrenata_end-4-flakes"
if [[ -d "$dir" ]]; then
    echo "Processing: $dir"
    fix_broken_symlinks "$dir"
    total_fixed=$((total_fixed + $?))
fi

echo "=== Total broken symlinks fixed: $total_fixed ==="

# Subagent B: Symlink Loops
echo "--- Subagent B: Symlink Loops ---"

fix_symlink_loop() {
    local path="$1"
    if [[ -L "$path" ]]; then
        # Check if it's a loop
        if ! readlink -f "$path" >/dev/null 2>&1; then
            echo "  Removing symlink loop: $path"
            rm -f "$path"
            return 1
        fi
    fi
    return 0
}

# HyDE-Project_hyde / Source/assets/hyde.png
path="/home/toxic/projects/dotfiles_pull/repos/HyDE-Project_hyde/Source/assets/hyde.png"
fix_symlink_loop "$path" || echo "Fixed loop at $path"

# bryanwills_HyDE-arch / Source/assets/hyde.png
path="/home/toxic/projects/dotfiles_pull/repos/bryanwills_HyDE-arch/Source/assets/hyde.png"
fix_symlink_loop "$path" || echo "Fixed loop at $path"

# ZanzyTHEbar_dragonarchy / packages/hardware/.config/systemd/user/timers.target.wants/fprintd-watchdog.timer
path="/home/toxic/projects/dotfiles_pull/repos/ZanzyTHEbar_dragonarchy/packages/hardware/.config/systemd/user/timers.target.wants/fprintd-watchdog.timer"
fix_symlink_loop "$path" || echo "Fixed loop at $path"

echo "=== Fix completed at $(date) ==="
