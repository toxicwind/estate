# Fleet Shims

Platform-specific shims and helpers for fleet device management.

## Why shims?

Fleet devices run on different platforms with different capabilities:
- **CoreELEC** (Linux): full SSH access, systemd, standard Linux tools
- **Android TV**: limited to JSON-RPC API, no SSH, APK-based apps

A shim abstracts these differences so fleet tooling can work across platforms
without caring about the underlying OS.

## Layout

- `kodi/` — shims for Kodi instances (both CoreELEC and Android TV variants)
- `android/` — shims for Android devices (ADB, APK management)

## Usage

Shims are sourced or executed by fleet tooling in `../` (kodi-fleet, android-fleet).
Each shim handles platform detection and capability negotiation.

See the parent fleet README for the full device inventory.
