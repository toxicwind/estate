# FreeInference Upstream Proof — 2026-10-16

## Verdict: PASS — freeinference.org routes to real upstream

### 1. DNS Resolution (no /etc/hosts intercept)

`dig` and `dnsx` both resolve freeinference.org to Cloudflare IPs:

| Domain | IPs | Resolver |
|---|---|---|
| freeinference.org | 172.67.197.180, 104.21.92.204 | public DNS (Cloudflare 1.1.1.1) |
| staging.freeinference.org | same | Cloudflare |
| doc.freeinference.org | same | Cloudflare |

No /etc/hosts entry exists — resolution is purely authoritative DNS → Cloudflare CDN → upstream.

### 2. TLS / Certificates

All subdomains terminate on Cloudflare (proxied). SNI reveals:
- `doc.freeinference.org` → Furo docs (Sphinx-based)
- `staging.freeinference.org` → Next.js/React/Node.js app
- `status.freeinference.org` → Model status dashboard
- `agent-traces.freeinference.org` → "FreeInference Agentic Dataset"

### 3. API Proof (OpenAI-compatible shapes)

Endpoint: `https://freeinference.org/v1`
Auth: `X-API-Key: hyi-d…B-4` (real key, redacted)

| Test | Result |
|---|---|
| `/v1/models` | 200, 6 models returned |
| `/v1/chat/completions` (OpenAI shape) | 200, model: glm-5.3-flash |
| `/v1/messages` (Anthropic shape) | 200, model remapped to qwen3.6-35b |
| `/v1/embeddings` | 200, dimensions: 1024 (bge-m3) |
| Concurrent 2x same model | 1×200, 1×429 (global limit: 1 concurrent/key) |
| Concurrent 2x different models | 1×200, 1×429 (global limit) |

### 4. Models Found

| Model ID | API Name | Shape Support |
|---|---|---|
| glm-5.3-flash | glm-5.3-flash | chat/completions, messages |
| minimax-m3 | minimax-m3 | chat/completions |
| qwen3.6-35b | qwen3.6-35b | chat/completions, messages |
| diffusiongemma | diffusiongemma | ??? |
| deepseek-v4-flash | deepseek-v4-flash | chat/completions |
| bge-m3 | bge-m3 | embeddings |

### 5. Subdomain Surface

14 subdomains found via subfinder. 10/14 live:

- `agent-traces.freeinference.org` — Agentic Dataset
- `data.freeinference.org` — Open Data Hub
- `doc.freeinference.org` — Documentation (Furo)
- `doc.staging.freeinference.org` — Staging docs
- `internaldoc.freeinference.org` — internal docs (521?)
- `openinfra.freeinference.org` — Open Infra (Harvard MaDSys)
- `opendata.freeinference.org` — Open Data (mirror)
- `privacy.freeinference.org` — Privacy page
- `r2.freeinference.org` — R2 storage
- `status.freeinference.org` — Model status
- `status.staging.freeinference.org` — Staging status
- `staging.freeinference.org` — Main app (Next.js)
- `www.freeinference.org` — Redirect/landing (521)
- `www.privacy.freeinference.org` — Privacy subpage

### 6. Concurrency Conclusions

- freeinference enforces **ONE concurrent request per API key** (provider-side)
- The limit is global, not per-model
- UAs treated identically — pure arrival-order serialization
- `/v1/messages` silently remaps model field (glm → qwen3.6-35b)
- Do not trust `model` in `/v1/messages` response — verify payload

### 7. Evidence Artifacts

- Recon data: `/tmp/kilo/ferret-freeinf/` (dns.txt, subs.txt, hosts-live.txt, recon.json)
- Concurrency script: `estate/findings/prior-audits/freeinference-concurrency-recon.sh`
- API key from: `/home/toxic/.secrets` (FREEINFERENCE_API_KEY)

### 8. Security Note

- API key stored in `/home/toxic/.secrets` (keyring fallback)
- No hardcoded keys in nim-omnibus.sh (only commented placeholder)
- Backups: `/home/toxic/.secrets/2026-10-16-nim-keys.bak`
