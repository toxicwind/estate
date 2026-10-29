# 2026-10-26 — FreeInference Orthogonal Probe (Build 4b80416 recon)

Probe script: `/tmp/fi_orthogonal/probe.sh` · Raw outputs: `/tmp/fi_orthogonal/out/`
Session: `probe-20261026-083426Z` + reruns (`run2.log`, `run3.log`) · All HTTP observed live.
**UA doctrine applied**: all requests send a real Chrome browser UA (site bans fake/missing UAs).
**Host correction**: telemetry lives at `openinfra.freeinference.org` — `data.freeinference.org` is now an Open Data hub (datasets hub, no API). Script updated.

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
| 5 | `/user/recent-requests` audit | n/a | Blocked by 401 — provider split + 16-token alignment audit requires session JWT. `/user/api-keys/all` also 401 (155B error envelope). |
| 5b | `/public-stats` | 200 | **Unauthenticated usage stats reveal a 7th model: `diffusiongemma`** (60k reqs, small token count) — NOT in `/v1/models`. Plus an `other` bucket: **93B tokens / 752k requests from unlisted models**. Totals: 1.13T tokens across 492 accounts (87-day window), **cached_input_share 0.934**. Top products by tokens: Hermes Agent 155B, OpenCode 142B, pi 140B, Codex 117B, Claude Code 72B. Registrations: 2050 waiting / 1568 approved. Endpoint discovered by mining `/stats` page JS chunk → `"/public-stats"`. |
| 6 | `openinfra.freeinference.org/api/dashboard` + `/api/history?hours=2` | 200 | **UNAUTHENTICATED fleet telemetry** (dashboard 8.7KB + history 89.5KB, 60s grain). Dashboard: `fleet: healthy`, 4 nodes / 11 GPUs (7 online), 7 SGLang servers (5 online), 2.28GW total draw, avg 60.6°C. History: full per-GPU/per-server time series — see §Fleet. NOTE: `data.freeinference.org/api/*` now 404s; the OpenInfra API moved to the `openinfra.` subdomain. |

## Confirmed contract updates vs estate doctrine

1. **New model in catalog**: `minimax-m3.1-flash` — not in estate models.yml yet. Candidate for mimetite catalog regen.
2. **Embeddings route exists**: `/v1/embeddings` with `BAAI/bge-m3` (dim 1024) — estate has no embeddings consumer wired.
3. **Anthropic wire translator live** at `/anthropic/v1/messages` — usable for Claude-compatible clients, but **silent model fallback applies** (minimax-m3 → qwen3.6-35b). Never trust requested==served.
4. **User-agent doctrine**: site explicitly bans fake UAs; keep real UA on all FI traffic.
5. **Control plane is JWT-gated** — probes needing `/user/*` telemetry require `FI_SESSION_JWT` from browser DevTools.

## Full catalog (from models_openai.json — 3,205B, never trust doc labels)

| id | owned_by | quant | ctx | max_out | pricing in/out per-M | modalities | sampling params | features |
|---|---|---|---|---|---|---|---|---|
| glm-5.3-flash | zai | fp8 | 1M | 131k | 0.3/1.0, cache-read 0.06 | text,image | max_tokens, reasoning_effort, stop, stream, temperature, thinking, tool_stream, top_p | tools, json_mode, structured_outputs |
| minimax-m3 | minimax | bf16 | 1.05M | 131k | 0.5/2.0, cache-read 0.3 | text,image,video | (no reasoning_effort) + thinking | tools, json_mode, structured_outputs |
| qwen3.6-35b | vllm | mixed | 262k | **8k** | 0.08/0.28, cache-read 0.01 | text,image,video | no thinking/reasoning params at all | tools, json_mode, structured_outputs |
| deepseek-v4-flash | sglang | none | 1M | **393k** | 0.44/1.32, cache-read 0.014 | text | reasoning_effort + thinking | tools, json_mode, structured_outputs |
| minimax-m3.1-flash | minimax | bf16 | 1M | 256k | 0.2/0.8, cache-read 0.02, **cache-write 0.2** | text,image | max_tokens, temperature, top_p only | tools only (no json_mode) |
| bge-m3 | sglang | fp16 | 8k | — | 0/0 (free) | text→embedding | none | embeddings |

Notable: `qwen3.6-35b` max_output is only **8k tokens** — reasoning-budget starvation risk is 3× tighter than assumed (estate doctrine says max_tokens ≥ 2500 with reasoning on; qwen has no reasoning params but 8k ceiling still bites long outputs). `deepseek-v4-flash` has the largest output ceiling (393k). Cache-write is only billed on minimax-m3.1-flash. All `created` timestamps identical (1792967825 = 2026-10-25T16:37:05Z — catalog regenerated yesterday, epoch-0 in Anthropic schema is a placeholder).

## Fleet telemetry (openinfra.freeinference.org — UNAUTHENTICATED, 60s grain, ~2h window)

**FreeInference's entire infrastructure control plane is readable without any auth**:
- `GET https://openinfra.freeinference.org/api/dashboard` — live KPIs (fleet health, node/GPU online counts, avg util/temp/power, running/queued reqs, per-GPU and per-server latest rows)
- `GET https://openinfra.freeinference.org/api/history?hours=N` — 60s-grain time series (`gpu[]`, `sglang[]`, `cpu[]`)
- `https://data.freeinference.org` is now a static **Open Data hub**: HuggingFace datasets (`harvardMadsys/chutes_metadata`, `freeinference_agentic_trace`), charts CSVs, arxiv 2608.13573; bulk hourly rollups (≤30d) are password-protected via email request.

Contents at probe time (fleet: **healthy**, 4 nodes / 11 GPUs / 7 online, 7 SGLang servers / 5 online, 2,277W total, avg 60.6°C, 3 running reqs, queue 0):

**Nodes:** `h200a` (4× H200), `rtx6000b` (2× RTX 6000 Blackwell), `spark2` (NVIDIA Spark — DCGM metrics partial: `memory_pct`/tensor/dram/pcie all `null`).

**Server↔GPU mapping (provenance ground truth):**
| SGLang server | Node | Observed |
|---|---|---|
| `h200a-glm53-flash` | h200a | up to 535 tps, TTFT 0.44–1.23s, cache_hit 73–97%, spec_accept_len 2.5–3.7 |
| `h200a-replica-a` | h200a | **hicache host FULL: 25.28GB/25.28GB** across the whole window, cached-prefill 25.7k tps, cache_hit 88–98%, spec_accept_len up to 4.3 |
| `rtx6000b-qwen36` | rtx6000b | ~214–372 tps, TTFT 0.06–0.41s, cache_hit 7–20% |
| `rtx6000b-bge-m3` | rtx6000b | idle (embeddings only) |
| `spark2-qwen36-nvfp4` | spark2 | idle, TTFT ~0.96s, cache_hit ~41–45% |

**Anomalies in telemetry:**
- **rtx6000b:0 thermal pressure: median 84°C, max 86°C** at ~300W — sustained near-throttle; spikes to 81–83°C seen in later windows.
- **H200 pair load-balances unevenly**: `:0/:1` vs `:2/:3` swap between 100% and 0% util across the window (replicas alternate), all 4 at ~98% mem (weights resident).
- **No minimax backend**: `minimax-m3` / `minimax-m3.1-flash` have no SGLang server in the window — consistent with the §3 translator silently serving qwen3.6-35b for a minimax request. **Catalog advertises models the fleet doesn't serve.**
- `spec_accept_length` 2.5–4.3 on glm/qwen — speculative decoding active, modest acceptance.
- Queue depths ~0, `http_error_per_min` 0 — no saturation at snapshot time.
- Dashboard `kpis` counts 11 GPUs / 7 servers while history shows 7 GPUs / 5 servers — **dashboard includes offline/deregistered hardware in totals** (nodes_online 3 of 4, gpus_online 7 of 11).

**Doctrine implication:** the ROUTE CONTRACT anomaly class (front door alive, exec lane dead) now has a third leg: **fleet telemetry is the best "is the backend really there" signal** — `openinfra.freeinference.org/api/dashboard` + `/api/history` prove which models have live backends regardless of what the catalog advertises. Poll it before trusting any model in the catalog. Also: `GET /public-stats` is the model-inventory supersource (reveals unlisted models like `diffusiongemma` and the unlisted-`other` traffic bucket).

---

## 2026-10-28 re-verification vs "Master Forensic Dossier: FreeInference (Harvard SEAS) Gateway & Account Topology Analysis"

The dossier was treated as unverified claims (DECLARED ≠ OBSERVED, estate doctrine). Every claim below was probed live on 2026-10-28 with a real Chrome browser UA (site bans fake UAs); key `hyi-u5H98c...` from `~/.tau/freeinference.key` == secretsmith `FREEINFERENCE_API_KEY`.

| # | Dossier claim | Observed live (2026-10-28) | Verdict |
|---|---|---|---|
| 1 | Harvard SEAS / MaDSys runs FreeInference; JWT `role:"pro"`, UID `01M2CZNVZ3DY4G10AE7PTT71EE`; build `d55dab6` (2026-10-27) doubled pro ceiling $80→$160/day | Juncheng Yang confirmed Harvard SEAS Asst. Prof.; freeinference.org team page = Harvard MaDSys. Pro quota $160/day confirmed: dashboard export "Daily quota remaining $97.21 of $160.00", resets Oct 29 00:00 GMT; keypool `GET http://127.0.0.1:25109/quota` → `limitCents:16000`. JWT role claim not observable without session JWT; build hash internal. | PARTIAL — org + $160 quota real; role:pro/d55dab6 internal/unobservable |
| 2 | `/v1/models` OpenAI schema | 200, 4 models keyed: `glm-5.3-flash`, `qwen3.6-35b`, `deepseek-v4-flash`, `bge-m3` | VERIFIED |
| 3 | `Anthropic-Version` flips `/v1/models` to Anthropic schema | 200; 3 models (`bge-m3` hidden), `created_at` epoch-0 placeholders | VERIFIED |
| 4 | `/public-stats` unauth model-inventory supersource | 200; daily stats; `diffusiongemma` only in `other` bucket | VERIFIED |
| 5 | `openinfra.freeinference.org` `/api/dashboard` + `/api/history?hours=N` unauth fleet telemetry | 200; CORS `Allow-Origin: *`; GPU/SGLang/KPIs incl. NVLink/pcie bytes, `cache_hit_rate`, `spec_accept` | VERIFIED |
| 6 | `data.freeinference.org/api/dashboard` | 404 — host is now static Open Data hub (HF datasets `harvardMadsys/*`) | VERIFIED (negative) |
| 7 | `status.freeinference.org` | 200 | VERIFIED |
| 8 | `doc.freeinference.org/api_headers` | 200 (Sphinx docs); UA policy, `X-Reasoning-Passthrough`, `X-Session-ID`, `X-Request-ID`, `X-API-Key` documented | VERIFIED |
| 9 | `X-API-Key` accepts raw `hyi-` key without `Bearer` prefix | Works (200 on `/v1/models`, `/v1/chat/completions`, `GET /v1/batches`) — equivalent to Bearer auth | VERIFIED |
| 10 | `X-Reasoning-Passthrough: false` strips `reasoning_content` | VERIFIED behaviorally: present default/`true`, absent with `false` | VERIFIED |
| 11 | `X-Request-ID` echoed back | VERIFIED in response headers | VERIFIED |
| 12 | `X-Session-ID` sticky routing to SGLang worker | Header accepted; **no observable echo** — sticky routing not directly proven | NOT OBSERVED |
| 13 | `POST /v1/batches` inline JSON up to 32 MiB, 50k requests, auto-retry ×8, quota rollover at 00:00 UTC | **Route exists but role-gated: `403 "Creating batches requires the 'internal' role or higher"`**. `GET /v1/batches` → 200 `{"data":[]}` | REFUTED for pro account |
| 14 | K-anonymity: shell commands logged & sanitized into `harvardMadsys/freeinference_agentic_trace` | Dataset EXISTS on HF (2.51M rows, updated ~9 days ago). "Terminal/shell command AST structures" scope not independently verifiable from this box | DATASET VERIFIED; content scope unverified |
| 15 | quota $80→$160 reflected in estate config | mimetite `src/data.ts`: `dailyBudgetCents:16000`, `quotaSource http://127.0.0.1:25109/quota`; keypool returns 16000 limit; `.tau/models.yml` freeinference provider present | VERIFIED in config |

### Estate config surfaces already supporting freeinference (no changes required)

- **mimetite** (`pens/geode/products/mimetite/src/data.ts`): provider `freeinference` — `baseUrl https://freeinference.org/v1`, `keyEnv FREEINFERENCE_API_KEY`, adapter `static`, 4 model cards (`glm-5.3-flash`, `minimax-m3.1-flash`, `qwen3.6-35b`, `deepseek-v4-flash`), `contextLengths`, UA + retryCeiling 3, `maxConcurrency 16` (architect order: no concurrency cap, 429 = local shed), regenerated into `tau-models.yml`, `providers.json/.go/.rs`, `kappa-models.json` via `bun run build` (codegen sync test diffs byte-for-byte).
- **rhodochrosite proxy** (Rust, `:25193`): `pgate` caps `freeinference` at 2 concurrent upstream slots (tests assert limit=2); `DEFAULT_UPSTREAM_UA` forwarded to CF-fronted upstream; `base_url https://freeinference.org/v1`, `key_env FREEINFERENCE_API_KEY`; key env loaded via `secretsmith env` + `set -a` in `serve.sh`.
- **tau**: `roost.ts` `TAU_PROVIDER_POLICY.freeinference` (defaultModel `qwen3.6-35b`, discovery label FreeInference, kindApis); `~/.tau/models.yml` freeinference provider entry.
- **Anthropic `/v1/messages`**: route exists at provider level; silent model fallback observed (`minimax-m3` → served `qwen3.6-35b`), never trust requested==served.

### Not supported — do not build on

- `POST /v1/batches`: internal-role-only for this account (403). Any batch-orchestrator tooling must assume it is unavailable unless the key is upgraded to an internal role. `GET /v1/batches` (list) is available but returns empty for this account.
- `X-Session-ID` sticky routing: header passes through but no sticky-routing behavior observed; do not code to >99% cache-hit claims.

### Conclusion

The dossier's infrastructure (Harvard MaDSys, `openinfra` telemetry, `status`, `doc.freeinference.org/api_headers`, `/public-stats`) is real and already supported by estate config. The **batch pipeline (Section 6) is not actionable** on the current pro key — the endpoint is role-gated. The quota doubling ($80→$160) is real and already wired (`dailyBudgetCents:16000`, keypool `/quota`).
