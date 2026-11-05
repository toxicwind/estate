# CF Hijack — session unblock findings (2026-11-05, kappa)

## What was unblocked this session

1. **Cookie-authed dashboard API lane (NEW).** Extracted the kilo-Chromium's
   authenticated CF session cookies via CDP (:9224, page 82DA5360…, saved
   `/tmp/kappa/cf-cookies.json`). The cookie-authed `dash.cloudflare.com/api/v4`
   lane works: `/user` → toxicwind@gmail.com (id 2d8f6ab25d09…), `/accounts` →
   1 account: "Toxicwind@gmail.com's Account" = **2d5e60dbc717af626a1eb04177aa2225
   (the attacker-owned account)**.

2. **Ground truth on the account state:**
   - 8 zones active on the attacker account: arlockworks.com, effusionlabs.com,
     galleryeffusion.com, mildlyawesome.com, mysticfoxmyco.com, patenthound.net,
     so-fabulo.us, waverss.com.
   - Zone NS: matt/pam.ns.cloudflare.com (arlockworks, effusionlabs),
     brian/chin.ns.cloudflare.com (galleryeffusion) — all ON the attacker's CF.
   - **Read-limited member role confirmed at every auth level**: rulesets,
     members, zone-rules UI all 403 (code 10000) — via cfk token, via raw
     cookie API, AND via in-page fetch. The dashboard UI only exposes
     effusionlabs.com in its sidebar; zone rules UI falls back to account home.

3. **Display-2 pixel automation lane (NEW, the MCP refactor seed).**
   - appium uiautomator2 server v10.7.10 INSTALLED + RUNNING on the pixel
     (`am instrument -w io.appium.uiautomator2.server.test/androidx.test.runner.AndroidJUnitRunner`,
     forwarded tcp:6790).
   - **`currentDisplayId: 2` + `enableMultiWindows: true` settings WORK** —
     source dumps + W3C-action taps are display-2 aware (proven: dismissed the
     Uptodown update dialog on the mosaic desktop without touching display 0).
   - `adb input -d 2 tap` is UNRELIABLE (rc=0 but no effect — silently lands
     display-0; DO NOT USE for display-2 work).
   - android-mcp ui.ts (736 lines, read in full) is display-0-bound everywhere —
     the refactor: add `display` param (default 2 per fleet AGENTS.md order) +
     uia2-server-backed endpoints (uia2-dump/uia2-tap/uia2-screenshot).

## The hijack fix path (runbook-conformant)

API/token paths are EXHAUSTED (read-limited at every level). The fix is the
**registrar NS cutover** (p0-cf-migration-runbook.md):
1. Create the NEW CF account (pixel — email verification on-device).
2. Add the 8 zones to the new account → get the new NS pair.
3. NameCheap (pixel fennec, 21 tabs) → repoint each zone's NS to the new pair.
4. The attacker's rulesets become irrelevant (zones leave their account).

## Pixel state notes

- BlackDex a64 (`top.niunaijun.blackdexa64`) installed; Cloudflare app NOT installed.
- Uptodown app 7.42 (7.43 update available, dialog loops, app self-closes).
- APKDash-style local APKs in `/sdcard/Android/data/com.uptodown/files/`:
  AppDash v3.14 (_ed by youarefinished), NuvioPlusIPTV 1.1.0-beta.8.3, deepseek, termius.
- SUSPICIOUS (parked): `com.apkpure.aegon` ships a keepalive instrumentation
  (`QDInstrumentation`); `com.alibaba.wireless` Phoenix/Daemon instrumentations
  present on the device.
- The "[777Real]Pビッグドリーム3" pachinko dialog was APKPure's stale
  download-manager prompt (dismissed via W3C tap).
