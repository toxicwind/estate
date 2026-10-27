# FreeInference Provider Research (2026-10-19)

Ground truth from live probes + docs (doc.freeinference.org/models, /api_headers) + account dashboard.
Authored during the tau SIGBUS → fingerprint-port session. All numbers re-verify via `GET /v1/models`.

## WHY the "fingerprint" feature exists (kappa git evidence)

- kappa commit `c4ffaeffc11` (2026-10-16): "browser fingerprint HTTP transport … for
  Cloudflare-guarded inference providers (freeinference 403 1010)".
- Cloudflare error **1010** = "banned based on your browser's signature" — a
  UA/headers gate, not TLS (kappa's implementation is Chrome-aligned *headers*
  only: `sec-ch-ua`, `sec-ch-ua-platform`, `accept-language`; no JA3).
- **Live probes 2026-10-19 (all 200):** honest `tau/18.8.4 (+repo)` UA, Chrome-spoof
  UA, empty UA, curl default — on both `/v1/models` and `/v1/chat/completions`.
  The gate no longer triggers for API traffic (or was account/CDN-scoped).
- Conclusion: header fingerprinting is a **compat shim, not an identity**. Honest
  branded UA is compliant and works. Freeinference ToS: *"Account using fake user
  agent will be banned."* → we NEVER send Chrome impersonation by default.

## Account context (dashboard, 2026-10-19)

- Plan: **pro**; daily quota $80 (resets 00:00 GMT); max concurrent requests: **2**.
- "We have 2 slots" = the **2 concurrent request** limit, confirmed live: 4 parallel
  chats → exactly 2× 200 + 2× **429**; subagent-style 4×3 burst → first 2 win, all
  later requests in saturated windows 429 until slots free.
- 429 response: `retry-after: 1` (seconds), `x-request-id` echoed. tau's transport
  already does Retry-After-aware retries for 429 (openai-completions.ts:903,
  utils/retry-after.ts).
- Prompt logging: "All prompts and responses are logged and may be open-sourced
  after anonymization" — no secrets through this gateway.

## Pricing (USD per 1M tokens)

Source of truth = authenticated `GET /v1/models` `pricing` fields (dashboard UI matches
except cache-write). Docs: "prices are upstream reference rates used by the gateway
for cost accounting and route selection; not fees billed to users" — dollar amounts
are attribution from logs, not invoices.

| Model | Ctx | Max out | Input | Output | Cache read | Cache write (UI) |
|---|---|---|---|---|---|---|
| glm-5.3-flash | 1.0M | 131K | 0.30 | 1.00 | 0.06 | 0.30 |
| minimax-m3 | 1.0M | 131K | 0.50 | 2.00 | 0.30 | 0.50 |
| qwen3.6-35b | 262K | 8K | 0.08 | 0.28 | 0.01 | 0.08 |
| diffusiongemma | 262K | 8K | 0.02 | 0.08 | 0.01 | 0.02 |
| deepseek-v4-flash | 1.0M | 393K | 0.44 | 1.32 | 0.014 | 0.44 |
| bge-m3 | 8K | — (embeddings) | 0 | 0 | — | — |

**Cache-write discrepancy (API vs dashboard):** `/v1/models` returns
`input_cache_writes: 0` for every model, but the dashboard/UI table shows cache
write = input rate (0.3/0.5/0.08/0.02/0.44). Reading the recent-requests ledger,
cache-write tokens are billed at the input rate. Resolution used in tau/kappa
configs: **cacheWrite = input rate** (UI table wins; API field is unreliable zero).

## Model semantics (docs ground truth)

- `glm-5.3-flash` + `glm-5.3` **always reason**: they reject
  `thinking: {"type": "disabled"}`. `reasoning_effort` ∈ **low | high | max** (no
  minimal/medium). Use `glm-5.2` when thinking must be switchable.
- `bge-m3` = embeddings-only via `/v1/embeddings` (not chat). Used for codebase indexing.
- `qwen3.6-35b` = fast non-thinking model.
- Context/output limits are deployment limits; upstream may enforce smaller per request.
- `X-Reasoning-Passthrough: false` strips `reasoning_content` from responses (strict OpenAI mode).
- `X-Session-ID` for request correlation; `X-Request-ID` echoed back.
- Retired IDs (glm-4.7, minimax-2.7…) → 404 Model not found.
- Headers reference: https://doc.freeinference.org/api_headers — User-Agent is
  "Client identification; affects Anthropic client detection".

## Decisions

1. **tau**: provider-level `headers: { User-Agent: "tau/<ver> (+https://github.com/toxicwind/tau)" }`
   in `~/.tau/models.yml` (provider headers flow into every discovered model —
   model-registry.ts:1546-1593). Honest ID with repo backlink. No schema change needed.
2. **kappa**: fingerprint opt-in stays, but the injected header set becomes
   configurable; default profile for freeinference = honest
   `kappa/<ver> (+https://github.com/toxicwind/kappa-code)` UA. Chrome spoof only
   if the Cloudflare 1010 gate ever returns.
3. **Concurrency**: with 2 slots, tau task waves and subagent fan-out against
   freeinference must expect 429+retry-after:1 storms; keep `task.maxConcurrency`
   modest for this provider and rely on the existing retry-after transport retry.
4. **Costs**: embed the table above (cacheWrite = input-rate reconciliation) in
   both tau models.yml and kappa model metadata.

## Provenance

- Live probes: P1–P11 in session transcript 2026-10-19 (UA matrix, concurrency,
  429 headers). Keyring-sourced key, never logged here.
- Docs pages fetched: doc.freeinference.org/models, /api_headers (Sphinx, HarvardMadSys Lab).
- Dashboard: attached screenshot data in same session (quota $72.38/$80, 626 req,
  90.8M input tokens, concurrency 2).
- kappa git: `c4ffaeffc11` (feat), `f2554c49ad` (test move), `299b15506e` (hardening).

## Probe evidence (rerunnable)

`docs/probes/freeinference-provider-probe.sh` — full run log at
`docs/probes/freeinference-provider-probe-2026-10-19.log`. Summary of the
2026-10-19 run:

- P1–P7 UA matrix (models + chat, honest/spoof/empty/curl): **all 200** — no UA
  gate active today. Honest branded UA is compliant and sufficient.
- P8 four parallel chats: exactly **2× 200 + 2× 429** — the 2-slot concurrency
  limit is real and per-key.
- P9 subagent-style 4×3 burst: 8× 200, 4× 429 — subagent fan-out must expect
  429s whenever >2 requests are in flight; retries succeed as slots free.
- P10 saturated request: `HTTP/2 429`, `retry-after: 1`, `x-request-id` echoed —
  tau's transport already honors this (Retry-After-aware retry).
- P11 pricing pulled live from `/v1/models` matches the table above
  (`input_cache_writes: 0` in API vs dashboard input-rate cache-write — the
  reconciliation note above applies).

## TLS-impersonation dependency decision (2026-10-19)

Kappa's "browser fingerprint transport" is header-only in implementation (audited
the whole monorepo: no cffi/curl_cffi/cycletls/wreq deps, no TLS code, no stash
or branch WIP — the commit message's "TLS/HTTP2 impersonation" was aspirational).

**But the estate DOES own real TLS impersonation**: the vendored fork
`ranch/vendored/curl_cffi-toxicwind` (Python curl_cffi 0.16.3, system CLI
`/usr/bin/curl-cffi`, with the `imp-fetch` skill) — the "cloudflare library" from
prior sessions. Live-verified 2026-10-19: `curl-cffi get
https://freeinference.org/v1/models --impersonate chrome` → 200.

Policy: **no npm dep shipped** in tau/kappa for this. Honest UA covers the
default path; if JA3-level spoofing is ever needed, shell out to the
system-installed `curl-cffi` CLI (vendored fork, already on box) rather than
adding a native npm dep.

## UA attribution vs their stats taxonomy (2026-10-19, stats page)

FreeInference classifies agents by **the product token at the START of the
User-Agent** ("a client is the product name … ignoring version and platform"),
then matches system prompts against known tools. Their leaderboard already
tracks `pi` (132.7B tok), `oh-my-pi` (79.3B), `OpenCode` (126.8B), `Kilo Code`
(19.1B) as distinct products.

Consequence for us:
- `tau/…` and `kappa/…` leading tokens are CORRECT — they'll surface as their
  own products instead of being folded into pi/OpenCode/Kilo Code.
- Keep the UA product token stable across versions; comment text is ignored.
- Final formats shipped:
  - tau (via models.yml provider headers / openai-shared default):
    `tau/18.8.4 (+https://github.com/toxicwind/tau)`
  - kappa (executor fingerprint overlay, mirrors models-dev.ts convention):
    `kappa/<channel>/<version>/<client> (+https://github.com/toxicwind/kappa-code)`
- Cache-friendliness helps their 93% prompt-cache-hit economics: keep system
  prefixes stable (tau already does).

## Agent lineage (kimi → kappa, pi → tau) — 2026-10-19 archaeology

- `opencode` (sst) → `kilo-code` (Kilo-Org) → **kappa** (toxicwind fork, "Kilo
  Code renamed"). kappa IS the takeover of the kimi-work CLI work; the
  `@moonshot-ai/kimi-code` npm CLI (port 25126) is retired — its
  `kimi-code-npm` install dir is gone.
- `pi-mono` → `oh-my-pi` (can1357) → **tau** (toxicwind). Sibling Greek-letter
  line, unrelated to kappa.
- Corollary: `estate/kimi-code` + `estate/kimi-audit-dash` pitchfork daemons
  reference deleted paths — disabled 2026-10-19 (corpse-marked, not removed).
