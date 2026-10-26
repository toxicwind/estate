# vLLM sampling-parameter edge probe — 2026-10-26

**Scope:** all 5 kappa.jsonc providers (freeinference, hodos, nim, agele, atria) × per-model
sampling/edge cases, live-probed against `/v1/chat/completions` (DECLARED ≠ OBSERVED —
catalog claims never trusted; every cell below is an HTTP-observed result).

- Raw matrix: `/home/toxic/scratch/vllm-edge/results.jsonl` (full lanes) +
  `results-repass.jsonl` (429-repass, global 1-in-flight queue, full req/res bodies).
- Packet capture: `/home/toxic/scratch/vllm-edge/capture.pcapng` (tcpdump `-i any`,
  freeinference + :25193/:25100/:8000).
- Prior art: `2026-10-25/vllm-reasoning-recon.md` (reasoning knobs) — this probe extends to
  the vLLM sampling surface the kappa configs were missing.

## Findings

### F1 — kappa `nim` provider pointed at a retired, deleted route (FIXED)
- kappa.jsonc `nim` → `http://127.0.0.1:8000/v1` + `NIM_PROXY_KEY`: connection refused (no
  listener). mimetite `src/data.ts` records `nim-local` **deleted 2026-10-09** — the docker
  `nim-proxy` pass-through (80 ids, all identical to integrate.api.nvidia.com, zero unique)
  was removed for violating the port SSOT. The kappa provider was never regenerated → ghost.
- `NIM_PROXY_KEY` is absent from the secretsmith keyring (extraction returns nothing) and 401s
  on hodos :25193 — double-dead credential.
- **Fix applied (kappa.jsonc):** `nim` repointed to the live estate chain
  `http://127.0.0.1:25193/v1` + `{env:HODOS_API_KEY}` (hodos/rhodochrosite router; flock name
  retired). Verified live: `z-ai/glm-5.3-flash` → 200 stop, real completions
  (probe rows `hodos/z-ai/glm-5.3-flash/*`).

### F2 — hodos catalog lists a dead model (route-contract anomaly, OPEN)
- `nvidia/nemotron-3-super-120b-a12b` appears in `GET :25193/v1/models` (554 ids) but **404s
  on every completion** (15/15 probe rows + manual recheck). Catalog membership ≠ serving.
- First manual curl was a **false pass** — JSON error body parsed into `choices[0]` defaults.
  Lesson recorded: curl verification must assert HTTP status + `finish_reason`, not "has JSON".

### F3 — z-ai/glm-5.3-flash via hodos (NIM backend): strict validator (200s + 400s)
- 200: baseline, temperature 0.6/2.0, top_p 0.95, top_k 50, repetition_penalty 1.05,
  presence_penalty 0.5, frequency_penalty 0.5, seed, n=2, max_tokens=1.
- 400: **`min_p`** (vLLM-native param NOT accepted by this backend), **unknown body fields**
  (`kappa_edge_probe` rejected — NIM validates strictly, freeinference ignores junk), and
  `combo` (rejected because it contains `min_p`).
- Config consequence: per-model options for NIM-served models must NOT include `min_p` or any
  unvalidated field.

### F4 — freeinference sampling surface (4 models)
Observed matrix (status per model × case; 429s repassed via queued limiter):

| case | glm-5.3-flash | minimax-m3 | qwen3.6-35b | deepseek-v4-flash |
|---|---|---|---|---|
| baseline / t0 / t0.6 / t2.0 | 200 | 200 | 200 | 200 |
| top_p 0.95 | 200 | 200 | 200 | 200 |
| **top_p 1.5** | — | **400** | — | **400** |
| top_k 50 / 1 | 200 | 200 | 200 | 200 |
| min_p 0.05 | 200 | 200 | 200 | 200 |
| repetition_penalty 1.05/0.5 | 200 | 200 | 200 | 200 |
| presence/frequency_penalty | 200 | 200 | 200 | 200 |
| seed / stop / n=2 / max_tokens=1 | 200 | 200 | 200 | 200 |
| max_tokens 0 / -1 | 429→repass | 429→repass | 429→repass | **400** |
| thinking_token_budget 0/-1/-5/"100" | 429→repass | 429→repass | 429→repass | **200 (accepted+ignored)** |
| `thinking: false` (boolean) | 429→repass | **400** | 429→repass | **400** |
| `thinking: {type:"disabled"}` | 429→repass | 429→repass | 429→repass | **200** |
| reasoning_effort medium | 200 | 429→repass | 429→repass | 200 |
| **junk param** | **200 (ignored)** | 429→repass | 200 (ignored) | 200 (ignored) |
| all-combo | 200 | 429→repass | 200 | 200 |

- freeinference accepts out-of-range `temperature=2.0` (no server-side clamp) — clients own
  sanity. top_p > 1 IS validated (400).
- `thinking: false` boolean form **rejected by minimax-m3 AND deepseek-v4-flash** →
  confirms + extends the 2026-10-25 finding ("disabled-form still to re-verify" → verified:
  never send boolean `thinking`).
- deepseek accepts any `thinking_token_budget` including `-5` and `"100"` (string) → the knob
  is a silent no-op on deepseek; do not encode it as meaningful config.
- Unknown fields are ignored (200) — safe for kappa's providerOptions passthrough.

### F5 — 429 contention is production traffic, with process-level proof (pcap + ss)
- freeinference error string: `Too many concurrent requests (limit: 2)`. glm/minimax rows
  429-storm while qwen/deepseek pass — because production uses glm/minimax.
- `ss -tnp`: **hodos router (pid 1963751) holds 5 concurrent Cloudflare/freeinference
  connections** (estate/* routes fan out), live kappa session pid 2963521 on freeinference,
  plus tau/firefox on CF fronts. Probes ran 1-in-flight and still lost → observer effect at
  process granularity. pcapng: 6.9MB / 134s pre-existing outbound TLS stream to 104.21.92.204.

### F6 — agele (llama-swap :25100) is fully broken (OPEN)
- All 60 probes: **500 `upstream command exited prematurely`** (45) or **404 `no router for
  requested model`** (15) across fast/code/qwen-flash-256k/kimi-auto. Front door 200, exec
  lane dead — route-contract divergence, same shape as anomaly #5 (2026-10-23).

### F7 — hodos estate routes: OpenRouter credit starvation (OPEN, external)
- `estate/fast`: 15/15 **402 `Insufficient credits` (openrouter.ai)**.
- `estate/auto`: mixed 200/402 — the smart route lands on OpenRouter-backed models part of
  the time. estate "free" strategy is credit-starved in practice.

### F8 — atria: healthy + honest validation
- 14/15 probes 200 across the whole sampling surface (incl. temp 2.0, junk ignored, combo);
  single 400 is `max_tokens=0` with a clean bound message (`1..65536`). Model of good
  validator behavior.

### F9 — kappa-code drift: provider hardcodes vs per-model config vs mimetite (OPEN, refactor)
- `ProviderTransform.temperature/topP/topK` (packages/cli/src/provider/transform.ts:614-662)
  hardcode ID-substring tables (`minimax-m2`, `glm-4.6/4.7`, `kimi-k2`, ling…). **None match
  the estate's live model IDs** (minimax-m3, glm-5.3-flash, qwen3.6-35b, deepseek-v4-flash)
  → freeinference requests go out with NO sampling params at all; server defaults apply.
- The `deepseek-v4-flash → top_p 0.95` rule (transform.ts:644) fires only for providerID
  kappa/deepseek/opencode* — **not freeinference** → same model gets different params per
  provider, decided by hardcoded substrings.
- mimetite is the declared SSOT ("if it names a provider or a model id, it reads the
  mimetite; hand-maintained inventories are a bug") and already emits kappa artifacts
  (`~/.config/kappa/kappa-models.json`, Profile 2). The per-model fix: encode verified
  sampling options as per-model config (kappa.jsonc now; mimetite sampling facts +
  codegen as the permanent home), demote the ID tables to catalog fallbacks.

### F10 — `marketplace` config warning: fixed in source, stale binary (FIX IN FLIGHT)
- Warning `Unrecognized key: marketplace` on every kappa start. Fix exists:
  kappa-code `97db73668d` (2026-10-25 17:14) recognizes marketplace/marketplaces — but the
  deployed binary was built 2026-10-24 03:41. Redeploy in progress (green-blue: old binary
  stays runnable until new one verifies).

## Config changes applied
1. `~/.config/kappa/kappa.jsonc` (= dots repo) `nim` provider: :8000/NIM_PROXY_KEY →
   :25193/HODOS_API_KEY (F1).
2. freeinference per-model sampling options: added after repass completion (see F4 verdict).

## Follow-ups spawned
- F2: quarantine/prune `nvidia/nemotron-3-super-120b-a12b` in hodos serving set (mimetite
  live-discovery would have caught it — two-refresh prune).
- F6: agele/llama-swap repair (upstream crash + missing routes).
- F7: fund OpenRouter or re-pin estate routes to non-OpenRouter backends.
- F9: TDD refactor of ProviderTransform ID tables → config/catalog-driven (kappacode mirror
  rule applies; kappa.jsonc options already flow via providerOptions → request body).
- F10: pitchfork-managed kappa binary redeploy + version-pin.
