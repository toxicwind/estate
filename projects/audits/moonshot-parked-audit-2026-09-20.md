# Moonshot peer PARKED-audit — keep parked, rewire, or restore?

- **Date:** 2026-09-20 ~15:05 MDT
- **Auditor:** moonshot-parked-audit (ember, subagent)
- **Scope:** the PARKED `moonshot` peer in `/home/toxic/sovereign/config/herd.yaml` (lines 749–768), against all information as of 2026-09-20.
- **Status:** PROPOSED — nothing was applied. No shared file was edited, no daemon touched.
- **Verdict: RESTORE the moonshot peer** (proposed diff in §5, Chris decides).

## TL;DR

The direct Moonshot key is **verified live today** (`GET api.moonshot.ai/v1/models` → HTTP 200, serving `kimi-k2.6` + `kimi-k2.7-code`). Every other Kimi route is down right now: OpenRouter paid Kimi → **402 "Insufficient credits"** on the live `_1` key (measured today, not a wiring defect — no rewire fixes billing); OpenRouter `:free` Kimi variants → 404; Pollinations peer parked (herd binary P1 dummy-Bearer bug); NIM deleted by debate verdict; HF `hf-free` peer disabled (tokens refreshed today but the peer is unverified). The current 429 on Moonshot chat is a **transient routing signal per standing doctrine**, observed twice today, and the estate already has cooldown machinery for it. Keeping the peer parked leaves Kimi fully dark while a live provider key exists — that fails "maximal without losing." Restore as the k2-line route; k3 stays on the honest OpenRouter route (402 until credits land).

---

## 1. Method

- Reached yote via `~/workspace/bin/yote-conn` (WS lane, 133 ms exec probe).
- Read the live `config/herd.yaml` moonshot block, modelMap, alias shims, `config/keypools.yaml`, `config/model_constraints.yaml`, keypool `/status` + audit log, herd `/v1/models`.
- Live-probed: Moonshot `/v1/models`, Moonshot chat (`kimi-k2.6`, exact-token prompt), OpenRouter `/v1/auth/key`, OpenRouter chat (`moonshotai/kimi-k3`, exact-token prompt), keypool paid-pool passthrough.
- Exact-token probe protocol (same as the v3 probe): prompt `Output exactly: ABSTRACT-7X3Q. No other text.`, verdict requires verbatim match.
- Borrowed patterns: `~/workspace/skills/github/SKILL.md` (auth-first diagnostics: a 401/403 is a question about the request before the key — applied to the 402 by reading the response body, not the status alone); `~/workspace/skills/exa/SKILL.md` (neural search for September-2026 Moonshot status).
- Prior art read, not reinvented: `~/workspace/audits/kimi-k3/kimi-k3-provider-research.md` (OpenRouter/Pollinations/NIM/Moonshot catalog, 2026-09-20), `projects/openrouter-probe/RANKING.md` (v3 speculative ranking).
- No raw secrets were read, printed, logged, or committed. Key presence checked by name only; values stayed in `/home/toxic/.secrets` (0600).

## 2. Evidence table (all observed 2026-09-20 ~14:56–15:05 MDT unless noted)

| # | Route / claim | Observation | Timestamp | Standing |
|---|---|---|---|---|
| E1 | Moonshot direct key live | `GET https://api.moonshot.ai/v1/models` with `MOONSHOT_API_KEY` (name present, `/home/toxic/.secrets` line 193, `export`-prefixed) → **HTTP 200**, models = `["kimi-k2.7-code", "kimi-k2.6"]`. Verbatim from the API. **No kimi-k3 on this key.** | 15:00 MDT | LIVE |
| E2 | Moonshot direct chat | `POST /v1/chat/completions`, `kimi-k2.6`, exact-token probe → **HTTP 429 Too Many Requests**. Config comment records the same 429 at ~09:00 today. | 15:00 MDT | TRANSIENT per doctrine (429 = routing signal, cooldown, not death) |
| E3 | OpenRouter `_1` key auth | `GET openrouter.ai/api/v1/auth/key` → **HTTP 200**, `usage: 0.00153165`, `limit: null`, `is_free_tier: false`. Key authenticates; account is not free-tier-flagged. | 15:01 MDT | LIVE (auth) |
| E4 | OpenRouter paid Kimi | `POST /v1/chat/completions`, `moonshotai/kimi-k3`, exact-token probe, `_1` key → **HTTP 402** `{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits",...}}` | 15:02 MDT | BILLING STATE — no config change fixes this; Chris's call (money) |
| E5 | Keypool `/status` (:25109) | `openrouter-free`: both keys `down`, `http:429`, `recover_in_s=0` (revalidatable). `openrouter-paid`: both key names `down`, `http:402`, cooldown ~155 s. `gemini`: mixed 402/429. | 14:57 MDT | transient across the board |
| E6 | Keypool audit log | Burst ~14:54 MDT: `select` events for `moonshotai/kimi-k3` + `moonshotai/kimi-k2.6` on `openrouter-paid` → `failover` `http_status: 402`, `cooldown_s: 300`. Independent corroboration of E4. | 14:54 MDT | 402 = entitlement/billing, not key death |
| E7 | Keypool passthrough probe | `POST 127.0.0.1:25109/openrouter-paid/v1/chat/completions` (`moonshotai/kimi-k3`) → **HTTP 502** `{"error":"keypool 'openrouter-paid': no healthy key"}` — honest no-healthy-key, keys in 402 cooldown. | 15:03 MDT | expected during cooldown |
| E8 | herd `/v1/models` (live) | 91 models; **`moonshot/*`: none** (parked = genuinely inactive); Kimi only as `openrouter-pool/moonshotai/kimi-k2.6`, `openrouter-pool/moonshotai/kimi-k3` (both 402-backed right now). | 15:04 MDT | Kimi fully dark via herd |
| E9 | OpenRouter `:free` Kimi | No `moonshotai/*:free` variant in catalog (provider-research, 17 `moonshotai/kimi*` entries, all paid); v3 probe: no Kimi ID among the 10 winners; config note: `:free` variants 404 "unavailable for free". | 2026-09-20 | DEAD route |
| E10 | Pollinations Kimi | Peer parked: herd binary bakes P1 dummy-Bearer, Pollinations now 401s it; proper fix is rebuilding herd from `projects/herd`. Separate workstream. | 2026-09-20 | PARKED (binary bug) |
| E11 | NIM Kimi | Deleted, not demoted, by debate verdict (24h 429 soft-locks poison fail-fast routing). | 2026-09-20 | DELETED |
| E12 | HF `hf-free` peer | Peer disabled in config (stale "401 dead keys" comment), BUT a new fine-grained HF token was installed to all 4 HF vars today and verified via `whoami-v2`. Peer never re-probed since. | 2026-09-20 | UNVERIFIED — revive-order says HF first (see §4) |
| E13 | v3 reliability probe | 446 IDs × 3 passes; only 10 ever returned the token. Relevant: `openrouter/free` 1/3 exact. Kimi absent from winners. | 2026-09-20 ~15:00 | speculative ranking in `projects/openrouter-probe/RANKING.md` |
| E14 | Web (Exa, Sep 2026) | ai-api-hub Moonshot provider page (pub. 2026-09-12, verified 2026-09-13): current catalog = Kimi K3 (coding/knowledge flagship) + K2.7 Code family + general-purpose K2.6; older Moonshot/Kimi IDs retired. Consistent with E1's live model list. | fetched 15:05 MDT | secondary, consistent |

**What was NOT achieved:** no successful chat completion on any Kimi route today (Moonshot 429, OpenRouter 402). The restore recommendation rests on key-liveness + model-list-liveness + doctrine + measured need — stated plainly, not as a completed chat.

## 3. Config state (live file)

- **Parked block** (`config/herd.yaml` 749–768): comment claims key live (200 on `/v1/models` ~09:00) but chat 429; documents PARKED-as-standby with RESTORE instructions (uncomment + re-probe chat to 200). Peer would serve `kimi-k2.6`, `kimi-k2.7-code` via `https://api.moonshot.ai` (no `/v1` suffix; router joins path), `apiKey: ${env.MOONSHOT_API_KEY}`.
- **modelMap** (53–54): `kimi-k2 → moonshotai/kimi-k2.6`, `kimi-k3-nim → moonshotai/kimi-k3` (both OpenRouter-namespaced, both 402-backed today).
- **Alias shims** (186–202): `kimi`, `kimi-k2` → `openrouter-pool/moonshotai/kimi-k2.6`; `kimi-code` → `openrouter-pool/moonshotai/kimi-k2.7-code`. Retargeted from `moonshot/*` when the peer was parked.
- **Revive-order policy** (`config/model_constraints.yaml`, debate verdict 2026-09-20): *"HuggingFace Inference Providers first, Moonshot-direct only on measured need, NIM never again as primary."* The same file notes kimi-k3 "REVIVED via the OpenRouter key-pool" — **stale as of E4** (OpenRouter Kimi is 402 today).

## 4. The three bids

### Bid A — Keep parked
**Steelman:** chat is 429 right now (twice today); restoring churns a shared config and needs a herd restart on a shared tree with an active coordinator; the HF tokens were refreshed today and the debate verdict orders HF-first, so the disciplined next step is an HF re-probe, not a Moonshot restore; the parked comment already documents the restore path for later.
**Elimination:** the 429 is explicitly transient per standing doctrine — parking *because of a transient signal* contradicts it. "HF first" is about revive *order*, and the HF peer is unverified; nothing in the verdict forbids preparing/approving the Moonshot restore in parallel. Keeping parked as a final state leaves Kimi with zero working routes while a verified-live provider key exists. Verdict: **reject as final state** (acceptable only as "parked pending the HF probe," which is a schedule, not a strategy).

### Bid B — Rewire kimi routes to the live `_1` key
**Steelman:** minimal churn; the `_1` key authenticates (E3); the wiring already exists.
**Elimination:** it is already the current wiring (modelMap + shims → `openrouter-pool` → keypool paid pool → `_1` key material). E4 proves the failure is **billing** (`limit_source: openrouter_credits`), not wiring. No rewire can fix a 402. This bid is a no-op. Verdict: **eliminate**.

### Bid C — Restore the moonshot peer
**Steelman:** E1 — key and model list verified live *today*; E14 — the two served IDs are Moonshot's current K2 line (K2.6 general, K2.7-code specialist); doctrine RANKING > FREE-ON-PROVIDER > PAY ranks a direct-provider route above a 402'd aggregator; **measured need is met** — every other Kimi route is down (E4), parked (E10), deleted (E11), dead (E9), or unverified (E12); the 429 (E2) is transient and the estate already does cooldown + revalidation; restoring is router-config-only, which respects the standing rule that model selection lives in router config, never in model-family tooling; nothing is deleted — the OpenRouter route stays as the honest k3 path.
**Weaknesses, owned:** no k3 on this key (k3 stays OpenRouter-402 until Chris adds credits — visible, correct signal); no successful chat completion measured today (429 at probe time); HF-first per the revive order — so recommend the HF re-probe as a parallel task, not a blocker.
Verdict: **WINNER.**

## 5. Verdict and recommended diff (PROPOSED — NOT APPLIED)

**Restore the `moonshot` peer as the K2-line route.** Concretely, in `config/herd.yaml`:

```diff
-  # --- moonshot: Moonshot AI direct (PARKED 2026-09-20) ---
-  # MOONSHOT_API_KEY is live (verified HTTP 200 on /v1/models 2026-09-20 ~09:00)
-  # but chat returned 429 on the ~09:00 probe. Per doctrine a 429 is TRANSIENT,
-  # so this peer is PARKED as a documented standby -- NOT deleted. Kimi currently
-  # routes via openrouter-pool (key-pool sidecar :25109). If 429s persist for hours,
-  # suspect balance exhaustion and top up. RESTORE: uncomment the block below and
-  # re-probe chat completions to HTTP 200 before relying on it.
-  # Model IDs verbatim from api.moonshot.ai/v1/models.
-  # kimi-k2.6 = main Kimi; kimi-k2.7-code = code specialist. No kimi-k3 on this key.
-  # NOTE: proxy has no /v1 suffix -- the router joins proxy + /v1/chat/completions.
-  # moonshot:
-  #   proxy: https://api.moonshot.ai
-  #   apiKey: ${env.MOONSHOT_API_KEY}
-  #   models:
-  #     - kimi-k2.6
-  #     - kimi-k2.7-code
-  #   timeouts:
-  #     connect: 30
-  #     keepalive: 30
-  #     responseHeader: 120
-  #     tlsHandshake: 10
-  #     idleConn: 90
+  # --- moonshot: Moonshot AI direct (RESTORED 2026-09-20, moonshot-parked-audit) ---
+  # Key verified live 2026-09-20 ~15:00 MDT (HTTP 200 on /v1/models; serves
+  # kimi-k2.6 + kimi-k2.7-code, no kimi-k3 on this key). Chat was 429 at probe
+  # time -- TRANSIENT per doctrine; herd peer failover + cooldown apply. If 429s
+  # persist for hours, suspect balance exhaustion, re-park, and top up.
+  # OpenRouter Kimi is 402 "Insufficient credits" (E4) -- this peer is the
+  # working K2-line route until credits land or HF-free revives. k3 has no
+  # direct route: kimi-k3-nim stays on openrouter-pool (honest 402).
+  # Model IDs verbatim from api.moonshot.ai/v1/models.
+  # NOTE: proxy has no /v1 suffix -- the router joins proxy + /v1/chat/completions.
+  moonshot:
+    proxy: https://api.moonshot.ai
+    apiKey: ${env.MOONSHOT_API_KEY}
+    models:
+      - kimi-k2.6
+      - kimi-k2.7-code
+    timeouts:
+      connect: 30
+      keepalive: 30
+      responseHeader: 120
+      tlsHandshake: 10
+      idleConn: 90
```

Retarget the Kimi alias shims back to the direct peer (they were moved to `openrouter-pool/*` when parked; that target is 402 today):

```diff
-  # Retargeted 2026-09-20 (herd-deployer) from moonshot/* to openrouter-pool/* — the moonshot
-  # peer is parked; Kimi routes via the OpenRouter key-pool sidecar.
+  # Retargeted 2026-09-20 (moonshot-parked-audit) from openrouter-pool/* back to
+  # moonshot/* — the direct peer is restored; openrouter-pool Kimi is 402
+  # "Insufficient credits" until the account is topped up.
   kimi:
-    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target openrouter-pool/moonshotai/kimi-k2.6
-    description: "Kimi (alias -> openrouter-pool/moonshotai/kimi-k2.6)"
+    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target moonshot/kimi-k2.6
+    description: "Kimi (alias -> moonshot/kimi-k2.6)"
     metadata:
-      alias_of: openrouter-pool/moonshotai/kimi-k2.6
+      alias_of: moonshot/kimi-k2.6
   kimi-k2:
-    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target openrouter-pool/moonshotai/kimi-k2.6
-    description: "Kimi K2 (alias -> openrouter-pool/moonshotai/kimi-k2.6)"
+    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target moonshot/kimi-k2.6
+    description: "Kimi K2 (alias -> moonshot/kimi-k2.6)"
     metadata:
-      alias_of: openrouter-pool/moonshotai/kimi-k2.6
+      alias_of: moonshot/kimi-k2.6
   kimi-code:
-    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target openrouter-pool/moonshotai/kimi-k2.7-code
-    description: "Kimi code specialist (alias -> openrouter-pool/moonshotai/kimi-k2.7-code)"
+    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target moonshot/kimi-k2.7-code
+    description: "Kimi code specialist (alias -> moonshot/kimi-k2.7-code)"
     metadata:
-      alias_of: openrouter-pool/moonshotai/kimi-k2.7-code
+      alias_of: moonshot/kimi-k2.7-code
```

Optional (recommended, Chris's call) — point the default `kimi-k2` route name at the live peer instead of the 402'd aggregator ID; `kimi-k3-nim` stays on OpenRouter (only k3 route):

```diff
-    kimi-k2: moonshotai/kimi-k2.6
+    kimi-k2: moonshot/kimi-k2.6
     kimi-k3-nim: moonshotai/kimi-k3
```

Deployment (only on Chris's approval — shared tree, shared daemon):
1. Apply the diff to `config/herd.yaml`.
2. Restart herd via the canonical `pitchfork-restart` wrapper (SIGHUP does not reload peer topology — code/config change needs the restart path the estate already uses).
3. Verify: `moonshot/kimi-k2.6` and `moonshot/kimi-k2.7-code` appear in herd `/v1/models`; exact-token probe returns `ABSTRACT-7X3Q` verbatim.
4. If chat 429s persist for hours after restore: re-park and investigate balance (per the block comment).

## 6. Follow-ups (not this audit's scope, recorded so they aren't lost)

- **HF-first re-probe:** per the debate revive order, probe `hf-free` (`router.huggingface.co`, `moonshotai/Kimi-K3`) with the refreshed HF token. If it serves free again, HF becomes the k3 route and moonshot-direct stays the k2-line route. The config comment claiming dead HF keys is stale.
- **OpenRouter credits:** the 402 is `limit_source: openrouter_credits`. Topping up restores `openrouter-pool/moonshotai/kimi-k3` (k3's only current route) and the paid pool generally. Chris's money call.
- **model_constraints.yaml staleness:** the note claiming kimi-k3 "REVIVED via the OpenRouter key-pool" is contradicted by E4. Update or annotate when the restore/credit decision lands.
- **Moonshot chat re-probe:** one exact-token completion on `moonshot/kimi-k2.6` after restore, to close the loop E2 left open.

## 7. References

- Live config: `/home/toxic/sovereign/config/herd.yaml` (moonshot block 749–768, modelMap 53–54, shims 186–202); `config/keypools.yaml` (paid-pool health = `GET /v1/auth/key`); `config/model_constraints.yaml` (revive-order debate verdict).
- Keypool: `http://127.0.0.1:25109/status`, `/home/toxic/sovereign/data/keypool-audit.jsonl`, `bin/herd-keypool.py` (`free_only` enforcement, cooldown + recovery sweep).
- Prior research: `~/workspace/audits/kimi-k3/kimi-k3-provider-research.md` (OpenRouter/Pollinations/NIM/Moonshot catalog 2026-09-20); `projects/openrouter-probe/RANKING.md` + `probe_reliability.py` (v3: 446 IDs, 10 winners).
- Web (via `~/workspace/skills/exa/SKILL.md`): https://ai-api-hub.com/providers/moonshot/ (pub. 2026-09-12, verified 2026-09-13); https://www.kimi.com/en/help/kimi-api/api-rate-limits (official rate-limit docs); Moonshot status https://status.moonshot.cn/ (per provider-research).
- Standing rules applied: `~/AGENTS.md` (model-family tooling never hardcodes model IDs — this audit proposes router-config changes only); 429/402 = transient routing signals (cooldown + auto-recovery); verify-before-claiming (every status above was probed live this session).
