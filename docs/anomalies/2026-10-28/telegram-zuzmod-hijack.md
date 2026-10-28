# 2026-10-28 anomalies — telegram hijack (ZUZMOD) + naming hygiene (tau)

All items verified with live probes / real traffic this session.
Charter: every anomaly gets a capability-contract test before its fix is trusted.

| # | Anomaly | Essence | Fix (committed) |
|---|---|---|---|
| 27 | **Telegram presence operated externally (ZUZMOD)** | @crawlspace_coyote_bot replies "Powered by ZUZMOD Network" and a BotFather-shaped entity tells the account "all our tools, bots & updates have permanently migrated to t.me/ZUZMOD" — but **zero estate source contains ZUZMOD** (grep across pens/*, estate) and **no local process holds TELEGRAM_BOT_TOKEN for the coyote bot** (checked 40 running pids via /proc environ). The bot is operated by an external party; the "migration" message is a squatter/phishing funnel. | ranch arroyo/overlord taas.ts: `OFFICIAL_BOTFATHER_ID = 93372553` guard — token replies trusted ONLY from the official sender; impostor replies return a structured refusal and the token regex never runs on untrusted text. Coyote-bot revocation pending real-BotFather session auth (human-gated). |

## Contract test (for #27)

```bash
# The guard: taas.ts must refuse token replies from any sender != 93372553.
grep -n "OFFICIAL_BOTFATHER_ID = 93372553" \
  /home/toxic/pens/ranch/arroyo/overlord/src/taas.ts
# And the negative-space probe: no estate source may carry the external branding.
grep -rq "ZUZMOD" /home/toxic/pens/ranch/arroyo /home/toxic/pens/barn/src 2>/dev/null && echo "FAIL: branding leaked into estate code" || echo "PASS: estate code clean"
```

## Human-gated follow-ups (the Oracle cannot approve these — account actions)

1. When TaaS session auth lands (`GET :25243/telegram/login`, code from phone):
   message the REAL @BotFather (verify sender id 93372553 in the probe output),
   `/revoke` + recreate @crawlspace_coyote_bot under estate-held keyring.
2. NEVER join t.me/ZUZMOD or interact with lookalike BotFathers.
3. Audit what ZUZMOD had access to: the coyote bot's chat history + any bots
   created during the compromised period (via real BotFather /mybots once authed).
