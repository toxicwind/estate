# Fleet Shims

Platform-specific shims and helpers for fleet device management.

## Why shims?

Fleet devices run on different platforms with different capabilities:
- **CoreELEC** (Linux): full SSH access, systemd — but not bash (uses sh/ash or other)
- **Android TV**: ADB shim, APK-based apps, no SSH

A shim abstracts these differences so fleet tooling can work across platforms
without caring about the underlying OS.

## Shim types

- `android/` — **ADB shim**. Android devices are managed via ADB (Android Debug Bridge).
  APK installation, shell commands, file transfer all go through ADB.
- `kodi/` — **RPC shim**. Kodi instances expose JSON-RPC API on :8080.
  Works on both CoreELEC (living room box) and Android TV (bedroom APK).
  No SSH needed — pure HTTP JSON-RPC.
- CoreELEC boxes also have SSH (`root:coreelec`), but the shell is not bash —
  shims must use POSIX sh or another available shell.

## Layout

- `kodi/` — shims for Kodi instances (both CoreELEC and Android TV variants)
- `android/` — shims for Android devices (ADB, APK management)

## Usage

Shims are sourced or executed by fleet tooling in `../` (kodi-fleet, android-fleet).
Each shim handles platform detection and capability negotiation.

See the parent fleet README for the full device inventory.
