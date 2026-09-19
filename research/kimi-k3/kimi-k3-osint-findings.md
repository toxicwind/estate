# Kimi K3 + NVIDIA NIM — Deep OSINT Findings

Date: 2026-09-19. Baseline (timeline, top_p=0.95, effort ladder, 429s, trial terms) already covered in `~/workspace/your_files/kimi-k3-nim-analyst.md`. This file holds only non-obvious / deeper findings.

## S0. Social chatter (Threads/IG/FB sweep, 2026-08-01 → 2026-09-19)

- **How-To Geek (Facebook, 2026-09-10, 640K followers, verified):** posted a graphic screenshotting NVIDIA's "Models" page — **38 models filtered by "Free Endpoint," highlighting `moonshotai/kimi-k3`** as a "multimodal MoE for coding and image understanding," with copy "Stop paying for Claude and ChatGPT — NVIDIA is offering free models that're just as good." Mainstream publisher treating K3-on-NIM as live and free. URL: https://www.facebook.com/howtogeek/posts/pfbid0EtPHSoRPPnLXRA3MVXN4LkQ784k3fcZE8w7zSYgVmC4kSmQ1XSuXzNF25XSxsauMl
- **@joonahn_ai (Instagram reel, 2026-08-29):** reshares an X post by @visnu: "nvidia is casually giving you free access to Kimi K3 + more AI models" — no credit card, no subscription, one API key for multiple models incl. Kimi K3, Muse Glimmer 30B, Llama Guard 4 12B. URL: https://www.instagram.com/reel/Dcos1aYAGT-/
- **@lev_ai_than (Instagram reel, 2026-09-02):** "39 AI models on NVIDIA Build offer free API endpoints (out of 99 total) with **no expiring trial** and no credit card required... change base URL to `integrate.api.nvidia.com`." Note the tension: creators claim "no expiring trial" while NVIDIA's trial ToS says not-for-production. URL: https://www.instagram.com/reel/DcxKRv9lPl_/
- No organic user complaints about K3-on-NIM errors found in this sweep — chatter is promotional ("free K3!"), not debugging. The debugging happens in GitHub issues instead.

## S1. Web corroboration (supplemental, 2026-09-19)

- **bauka0/nvidia-nim-provider** (VS Code extension, updated ~5 days ago): ships per-model adapters; Kimi K3 is its top-ranked model (Intelligence Index 44, 1M ctx, reasoning None/Low/High/Max, tools+vision yes). Also lists **GLM 5.3 Flash** — i.e., GLM-5.2's removal was followed by a GLM successor landing on NIM. https://github.com/bauka0/nvidia-nim-provider
- **lianghong/codereview-cli** (commit ~20 days ago): added Kimi K3 (`kimi-nvidia-3`) + DeepSeek-V4-Pro-0813 as NIM entries; **removed five dead NIM endpoints** (each HTTP 410 with NVIDIA's own EOL date, recorded in `DEAD_UPSTREAM_FULL_IDS`); also removed `kimi-k2.6-nvidia` as curation. https://github.com/lianghong/codereview-cli/commit/608a94df8dbc1e24cd81f3ab8b7be9a1430e5f91
- **tibbee/pi-nvidia-nim-provider** (commit 2026-08-27): "2026-08-27 aliveness sweep found NVIDIA retired an entire generation since 1.5.0 (all Llama 3.x base models, Nemotron Super v1/v1.5 and Nano variants, Inkling, **GLM-5.2 — all HTTP 410**). It also surfaced Kimi K3, live on the API but unlisted on the build page." https://github.com/tibbee/pi-nvidia-nim-provider/commit/804b5ccc1536b0f2abb02405af48670e5ef61b68

## S2. Latency horror story + second default-switch (my finds, 2026-09-19)

- **dhruuvsharma/daxalgo-terminal** (commit 4535cbc, ~2026-08-29): "Default to NVIDIA kimi-k3" — made `nvidia/moonshotai/kimi-k3` the DefaultProvider across editions. The commit message documents a measured free-tier datapoint: **"kimi-k3 on the free tier took 167s to return a 43-token reply"** ("WIRED, in 168 seconds"). Author's conclusion: "a real build — context pack, skills, exemplar, several generations — will take minutes per turn." This is the most concrete public latency number for K3-on-NIM free tier, far worse than the 1–46s probe range. https://github.com/dhruuvsharma/daxalgo-terminal/commit/4535cbc1b60d73798f8c33eee706d1df9caac8be
- Same commit also documents a classic false-"broken provider" trap: NVIDIA quickstarts show the full endpoint URL as `invoke_url`, so users paste `https://integrate.api.nvidia.com/v1/chat/completions` as the base URL and the client double-appends the path → 404 "with no body worth reading, which reads as a broken provider or a rejected key." Another way K3-on-NIM "doesn't work" that isn't the model's fault.
- **models.dev catalog drift quantified** (anomalyco/models.dev#5288 notes): "~60 live IDs missing, ~58 listed entries no longer served, incl. rotated IDs like `deepseek-v4-flash` → `deepseek-v4-flash-0731`." The NIM catalog is not a catalog — it's a weather report. https://github.com/anomalyco/models.dev/pull/5288

## S3. Quantization footprint: MXFP4 confirmed (my finds, 2026-09-19)

- **zebrax0r/amd_mi355x_bunya_llm_tools_kimik3** (one-click K3 serving on AMD MI355X via SGLang): titles the recipe **"Kimi K3 (2.8T MoE, MXFP4)"** — MXFP4 is the serving quantization. Real weight download is **1561 GB** (debunks a viral blog claiming "~594 GB" and a nonexistent `moonshotai/Kimi-K3-MXFP4` repo). SGLang recipe uses `--dtype bfloat16` with tuned gfx950 FP4 MoE path (`SGLANG_AITER_K3_OPT=1`, `AITER_SITUV2_A8W4=1`); vLLM's day-0 image is `vllm/vllm-openai:kimi-k3`, **NVIDIA-only, no ROCm build**. https://github.com/zebrax0r/amd_mi355x_bunya_llm_tools_kimik3
- **RunInfra K3Turbo** (rightnow-ai/local-kimi README): commercial package running **the full 2.8T-param K3** targets an **8x B300 node (288 GB/GPU, 2304 GB/node, single NVLink domain)** — "It does not fit an 8x B200 node, and nothing about it runs on a consumer card." https://github.com/rightnow-ai/local-kimi
- **implicator.ai** (citing SemiAnalysis): K3 won't fit a single DGX B200 even at 4-bit precision; serving needs B300/MI355X or GB300 NVL72; Moonshot's own guidance recommends **supernodes of at least 64 accelerators**. Artificial Analysis cost/task: K3 **$0.94** vs GLM-5.2 $0.32 vs DeepSeek V4 Pro $0.04. K3 API: $0.30 cached / $3 input / $15 output per MTok. https://www.implicator.ai/moonshots-kimi-k3-wont-fit-on-a-single-nvidia-dgx-b200/
- Implication for the NIM question: NVIDIA serving K3 at free-tier scale almost certainly serves a quantized (MXFP4-class) build — the full-precision footprint is datacenter-exotic. Whether NIM's build matches Moonshot-direct quality is untested publicly; no benchmark delta published yet (open question for child C / angle 6).

## A4. GLM-5.2 → K3 migration (child-agent research)

### A4a. Key reframing: GLM-5.2's retirement is vendor-driven, cross-provider — not a NIM-only event

- **Nebius** removed `zai-org/GLM-5.2` from its live catalog on **2026-07-27** (replaced by GLM-5.1): "the pinned default no longer existed and the catalog was silently falling back to Kimi-K2.6 (which had no reasoning cap). Per request, **Kimi-K3 is now the default**" — https://github.com/shivaylamba/nebius-tf-relay/commit/271beef4616c9537a496fbb543dc9cb0584c7d4c
- **Tinfoil** emailed a deprecation notice: GLM 5.2 replaced by GLM 5.3, **action required by 2026-09-10**; live probe of `https://inference.tinfoil.sh/v1/models` returns no `glm-5-2` at all — https://github.com/OpenWhispr/openwhispr/pull/2018
- **NVIDIA NIM**: `z-ai/glm-5.2` answers **HTTP 410 Gone with EOL 2026-08-21**.
- z.ai is retiring GLM-5.2 everywhere; K3 is becoming the default replacement across providers, not just NIM.

### A4b. Projects that switched default/recommended to K3 after GLM-5.2 died

1. **shivaylamba/nebius-tf-relay** (2026-07-27): Kimi-K3 made default after Nebius removed GLM-5.2 — https://github.com/shivaylamba/nebius-tf-relay/commit/271beef4616c9537a496fbb543dc9cb0584c7d4c
2. **OpenHands/enterprise** (2026-08-17): "feat: set SaaS default model to Kimi K3 and migrate GLM 5.2 settings (#190)" — migration 145 rewrites managed `glm-5.2` strings to `kimi-k3` across settings JSON and encrypted LLM profiles — https://github.com/openhands/enterprise/commit/6a058707890a977dce71e9de0291fdef330f6071
3. **OpenHands/OpenHands PR #16657**: makes `openhands/kimi-k3` the default OpenHands model in Canvas, "mirroring how `glm-5.2` was rolled out" — https://github.com/OpenHands/OpenHands/pull/16657
4. **krishnan-chandra/kstack** (2026-08-14): "Replace GLM-5.2 with Kimi k3" across default reviewers/implementers (via OpenRouter) — https://github.com/krishnan-chandra/kstack/commit/41b4832b3ab5dc9990e054231d98f621bc16ebc7
5. **bauka0/nvidia-nim-provider v0.7.0** (~2026-08-24): added `moonshotai/kimi-k3` to picker + fallback priority list; removed `moonshotai/kimi-k2.6` ("NIM endpoint returns 404, replaced by Kimi K3") and `z-ai/glm-5.2` ("dropped from the NVIDIA NIM catalog") — https://github.com/BaUka0/nvidia-nim-provider/releases/tag/v0.7.0
6. **nvidia/nemoclaw PR #10242** (~2026-08-25): "drop GLM 5.2 from the NVIDIA featured menu" — adds `z-ai/glm-5.2` to `RETIRED_NVIDIA_FEATURED_MODEL_IDS`; quote: "the deny-list and its policy comment already exist for models whose catalogs outlive their NVIDIA Endpoints routes" — https://github.com/NVIDIA/NemoClaw/pull/10242
7. **OpenWhispr** went the other way: default `glm-5-2` → `glm-5-3` on Tinfoil (same-family successor), while noting Tinfoil's catalog also serves `kimi-k3` — https://github.com/OpenWhispr/openwhispr/pull/2018

### A4c. The Aug 2026 removal wave — exact EOL dates (all HTTP 410 with NVIDIA's own EOL message)

From the codereview-cli Aug-29 audit (https://github.com/lianghong/codereview-cli):
- `mistralai/mistral-small-4-119b-2603` — EOL 2026-07-27
- `qwen/qwen3.5-397b-a17b` — EOL 2026-07-27
- `mistralai/mistral-medium-3.5-128b` — EOL 2026-08-07
- `z-ai/glm-5.2` — EOL 2026-08-21
- `stepfun-ai/step-3.7-flash` — EOL 2026-08-28
- "NIM now serves no Mistral, Qwen, GLM or StepFun model at all" — 27 models remained.
- Companion evidence (omniroute #9824, observed 2026-08-08): `deepseek-ai/deepseek-v4-pro` returned 410 ("reached end of life on 2026-08-07T09:00:00Z") while `nvidia/z-ai/glm-5.2` still returned 200 that day — https://github.com/diegosouzapw/omniroute/issues/9824

### A4d. What the rotation signals about NIM's free-tier lifecycle

- **Churn velocity is weeks, not quarters**: six third-party model families dead between 2026-07-27 and 2026-08-28. Even the replacement `z-ai/glm-5.1` was already out of NIM's authenticated catalog by 2026-09-02 (nimakai pool refresh — https://github.com/dirmacs/nimakai/blob/HEAD/CHANGELOG.md).
- **No advance notice in-catalog**: removals discovered only by live probing. NemoClaw keeps a permanent deny-list because "catalogs outlive their NVIDIA Endpoints routes."
- **No published statement from NVIDIA or z.ai explaining the removals.** The 410 bodies carry only EOL dates. Proximate driver is consistent with vendor model retirement (inference, not a published statement).

## A5. Moonshot capacity & NIM-endpoint incidents (child-agent research)

### A5a. July demand crunch did NOT demonstrably affect the NIM endpoint

- The pause applied to **consumer subscriptions on Moonshot's own platform**, announced 2026-07-19 by @Kimi_Moonshot: "Kimi K3 has received far more love than we expected, and our GPUs are feeling it. Over the past 48 hours, demand has pushed close to the limits of our current capacity. To protect the experience of existing subscribers, we're temporarily pausing new subscriptions…" — https://beincrypto.com/moonshot-ai-pauses-kimi-k3-subscriptions/
- TechNode (2026-07-20) on the official statement "To Kimi Users: An Update on Compute Capacity Constraints and Subscription Suspension": "user requests in the 48 hours following the Kimi K3 launch had surged far beyond its projections" — https://technode.com/2026/07/20/kimi-k3-overwhelms-capacity-just-days-after-launch-suspends-new-consumer-subscriptions/
- NIM runs on NVIDIA infrastructure, not Moonshot's consumer cluster; K3 went live on NIM ~Aug 20, a month after the pause. **No reporting links the demand crunch to the NIM endpoint.**
- Capacity timeline: 2026-07-16 K3 launch → 07-19 subscription pause → 07-19/20 membership restructured (Kimi Membership vs Kimi Code Membership) → 07-27 full open weights released → 07-30 Moonshot closed funding at **$35B valuation** → 07-31 Bloomberg: Alibaba Cloud supplied Moonshot **20,000 Nvidia H200 GPUs** (Alibaba denied).

### A5b. Documented incidents of `moonshotai/kimi-k3` ON NIM (late Aug – early Sep 2026)

1. **2026-08-31 14:10:35Z — per-model 429 storm + one 502** (firedmosquito831/my-claude-code v6.19.0): "a request for `nvidia_nim/moonshotai/kimi-k3` on a three-key NVIDIA NIM pool met **fourteen 429s in fifteen tries**." Direct probes in the same minute: kimi-k3 returned 429 on all three keys within 0.1s while nemotron and a MiniMax model answered on those same keys in the same second — **the limit was the model's**. Request took 81 seconds, fell over to another provider. "NIM sends no `Retry-After`" — https://github.com/FiredMosquito831/my-claude-code-legacy/releases/tag/v6.19.0
2. **"Near unusable at times"** (tibbee/pi-nvidia-nim-provider README): "probe latency ranged from 1 s to 46 s for the same request and the free-tier endpoint repeatedly rate-limits (429) in bursts… treat it as a capacity-constrained endpoint" — https://github.com/tibbee/pi-nvidia-nim-provider/blob/HEAD/README.md
3. **2026-09-02 — K3 excluded from a production routing pool for timeouts** (dirmacs/nimakai CHANGELOG): "`moonshotai/kimi-k3` probed but **consistently timed out (60-90s across 3 keys)** and was not adopted"; adopted instead: gpt-oss-120b, gpt-oss-20b, nemotron-3-super-120b ("all proven live, 0.8s-3.5s") — https://github.com/dirmacs/nimakai/blob/HEAD/CHANGELOG.md
4. No documented case of the K3 endpoint disappearing from the NIM catalog — failures are 429s, 502s, extreme latency, never 410s.

### A5c. Throttling vs capacity

- No evidence of deliberate throttling vs other models; strong evidence the K3 NIM endpoint is **capacity-constrained relative to siblings** (per-model 429s, Aug-31 incident).
- No public Moonshot status page for K3 capacity incidents found.

## A6. Full model vs quantized variant on NIM (child-agent research)

### A6a. The MXFP4/MXFP8 claim is OFFICIAL Moonshot — CONFIRMED

MoonshotAI/Kimi-K3 GitHub README, section 4: "Kimi K3 applies **quantization-aware training from the SFT stage onward**, using MXFP4 weights with MXFP8 activations for broad hardware compatibility." Same claim in Moonshot's technical report (arXiv:2607.24653). The codereview-cli changelog line was quoting Moonshot, not inferring. https://github.com/MoonshotAI/Kimi-K3

### A6b. No full-precision K3 exists — the native release IS already 4-bit — CONFIRMED

Independent checkpoint analysis (llmrequirements.com, ~Sep 2026): "the checkpoint stores routed experts at 4-bit MXFP4 while attention layers, shared experts, the dense MLP, lm_head, and the vision tower remain in BF16 (source: HuggingFace config.json, July 27, 2026)." Key numbers: 96 safetensors shards, **1,561 GB total** (not naive 2.8T×4bit=1,400 GB, because non-expert layers ship BF16); "No BF16 checkpoint exists. No Q2 checkpoint exists." Block-scale metadata: one uint8 E8M0 scale per 32 values (~6.25% overhead). https://llmrequirements.com/news/kimi-k3-launched

### A6c. NVIDIA adds a SECOND quantization layer: Kimi-K3-NVFP4 — CONFIRMED (primary NVIDIA source)

https://huggingface.co/nvidia/Kimi-K3-NVFP4 — official NVIDIA model card, released **08/14/2026**, "quantized with nvidia-modelopt v0.45.0": "The NVIDIA Kimi-K3-NVFP4 model is **the quantized version of Moonshot AI's Kimi-K3 model**." Recipe: "obtained from Kimi-K3 **without calibration data**. The **source MXFP4 routed-expert weights were converted to NVFP4** using `input_scale=1.0`, while the supported attention projection weights in KDA and MLA were quantized to 128×128 per-block FP8. **Other checkpoint tensors retain their original precision.**" Upstream PR: nvidia/model-optimizer PR #2206, commit 5500999d0b3f2e5e209ea4c67ffd5e5335128134. https://github.com/nvidia/model-optimizer/commit/5500999d0b3f2e5e209ea4c67ffd5e5335128134

### A6d. Quality delta of NVIDIA's extra quantization: <1 percentage point — CONFIRMED

NVIDIA's head-to-head eval table on the NVFP4 card (temperature=1.0, top_p=0.95, 65,536-token generation; original vs NVFP4): GPQA Diamond 0.9321→0.9277; SciCode 0.58376→0.5858; MMMU-Pro 0.8063→0.7983; AA-LCR 0.7500→0.7506; IFBench 0.7440→0.7493; Terminal-Bench 2.1 0.8034→0.8020. Largest delta: MMMU-Pro −0.8pp. Essentially no degradation.

### A6e. VRAM/compute footprint — CORROBORATED

NVFP4 card Inference section: "**Test Hardware: 8 NVIDIA Blackwell B300 GPUs**"; first launch downloads ~**1.6 TB** into HF cache; validation config TP8, `--max-model-len 196608` (not full 1M context — context and concurrency tuned together against memory). Supported hardware: "NVIDIA Blackwell — B200 and B300."

### A6f. Does the hosted endpoint serve the NVFP4 build? — INFERENCE (gap)

No source explicitly states the hosted `moonshotai/kimi-k3` endpoint's precision. Inference for yes: NVIDIA produced NVFP4 (released 08/14/2026, *before* the Aug-28 card listing) as "ready-to-deploy" for inference providers; native-MXFP4/BF16-mixed weights are far less efficient to serve on Blackwell; NIM products are TensorRT-LLM/Model-Optimizer-packaged by design. Follow-up probe idea: compare outputs/latency fingerprints between hosted endpoint and downloadable checkpoints.

## A7. NIM trial terms specifics (child-agent research)

### A7a. Not credit-based; rate-limited. ~40 RPM community baseline — CORROBORATED

miztertea/nim-proxy research doc (validated 2026-07-02, citing NVIDIA staff on dev forums): "build.nvidia.com trial usage is **not credit-based** — governed by a rate limit that **depends on model, use case, and current overall traffic**, practical community baseline **~40 requests per minute per key**. (Older docs describing 1,000 signup credits reflect the previous scheme.)" Keys per developer account; registration requires unique email **and phone number**. https://github.com/miztertea/nim-proxy/blob/HEAD/knowledge/research/nim-free-tier-40rpm-no-credits.md ; forum thread: https://forums.developer.nvidia.com/t/clarity-on-nim-api-free-tier-rate-limit-increases/369624 (May 2026)

### A7b. K3 card advertises "up to 40 RPM, 10,000 requests/day" — CORROBORATED (via secondary scrape)

freeinferencing.com provider audit (snapshot 2026-09-13, quoting NVIDIA's live model page): "NVIDIA's live model page advertises a free endpoint, a 1,048,576-token context, **up to 40 requests/minute, and 10,000 requests/day**; API reference caps output at 65,536 tokens/request." Caveat in same source: NVIDIA's limit text says rates "**may vary by model** and traffic from other users **may cause throttling**" — phrasing is "up to", allowance is development/prototyping-only. Current marketing phrase: "**Unlimited prototyping**." https://freeinferencing.com/provider/nvidia_build/

### A7c. Actual trial-terms text — CONFIRMED

NVIDIA API Trial Terms of Service §1.3: "these versions are **not intended for use in production** or business-critical systems." §1.4: "The API Services are available for your **limited use for a limited time**… You must have a separate service subscription ('Subscription') from NVIDIA or a third-party service provider to use the API Service in production… you **may only use the API Service for internal testing and evaluation purposes, not in production**." Official PDF: https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf

### A7d. Is K3 throttled harder? — CORROBORATED yes (practically)

Per-model variance is official policy ("may vary by model"). K3-specific: tibbee README "near unusable at times… repeatedly rate-limits (429) in bursts"; codereview-cli: "NIM's free tier returned HTTP 429 for **every** forced-`tool_choice` attempt"; Fabian Gwinner (Medium, Jun 2026): "bigger models (such as GLM or Deepseek) have limits like **10 or 20 to 50 request per hour**."

### A7e. Privacy: free-tier prompts are trainable — CONFIRMED via audit

freeinferencing.com's reading of free developer terms: "The free developer terms permit **storage and broad product, service, and underlying-model improvement uses**… The terms do **not** make a narrow no-training commitment… users should **treat training or equivalent improvement use as permitted**."

## A1. NVIDIA Developer Forums thread (child-agent research)

- **Thread:** "Kimi-k3 model availability request" (Models category) — http://forums.developer.nvidia.com/t/kimi-k3-model-availability-request/377282
- **OP — 2026-07-17:** "Please advise on your intent to publish Kimi-K3 open-weight models for testing purposes… with full context window availability to overcome the 202K context limitation of previous models."
- **Reply ("cpp") — 2026-07-18:** "i doubt they will have the power to give a 3T model for us for free" and "i still want the kimi k3 to be hosted on the nvidia nim if they want they can remove the model like minimax3, minimax2.7 and kimi k2.6 to make space to host the kimi k3"
- **Reply (Aharpster, NVIDIA Brev team staff):** "Hi there, The build team is constantly trying to bring the latest updates. Stay tuned! Best, Aharpster"
- **Status:** No solution/answered marker; 3 posts total; dead since July 18. **No timeline commitments — pure generic "stay tuned."** K3 went live ~Aug 20 / officially listed Aug 28 **with nobody closing the loop in the thread.** The requesters' ask was fulfilled; nobody told them.

## A2. Stale-claim forensics (child-agent research)

- **The documented downstream of the thread:** open-free-router commit `a32e0bf` (2026-08-03, "K3 confirmed not yet available") cites the thread verbatim as evidence: "confirmed K3 is NOT on NVIDIA NIM as of this writing (a live, unresolved NVIDIA Developer Forums thread from days earlier explicitly asks NVIDIA to add it…)" — https://github.com/noeljudenoel/open-free-router/commit/a32e0bfefa44f2f0c2bd83edd55630f8d0c9deef
- **0xzr/freellmpool** — `docs/MODEL_ACTIVITY_AUDIT_2026-08-29.md` (dated 2026-08-29, one day *after* the official listing, still live on HEAD, never refreshed): "`moonshotai/kimi-k3` … are listing-only and disabled. No fresh credentialed success is claimed for any candidate." Conservative methodology (disabled for lack of credentialed verification), but now stale. https://github.com/0xzr/freellmpool/blob/HEAD/docs/MODEL_ACTIVITY_AUDIT_2026-08-29.md
- **mvalentsev/awesome-free-ai-coding** `providers/nvidia-nim.md` ("last verified by a probe on 2026-09-17", generated 2026-09-19): K3 entirely absent from probe-verified callable IDs — silent omission, not explicit claim. https://github.com/mvalentsev/awesome-free-ai-coding
- **NOT stale:** freeinferencing.com/provider/nvidia_build/ lists `moonshotai/kimi-k3` as a live free endpoint (1,048,576 ctx, up to 40 RPM, 10K/day) — current as of crawl.
- No currently-live page found explicitly asserting "K3 is not on NIM" with a post-Aug-20 date. The stale residue is: dated audits never refreshed, silently-omitted probe lists, and the (now-fixed) exclusion test.

## A3. The K3-exclusion test — resolved (child-agent research, repo cloned + git history read)

- **The test no longer exists.** Removed in commit `cf4e4fd` (2026-09-02, "chore(release): 0.3.0 — probe-then-trust verification, NIM funnel redesign, Kimi K3 tier/high").
- **History:** added 2026-08-03 as `test_kimi_k2_6_included_k3_excluded`, docstring: "K2.6 is the newest Kimi actually free on NVIDIA NIM. K3 was requested but does not exist on NIM yet — must not appear even though a plausible-looking entry for it is present in the mocked upstream response, guarding against ever adding it on a guess."
- **Replacement** `test_kimi_k3_included` docstring: "K3 IS listed on the live NIM catalog as of 2026-09-02 (verified against the authenticated /v1/models response). The historical exclusion here was correct then — NIM didn't host it — and is stale now."
- **Current state (main):** kimi-k3 IS in `registry.default.yaml` nvidia-nim section (`upstream_id: moonshotai/kimi-k3`) and in `tiers.py` `tier/high` pool; comment: "2026-09-02 live-probe snapshot of NIM's catalog: every entry below answered a real chat completion (kimi-k3 is catalog-listed but did not answer within 150s that day — kept per the all-free-NIM funnel…)"
- **The inversion:** K3 was **kept while unresponsive >150s**; **kimi-k2.6 was REMOVED** — "NIM's catalog also lists ~38 chat models that 404 ('Function not found') on real requests — kimi-k2.6 included, which is why it was removed here." The previously-trusted K2.6 flagship got cut; the new K3 got in.
- **No debate about it:** zero open issues, zero forks, no PRs. The flip happened unilaterally in a single release commit.
- **Self-documenting stale chain, end to end:** forum thread (Jul 17, unresolved) → exclusion commit citing that thread as evidence (Aug 3) → reversal commit (Sep 2) with the maintainer's epitaph: "The historical exclusion here was correct then — NIM didn't host it — and is stale now."
