Subject: P0 — Account hijack + malicious redirects on account 2d5e60db…2225 (attacker-owned)

Cloudflare Trust & Safety / Abuse,

Account 2d5e60db…2225 (login: noo056272@gmail.com) was hijacked on 2026-10-30
from its legitimate owner (evidence: 18-month audit-log export, attached
timeline). The attacker deployed dynamic_redirect rulesets / legacy Page Rules
issuing 301 redirects of 8 customer domains to https://femboy.pp.ua/ — motive
evidenced as anti-gay targeting of the femboy.pp.ua community's rival domains.
On 2026-11-02 16:23–16:28 UTC the attacker destroyed evidence (token_roll /
token revoke on yellow-fire-6591, dedi-ops, omp-ai-gateway).

Current state (2026-11-03, live-verified):
* All 8 zones re-added to the hijacked account and re-serving the 301 →
  femboy.pp.ua (waverss.com, so-fabulo.us, mildlyawesome.com,
  galleryeffusion.com, effusionlabs.com, mysticfoxmyco.com, patenthound.net —
  arlockworks.com DNS-only, unaffected at the edge).
* Every legitimate-owner credential has been revoked by the attacker.
* Registrars: NameCheap (RDAP-verified, all zones, clientTransferProhibited).
  NS still delegated to matt/pam.ns.cloudflare.com (attacker account pair).
* The legitimate owner is executing registrar NS cutover to a new CF account.

Requested actions:
1. Freeze / suspend account 2d5e60db…2225 pending investigation (owner-sticky
   account under attacker control).
2. Preserve full audit logs + zone configs as evidence (active incident).
3. Fast-track: the hijack is LIVE malicious redirects on 7 domains incl.
   customer-facing businesses.

Evidence bundle: 18-month audit export (1300 events), attacker event detail
(18 events), DNS snapshots, RDAP timestamped — available on request; attached.

Contact: registered domain owner of record via WHOIS/NameCheap contacts.
