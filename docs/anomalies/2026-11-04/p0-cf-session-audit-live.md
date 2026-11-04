# P0 CF hijack — 2026-11-04 live session audit (SUPERSEDES the 2026-11-02 chain)

> Live-verified via the phone fennec session on 2026-11-04. This document is
> the current truth and **supersedes** the 2026-11-02 dossiers where they
> disagree. Docs lie; code/API is absolute — every claim below was confirmed
> by a live `/api/v4/*` probe through the logged-in fennec session.

## TL;DR (what changed vs the 2026-11-02 chain)

1. **The fennec session is READ-ONLY, not owner.** toxicwind@gmail.com holds
   only the **"Trust and Safety Read"** role on account `2d5e60dbc…2225`
   (`zone/org/blocks edit=false`). The account owner is the attacker's login
   email `noo056272@gmail.com` (Super Administrator, undeletable).
2. **"Attacker controls the gmail" is WRONG.** The architect confirmed we
   control `toxicwind@gmail.com`. The attacker controls the CF *account owner*
   login email (`noo056272@gmail.com`), NOT the gmail itself.
3. **No fix inside the attacker's account is possible via this session** —
   read-only. The registrar NS migration (runbook Phase 2) remains the only
   durable fix, and it still needs NameCheap panel access (no API creds).
4. **The fennec RDP lane now works** — the "empty listTabs" blocker was a
   malformed frame-length bug in the raw probes, not a fennec fault. The Bun
   client (`src/rdp.ts`) was correct all along.

## Verified evidence (live probes, 2026-11-04)

### Session identity + access level
- `GET /api/v4/user` → 200
  `{id:"2d8f6ab25d093b8ad70a05d819cde9ea", email:"toxicwind@gmail.com",
    username:"toxicwind", organizations:[], created_on:"2013-12-17"}`
- `GET /api/v4/memberships` → 200, membership `d0db60dd2c82cb6995770a2d6ddc9151`
  - status: `accepted`
  - roles: `["Trust and Safety Read"]`
  - permission_groups: only `84808c8d19f84b29a63457934b8a18dc` (Trust and Safety Read)
  - permissions: `{blocks:{edit:false,read:true}, organization:{edit:false,read:true}, zone:{edit:false,read:true}}`
- `GET /api/v4/accounts` → 200, account `2d5e60dbc717af626a1eb04177aa2225`,
  name **"Toxicwind@gmail.com's Account"**, created `2013-12-17T20:13:03Z`
  → the account was originally toxicwind's; the attacker re-owned it.

### What the read-only session CANNOT do (403/10000)
- `GET /api/v4/accounts/{acc}/memberships` → 403 (10000 auth error)
- `GET /api/v4/accounts/{acc}/members` → 403 (10000 auth error)
- `GET /api/v4/zones/{zone}/pagerules` → 403 (9109 unauthorized)
- `GET /api/v4/zones/{zone}/rulesets` → 403 (10000 auth error)
- `POST /api/v4/user/tokens` → 403 (Cloudflare bot-protection block page)

### What the read-only session CAN read
- `GET /api/v4/zones?per_page=50` → 200, 8 zones: arlockworks.com,
  effusionlabs.com, galleryeffusion.com, mildlyawesome.com, mysticfoxmyco.com,
  patenthound.net, so-fabulo.us, waverss.com
- `GET /api/v4/user/tokens?per_page=100` → 200 (names only; the existing
  `cfat_` token is DEAD: `/user/tokens/verify` → 1000, `/zones` → 9109)
- `GET /api/v4/user/tokens/permission_groups` → 200 (421 groups)

## Corrected claims vs the 2026-11-02 chain

| Claim (2026-11-02) | Corrected (2026-11-04) |
|---|---|
| "Attacker controls the gmail" | WRONG. We control `toxicwind@gmail.com`. |
| "All CF credentials dead" | Confirmed. `cfat_FMfXP…` → 1000/9109. |
| "Account owned by attacker" | Confirmed. Owner login = `noo056272@gmail.com`. |
| "Containment neutralized attacker" | NOT durable. Re-hijacked; session now read-only. |

## Migration path (unchanged, still the only durable fix)
Runbook `p0-cf-migration-runbook.md` Phase 1–5. Phase 2 (registrar NS cutover
at NameCheap) is the kill switch and still needs NameCheap panel access.
Phase 1 step 1 (new CF account via fennec on the Pixel) is executable via the
now-working fennec lane but needs a fresh trusted email + CAPTCHA (human step).

## Next actions
- [ ] Registrar NS cutover at NameCheap (human step, blocked on panel access)
- [ ] New CF account + DNS rebuild per runbook Phase 1/3
- [ ] fennec-cdp Bun rewrite polish + argos indexing (non-blocked, in progress)