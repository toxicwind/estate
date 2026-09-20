# README audit — toxicwind/sovereign-end4 @ f4694c179cf5b3f3d1c9a40992ac0cb6c0aca48c — 2026-09-14

**Verdict:** NEEDS UPDATE

Tarball matches HEAD (`f4694c179`, 2026-09-14). Repo: private, "Usability-first dotfiles". README title still says **sovereign-hypr** although the repo was renamed to sovereign-end4 in `e5298a58e` (2026-07-28, "complete fork rebrand + README overhaul") — the rebrand missed the title, ASCII banner, structure diagram, and `install.conf.yaml` header.

Mechanical (`bin/audit.py`): README exists (23,121 chars / 337 lines) PASS; relative links PASS; versions/badges PASS; mentioned-paths FAIL (10 `hypr/...` / `scripts/...` paths — mostly an install-relative vs repo-relative prefix issue, see below); external links WARN — 5 unauthenticated failures, of which 3 are genuinely dead (see claims 48).

Path convention: README paths like `hypr/custom/env.lua` and `scripts/colors/...` are relative to the *installed* locations (`~/.config/hypr/`, quickshell `ii/` script dir). In the repo they live under `dots/.config/hypr/...` and `dots/.config/quickshell/ii/scripts/...` (mapping confirmed in `install.conf.yaml`). The README never states this.

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| Title/banner: "toxicwind/sovereign-hypr // ii" | Repo is `toxicwind/sovereign-end4`; rename commit `e5298a58e` | STALE |
| Feature list: e621 male furry wallpapers, score>80, auto-upscale | `dots/.config/quickshell/ii/scripts/colors/random/random_e621_wall.sh:40` (query tags), `:31-36` (userAgent parse), upscayl present | VERIFIED |
| Feature list: Mac Launcher "804-app Launchpad" | `dots/.config/quickshell/ii/modules/mac_launcher/AppDatabase.qml` has 114 `"name":` entries | WRONG |
| Feature list: "Art/Anime/Furry-aware focus detection (Haar cascades)" | `.../scripts/colors/find_focus.py` (66 lines) uses Canny edges, saturation, hue — no Haar cascades, no Laplacian | WRONG |
| Feature list: "Exponential backoff with full jitter (AWS SRE spec)" | No backoff/jitter/retry in `.../scripts/screenshot-region.sh` or `.../modules/common/utils/RecursiveFallback.qml` | WRONG |
| Feature list: PAM keyring | `scripts/apply-keyring-pam.sh` exists; content matches documented sed lines | VERIFIED |
| Hyprland Core table: `hypr/custom/env.lua` vars | `dots/.config/hypr/custom/env.lua` — 4/4 nvidia/mozilla vars present | VERIFIED |
| Hyprland Core table: `hypr/custom/keybinds.lua` SUPER+Return → wezterm | `dots/.config/hypr/custom/keybinds.lua` is a 9-line comment stub; binding is at `dots/.config/hypr/hyprland/keybinds.lua:348-349` | WRONG (path) |
| Hyprland Core table: `hypr/custom/variables.lua` terminal="wezterm" | `dots/.config/hypr/custom/variables.lua:1` | VERIFIED |
| Hyprland Core table: `hypr/hyprland/colors.lua` borders `rgba(3f484b77)` / `rgba(171c1e33)` | Actual: `rgba(4a464677)` / `rgba(1e1b1b33)` (`dots/.config/hypr/hyprland/colors.lua:4-5`; matugen-regenerated) | STALE |
| Hyprland Core table: `hypr/hypridle.conf` hyprlock + dpms | `dots/.config/hypr/hypridle.conf:1,19-20` | VERIFIED |
| Hyprland Core table: `hypr/hyprland/execs.lua` removed gnome-keyring-daemon | No `keyring-daemon` in either execs.lua | VERIFIED |
| Hyprland Core table: `hypr/hyprland.lua` loads focuswindow plugin | Loaded via `dots/.config/hypr/hyprland/plugins.lua:8` (`custom.plugins.focuswindow` exists) | VERIFIED* |
| Hyprland Core table: `hypr/custom/input.lua`, `windowrules.lua`, `plugins/focuswindow.lua` new | All exist under `dots/.config/hypr/custom/` | VERIFIED |
| Hyprlock table: matugen colors + `$background_image` | `dots/.config/hypr/hyprlock/colors.conf:1,12` | VERIFIED |
| Hyprlock table: clock `$TIME12` | `dots/.config/hypr/hyprlock.conf:47` | VERIFIED |
| QuickShell: `Config.qml` e621 NSFW keywords | `.../modules/common/Config.qml:606-607` | VERIFIED |
| QuickShell: `Background.qml` middleFraction → X+Y split | Single `middleFraction: 0.5` (`.../modules/ii/background/Background.qml:61,122`); parallax exists via `parallaxTotalPixelsX/Y` | WRONG (detail) |
| QuickShell: `find_focus.py` Haar/Laplacian | See focus-detection row above | WRONG |
| QuickShell: `get_wallpaper_info.sh` dynamic venv + X/Y focus | Plain `python3` call, single focus value fallback 0.5 (`.../scripts/colors/get_wallpaper_info.sh`) | WRONG |
| QuickShell: `random_konachan_wall.sh` removed | Absent from entire tree | VERIFIED |
| QuickShell: `Booru.qml` e621 provider | `.../services/Booru.qml:60-64` | VERIFIED |
| QuickShell: `LauncherSearch.qml` e621wallpaper action | `.../services/LauncherSearch.qml:78-80` | VERIFIED |
| QuickShell: `welcome.qml` e621 button | `.../welcome.qml:45-50` | VERIFIED |
| QuickShell: `Workspaces.qml` "617 lines changed" | File is 320 lines; diff-stat vs upstream not derivable from tree | UNVERIFIED |
| Screenshot section: `RecursiveFallback.qml` rewritten with backoff, "no more nested try/catch" | File is still nested try/catch (Catch A/B) name-dropping ReAct 2210.03629 / Reflexion 2303.11366 — exactly what the README says was removed | WRONG |
| Screenshot section: `ScreenSnipToggle.qml` "uses new backoff-driven fallback" | No backoff/RecursiveFallback references in the file | WRONG |
| Screenshot section: `UtilButtons.qml` wires screenshot toggle | `.../modules/ii/bar/UtilButtons.qml:42-53` | VERIFIED |
| Mac Launcher module files (`AppDatabase.qml`, `MacLauncher.qml`, `refresh-apps.ts`) | All exist; `shell.qml:1` imports mac_launcher | VERIFIED |
| `scripts/prune-stale-sockets.sh` new | Exists at `.../ii/scripts/prune-stale-sockets.sh`, not repo-root `scripts/` | STALE (path) |
| `modules/common/widgets/*.qml` "removed 7 widget primitives" | 113 files remain in `.../modules/common/widgets/` | UNVERIFIED |
| `QuickConfig.qml` e621 label | `.../modules/settings/QuickConfig.qml:95` | VERIFIED |
| `Notifications.qml` timeout/persistence | `.../services/Notifications.qml:14,157,169` | VERIFIED |
| `translations/en_US.json` updated | Exists | VERIFIED |
| `.gitignore` tightened | 65 lines, exists | VERIFIED |
| Keyring Fix PAM command block | Matches `scripts/apply-keyring-pam.sh:13-15` | VERIFIED |
| Meta-packages: 14 `illogical-impulse-*` in `sdata/dist-arch/` | 14 dirs counted | VERIFIED |
| Meta-packages: "installed via `makepkg -si` from repo root"; `cd /home/toxic/projects/dots-hyprland` | Installed via `sdata/dist-arch/install-deps.sh` through `sdata/subcmd-install/1.deps-router.sh`; the cd path is a stale pre-rename path | STALE |
| Install: `./setup install-deps -f --skip-sysupdate` | `setup` (Python) subcommands are only `install/sync/check/checkbins/checkdeps/help` (`setup:405-411`); no `-f`, no `--skip-sysupdate` | WRONG |
| Install: `sudo ./scripts/apply-keyring-pam.sh` then `./setup install-files -f` | `install-files` subcommand does not exist | WRONG |
| Install: `./setup`, `./setup -y`, `./setup --dry-run` | Default `install`, `-y/--yes`, `-n/--dry-run` all exist | VERIFIED |
| Upstream Sync: "`./setup exp-merge` attempts automated rebase" | No `exp-merge` subcommand; `sdata/subcmd-exp-merge/` is a legacy directory unreferenced by `setup` | WRONG |
| Repo structure diagram (`sovereign-hypr/`, dots listing) | Stale name; omits `system-tuning/`, `docs/`, `dots-extra/`, `licenses/`, `dots/.bashrc*` (added in HEAD commit `f4694c179`) | STALE |
| Related repos: 7 links + port table (25100/25101/25102/25103/25203/25109/25120) | `toxicwind/byte-vision-proxy` 404, `toxicwind/rust-web` 404, `toxicwind/mcpproxy` 404 (correct: `toxicwind/mcpproxy-go`, public). sovereign, llama-swap, openfang (private), yote (private) resolve. Ports not verifiable from this tree | WRONG (3 links) / UNVERIFIED (ports) |
| License: "Upstream GPL-3.0. Personal fork changes: MIT" | `LICENSE` is pure GPL-3.0; no MIT grant for fork changes found (`licenses/` holds third-party notices only) | UNVERIFIED |
| Hardware header: 62 GiB DDR5 / zswap 25% = 15.5 GiB / 138 GiB swap | `system-tuning/sysctl/99-zswap-vm.conf` says "62GB RAM"; swap size is a system property, not in tree | VERIFIED (tree-consistent) / UNVERIFIED (swap size) |

\* Substance verified, file attribution slightly off.

## Missing from README

- `system-tuning/` (`apply-system-tuning.sh`, limine, sysctl zswap confs, udev) — the hardware-tuning section never references it.
- `docs/` (`AUDIT_SYSTEM_TUNING_AND_OPTIMIZATIONS.md`, `cachyos-kernel-limine-tuning.md`).
- `dots-extra/` (emacs, fcitx5, fedora, fontsets, swaylock, via-nix).
- `licenses/` third-party license notices.
- `diagnose` top-level health-check script — unmentioned.
- `dots/.bashrc`, `.bashrc.env`, `.bash_profile` — added by HEAD commit `f4694c179` ("consolidate canonical bash dotfiles from live home"); structure diagram lists only fish/.
- Recent Sep commits with no README reflection: Super key dedicated to Quickshell search overview / Fuzzel moved (`347077e75` — README keybind table only mentions SUPER+Return); launcher hidden/noDisplay filtering + dedup (`1179bfc15` — likely why AppDatabase is 114 not 804); grim+slurp crash-proof screenshot engine replacing the backoff design (`42f4f58a6` — README still documents the backoff design); keyring popup elimination (`787ef913d`); PrintScreen dispatch fix; translator string-buffer fix.
- Commit `70b77587c` (2026-07-29, "exponential backoff engine") is what the README's screenshot section describes; the Sep-02 desktop-sync commits (`d7ddc49d8`, `28ef2bf71`) appear to have restored upstream's non-backoff versions without updating the README.

## Quickstart check

- [ ] Commands exist — `install-deps`, `install-files`, `exp-merge`, `-f`, `--skip-sysupdate` do not exist; a user copy-pasting step 2/4 fails immediately
- [ ] Ports/config keys match code — port claims belong to other repos, unverifiable here; 3/7 related-repo links dead
- [ ] A fresh user could follow it end to end — No: installation section is invalid as written, and the meta-package `cd` path is stale

## Action taken

- **FIXED 2026-09-14 ~12:05 MDT** in commit `26c0ad7` (pushed `f4694c1..26c0ad7`, main): bruteforce README rewrite — real `setup` CLI (`install`/`sync`/`check`/`checkbins`/`checkdeps`/`help`, `-y`/`-n`/`--skip-deps/--skip-links/--skip-setups`), grim+slurp screenshot reality (July backoff experiment documented as superseded), sovereign-end4 rebrand completed (title, banner, diagram, `install.conf.yaml` header), 804→114 apps, border rgba corrected (incl. bg `rgba(161313FF)`), keybinds path fixed (`hypr/hyprland/keybinds.lua`) + Super-overview/Fuzzel→Super+D, find_focus/Background/get_wallpaper_info details corrected, 3 dead related-repo links dropped/fixed (mcpproxy→mcpproxy-go), new "Recent Changes" section (Super key, launcher dedup, keyring popup, PrintScreen, bash dotfiles, system-tuning/docs/dots-extra/licenses/diagnose), path-convention note added, structure diagram completed.
- Untouched (out of scope / unverifiable from tree): "617 lines changed" Workspaces.qml claim, "removed 7 widget primitives" claim, "Personal fork changes: MIT" license claim.

Note: the GitHub tarball endpoint 302-redirects to a signed `codeload.github.com` URL; fetching that URL *with* the surrogate `Authorization` header 404s — fetch it bare (the `?token=` in the URL is the auth).
