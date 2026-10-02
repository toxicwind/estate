# Fleet Shims

Platform-specific shims and helpers for fleet device management.
Tools live alongside their shims — no separation between abstraction and implementation.

## Why shims?

Fleet devices run on different platforms with different capabilities:
- **CoreELEC** (Linux): full SSH access, systemd — but not bash (uses sh/ash or other)
- **Android TV**: ADB shim, APK-based apps, no SSH

A shim abstracts these differences so fleet tooling can work across platforms
without caring about the underlying OS.

## Shim types

- `android/` — **ADB shim**. Android devices are managed via ADB (Android Debug Bridge).
  APK installation, shell commands, file transfer all go through ADB.
  Tools: `bin/pixel-adb-keepalive.sh` (Pixel wireless debugging keepalive).
- `kodi/` — **RPC shim**. Kodi instances expose JSON-RPC API on :8080.
  Works on both CoreELEC (living room box 246) and Android TV (bedroom 225, Kodi APK).
  No SSH needed — pure HTTP JSON-RPC.
  Tools: `bin/kodi-audit`, `bin/kodi-handoff`, `bin/kodi-resume`.
- CoreELEC boxes also have SSH (`root:coreelec`), but the shell is not bash —
  shims must use POSIX sh or another available shell.

## Layout

```
fleet/shims/
├── README.md       # this file
├── kodi/           # Kodi fleet: RPC-based tooling for both boxes
│   ├── bin/        # kodi-audit, kodi-handoff, kodi-resume
│   ├── docs/       # box-inventory, menu-latency
│   ├── addons/     # lasso, manifold-upstream
│   ├── forensics/
│   └── tests/
└── android/        # Android fleet: ADB-based tooling
    ├── bin/        # pixel-adb-keepalive.sh
    ├── docs/       # devices.md
    └── phone-backup/
```

## Usage

Each platform folder is self-contained: shims + tools + docs together.
No cross-folder imports — if you need something from another platform, that's
a sign the abstraction is leaking.

See `kodi/README.md` for the Kodi box inventory (246=CoreELEC, 225=APK).
See `android/docs/devices.md` for Android device inventory.
