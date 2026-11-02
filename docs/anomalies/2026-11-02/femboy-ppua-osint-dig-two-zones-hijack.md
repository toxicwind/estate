# 2026-11-02 — femboy.pp.ua OSINT dig + second hijacked zone discovered (retro dossier)

All items verified with live probes / real traffic this session. Charter:
every anomaly gets a capability-contract test before its fix is trusted.
(Charter from the D-2026-10-23 program — keep it.)

## The hijack is TWO zones, not one

**Symptom:** `mildlyawesome.com` apex (http and https) 301s to
`https://femboy.pp.ua` at the Cloudflare edge (verified via `curl -D -`:
`location: https://femboy.pp.ua`, HTTP/2 301, `server: cloudflare`).
Prior dossier (`mosaic-merge-ghas-transport-keyleak.md`) documented only
galleryeffusion.com.

**Root cause:** same class as galleryeffusion — a CF-level redirect rule on a
zone we own (NameCheap 2023, Cloudflare NS) bouncing the domain into the
femboy.pp.ua funnel. `moment.mildlyawesome.com` (the agentic-moment product's
intended surface) is **NXDOMAIN** — consistent with the hijack holding the
zone's routing.

**Remediation:** `/home/toxic/tmp/netrace/fix-hijack.sh` currently targets
galleryeffusion.com only. A second run is needed against the mildlyawesome.com
zone (zone id lookup + redirect rule deletion + tunnel CNAME restoration).
Blocked on the same human unlock (CF dashboard login / token creation — all
keyring CF tokens dead per `p0-hijack-final-gate.md`).

**Contract test:** `curl -sI https://mildlyawesome.com` MUST NOT return a
`location` header pointing at femboy.pp.ua after fix.

## femboy.pp.ua infrastructure (verified)

- **Apex `femboy.pp.ua`**: Cloudflare (cody/lisa.ns.cloudflare.com), IPs
  172.67.184.134 / 104.21.84.9 (+ 2606:4700::/32). `cf-cache-status: DYNAMIC`,
  `speculation-rules` header — a real origin behind CF, NOT Pages.
- **Mail**: Zoho EU (mx.zoho.eu, mx2, mx3) + SPF `include:zohomail.eu`.
  Google site-verification TXT present (they registered it with Google).
- **Zone**: pp.ua SOA = ns1.uadns.com, hostmaster.drs.ua — Ukrainian free-domain
  registry.
- **Sibling `pon4ikisdonut.pp.ua`**: GitHub Pages
  (`x-github-request-id`, `x-fastly-request-id`, `via: varnish`) — static
  personal site, same CF nameservers.

## Content structure (verified via /api/profiles + likes.php)

The apex is **PHP-backed** (not static):
- `GET /api/profiles` → JSON array of 15 profiles (id, name, telegram, photo,
  bio, tags).
- `GET /likes.php?action=get` → like counts per profile id.
- Tags: notags(7), politics(2), sysadmin(1), taken(1), inoagentnomer1(1),
  kfc(1), 42(1), kotlin(1), нету(1).
- Every profile carries a Telegram handle (`@pon4ikisdonut`, `@fishnothere`,
  `@maximkatz`, …) — the site is a Telegram-community directory.
- `sub.pon4ikisdonut.pp.ua` = "pon4ikdomains" — a **personal-subdomain-for-hire
  service** (Cloudflare Proxy + DNS records + Telegram-stars payment), wired to
  `t.me/pon4ikdomain_bot`. Same GitHub Pages backend. This is the operator's
  business: renting subdomains under .pp.ua.

## The hijack pattern (deep read)

The operator runs a subdomain-rental service on the .pp.ua free-domain
registry (uadns/DRS) and is redirecting Cloudflare-hosted domains into the
funnel via CF redirect rules on zones where they hold (or once held) NS
control. galleryeffusion.com and mildlyawesome.com both point at
`921731c6-ac0f-4eb3-b5b4-ea884fd41904.cfargotunnel.com` as their intended
origin (per fix-hijack.sh) — the tunnel ingress was deleted/bypassed and the
301 was inserted.

## Lessons (do not regress)

1. The hijack affects TWO zones — any domain with Cloudflare NS + a dead
   tunnel ingress is in scope until the redirect rules are deleted.
2. `prisoner` on the LG TV cannot drive Luna (rc=1 on everything) — the
   dev-mode SSH account has no Luna service role; `luna-send` is root-only.
3. `lgroot` is circularly broken: it shells `luna-send` (root-only binary) as
   prisoner via novacom — exit 126 even for `whoami`.
4. Session forensics are capture-limited: the HTML export's 49MB script #1 is
   base64 of the full session (keys: header/entries/leafId/systemPrompt/tools;
   13,923 entries) — decode THAT, never scrape the rendered DOM.
