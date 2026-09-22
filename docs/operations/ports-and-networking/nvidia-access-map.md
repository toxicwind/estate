# NVIDIA API Access Map — NVCF-DIG (2026-09-21)

Exhaustive read-only enumeration of what our NVIDIA identity (`nvapi-…` build key)
can actually touch. Probe script: `bin/nvcf-access-probe.py` (re-runnable, key
never printed, email redacted from reports). Chris's hypothesis — "our NVIDIA
account has more accessible APIs than the front door and we're missing them" —
is **disproven** for anything invocable. Details below.

Our identity (two independent sources agree):
- NGC user `toxicwind` (id 2815195), verified, ORG_OWNER + PUBLIC_API_ENDPOINTS_USER
  on org **EffusionLabs** (INDIVIDUAL, private, id 2689912)
- NVCF/NCA billing account id: `iuh5eKGaKSnWglC73O7UeZBzNHZ5aP7TLHyJpM-rxWY`
  (seen both in NGC org `billingAccountId` and in per-model 404 entitlement bodies)
- Product enablements: `NGC_ADMIN_EVAL` (AI_FOUNDATIONS, exp 2027-07-17),
  `NGC_ADMIN_DEVELOPER` (NIM_DEV). No NVCF product enablement, no paid tier.
- `hasSignedNVCFEULA: false`, `hasSignedLlmEULA: false`

## Working surfaces (real responses)

| # | URL | Auth | Status | Verdict |
|---|-----|------|--------|---------|
| 1 | `GET https://integrate.api.nvidia.com/v1/models` | Bearer (also works with NO auth — public catalog) | 200 | 81 models, minimal fields only (`created,id,object,owned_by`). No per-model endpoint/base-URL hints. |
| 2 | `GET https://integrate.api.nvidia.com/v1/models/moonshotai/kimi-k3` | Bearer | 200 | Same minimal fields. |
| 3 | `POST https://integrate.api.nvidia.com/v1/chat/completions` | Bearer | 200 for `moonshotai/kimi-k3` | THE only invocable surface. Genuine Kimi K3, 2–4 min cold load (wrapped by `bin/nim-kimi-sidecar.py` :25163). Strip `top_p` (NVIDIA 400s it). |
| 4 | `GET https://api.nvcf.nvidia.com/v2/nvcf/functions` | Bearer | 200 | 203 functions: 110 ACTIVE / 90 INACTIVE / 3 DEGRADING — **all 203 `ownedByDifferentAccount: true`**. Read-only catalog; nothing ours. |
| 5 | `GET https://api.nvcf.nvidia.com/v2/nvcf/assets` | Bearer | 200 | `{"assets":[]}` — we own zero assets. |
| 6 | `GET https://api.ngc.nvidia.com/v2/users/me` | Bearer | 200 | Full identity record (see above). |
| 7 | `GET https://api.ngc.nvidia.com/v2/orgs` | Bearer | 200 | 1 org: EffusionLabs (see above). |
| 8 | `GET https://api.ngc.nvidia.com/v2/models` | Bearer | 200 | Public NGC model-registry catalog (QA canary entries) — not our models. |

## Proven negative (each independently confirms "front-door-only")

1. **NVCF functions are other-account and unaddressable.** All 203 list entries have
   `ownedByDifferentAccount: true`. `GET /v2/nvcf/functions/{uuid}` with a real UUID
   from the list → **404** `No static resource` — cross-account functions aren't
   addressable by us at all. `GET /v2/nvcf/authorizations/functions/{uuid}`
   (documented per-function authorized-accounts path) → **403** `Access Denied` —
   we can't even read who *is* authorized; that needs the `authorize_clients` scope.
   Per NVIDIA docs, a function belongs to its creator's cloud account and invocation
   credentials must reference the same account.
2. **Model entitlement is per-function, and we have exactly one.**
   `POST /v1/chat/completions` for `moonshotai/kimi-k2.6` (same publisher, in catalog)
   → **404** `Function '23d4f03a-…': Not found for account 'iuh5…'` in 116ms.
   Same for `nvidia/llama-3.1-nemotron-70b-instruct` → **404** `Not found for account`
   in 121ms. (An earlier probe of `qwen/qwen3-235b-a22b` 404'd but that id isn't in
   the catalog — invalid test, redone properly here.) The 81-model list is the public
   catalog, not our allowlist.
3. **No async/genai entitlement.** `GET https://ai.api.nvidia.com/v1/genai` and
   `/v1/genai/moonshotai/kimi-k3` → **404** (the documented 202 + `NVCF-REQID`
   polling contract has no entitled function to exercise against).
4. **No account introspection surfaces.** `GET /v1/usage`, `/v1/billing` on integrate
   → 404. Bare `GET /v2/nvcf/authorizations` → 404 (not a route; per-function path is
   the real one). `GET /v2/nvcf/deployments` → 404. `api.nvidia.com` unreachable
   from yote egress. build.nvidia.com key metadata is UI-only
   (`build.nvidia.com/settings/api-keys`) — no public endpoint exists.
5. **Auth scheme is Bearer-only.** No-auth on NVCF → 401; `nvcf-api-key` header
   variant → 401. (No-auth on integrate `/v1/models` → 200: it's public.)

## What would unlock more (Chris's call)

1. **Model entitlement** — the `Not found for account` 404 is per-account. NVIDIA
   (build.nvidia.com) controls which catalog functions our NCA id may invoke;
   a paid tier / wider allowlist is their grant to make.
2. **NVCF function access** — the owning account's admin must add our NCA id
   (`iuh5eKGaKSnWglC73O7UeZBzNHZ5aP7TLHyJpM-rxWY`) via
   `PATCH /v2/nvcf/authorizations/functions/{id}/add`. Nobody can do this but them.
3. **Key scope** — we already hold `PUBLIC_API_ENDPOINTS_USER` (the scope the docs
   say is required; without it inference 404s). `authorize_clients` scope would
   unlock NVCF authorization management — an NGC org-admin/key-issuer action.
4. **Sign the NVCF EULA** (`hasSignedNVCFEULA: false`) — prerequisite for any NVCF
   function ownership/invocation on our side.

## Judgment calls / oracle

No oracle verdicts were needed. The one genuine fork — whether to POST-invoke an
ACTIVE internal NVCF function to capture the exact invoke error — was decided
against by the task's own read-only rule (an invoke creates an execution on
another account's function); the 403 on the authorizations read plus
`ownedByDifferentAccount: true` on all 203 functions already proves
non-invocability without it. The invalid qwen entitlement probe was caught and
redone against real catalog ids rather than debated.

## Repro

```
python3 bin/nvcf-access-probe.py [--report /tmp/nvcf-access.json]
                                  [--inference-models a/b,c/d] [--no-inference]
```

Probe script commit: `0ad1161efc` · This doc: `docs/nvidia-access-map.md`.
Key material: `/home/toxic/.secrets` (`NVIDIA_API_KEY`), read-only, never committed.
