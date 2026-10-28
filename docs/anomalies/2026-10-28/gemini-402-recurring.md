# Anomaly: recurring 502/402 on `rhodochrosite.azurite/models/gemini-flash-tool-retrieval`

**Date:** 2026-10-28
**Box:** awrawr-pc (estate)
**Reporter:** user (ground truth)
**Status:** diagnosed — root cause is architect-gated (prepay depletion); no fix applied yet.

---

## Symptom

A tau/kappa session pinned to `rhodochrosite.azurite/models/gemini-flash-tool-retrieval` fails with:

```
Error: Retry budget exhausted after 3 retries: 502 keypool upstream: Error: HTTP 402
Error: Retry failed after 3 attempts: 502 keypool upstream: Error: HTTP 402
```

Route chain: agent → rhodochrosite (:25193) → keypool (:25109, pool `gemini-eap-interactions`) → Google `generativelanguage.googleapis.com/v1beta/interactions`.

---

## Error-class table

| Error class | Surface | Meaning | Verdict in this incident |
|---|---|---|---|
| `502 keypool upstream: HTTP 402` | tau→rhodochrosite→keypool | keypool's selected key returned 402 from Google; all retries exhausted | **Observed (user report)** |
| `402 RESOURCE_EXHAUSTED` | Google `generateContent` | prepayment credits depleted | **Root cause — live key `GEMINI_EAP_KEY`/`_1`** |
| `400 INVALID_ARGUMENT / API_KEY_INVALID` | Google `generateContent` | malformed request or invalid key format | Ruled out (probe artifact, see below) |
| `401 UNAUTHENTICATED` | Google `generateContent` | key not valid | `GEMINI_EAP_KEY_2`–`_5` (dead) |
| `403 PERMISSION_DENIED (leaked)` | Google `generateContent` | key reported leaked | `GEMINI_EAP_KEY_6` (dead) |
| `200 /v1beta/models` | keypool health probe | non-billing model catalog | Misleading — marks depleted key "healthy" |

---

## Probe evidence (all output persisted to `/tmp/gemini-audit/`)

### 1. Keypool `/status` → `/tmp/gemini-audit/status.json`

Pool `gemini-eap-interactions` (upstream `https://generativelanguage.googleapis.com`):

| Key | fingerprint | state | latency_ms |
|---|---|---|---|
| `GEMINI_EAP_KEY` | `4bf598955f69` | **healthy** | 76 |
| `GEMINI_EAP_KEY_1` | `4bf598955f69` | **healthy** | 83 |
| `GEMINI_EAP_KEY_2` | `4bf598955f69` | down | — |
| `GEMINI_EAP_KEY_3` | `4bf598955f69` | down | — |
| `GEMINI_EAP_KEY_4` | `4bf598955f69` | down | — |
| `GEMINI_EAP_KEY_5` | `4bf598955f69` | down | — |
| `GEMINI_EAP_KEY_6` | `d03cd67ae3e5` | down | 91 |

Note: `GEMINI_EAP_KEY` … `_5` share one fingerprint (`4bf598955f69`) — same underlying credential, different env names. `_6` is distinct (`d03cd67ae3e5`).

The `/status` schema has no persistent strikes table: this Bun port of the keypool (`pens/olympus/products/kryptos/keypool/src/pool.ts`) uses in-memory `markDown`/cooldown per key; anomaly #15's per-(provider,model) 3-strike/15-min-decay quarantine is **not implemented** here, so there are no stale strikes to reset.

### 2. Live config path resolution

`pgrep -f keypool` → PID 533172 (`bun /home/toxic/pens/olympus/products/kryptos/keypool/src/index.ts`). `/proc/533172/cmdline` has **no** `--config` override, so the live config **is** `estate/config/keypools.yaml` (no drift vs the estate clone).

`gemini-eap-interactions` pool definition in `keypools.yaml`: protocol `gemini-interactions`, upstream `https://generativelanguage.googleapis.com`, auth header `x-goog-api-key: "{key}"` only. **No `x-goog-user-project` header anywhere in keypool code** (`pool.ts`, `translate.ts`, `server.ts`, `config.ts`) — anomaly #25 ruled out by inspection.

### 3. Masked keys via `secretsmith env` → `/tmp/gemini-audit/keys.txt`

Clean-env invocation `env -u BASH_ENV -u ENV bash -c 'secretsmith env'`; values stripped of surrounding quotes; masked to first 12 chars:

```
GEMINI_EAP_KEY=AIzaSyCwrN3Y...
GEMINI_EAP_KEY_1=AIzaSyCwrN3Y...
GEMINI_EAP_KEY_2=AQ.Ab8RN6J3B...
GEMINI_EAP_KEY_3=AQ.Ab8RN6Jq9...
GEMINI_EAP_KEY_4=AQ.Ab8RN6Jq3...
GEMINI_EAP_KEY_5=AQ.Ab8RN6K7U...
GEMINI_EAP_KEY_6=AIzaSyCLnlbO...
```

(Full keys never printed; never committed.)

### 4. Live key classification vs Google — REAL `generateContent` (not `/v1beta/models`)

Per anomaly #5 rule, `/v1beta/models` 200 proves nothing; billing is only hit on `generateContent`. Each key POSTed `{"contents":[{"parts":[{"text":"hi"}]}]}` to `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent` with `x-goog-api-key: $KEY`. Bodies saved to `/tmp/gemini-audit/gencontent-*.json`; summary in `/tmp/gemini-audit/gencontent-summary.json`.

| Key (masked) | HTTP code | Classification |
|---|---|---|
| `GEMINI_EAP_KEY` = `AIzaSyCwrN3Y…` | **402** `RESOURCE_EXHAUSTED` | **prepayment depleted (live)** |
| `GEMINI_EAP_KEY_1` = `AIzaSyCwrN3Y…` | **402** `RESOURCE_EXHAUSTED` | **prepayment depleted (live)** |
| `GEMINI_EAP_KEY_2` = `AQ.Ab8RN6J3B…` | 401 `UNAUTHENTICATED` | dead |
| `GEMINI_EAP_KEY_3` = `AQ.Ab8RN6Jq9…` | 401 `UNAUTHENTICATED` | dead |
| `GEMINI_EAP_KEY_4` = `AQ.Ab8RN6Jq3…` | 401 `UNAUTHENTICATED` | dead |
| `GEMINI_EAP_KEY_5` = `AQ.Ab8RN6K7U…` | 401 `UNAUTHENTICATED` | dead |
| `GEMINI_EAP_KEY_6` = `AIzaSyCLnlbO…` | 403 `PERMISSION_DENIED` (leaked) | dead |

Control: clean key re-tested → `/v1beta/models` = **200**, `generateContent` = **402** (saved to `/tmp/gemini-audit/models-probe-clean.json`, `gencontent-clean.json`). Confirms the health-probe vs billing gap: the keypool's health probe hits `/v1beta/models` (200, non-billing) and marks the depleted key **healthy**, so `pick()` keeps selecting it first → retries hit 402 → retry budget exhausted → 502.

### 5. Full-chain probe

- `GET http://127.0.0.1:25193/health` → **200 ok** (saved `/tmp/gemini-audit/rhodochrosite-health.json`).
- `POST http://127.0.0.1:25193/v1/chat/completions` model `rhodochrosite.azurite/models/gemini-flash-tool-retrieval` (proxy bearer auth from `/home/toxic/.tau/rhodochrosite.key`) → **502** `{"error":{"code":"bad_gateway","message":"upstream response failed or timed out","type":"proxy_error"}}` (saved `/tmp/gemini-audit/chain-chat.json`).

`~/.tau/models.yml` defines `rhodochrosite.azurite` with `baseUrl: http://127.0.0.1:25109/gemini-eap-interactions` (count 26 baseUrl lines; `rhodochrosite.azurite` among them).

### 6. Mimetite catalog check

`pens/geode/products/mimetite/src/data.ts` rhodochrosite `azurite` def: `baseUrl: http://127.0.0.1:25109/gemini-eap-interactions` — **correct**, matches the keypool pool path. No catalog drift.

---

## Root cause

**Prepayment credits are depleted on the single live Google EAP key (`GEMINI_EAP_KEY` / `GEMINI_EAP_KEY_1`).** The keypool health probe only hits the non-billing `/v1beta/models` endpoint (200), so it marks the depleted key healthy and `pick()` selects it first; every real `generateContent` through the `gemini-eap-interactions` pool returns 402, retries exhaust the budget, and rhodochrosite surfaces a 502. All other pool keys are dead (401 ×4, 403 leaked). Billing/account state is **architect-gated** — no funds may be added and no billing toggles may be changed by this agent.

---

## Fix applied

**None applied — root cause is architect-gated.** The authorized in-scope fixes were checked and found not applicable:

| Authorized fix | Check | Result |
|---|---|---|
| Remove `x-goog-user-project` from live pool config | Header absent from keypool code and `keypools.yaml` | Not present — nothing to remove |
| Reorder live key first | Both live keys (`_1`, `_1`) are 402-depleted; no healthy key exists to promote | No healthy key to reorder to front |
| Reset stale strikes table | This Bun keypool port has no persistent strikes (in-memory `markDown`/cooldown only) | No strikes table to reset |

No repo source/config changes were made. `estate/config/keypools.yaml`, `pens/olympus/products/kryptos/keypool/`, and `pens/geode/products/mimetite/src/data.ts` are all correct as-is.

---

## Exact gated remediation (architect action)

The prepayment balance on the Google Cloud project owning `GEMINI_EAP_KEY`/`_1` (project `gen-lang-client-0111199472`, project number `654595778272`, per `keypools.yaml` comments) is depleted. Remediation — **to be performed by the architect, not this agent**:

1. Open **AI Studio** at `https://aistudio.google.com/projects`, select project `gen-lang-client-0111199472` (654595778272).
2. Either add prepayment funds to restore the paid tier, **or** disable billing → Free Tier toggle.
3. After the project has an active billing/free tier, `GEMINI_EAP_KEY`/`_1` will return 200 on `generateContent`; the keypool health probe will confirm healthy and the full chain through :25193 will return 200.

Read-only billing-state check (optional, no account-state changes): the architect's Pixel 9 Pro XL is available via flotilla MCP at `http://127.0.0.1:25245/mcp` — read-only only, no taps that change account state.

---

## Verification receipt

**Blocked — architect-gated.** Cannot produce a real-generation 200 until prepayment is restored. Evidence captured:

- `/tmp/gemini-audit/gencontent-summary.json` — all 7 keys classified vs Google `generateContent`
- `/tmp/gemini-audit/gencontent-clean.json` — live key → 402 `RESOURCE_EXHAUSTED`
- `/tmp/gemini-audit/models-probe-clean.json` — same key → 200 on `/v1beta/models` (probe gap proven)
- `/tmp/gemini-audit/status.json` — keypool marks depleted key healthy
- `/tmp/gemini-audit/chain-chat.json` — full chain :25193 → 502 bad_gateway
- `/tmp/gemini-audit/keys.txt` — masked keys (first 12 chars only)

Once the architect restores prepayment/free tier, re-verify:
1. `curl -s http://127.0.0.1:25109/status` → `GEMINI_EAP_KEY` state `healthy`
2. Real `generateContent` with `GEMINI_EAP_KEY` → **200**
3. `POST :25193/v1/chat/completions` model `rhodochrosite.azurite/models/gemini-flash-tool-retrieval` → **200**

---

## Files written (audit only; no repo changes, no secrets)

- `/tmp/gemini-audit/status.json`, `keys.txt` (masked), `gencontent-*.json`, `gencontent-summary.json`, `models-probe*.json`, `gencontent-clean.json`, `rhodochrosite-health.json`, `rhodochrosite-chat.json`, `chain-chat.json`
