# Post-acceptance reclaim script (RUN AFTER toxicwind accepts CF invite)

Trigger: architect signs up/logs into dash.cloudflare.com with
toxicwind@gmail.com and accepts the pending Super Admin invite.

Then, IN ORDER (needs the USER session, not cfat_ tokens):

1. Page Rules audit (the 1011 blind spot — the attacker's 301):
   Dashboard: each domain → Rules → Page Rules → DELETE any rule
   redirecting to femboy.pp.ua. (User session sees what cfat_ cannot.)

2. Ownership change: Profile → Account → (as Super Admin + verified email)
   initiate account email/ownership change to toxicwind@gmail.com.
   If the flow demands the current owner's password → CF Support ticket
   with: audit evidence bundle + registrar (NameCheap) proof of control.

3. Zone re-adds: Add site → the 8 domains → set the new NS pair →
   registrar NS cutover (NameCheap) → rebuild DNS from snapshot:
   estate/docs/anomalies/2026-11-02/cf-hijack-evidence/cf-zone-dns-snapshot.json
   ⚠️ galleryeffusion.com: snapshot record (CNAME pornhub.org) is the
   ATTACKER'S — replace with the intended tunnel/origin CNAME.

4. moment.mildlyawesome.com CNAME → GitHub Pages
   (185.199.108.153/.109/.110/.111 or toxicwind.github.io custom domain).

5. Credential rotation sweep: revoke cfat_zQe…66c5 + CLOUDFLARE_TUNNEL_TOKEN
   (both lived on the attacker's account), all keyring CF entries; rotate
   gmail: Security → 2FA → App passwords revoke ALL; POP/IMAP disable;
   third-party access sweep; sign out all unknown sessions.
