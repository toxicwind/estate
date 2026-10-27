# Upstream `/v1/models` Discovery — provider catalog & per-endpoint finder

Reference for the estate's OpenAI-compatible model surface: how to find each
upstream provider's `/v1/models`, what vision-capable models each exposes, and
how to dip a screenshot through them for agent-display (`:99`) verification.

Source of truth: the AST of the rhodochrosite gateway at
`ranch/rhodochrosite/proxy/src/mimetite_providers.rs` (the canonical provider catalog) and
`~/.rhodochrosite/nim-data/config.json` (the live 9-provider federation).

## 1. The upstream provider catalog (from `mimetite_providers.rs`)

Each upstream is an OpenAI-compatible endpoint. Its model list lives at
`<base_url> + models_path`, defaulting to `<base_url>/models` **or** `<base_url>/v1/models`
depending on whether `base_url` already ends in `/v1`.

| provider          | base_url                              | model-list URL         | key env                 |
| ----------------- | ------------------------------------- | ---------------------- | ----------------------- |
| nvidia            | `https://integrate.api.nvidia.com/v1` | `.../v1/models`        | `NVIDIA_API_KEY`        |
| groq              | `https://api.groq.com/openai/v1`      | `.../openai/v1/models` | `GROQ_API_KEY`          |
| together          | `https://api.together.xyz/v1`         | `.../v1/models`        | `TOGETHER_API_KEY`      |
| cerebras          | `https://api.cerebras.ai/v1`          | `.../v1/models`        | `CEREBRAS_API_KEY`      |
| openai            | `https://api.openai.com/v1`           | `.../v1/models`        | `OPENAI_API_KEY`        |
| freeinference     | `https://freeinference.org/v1`        | `.../v1/models`        | `FREEINFERENCE_API_KEY` |
| moonshot          | `https://api.moonshot.ai/v1`          | `.../v1/models`        | (moonshot key)          |
| bitdeer           | `https://api-inference.bitdeer.ai/v1` | `.../v1/models`        | (bitdeer key)           |
| deepseek          | `https://api.deepseek.com`            | `/v1/models`           | (deepseek key)          |
| wandb             | `https://api.inference.wandb.ai/v1`   | `.../v1/models`        | (wandb key)             |
| kimi-auto (shim)  | `http://127.0.0.1:25153/v1`           | `.../v1/models`        | (local shim)            |
| omniroute (local) | `http://127.0.0.1:20130/v1`           | `.../v1/models`        | (local gateway)         |

Plus the live federation in `~/.rhodochrosite/nim-data/config.json` (9 providers): nvidia,
groq, together, cerebras, github (`https://models.github.ai/inference`), openai,
siliconflow (`https://api.siliconflow.com/v1`), **freeinference**, and a local
google/Gemini-EAP socket at `127.0.0.1:25109`.

## 2. The rhodochrosite gateway (`:25193`) — single federated `/v1/models`

The gateway proxies all of the above behind ONE endpoint:

```
GET http://127.0.0.1:25193/v1/models
Authorization: Bearer <proxy-api-key>
```

The proxy key is in `~/.rhodochrosite/nim-data/config.json` (the federation's own
`Authorization` token, distinct from the per-provider keys). A missing/invalid
key returns `{"error":{"code":"unauthorized",...}}` (observed 2026-10-22).

## 3. Vision-capable models (for agent-display screenshot audits)

From the NIM catalog (85 models) the screenshot-aware models are:

- `meta/llama-3.2-11b-vision-instruct` (NIM / all federated providers)
- `meta/llama-3.2-90b-vision-instruct`
- `microsoft/phi-3-vision-128k-instruct`
- `nvidia/nemotron-3.5-super-vl-120b-a12b`
- `google/gemma-3-12b-it` / `google/gemma-3-4b-it`

From freeinference (6 models): `glm-5.3-flash`, `qwen3.6-35b`, `minimax-m3`
are multimodal-capable; `deepseek-v4-flash` and `diffusiongemma` are not reliable
vision. `google/gemini-*` (local EAP `:25109`) is strongly vision-capable.

## 4. Live dip (verified 2026-10-22)

Benchmark on the 4K `:99` grid screenshot (`/home/toxic/disp_grid.png`,
downscaled to 1100px), question = "how many apps + grid positions + colors"
(ground truth: 4 apps, 2×2, RustDesk top-left / Chrome top-right / 2 terminals).

| provider            | model                                    | vision  | latency | screenshot result                                                                             | verdict            |
| ------------------- | ---------------------------------------- | :-----: | ------: | --------------------------------------------------------------------------------------------- | ------------------ |
| freeinference       | `qwen3.6-35b`                            |   yes   |  ~665ms | "4 apps in 2x2: top-left (TeamViewer), top-right Chrome, bottom terminals; pink/blue accents" | ★ accurate + fast  |
| freeinference       | `glm-5.3-flash`                          |   yes   | ~5872ms | "Four"                                                                                        | correct, slow      |
| nvidia (+federated) | `meta/llama-3.2-11b-vision-instruct`     |   yes   |       ─ | (subagent benchmark)                                                                          | see ranch/         |
| nvidia              | `meta/llama-3.2-90b-vision-instruct`     |   yes   |       ─ | ─                                                                                             | see ranch/         |
| nvidia              | `microsoft/phi-3-vision-128k-instruct`   |   yes   |       ─ | ─                                                                                             | see ranch/         |
| nvidia              | `nvidia/nemotron-3.5-super-vl-120b-a12b` |   yes   |       ─ | ─                                                                                             | see ranch/         |
| nvidia              | `google/gemma-3-12b-it`                  |   yes   |       ─ | ─                                                                                             | see ranch/         |
| freeinference       | `minimax-m3`                             | partial |       ─ | ─                                                                                             | see ranch/         |
| google (local EAP)  | `models/gemini-3.8-flash`                |   yes   |       ─ | ─                                                                                             | see ranch/         |
| nvidia              | `nvidia/llama-3.1-nemotron-70b-instruct` |   no    |       ─ | (negative control)                                                                            | should fail vision |

Full ≥10-model table with timings lives in the `ranch/` vision project. Winner so
far: **`qwen3.6-35b` (freeinference)** — accurate grid/app/color read at ~665ms.

## 5. Use

```bash
# list a provider's models
curl -s <base_url>/v1/models -H "Authorization: Bearer $NVIDIA_API_KEY"

# federated list through the gateway
curl -s http://127.0.0.1:25193/v1/models -H "Authorization: Bearer <proxy-key>"

# vision check a screenshot (freeinference)
#  content = [{type:image_url, image_url:{url:"data:image/png;base64,..."}}]
curl -s https://freeinference.org/v1/chat/completions \
  -H "Authorization: Bearer $FREEINFERENCE_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"glm-5.3-flash","messages":[{"role":"user","content":[{type text, ...},{type image_url, ...}]}]}'
```
