# Keeper Desktop — Status & Re-auth Runbook (2026-10-22)

Consolidated findings from the keeper/Google/desktop work. Status verified live.
Pick up future work from here; do not re-derive.

## 1. Keeper is now a REAL desktop (WM) — WORKED

Root cause of "not a real desktop / resize doesn't apply": DISPLAY `:99`
(Xvnc agent-display) had **no window manager**, so the headed keeper Chromium
had no decorations, `--start-maximized` was a no-op, and window resizes never
propagated to the page.

Fix (real config):

- Added `[daemons.agent-wm]` to `estate/pitchfork.toml`: runs `openbox` on
  `:99` (`after = ["agent-display"]`, `ready_cmd` uses `xprop ... _NET_SUPPORTING_WM_CHECK`).
- `openbox` was already installed (`openbox-3.6.1`).
- `~/.config/openbox/autostart` maximizer (wmctrl) for any Chromium window.

Verified:

- `wmctrl -m` → `Name: Openbox`; `xprop -root _NET_SUPPORTING_WM_CHECK` set.
- Autonomous resize: root resized to `1100x700` → Chrome window AND page
  `innerWidth` auto-followed with **no manual wmctrl**; ditto `1600x900`.
- Restart persistence: `bin/pitchfork-restart estate/agent-wm` keeps openbox up.

## 2. ANY-APP DESKTOP — the keeper is not Chromium-only

DISPLAY `:99` is a real WM-managed desktop. Independent GUI apps launch and get
WM-managed windows alongside the keeper Chromium — proven with a non-browser
app (`xmessage`) plus RustDesk, all showing in `wmctrl -l` on `:99`.

Durable helper to open any app on the agent desktop:

```bash
estate/bin/keeper-open <command...>   # e.g. keeper-open firefox, keeper-open kitty
```

It pins `DISPLAY=:99` (via `KEEPER_DISPLAY` override only — never inherits an
ambient caller DISPLAY like `:0`), `setsid`-detaches, and lets openbox manage
the window. Add `--class` if a caller needs to reference a stable WM class.

NOTE: the keeper process model is one persistent Chromium; other apps are meant
to be spawned this way (or docked via keeper-floaty/signalhead), not as more
keep-alive Chromiums.

## 3. Cookie persistence WORKS — survives relaunch

The full Google session injects (15/15) and:

- Persists in-memory across page navigation.
- Persists to disk — profile sqlite `nv-audit/Default/Cookies` holds real
  encrypted blobs (`SID enc_len 195`, `__Host-GAPS enc_len 99`, `LSID 355`).
- Survives a full keeper restart: after `pitchfork-restart browser-keeper`, the
  keeper still holds 31 google cookies incl `SID, __Secure-1PSID, __Host-GAPS,
SAPISID, LSID` (verified via `Storage.getCookies`).

NOTE: `secretsmith chromium-cookies` reports these as `decrypted:false /
vlen 0` — that is a **secretsmith-vs-running-Chromium os_crypt key mismatch**,
NOT data loss. The values are present (raw sqlite `length(encrypted_value)` is
non-zero). Do not chase that.

## 3. The estate ALREADY has the canonical Gemini-web auth pattern — REUSE IT

`ranch/mesh/pylae/open-sse/executors/gemini-web.ts`:

- Needs `__Secure-1PSID` **+ `__Secure-1PSIDTS`** + `__Secure-1PSIDCC`.
- Injects via `context.addCookies([... { secure:true, domain:".google.com", path:"/" }])`.
- Targets **`gemini.google.com/app`**, validates via the composer / StreamGenerate.

The earlier AI-Studio attempts failed because they **omitted `__Secure-1PSIDTS`
and `__Secure-1PSIDCC`** (the ones not in the picked subset). The vault DOES
contain them (`.google.com`, TS=77ch, CC=76ch).

Using the full set on the keeper: `gemini.google.com/app` loads with the
**composer present** (`hasComposer:true`, no hard redirect). Re-auth command that
sets the full auth set into the keeper, then opens gemini.google.com/app:

```bash
cd /home/toxic/estate/ranch/keeper
BROWSER_KEEPER_CDP=http://127.0.0.1:25154 bun /tmp/gemini-auth.cjs
```

## 4. AI Studio — Google server-side revalidation wall

Even with the complete cookie set, `aistudio.google.com/app` still redirects to
`accounts.google.com` sign-in (verified repeatedly). This is **Google session
re-validation**: a cookie copy across browsers is demoted to signed-out/semi
state regardless of cookie correctness. The document `estate/ops/gemini-eap/BILLING.md`
documents the deeper wall: the EAP Tool-Retrieval model needs prepay credits on
the AI Studio project (`HTTP 402 RESOURCE_EXHAUSTED`).

Actionable: a **one-time real sign-in** in the keeper for the Google account on
the EAP project unblocks AI Studio + tool-retrieval; then `__Secure-1PSIDTS` is
issued by Google itself and everything flows via Pylae's gemini-web pattern.

## 5. Landing state — cookie-vault port fix

Landed on `ranch` `origin/main`:

- `cookie-vault/src/cli.js` defaults keeper CDP to SSOT `25154`
  (`BROWSER_KEEPER_CDP_PORT || "25154"`), no hardcoded `:9223`.
- `cookie-vault/README.md` added.
- `estate/pitchfork.toml` `validationMatrix` (cookie-vault scope) + `[daemons.agent-wm]`.
- Verified `bun --check` + `bun test` (21/21) pass; keeper smoke PASS on `:25154`.

## Re-auth essentials

- Full auth cookie names (vault): `SID, HSID, SSID, APISID, SAPISID,
__Secure-1PSID, __Secure-1PSIDTS, __Secure-1PSIDCC, __Secure-3PSID,
__Secure-1PAPISID, __Secure-3PAPISID, LSID, NID, SIDCC, OTZ, __Host-GAPS`.
- Real keeper CDP: `http://127.0.0.1:25154` (SSOT `config/ports.env`).
- Throwaway `:9223` chrome-for-testing is NOT the keeper — never point cookie
  tools at it.
