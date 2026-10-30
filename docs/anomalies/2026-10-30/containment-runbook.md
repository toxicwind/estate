# DEDI / mildlyawesome.com containment runbook (2026-10-30)

## What's verified (facts only)
- **Origin IP**: `172.96.160.178` — AS23470 ReliableSite.Net LLC, Los Angeles (the dedi #3327).
- **mildlyawesome.com**: apex Cloudflare-proxied (104.21.89.202 / 172.67.147.41). NS pam/matt.cloudflare.com.
- **SSH**: port 22 open (ED25519). root + `DEDI_USE_PASSWORD_AUTH=1` (password auth).
- **Estate config** (keyring): DEDI_HOST / DEDI_REMOTE_HOST = `172.96.160.178`, DEDI_PUBLIC_HOST = mildlyawesome.com, DEDI_USER / DEDI_OPS_AUTH_USERNAME = root.
- **CF creds**: both stored tokens invalid (code 1000/9109). Not the live-credential source.

## NOT verified / retracted
- Dokploy panel as a *public* vector → **RETRACTED** (NXDOMAIN publicly; only reachable from the estate net via direct-IP Host-header). No confirmed public entry path.
- The actual attacker entry vector is UNCONFIRMED pending console/SSH access.

## The one missing credential
DEDI root password — **absent from every estate secret store** (verified 2026-10-30: 175 keyring labels incl. 11 DEDI/RELIABLESITE password candidates, ~/.secrets, .env, projects.env). Only available from the ReliableSite panel / KVM (phone).

## Execute (when credential available)
```bash
DEDI_PW=<password> bash contain-mildlyawesome.sh --inspect-only   # recon first
DEDI_PW=<password> bash contain-mildlyawesome.sh                  # stop exposed containers + evidence
```

## Cloudflare rotation (separate)
1. Mint new API token on the CF dashboard (phone).
2. Verify: `curl -H "Authorization: Bearer $NEW" https://api.cloudflare.com/client/v4/user` → 200.
3. Rewrite keyring: `secretsmith set CLOUDFLARE_API_TOKEN` + `CF_API_TOKEN` (label-only).
4. Archive old (already at ~/sovereign/scratch-archive/20261030-cloudflare-rotated/).
5. Audit whether `mildlyawesome.com` zone = ours → if so, account hygiene.

## Related
- Damage dossier: `cloudflare-leak-damage.md` (same dir)
- Keypool now health-probes CF tokens (config/keypools.yaml `cloudflare` pool).