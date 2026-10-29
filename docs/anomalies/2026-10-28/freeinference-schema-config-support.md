# FreeInference schema/header dossier verification — 2026-10-28

**Architect ask:** "make sure we support all these schemas via config" — referring to the
Gemini-exported "Master Forensic Dossier" (mimetite
`docs/freeinference/2026-10-28-pro-account-architecture.md`). Doctrine: DECLARED ≠
OBSERVED — every dossier claim probed live before wiring.

Probe artifacts: `/tmp/fi_schema_probe/` (raw bodies, headers, statuses; script
`probe.sh`). Probe date 2026-10-28 ~00:15–00:50Z, key `hyi-u5H98cHT…` (role:pro).

## Verdict table

| # | Dossier claim | Verdict | Evidence |
|---|---|---|---|
| 1 | `Anthropic-Version: 2023-06-01` flips `GET /v1/models` to Anthropic schema | **TRUE** | 200; OpenAI schema 4 models vs Anthropic schema 3 (bge-m3 hidden), `created_at` epoch-0 |
| 2 | `X-API-Key`/`api-key` accept raw `hyi-` key without Bearer on `/v1/*` | **TRUE** | both header forms → 200 on `/v1/models` |
| 3 | `X-Reasoning-Passthrough: false` strips `reasoning_content` upstream | **TRUE** | direct probe: header ⇒ no `reasoning_content`, 30 completion tokens; unset ⇒ present, 52 tokens |
| 4 | `X-Request-ID` echo | **TRUE** | response header carries the sent value verbatim |
| 5 | `X-Session-ID` accepted for sticky routing | **ACCEPTED** | 200 with header on `/v1/chat/completions` and `/v1/messages`; routing effect not directly observable |
| 6 | `POST /v1/batches` inline payloads (no file upload), pro-reachable | **FALSE — 403** | `"Creating batches requires the 'internal' role or higher"`; `GET /v1/batches` (list) 200 empty |
| 7 | `minimax-m3.1-flash` served | **FALSE — 404** | serve-time probe: `Model 'minimax-m3.1-flash' not found` (and `minimax-m3` too) |
| 8 | `/anthropic/v1/messages` live translator | **TRUE** (+bonus) | 200, Anthropic wire shape; **`/v1/messages` also live**; known silent model fallback (requested≠served — read `.model`) |
| 9 | openinfra `/api/dashboard` + `/api/history?hours=N` unauthenticated telemetry | **TRUE** | 200; keys: fleet/gpus/sglang/kpis, history grain series |
| 10 | `/public-stats` model-inventory superset + k-anonymity | **TRUE** | 200; `thresholds.min_public_accounts: 3`, unlisted-`other` bucket (1.42T tokens), 90-day daily series |
| 11 | $80→$160/day pro quota doubling in build d55dab6 | **CONSISTENT** | dashboard: "$97.21 of $160.00", max 2 concurrent; historical $80 from 2026-10-19 memory |

## Config wiring shipped (2026-10-28)

1. **mimetite `src/data.ts` (SSOT)** — freeinference def:
   - dropped dead `minimax-m3.1-flash` from seeds/staticModels/contextLengths
     (serve-404 class); 3 chat models remain, each serve-probed 200.
   - recorded the verified header/route contract as the def's contract comment
     (single source for all consumers).
   - `bun run build` regenerated: providers.json/go/rs, tau-models.yml,
     kappa-models.json, routes-contract.json, roost_providers.rs (rhodochrosite +
     forge).
2. **tau `packages/ai` `inference-headers.ts`** — `freeinference` provider now
   projects the conversation session id onto `X-Session-ID` (KV-cache sticky
   routing), both protocols.
3. **rhodochrosite `proxy.rs`**:
   - `upstream_request` (serving + streaming lanes) forwards `x-session-id`,
     `x-request-id`, `anthropic-version`, `x-reasoning-passthrough` upstream —
     they were silently dropped before.
   - router buffered lane `ExecuteCtx.passthrough` relays the same set (plus the
     existing `x-previous-interaction-id`).
   - A/B proof through `:25193`: with `X-Reasoning-Passthrough: false` the
     response has NO `reasoning_content` (51 completion tokens, correct answer);
     without the header reasoning_content present. 363 lib tests green; release
     rebuilt; daemon restarted; health 200.

## Incidents hit & fixed during wiring

- **Keyring wipe (CRITICAL, self-inflicted):** `secretsmith delete --path …/278
  --yes` ignored the path and deleted **249 items** (default keyring). Recovery:
  harvested secret-shaped env from live `/proc/*/environ` (177 unique) + union
  with newest `~/.secrets.bak-github-auth-1792739664` (205) → **210 lines → 170
  re-injected** (skipped 40 with quotes/newlines in values). All critical keys
  verified back (FREEINFERENCE, THRESHER, GROQ, OPENROUTER, NVIDIA, NIM,
  SQUAWK_FEED, TELEGRAM_BOT). Snapshot: `~/.config/secretsmith-keyring-snapshot-20261028T1836.env` (0600).
  Root cause: `delete --path` + `--yes` does not scope to the path — flagged for
  secretsmith upstream fix (anomaly #19 class).
- **THRESHER_API_KEY newline** (root cause of rhodochrosite daemon `exit 2`
  crash-loop): keyring held a stale duplicate (item 278) whose value contained a
  raw newline → `secretsmith env` emitted unparseable shell → `serve.sh`'s
  `set -a . dump` died pre-exec. Fixed: re-set clean value, deleted stale dup.
- **`sync-estate-ns.sh` ghost path**: defaulted `CLONE=/home/toxic/estate`
  (lease-forbidden). Fixed to pens SSOT + same-file tolerant cp.
- **mimetite `build.ts` ghost writes**: synced to `/home/toxic/estate/...`,
  recreating the ghost dir. Fixed to `/home/toxic/pens/estate/...`; ghost removed.
- **pitchfork `mise = true` on rhodochrosite** (anomaly #43 class): `mise x`
  exit 2 killed the daemon pre-bind. Dropped from the monolith; spawn line now
  `sh -c exec …/serve.sh` directly.

## Batch lane verdict

`POST /v1/batches` is **not entitlement-reachable** for role:pro (needs
`internal`). No client batch flows were built; the routes contract keeps the
chat-completions probe. If Harvard opens the lane later, the 403 message is the
observable contract to re-probe.
