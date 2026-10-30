# Leak Damage Assessment — 2026-10-30 (started)

## Scope (architect-directive)
ONLY Cloudflare credentials are treated as LEAKED. The FreeInference key and
other keys are NOT in scope (explicit directive). Cloudflare creds: KEYRING
`CLOUDFLARE_API_TOKEN` + `CF_API_TOKEN` (both 53-char API tokens), account id
(32-char `CLOUDFLARE_ACCOUNT_ID`) = toxicwind@gmail.com. Both stored tokens are
INVALID at admit (`GET /api/cloudflare/client/v4/user` -> code 9109 Invalid
access token) — so an attacker is NOT using the live keyring value; the leak
path is either a rotated-out token or a copied one.

## Exposure surface (verified live)
Tailscale funnel public endpoints (the blast radius if a CF token manages zones
for these):
- `https://estate.tailc9ac71.ts.net:25127` -> thresher MCP (= the gateway)
- `https://estate.tailc9ac71.ts.net:8443`  -> rhodochrosite LLM router (:25193)
- `https://estate.tailc9ac71.ts.net:8444`  -> :25218 (ranch-ui/delendai control plane)
`mildlyawesome.com` (the hijacked dedi #3327) NS = pam/matt.cloudflare.com,
A = 104.21.89.202 / 172.67.147.41 -> it IS a Cloudflare zone, origin hidden.

## Git history (verified)
All 5 pens have clean recent heads; no CF token in recent commits. The leak was
NOT via committed history (the recent commits are this session's renames/config
dedup). Stored CF tokens being invalid suggests attacker used a token that has
since been rotated, OR owns the Cloudflare account another way.

## Actions
- [ ] Mint NEW Cloudflare API token (architect on phone / CF dashboard)
- [ ] Verify new token: GET /user 200
- [ ] Update keyring (CLOUDFLARE_API_TOKEN + CF_API_TOKEN) to new value
- [ ] Archive old values to ~/sovereign/scratch-archive/20261030-cf-rotated/
- [ ] Kill/verify the mildlyawesome.com zone (is it OURS? did the hijacker add it?)
- [ ] Contain dedi #3327 (KVM/SSH, phone-gated)
- [ ] Finalize this damage assessment