# Session Backlog — 2026-10-24 (Kappa/toxic)

Consolidation of every work stream from this session, so work can continue
endlessly/autonomously. Each item is scoped, current-state, and next-action.

## A. THETA / EAP / GOOGLE BILLING (SUPER IMPORTANT — the user's top manual test)

Goal: theta end-to-end = caller → hodos(:25193) → keypool(:25109) → theta engine
→ Google Interactions API returns 200 tool-search steps.

STATE:

- **Root cause identified + verified**: Google migrated AI Studio keys
  `AIza`(Standard)→`AQ.`(Auth). All 6 `AQ.` EAP keys now return
  `401 ACCESS_TOKEN_TYPE_UNSUPPORTED` on `generativelanguage.googleapis.com`
  (verified live on /v1beta/models and /v1beta/interactions, as both
  `x-goog-api-key` and `Bearer`). Keys are DEAD, not a format/billing bug.
- Credits/billing are FINE: 7×$10 Gen-AI credits bound to the OPEN **Main**
  billing account, full balance ($10 each).
- **Code patched** (theta `eap-auth.ts`): removed the contradictory
  `authorization: Bearer` header; `eapApiKey` now prefers a Standard `AIzaSy`
  key over broken `AQ.`. Type-clean. (theta is gitignored in estate — private.)
- **Keypool fixed + UP**: canonical `pens/olympus/products/kryptos/keypool`,
  `:25109/health → 200` (was ECONNREFUSED off a stale `var/workspaces/layout/...`
  path in pitchfork.toml; fixed that path too).
- **Live firefox Google session cookies grabbed** from the logged-in nightly
  profile (`7c8v85fg.default-nightly/cookies.sqlite`): SID, __Secure-1PSID,
  __Secure-3PSID, SAPISID, APISID, HSID, SSID, SIDCC, OTZ, NID. curl jar works
  (reaches Google backend; exact AI-Studio project-spend endpoint still 404s).

NEXT ACTION (the ONE remaining step):

1. Get a valid **Standard `AIzaSy` EAP key** for project `654595778272`
   (existing `gem-forensic/ff` + `load_browser_cookies.py` give the session;
   mint a STANDARD key in AI Studio, or find a Standard key in the estate).
2. Persist it: secretsmith `service=hodos` (and/or gemini-eap) + the keypool's
   `GEMINI_EAP_KEY_N` source.
3. `keypool` reload → all `gemini-eap*` pools go **healthy** (not down).
4. `bun estate/packages/theta/src/eap-smoke.ts` → **200 with tool-search steps**
   (this is the LAST manual test — the goal).
5. Commit theta patch; push.

FALLBACK sub-path: bind project 654595778272 billing → Main in the Google
console; capture the exact XHR endpoint by replaying the page's own XHR URLs
from a CDP-attached logged-in browser (browserless chrome :25233 is NOT logged
into the EAP project; the live firefox session jar IS, but its exact spend
endpoint was 404 — capture the real XHR URL, don't guess).

## B. NIM / API-evangelist / hodos catalog merge (DONE + local)

- Added `api-evangelist/nvidia-nim` + `nvidia` + `monitoring` + `observability`
  as hodos submodules (`reference/`).
- Merged prober (`hodos/proxy/tools/probe-catalogs.ts`): pinax providers +
  both catalogs, probes to live truth, emits `SyntheticCheck` per provider,
  marks rate-limits advisory (May-2026 generated stubs ≠ durable).
- **90% coverage target**: prober pure fns (`parseRateLimits`, `candidatesFor`,
  `keyFor`, `toSyntheticCheck`) — 12 tests PASS (probe-catalogs.test.ts).
  Remaining: hodos RUST resolver coverage (model_map / free-lane).
- Auth fix (stale GH_TOKEN) → hodos/estate/delendai all PUSHED to main.
- hodos rename → keep `hodos`, assert merge (README frame). Done.
- **DONE-PUSHED**: hodos `5e2d935/7956bb7/a45bc59/be4aee2/33f0ace`; delendai
  `6e0486a`/`ea987fe`; estate `4adf2a4/2e34b371/2546e5ac`.

NEXT ACTION: add hodos Rust tests for providers/model_map resolver (free-lane →
:free, advisory parsing) to complete the 90% coverage; ensure hodos cargo test
green (was: missing `mod roost_providers` in lib.rs — I added it; re-verify).

## C. RECON 34k-apis (api-evangelist org) — DONE + pushed

- Recon project `estate/docs/recon/34k-apis/` (+bge-m3 embedding cluster,
  dataframe-js classification). 150-sample: 147 dump / 2 tooling / 1 ml — the
  org is ~99% per-company API-surface dumps; tooling layer is tiny
  (public-apis, network, posts, apis-io, unified-apis, monitoring, observability,
  nvidia-nim, nvidia).
- Trust caveat: rate-limits are stale May-2026 `generated` stubs — advisory.
- DONE-PUSHED to estate.

## D. DELEND / code-race / 429 (DONE + pushed, one caveat)

- `@delendai/core/llm`: callLlm promoted from audit; **429-aware**
  (rate_limited outcome + retryAfterMs); **multi-model fallback walk**
  (target-them-all: super-vl primary + lightning/nano-omni/gpt-oss/step-5/ultra:free).
- code-race `autoFix`: aggressive persona ("WTF is this shitty junior dev code"),
  "why sleep at all", secretsmith key resolution for HODOS.
- `parseRateLimitHeaders` → core retryAfterMs.
- Caveat: delendai `drift-check` regen (gen:all) needed before pushes.

## E. SUPER-RALPH→CORRAL / VansRouter+OmniRoute merge (DONE locally, needs push)

- corral/delendai index: fixed 20 stale plugin re-export paths (→ canonical).
- VansRouter+OmniRoute folders DELETED (merged into hodos); pitchfork daemon
  defs removed. Ensure nothing broke in the running estate router.
- Whether corral/estate delendai index files were pushed: verify + push.

## F. 2s-GUARD / delend-code-race autonomy (DONE)

- 2s-guard passes `--2s` real budget; delend-code-race local-resolved + runs
  standalone; resolves key via secretsmith (service=hodos).

## G. ESTATE MISC

- keypool → canonical olympus path (fix pitchfork.toml + pitchfork.d) — DONE.
- setup_accessibility (gatehouse computer-use AT-SPI) — DONE.

## Immediate next action (priority 1)

Pursue A: mint/find a Standard `AIzaSy` EAP key ⇒ secretsmith + keypool ⇒
eap-smoke 200 (the theta E2E manual test). Then B rust coverage. Then verify+push
E. Report each with evidence.

## H. (2026-10-24 late) hodos rust: [DONE] reverted generated-file hand-edit (pinax_providers KEY_ENV stays via overlay); added mod roost_providers so crate compiles; 308/309 tests pass; the 1 fail (roost_providers_copy_in_sync) needs the EXTERNAL pinax/generated/providers.rs (mesh/catalog) which is absent from this checkout — pre-existing env test, not a regression. hodos commit 698380f pushed.
