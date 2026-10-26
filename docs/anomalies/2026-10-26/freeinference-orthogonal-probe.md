# 2026-10-26 — FreeInference Orthogonal Probe (Build 4b80416 recon)

Probe script: `/tmp/fi_orthogonal/probe.sh` · Raw outputs: `/tmp/fi_orthogonal/out/`
Session: `probe-20261026-083426Z` · All HTTP observed live.

## Findings

| # | Probe | Result | Anomaly / Note |
|---|---|---|---|
| 1 | `/site-updates` | 200 | Banner: "fake user agent will be banned" (2026-07-30). Onboarding paused at capacity (2026-08-11). **Control plane treats missing UA as a ban-worthy signal — always send a real UA string.** |
| 1 | `/auth/accounts` | 200 | `{active_user_id:null, accounts:[], max_accounts:5}` with bare API key — leaks **max_accounts:5** plan limit without auth. |
| 1 | `/user/me`, `/user/usage`, `/user/api-keys/all`, `/user/recent-requests` | 401 | Confirmed hard split: data-plane (`hyi-` key) works, control-plane (`/user/*`) requires a **session JWT** (browser DevTools) — not obtainable from API key. ULID chronometry script needs that JWT; skipped. |
| 2 | `/v1/models` polymorphism | 200 both | Header-switch confirmed: default → OpenAI `list` schema (6 models incl. `bge-m3`); `Anthropic-Version: 2023-06-01` → Anthropic schema (`display_name`, `created_at` epoch-0, `has_more`). **Anthropic models list omits `bge-m3`** (5 vs 6) — embed model hidden from that schema. All `created_at` = epoch 0 (placeholder, not real registration dates). |
| 2b | Model ID boundaries | ✓ | `glm-5.3` (doc label) → 404; `glm-5.3-flash` → 200; `bge-m3` on chat → 404, on `/v1/embeddings` → 200, dim=1024, served as `BAAI/bge-m3`. Route-boundary enforcement is correct. glm-5.3-flash response carried `reasoning_content` even at max_tokens=1 (finish=length) — reasoning field appears on the wire regardless of budget. |
| 3 | `/anthropic/v1/messages` | 200 | Wire translator LIVE — but **model mismatch**: requested `minimax-m3`, served `qwen3.6-35b` (same silent-fallback class as the model-identity chain anomaly). `usage` omits cache fields entirely on this wire. |
| 4 | `X-Reasoning-Passthrough: false` | no-op | Message keys identical (`role`,`content`), usage identical (9 completion tokens both). On this model/prompt the header produced **no observable wire diff**. `X-Request-ID` echoed back verbatim in response headers (confirmed `req-…-on`). CF NEL/report-to telemetry headers present. |
| 5 | `/user/recent-requests` audit | n/a | Blocked by 401 — provider split + 16-token alignment audit requires session JWT. |
| 6 | `data.freeinference.org/api/dashboard` | empty | Returned empty/non-JSON (`top_level_keys: []`) — data-plane telemetry endpoint not publicly reachable or requires auth. `/api/history?hours=2` also empty. |

## Confirmed contract updates vs estate doctrine

1. **New model in catalog**: `minimax-m3.1-flash` — not in estate models.yml yet. Candidate for pinax catalog regen.
2. **Embeddings route exists**: `/v1/embeddings` with `BAAI/bge-m3` (dim 1024) — estate has no embeddings consumer wired.
3. **Anthropic wire translator live** at `/anthropic/v1/messages` — usable for Claude-compatible clients, but **silent model fallback applies** (minimax-m3 → qwen3.6-35b). Never trust requested==served.
4. **User-agent doctrine**: site explicitly bans fake UAs; keep real UA on all FI traffic.
5. **Control plane is JWT-gated** — probes needing `/user/*` telemetry require `FI_SESSION_JWT` from browser DevTools.

## Gaps (need JWT or rerun)
- ULID chronometry from session JWT (sub/sid/jti Crockford decode)
- Provider split + 16-token cache-block alignment audit (needs `/user/recent-requests`)
- OpenInfra GPU/SGLang telemetry (endpoint returned empty — check `data.` host reachability)
