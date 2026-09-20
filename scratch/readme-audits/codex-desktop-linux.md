# README audit — toxicwind/codex-desktop-linux @ 12cad6db7deb90052afc8229a4ba7209c5bf6637 — 2026-09-14

**Verdict:** NEEDS UPDATE (minor — no false claims; two doc gaps)

Mechanical (`bin/audit.py`): 6/7 checks PASS. The one WARN (`quickstart-entrypoints-exist` flagging `./install.sh` and `./scripts/install-desktop-entry.sh` as missing) is a **checker false positive** — it compares the literal `./`-prefixed token against the tree; both files exist and are executable (verified: `-rwxrwxr-x`).

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| Converts official macOS Codex.dmg into Linux-runnable Electron app | install.sh: get_dmg (persistent.oaistatic.com/codex-app-prod/Codex.dmg), patch_asar, download_electron (ELECTRON_VERSION=40.0.0) | VERIFIED |
| Installs robust desktop launcher | scripts/install-desktop-entry.sh: symlinks 3 bin scripts + 2 .desktop entries | VERIFIED |
| Background maintenance flow so installs are not piecemeal | bin/codex-desktop-maintain (138 lines): git fetch/pull, installer rerun | VERIFIED |
| Native module rebuild for Linux (better-sqlite3, node-pty) | install.sh build_native_modules(): detects versions, electron-rebuild 4.0.3 | VERIFIED |
| DMG cache refresh via CODEX_REFRESH_DMG=1; reuses Codex.dmg by default | install.sh get_dmg(): `[ "$refresh" != "1" ] && [ -s dmg ]` → reuse | VERIFIED |
| "Deterministic" Linux repack | Repack pipeline real; nothing pins DMG/npm inputs — "deterministic" is aspirational | UNVERIFIED (wording) |
| Launcher: Wayland/X11 flags + startup logging | bin/codex-desktop: CODEX_FORCE_X11 / CODEX_OZONE_MODE=force-wayland / auto; logs → ~/.local/state/codex-desktop/launch_*.log | VERIFIED |
| Normal launches run codex-desktop-maintain in background | bin/codex-desktop: `nohup .../codex-desktop-maintain` unless CODEX_AUTO_UPDATE=0 | VERIFIED |
| Maintain rate-limits checks, default every 6h | bin/codex-desktop-maintain: CHECK_INTERVAL="${CODEX_UPDATE_INTERVAL_SEC:-21600}" | VERIFIED |
| Maintain fetches/pulls repo updates, reruns installer if needed | bin/codex-desktop-maintain: git fetch, pull --ff-only when behind, changed → CODEX_REFRESH_DMG=$refresh install.sh | VERIFIED |
| CODEX_AUTO_UPDATE=0 disables background maintenance | bin/codex-desktop: `[[ "${CODEX_AUTO_UPDATE:-1}" == "1" ]]` gate | VERIFIED |
| CODEX_UPDATE_INTERVAL_SEC=21600 | bin/codex-desktop-maintain line 12 | VERIFIED |
| CODEX_FORCE_UPDATE=1 forces maintenance now | bin/codex-desktop-maintain: skips interval check when =1 | VERIFIED |
| CODEX_FORCE_REFRESH_EVERY_SEC=604800 (7d) | bin/codex-desktop-maintain line 13 | VERIFIED |
| Live status: CLI current vs npm latest, repo head/divergence, updater log tail, launch log tail | bin/codex-desktop-live-status: `codex --version`, `npm view @openai/codex version`, rev-parse + rev-list counts, tail update.log + launch_*.log | VERIFIED |
| `codex-desktop-live-status --gui` opens dashboard terminal | spawn_gui: ghostty → kitty → alacritty → xterm fallback | VERIFIED |
| "Codex Live Status" app-menu entry | scripts/install-desktop-entry.sh: codex-desktop-live-status.desktop, Exec=...--gui | VERIFIED |
| Repo layout (install.sh, 3 bin scripts, 2 scripts) | All 6 files present in tree | VERIFIED |
| Prerequisites (Node 20+, npm, python3, p7zip, curl, unzip, make/g++) | install.sh check_deps(): node npm npx python3 7z curl unzip + make/g++ + Node>=20 | VERIFIED |
| Arch `pacman -S nodejs npm python p7zip curl unzip base-devel` | Verbatim match with install.sh's own suggestion | VERIFIED |
| `npm i -g @openai/codex` for CLI | install.sh + start.sh error message + maintain auto-update all reference @openai/codex | VERIFIED |
| Troubleshooting: port 5175 for blank window | start.sh: `python3 -m http.server 5175` for webview | VERIFIED |
| Troubleshooting: CLI not found → check ~/.local/bin/codex | bin/codex-desktop-maintain symlinks/aligns ~/.local/bin/codex | VERIFIED |
| License: MIT | LICENSE: "MIT License" (copyright 2025 ilysenko, upstream author) | VERIFIED |
| Quickstart clone URL | `https://github.com/<your-user>/codex-desktop-linux.git` — placeholder, fails verbatim | STALE (wording) |

## Missing from README

- **`CODEX_CLI_AUTO_UPDATE`** (default 1): maintain auto-updates the Codex CLI via `npm i -g @openai/codex@latest` (bin/codex-desktop-maintain:12; added in commit aa7c08c7 "Add live status GUI and include Codex CLI auto-update in maintenance flow"). Real knob, zero README coverage — the one substantive gap.
- **Upstream sync workflow** (.github/workflows/upstream-sync.yml): disabled 2026-09-14 (commits d9f1d6e7, 12cad6db) because `codex-team/codex.desktop` doesn't exist; manual dispatch only. CI-only, low priority.
- Minor power-user knobs undocumented: `CODEX_DESKTOP_ROOT`, `CODEX_INSTALL_DIR`, `CODEX_TOOLCHAIN_CACHE`, `CODEX_CLI_PATH`, `GLOB_OVERRIDE_VERSION`.

## Quickstart check

- [x] Commands exist (`./install.sh`, `./scripts/install-desktop-entry.sh` — both executable)
- [x] Ports/config keys match code (5175, all CODEX_* vars verified against code)
- [~] A fresh user could follow it end to end — except the clone URL's `<your-user>` placeholder won't work verbatim; should be `toxicwind`

## Action taken

- None — REPORT ONLY per task. Suggested edits: document `CODEX_CLI_AUTO_UPDATE=0`, fix clone URL to `https://github.com/toxicwind/codex-desktop-linux.git`.
