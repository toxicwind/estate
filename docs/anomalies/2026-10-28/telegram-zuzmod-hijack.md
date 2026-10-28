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

---

# 2026-10-28 (later same day) — taas login chain + firewall (all fixed live, flotilla-mcp ship session)

| # | Anomaly | Essence | Fix (committed) |
|---|---|---|---|
| 28 | **Loopback bind = phone invisible** | taas bound `127.0.0.1` — phone got "Unable to connect" while box-side `curl 10.0.0.218:25243` also failed (000), yet health checks on 127.0.0.1 passed. Two different clients, two different truths. | taas.ts `hostname: "0.0.0.0"`; contract: probe from the REAL client (`adb shell nc -z`), never from the server's own stack |
| 29 | **nft LAN allowlist gap** | `inet awrawr_filter` policy drop with LAN tcp set `{22,3000-3001,8503,25100-25107,25203}` — 25243 missing; ping OK + box-local OK masked the drop. | 25243 added in `/etc/nftables.conf` (idempotent self-flushing file) + live `nft -f` reload; phone `nc -z` rc=0 proof |
| 30 | **Ghost gramJS property = permanent 502** | login GET checked `client.authorizationState` — not a gramJS client property → falsy forever → every login a 502 even when connected. Second bug: `client.connect()` resolves void; `!ok` treated success as failure. | liveness = `client.connected`; connect-void handled (`ok === false` guard only) |
| 31 | **gramJS helper shape drift** | high-level `client.sendCode({apiId,apiHash})` threw `undefined is not an object (evaluating 'data.constructor')` on 2.26.21. | raw TL invoke `new Api.auth.SendCode({phoneNumber, apiId, apiHash, settings: new Api.CodeSettings({})})` — version-stable; code now lands on the phone (`ok:true`, 3.9s) |
| 32 | **Verification-method mirage (thresher federation)** | `/api/v1/servers` returned `{"servers":[]}` and gateway `tools/list` showed 12 router-only tools — both LOOKED like broken federation while all 10 flotilla tools were live. | real proof = sessioned `retrieve_tools` through `:25127/mcp` (SSE-framed): `query=pixel` → `flotilla:pixel_*` namespaced; guide `docs/mcp-guide-thresher.md` §6 encodes the loop |

## Contract tests (for #28–#32)

```bash
# 28/29: client-side reachability is the only reachability
adb -s 10.0.0.77:43945 shell "nc -z -w 3 10.0.0.218 25243; echo rc=\$?"   # expect rc=0
grep -n "25243" /etc/nftables.conf                                        # expect the LAN set line

# 30/31: login code delivery works end-to-end (does NOT consume a code — only sends)
curl -s -m 40 http://127.0.0.1:25243/telegram/login                        # expect {"ok":true,...}

# 32: routed federation proof (sessioned retrieve_tools; see mcp-guide-thresher.md §6)
#     expect namespaced tools: flotilla:pixel_screenshot, flotilla:pixel_tap, …
```
