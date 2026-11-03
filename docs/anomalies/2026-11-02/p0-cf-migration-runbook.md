# P0 hijack — registrar NS migration runbook (2026-11-02)

> The CF account `2d5e60db…2225` is OWNED by the attacker (noo056272@gmail.com,
> Super Administrator, undeletable — API: "Cannot delete the account owner").
> NO fix inside that account is durable. Migration is the only permanent path.
> Evidence: `cf-hijack-evidence/` · Dossier: `p0-cf-account-owned-by-attacker.md`

## Current state (verified live)

- 8 zones on the attacker-owned account: arlockworks.com, effusionlabs.com,
  galleryeffusion.com, mildlyawesome.com, mysticfoxmyco.com, patenthound.net,
  so-fabulo.us, waverss.com
- Registrar of record: **NameCheap** for 7/8 zones (RDAP-verified 2026-11-02,
  all matt/pam NS): arlockworks, effusionlabs, galleryeffusion, mildlyawesome,
  mysticfoxmyco, patenthound, waverss. so-fabulo.us: RDAP unavailable (.US
  registry endpoint dead); NS still matt/pam → same attacker CF pair.
- All 7 proxied zones currently **301 → femboy.pp.ua** at the CF edge
- arlockworks.com: DNS-only (proxied=false); live A → 172.96.160.178 (origin,
  CLEAN) — resolution confirmed, NOT part of the redirect set
- Origin 172.96.160.178 (DEDI_HOST): CLEAN (404 direct, valid LE cert)
- The ONLY working CF credential: `cfat_zQe…66c5` (Zone:Read, pasted in a tau
  session, missed by the attacker's token cleanup). Treat as BURNED — the
  attacker can revoke it at any moment.
- `CLOUDFLARE_TUNNEL_TOKEN` (keyring): valid, tunnel 921731c6… — also treat as
  burned post-migration (it belongs to the attacker's account).
- Live resolver state (2026-11-02): so-fabulo.us → 172.67.146.128,
  mildlyawesome.com → 172.67.147.41, waverss.com → 104.21.37.232 (all CF edge
  = attacker account proxied); arlockworks.com → 172.96.160.178 (origin).

## Migration path (order matters)

### Phase 0 — preservation (before ANY change)
- [x] Full audit-log snapshot (18mo, 1300 events) → `cf-hijack-evidence/cf-audit-all.json`
- [x] Attacker event detail (18) → `attacker-audit.json`
- [x] DNS snapshot (8 zones) → `cf-zone-dns-snapshot.json`
- [x] Export registrar-side RDAP for 7/8 domains (timestamped) →
  `cf-hijack-evidence/registrar-rdap-20261102.json` (NameCheap everywhere;
  so-fabulo.us .US registry endpoint dead — NS still matt/pam = attacker CF)
- [ ] Screenshot CF dashboard zone list (if a logged-in session exists) —
  optional corroboration; the API audit is primary evidence.

### Phase 1 — new DNS home
1. Create a NEW Cloudflare account under a trusted email (NOT the toxicwind
   gmail if that account is compromised-adjacent; use a fresh alias).
   → This is the "generate new using firefox on pixel" step the architect
   ordered. One dashboard login; everything after is API.
2. Create an API token on the NEW account: Zone:Read + DNS:Edit on all zones
   to be migrated. Store via `secretsmith set CF_API_TOKEN_V2`.
3. Add all 8 zones to the new account; note the NEW assigned NS pair.

### Phase 2 — registrar NS cutover (the actual kill switch)
Per domain at the registrar (NameCheap for mildlyawesome.com; check each):
- [ ] Change nameservers: old (matt/pam, brian/chin, …) → NEW pair from Phase 1
- [ ] Do NOT enable registrar transfer — NS change only
- [ ] TTL: registrar glue typically ≤ 48h; lower any custom TTL first if possible
Order: least-critical first (waverss, so-fabulo.us) to validate the flow, then
the flagships (mildlyawesome.com, galleryeffusion.com, effusionlabs.com).

### Phase 3 — rebuild DNS on the new account
From the snapshot (1 record per zone):
```
arlockworks.com   A    172.96.160.178  proxied=false  ttl=300
effusionlabs.com  A    172.96.160.178  proxied=true
galleryeffusion.com CNAME pornhub.org  proxied=true   ← ATTACKER'S RECORD — do NOT
                                                      replicate; replace with the
                                                      intended tunnel/origin CNAME
mildlyawesome.com A    172.96.160.178  proxied=true
mysticfoxmyco.com A    172.96.160.178  proxied=true
patenthound.net   A    172.96.160.178  proxied=true
so-fabulo.us      A    172.96.160.178  proxied=true
waverss.com       A    172.96.160.178  proxied=true
```
Plus:
- `moment.mildlyawesome.com` CNAME → `toxicwind.github.io.` (agentic-moment
  surface; Pages custom-domain configured on the repo) — or A/AAAA to the
  Pages IPs per GitHub docs (185.199.108.153 etc.), proxied=false on the new
  account until SSL is proven.
- Recreate the tunnel on the NEW account (the old tunnel belongs to the
  attacker's account): `cloudflared tunnel create <name>` with the new token →
  NEW tunnel id → repoint the CNAMEs (fix-hijack.ts's `tunnelCname` constant).

### Phase 4 — verification (contract checks)
- [ ] `curl -sI https://<zone>` → NO `location: *femboy*` (exit 0 of
  `scripts/fix-hijack.ts --check <zone>` semantics)
- [ ] `https://moment.mildlyawesome.com` → 200 serving agentic-moment content
- [ ] Origin hit directly still 404/clean (unchanged)
- [ ] New-account audit log shows ONLY our actors

### Phase 5 — hardening (do not regress)
- [ ] Enable CF 2FA on the new account; account-level API token scopes minimal
- [ ] Never paste tokens into agent sessions (the `cfat_` graveyard lesson);
  keyring-only, `secretsmith exec` for consumers
- [ ] Alert rule: audit-log export on any member/token/ruleset change
  (audit-correlator can be pointed at the new account's audit feed)

## What NOT to do

- Do NOT attempt to fix the attacker's account (delete members, rotate their
  tokens) — no durable effect, and every action there is visible to them.
- Do NOT transfer domains between registrars mid-incident (60-day locks,
  clientTransferProhibited).
- Do NOT reuse the old account's tunnel token on the new account (it encodes
  the attacker's account id).
