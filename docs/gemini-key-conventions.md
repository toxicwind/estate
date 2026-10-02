# Gemini key conventions (verified 2026-10-02)

Every statement here was produced by a live probe or `gcloud`, not by a config file's
own metadata. `config/.secrets.json` carries `metadata.EAP` flags and they are **wrong**;
treat this document as the authority.

## The only EAP project

| project | id | EAP | evidence |
|---|---|---|---|
| **gen-lang-client-0111199472** | 654595778272 | **yes** | all six keys return `status: completed` on `POST /v1beta/interactions` and run the full `tool_search_call → tool_search_result → thought → function_call` loop |
| flashy-squirrel | 991309044265 | no | its key 401s on interactions |
| gallery-effusion | 55739192275 | no | 401 |
| gassist-d31c8 | 989227872366 | no | 401 |
| yotube-161921 | 269278422746 | no | 401 |

EAP (Gemini "Tool Retrieval") is a **project entitlement**, not a per-key property. A key
from any of the other four projects is worthless for this regardless of its metadata.
That is why all four Gemini pools in `config/keypools.yaml` draw from the same six keys:
cross-project rotation is not available, only cross-key rotation within one project.

## Live keys

`/home/toxic/.secrets`, lines 61-66. All six are on gen-lang-client-0111199472.

| variable | gcloud display name | notes |
|---|---|---|
| `GEMINI_EAP_KEY_1` | Gemini API Key 4 | **this is the key GCP flagged as publicly exposed on 2026-09-23.** Revoked by GCP? No — still live. Rotate it. |
| `GEMINI_EAP_KEY_2` | Gemini API Key 3 | |
| `GEMINI_EAP_KEY_3` | Gemini API Key | |
| `GEMINI_EAP_KEY_4` | Tasker | |
| `GEMINI_EAP_KEY_5` | CachyOS | |
| `GEMINI_EAP_KEY_6` | Generative Language API Key | |

Removed 2026-10-02: `GEMINI_EAP_KEY_0` (revoked by GCP after the exposure),
`GEMINI_API_KEY*` (all 401), `GOOGLE_API_KEY` (a byte-duplicate of `GEMINI_API_KEY_4`,
which is also 401), and the two keys created on gassist-d31c8 / flashy-squirrel.

## Auth header

Google's native endpoint takes the key in the **`x-goog-api-key` header**, not
`Authorization: Bearer`. Sending a valid key as a bearer token 401s. This is encoded once
in `services/keypool/src/pool.ts`:

```ts
export function upstreamAuthHeader(upstream: string, secret: string): [string, string]
// .../openai suffix          -> ["Authorization", `Bearer ${secret}`]
// generativelanguage.google… -> ["x-goog-api-key", secret]
// otherwise                  -> ["Authorization", `Bearer ${secret}`]
```

It used to exist only in `probe()`, so a pool probed green and then 401'd on every real
request. `server.ts::forward` now calls the same helper.

## Interaction protocol rules (empirical)

- `function_result` requires the **snake_case** wire field `call_id`. The SDK's camelCase
  `callId` is rejected: `400 Unknown parameter 'callId' at 'input[0]'`.
- `function_result` also requires `previous_interaction_id` naming the interaction that
  issued the `function_call`. Without it:
  `400 Please ensure that function response turn comes immediately after a function call turn.`
- `defer_loading: true` is only valid when `tool_search` is also in the tools array.
- Only the Interactions API supports tool retrieval. `generateContent` does not.

Because OpenAI-shaped callers have no handle for `previous_interaction_id`, the keypool
threads it: every response carries `x-interaction-id`, and the caller echoes it back as
`x-previous-interaction-id`. Verified two-turn tool loop through
`POST /gemini-eap-interactions/v1/chat/completions`.

## Models available on the EAP project

From `GET /v1beta/models` on gen-lang-client. Every id below returns a chat completion
through the keypool except where noted.

- `gemini-flash-tool-retrieval` — **the only model that runs the tool_search loop**
- `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`
- `gemini-3.1-pro-preview`, `gemini-3-flash-preview`
- `gemini-2.5-flash`
- `gemini-2.5-pro` — listed upstream, but **404 through the interactions pool**; excluded
  from the roost catalog and from tau's provider model list.

`gemini-3-pro-preview` is not on this project at all (404).

## Routing

```
tau/omp  ──flock :25193──▶  provider "google" (keyless, auth none)
                             │  base_url http://127.0.0.1:25109/gemini-eap-interactions
                             ▼
                        keypool :25109
                             │  picks one of the six keys (round-robin/failover)
                             │  rewrites OpenAI body → Interactions body
                             ▼
              generativelanguage.googleapis.com/v1beta/interactions
```

Single source of truth for the model list is `ranch/flock/roost/src/data.ts`. It
generates, in order:

1. `roost/generated/providers.{json,go,rs}`
2. `proxy/src/roost_providers.rs` — via `bun scripts/sync-roost-providers.ts --write`
   (**easy to forget; flock will serve the previous catalog until you do**)
3. `~/.tau/models.yml` and `estate/config/tau/models.yml` — both written directly by
   `roost/scripts/build.ts`. Never hand-edit `config/tau/models.yml`; the next build
   overwrites it.

Rebuild order after touching `roost/src/data.ts`:

```bash
cd ranch/flock/roost && bun run build            # regen + sync to tau
cd ..                && bun scripts/sync-roost-providers.ts --write
cd proxy             && cargo build --release
cp target/release/flock /home/toxic/.flock/flock   # daemon runs this copy
```

## Secrets hygiene

- `/home/toxic/.secrets` is the only live credential store. `config/.secrets.json` was a
  generated index carrying every plaintext value; it and its `.super-bak-*` snapshot were
  both tracked on `origin/main` and are now gitignored (`ops/gitignore/layers/40-config-ownership.gitignore`)
  and untracked.
- `@google/genai` reads `GOOGLE_API_KEY` / `GEMINI_API_KEY` from the environment and
  **ignores an explicit `apiKey` constructor argument** when either is set. For probes use
  `env -u GOOGLE_API_KEY -u GEMINI_API_KEY`.
- `FLOCK_API_KEY` shares a value with `NVIDIA_API_KEY` in `.secrets`. flock clients must
  send `Authorization: Bearer $FLOCK_API_KEY`; the literal `local-sovereign` in
  `pitchfork.toml` is rejected by the proxy.
