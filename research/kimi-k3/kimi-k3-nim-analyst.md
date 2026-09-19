# Kimi K3 on NVIDIA NIM: The "Not Working" Myth vs. Live Reality

**Analyst note — 2026-09-19, deep OSINT revision.** Tau is driving `kimi-k3-nim` live today — 85 measured streams at 25.5 tokens/sec with 2.71s mean time-to-first-token. Meanwhile mainstream aggregators and several open-source router projects still carry claims that Kimi K3 "isn't available" or "doesn't work" on NVIDIA NIM. Both statements were true at different times, for different reasons — and the residue of the old truth is still poisoning model catalogs. This revision replaces the baseline with the deep findings: a self-documenting stale-claim chain, a double-quantized model with no full-precision original, an industry-wide GLM-5.2 retirement that made K3 the default replacement, and concrete capacity numbers from live incidents.

## 1. The claim and the counterevidence

The claim, as carried by mainstream sources: Kimi K3 is not available or not working on NVIDIA NIM. The earliest and most-cited instance is an open-source router commit from early August 2026 that checked NVIDIA's catalog, found K3 absent, noted a live unresolved NVIDIA Developer Forums thread asking NVIDIA to add it, and concluded "K3 confirmed not yet available" — then wrote a test asserting K3 stays excluded even if it appears upstream, specifically to guard against adding it "on a guess" ([commit a32e0bf](https://github.com/noeljudenoel/open-free-router/commit/a32e0bfefa44f2f0c2bd83edd55630f8d0c9deef)). The fossil record matters because downstream aggregators (Exa-indexed docs, model-picker UIs, curated "free on NIM" lists) ingested the August state and never re-checked.

The counterevidence is that **Moonshot's K3 has been live on NVIDIA's hosted NIM catalog** at `integrate.api.nvidia.com/v1/models` since late August, was probe-verified working (vision, tools, thinking toggle, streaming) on 2026-08-27 while still unlisted on the build page, and was **officially listed on build.nvidia.com on 2026-08-28** with a 1,048,576-token context window ([tibbee CHANGELOG](https://github.com/tibbee/pi-nvidia-nim-provider/blob/HEAD/CHANGELOG.md)). Independent catalog work added `moonshotai/kimi-k3` provider entries the same week after verifying the wire schema empirically against the live endpoint ([anomalyco/models.dev#5288](https://github.com/anomalyco/models.dev/pull/5288), [ceocxx commit](https://github.com/ceocxx/models.dev/commit/d1b84739db8882df547561376be3b46037de8639)). Tau's engine carries a full Kimi family taxonomy with a dedicated `k3` family, effort-level routing (`kimi-k3-low/high/max`), and Moonshot K3 cost/limit handling — the shape of a model that is integrated, not aspirational. And per Chris, tau is driving `kimi-k3-nim` live right now, with measured local throughput to prove it (see §7).

## 2. Timeline: how "not available" became stale truth

| Date (2026) | Event |
|---|---|
| Jul 17 | NVIDIA dev-forums thread asks for K3 on NIM; staff replies "stay tuned," thread dies Jul 18 ([thread 377282](https://forums.developer.nvidia.com/t/kimi-k3-model-availability-request/377282)) |
| Jul 19 | Moonshot pauses new K3 consumer subscriptions — 48h demand surge near capacity limits ([beincrypto](https://beincrypto.com/moonshot-ai-pauses-kimi-k3-subscriptions/)) |
| Jul 27 | Nebius removes `zai-org/GLM-5.2` from its catalog, makes Kimi-K3 the default ([nebius-tf-relay commit](https://github.com/shivaylamba/nebius-tf-relay/commit/271beef4616c9537a496fbb543dc9cb0584c7d4c)) |
| Aug 3 | open-free-router codifies "K3 confirmed not yet available," citing the unresolved forums thread; adds `test_kimi_k2_6_included_k3_excluded` |
| Aug 14 | NVIDIA releases `nvidia/Kimi-K3-NVFP4` checkpoint on Hugging Face — a second quantization pass ([model card](https://huggingface.co/nvidia/Kimi-K3-NVFP4)) |
| ~Aug 20 | K3 appears on NIM; codereview-cli registers `kimi-k3-nvidia` / `moonshotai/kimi-k3` ([CHANGELOG](https://github.com/lianghong/codereview-cli/blob/HEAD/CHANGELOG.md)) |
| Aug 21 | `z-ai/glm-5.2` on NIM answers HTTP 410 Gone with EOL date |
| Aug 27 | Probe-verified live on the API but unlisted on the build page; latency swinging 1–46 s ([tibbee CHANGELOG](https://github.com/tibbee/pi-nvidia-nim-provider/blob/HEAD/CHANGELOG.md)) |
| Aug 28 | Officially listed on the build page; audit finds 5 of 10 NIM entries dead (410 Gone) — catalog volatility is the norm |
| Aug 31 | Per-model 429 storm on K3: 14×429 + 1×502 in 15 tries on a 3-key pool; no `Retry-After` sent ([release v6.19.0](https://github.com/FiredMosquito831/my-claude-code-legacy/releases/tag/v6.19.0)) |
| Sep 2 | open-free-router *removes* the exclusion test, replaces with `test_kimi_k3_included`; K3 kept in registry while unresponsive >150s that day; K2.6 removed for 404ing ([commit cf4e4fd](https://github.com/noeljudenoel/open-free-router/commit/a32e0bfefa44f2f0c2bd83edd55630f8d0c9deef)) |
| Sep 2 | nimakai excludes K3 from a production pool after consistent 60–90s timeouts; adopts gpt-oss + nemotron-3-super instead ([CHANGELOG](https://github.com/dirmacs/nimakai/blob/HEAD/CHANGELOG.md)) |
| Sep 10 | How-To Geek (640K followers) screenshots NIM's Models page with 38 "Free Endpoint" models highlighting `moonshotai/kimi-k3` — mainstream publisher treats it as live and free |
| Sep 19 | Tau driving `kimi-k3-nim` live; 85 streams at 25.5 TPS measured locally |

The stale-truth mechanism is worth naming explicitly: **the August "not available" verdict was correct when written**, then K3 shipped, and nobody with a megaphone issued the correction. Aggregators that snapshot catalogs rather than probing them still serve the August answer. Anyone evaluating K3-on-NIM from secondhand sources in September is reading fossils.

## 3. The stale-claim chain, self-documented end to end

The most unusual finding: the whole stale-truth pipeline is documented in public git history, including its own correction.

- **Jul 17:** Forums thread "Kimi-k3 model availability request" opens. NVIDIA Brev staff: "The build team is constantly trying to bring the latest updates. Stay tuned!" Three posts, dead since Jul 18, never updated when K3 went live ~Aug 20. Nobody closed the loop in the thread.
- **Aug 3:** open-free-router commit `a32e0bf` cites that thread verbatim as evidence that "K3 is NOT on NVIDIA NIM as of this writing" and adds `test_kimi_k2_6_included_k3_excluded`, docstring: "K3 was requested but does not exist on NIM yet — must not appear even though a plausible-looking entry for it is present in the mocked upstream response, guarding against ever adding it on a guess."
- **Sep 2:** Commit `cf4e4fd` ("chore(release): 0.3.0 — probe-then-trust verification") removes the exclusion test and adds `test_kimi_k3_included`, docstring: "K3 IS listed on the live NIM catalog as of 2026-09-02 (verified against the authenticated /v1/models response). **The historical exclusion here was correct then — NIM didn't host it — and is stale now.**" Zero forks, zero issues, zero PRs about it — the flip was unilateral. Maintainer's epitaph for the whole phenomenon, in one docstring.

Remaining stale residue, still live:
- **0xzr/freellmpool** `docs/MODEL_ACTIVITY_AUDIT_2026-08-29.md` (dated one day *after* the official listing, never refreshed): "`moonshotai/kimi-k3` … are listing-only and disabled. No fresh credentialed success is claimed for any candidate." Conservative methodology (disabled for lack of credentialed verification), now stale.
- **mvalentsev/awesome-free-ai-coding** `providers/nvidia-nim.md` ("last verified by a probe on 2026-09-17"): K3 silently absent from probe-verified callable IDs — omission, not explicit claim, but the effect on catalog consumers is the same.
- **NOT stale:** freeinferencing.com/provider/nvidia_build/ lists `moonshotai/kimi-k3` as a live free endpoint (1,048,576 ctx, up to 40 RPM, 10K/day).

## 4. The inversion: K2.6 got removed while K3 got kept

On Sep 2, NIM's catalog carried ~38 chat models that 404'd ("Function not found") on real requests — a Potemkin layer: "listed" ≠ "callable." The inversion nobody would predict: **kimi-k2.6, the previously-trusted flagship, was removed** for being in the 404 set, while **K3, listed but unresponsive >150s that day, was kept** per the maintainer's "all-free-NIM funnel" policy. This also explains freellmpool's "listing-only and disabled" verdict: on NIM, listing is a claim about a catalog, not a claim about an endpoint. The correct mental model is models.dev's quantified drift: "~60 live IDs missing, ~58 listed entries no longer served" — the NIM catalog is not a catalog, it's a weather report.

## 5. There is no full-precision K3 — and NVIDIA quantizes it twice

Moonshot's canonical release is *already* quantization-aware-trained from the SFT stage onward: MXFP4 routed-expert weights + MXFP8 activations + BF16 everything else, 1,561 GB across 96 safetensors shards. Independent checkpoint analysis confirms: "No BF16 checkpoint exists. No Q2 checkpoint exists." ([MoonshotAI/Kimi-K3 README](https://github.com/MoonshotAI/Kimi-K3), [llmrequirements.com](https://llmrequirements.com/news/kimi-k3-launched))

Then NVIDIA shipped a *second*, calibration-free quantization pass: the official `nvidia/Kimi-K3-NVFP4` checkpoint (released 08/14/2026, nvidia-modelopt v0.45.0) converts the MXFP4 routed-expert weights to NVFP4 and supported attention projections to 128×128 per-block FP8. NVIDIA published head-to-head evals proving the second pass costs <1 percentage point on every benchmark (GPQA Diamond 0.9321→0.9277, Terminal-Bench 2.1 0.8034→0.8020; largest delta MMMU-Pro −0.8pp) ([nvidia/Kimi-K3-NVFP4](https://huggingface.co/nvidia/Kimi-K3-NVFP4), [model-optimizer#2206](https://github.com/nvidia/model-optimizer/commit/5500999d0b3f2e5e209ea4c67ffd5e5335128134)).

The hosted endpoint's precision isn't directly confirmed by any source — but the NVFP4 build exists specifically as "ready-to-deploy" for inference providers, predates the Aug-28 card listing, and NVIDIA's NIM products are TensorRT-LLM/Model-Optimizer-packaged by design. It's very likely what NIM serves. The full-precision footprint (8×B300 node, single NVLink domain, ~1.6TB download) is datacenter-exotic; the native MXFP4/BF16-mixed weights are far less efficient to serve on Blackwell. Follow-up probe idea: compare output/latency fingerprints between the hosted endpoint and the downloadable checkpoints.

## 6. Why naive clients fail 100%: the strict endpoint

Availability is not the same as plug-and-play. K3's NIM endpoint is unusually strict about request shape, and every default that mainstream OpenAI-compatible clients inject happens to be a wrong one. Three independent client projects hit the same wall and had to ship K3-specific patches — which is itself evidence the endpoint is live (you cannot get a 400 validation error from a model that does not exist).

**The `top_p` immutability trap.** NVIDIA pins `top_p` per model, and K3 requires exactly `0.95`. Clients that inject the OpenAI default `top_p: 1.0` — which is most of them, since Claude Code's Anthropic protocol sends neither `top_p` nor `temperature` and proxies backfill defaults — receive `400 Validation: top_p is immutable for this model and must be 0.95, got 1` on every single request ([v5.61.0 postmortem](https://github.com/FiredMosquito831/my-claude-code-legacy/releases/tag/v5.61.0), [Alishahryar1/free-claude-code#1518](https://github.com/Alishahryar1/free-claude-code/pull/1518)). One project's postmortem is blunt: the bug was older than their rebrand; what changed was NVIDIA's contract, not their code. The fix was to stop inventing parameters entirely and let per-model overrides set `top_p: 0.95` explicitly for `nvidia_nim/moonshotai/kimi-k3` ([commit a50089d](https://github.com/firedmosquito831/my-claude-code-legacy/commit/a50089d2ce761d2641e0cba7fb4c41fc297187e8)). A client that does not know about the pin sees a 100% failure rate and reasonably — but wrongly — concludes the model is down.

**The reasoning-effort ladder gap.** K3 accepts only `low`, `high`, and `max` for `reasoning_effort`. Routers that forward `medium` verbatim get a 400; one router's fix clamps `medium→high`, `minimal→low`, `xhigh→max` for the `nvidia/*kimi*k3*` pattern after watching requests loop through 19 API keys ([zenrouter commit](https://github.com/zenrouter/zenrouter/commit/a073f380cd0ee43397fb8be83f44df2016cbe53c)). Separately, K3's thinking toggle lives in `chat_template_kwargs.thinking`, and a retry-path bug that stripped that field on 400s produced a subtler failure: requests succeeded but thinking appeared on only 2 of 111 calls, silently degrading the model's signature capability ([commit 8570ced](https://github.com/firedmosquito831/my-claude-code-legacy/commit/8570ced9ea8b05ebaaf87f033b5a2617ae0d0349)).

**Thinking is always on.** The model card states thinking cannot be disabled, and NIM bills reasoning inside `completion_tokens` — so output budgets must be sized accordingly (one project doubled its cap to 32,768 for K3 vs its K2.6 sibling). A client sized for non-reasoning output will truncate or misprice every call.

**The double-appended base URL.** A classic false-"broken provider" trap documented by daxalgo-terminal: NVIDIA quickstarts show the full endpoint URL as `invoke_url`, so users paste `https://integrate.api.nvidia.com/v1/chat/completions` as the base URL and the client double-appends the path → 404 "with no body worth reading, which reads as a broken provider or a rejected key." ([commit 4535cbc](https://github.com/dhruuvsharma/daxalgo-terminal/commit/4535cbc1b60d73798f8c33eee706d1df9caac8be)) Another way K3-on-NIM "doesn't work" that isn't the model's fault.

## 7. "Usable" with asterisks: capacity, latency, trial terms — with numbers

Even with the request shape correct, K3-on-NIM is a capacity-constrained endpoint, and the incidents are quantified:

- **Aug 31, 14:10:35Z:** 14×429 + 1×502 in 15 tries on a 3-key pool. Same-minute probes: kimi-k3 returned 429 on all three keys within 0.1s while nemotron and a MiniMax model answered on those same keys in the same second — **the limit was the model's**. NIM sends no `Retry-After`. One request took 81 seconds and fell over to another provider.
- **Free-tier horror datapoint:** a terminal project measured **167 seconds for a 43-token reply** on K3 free tier — "a real build … will take minutes per turn."
- **Sep 2:** nimakai excluded K3 from a production routing pool after consistent **60–90s timeouts** across 3 keys; adopted gpt-oss-120b, gpt-oss-20b, nemotron-3-super-120b ("all proven live, 0.8s–3.5s").
- **General probe range:** same-request latency 1–46 s, 429 bursts ([tibbee README](https://github.com/tibbee/pi-nvidia-nim-provider/blob/HEAD/README.md)).

**Tau's own numbers (local measurement, model_perf table, 2026-09-19):** 85 streams, 13,975 output tokens over 548.4 generation-seconds = **25.5 tokens/sec**, mean TTFT 2.71s. For context in the same table: qwen-flash-128k 38.2 TPS, ling-3.0-flash-vl 45.8 TPS, inkling-small 85.9 TPS. K3 is the slowest in tau's roster but the largest model by orders of magnitude — and it's the one doing the heavy oracle/judge work. The point isn't that 25.5 TPS is fast; it's that the endpoint answers, streams, and sustains multi-turn agent workloads.

**Trial terms.** NVIDIA lists K3 under trial terms: "not intended for use in production or business-critical systems" (§1.3); "you may only use the API Service for internal testing and evaluation purposes, not in production" (§1.4) ([Trial Terms PDF](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf)). Card-advertised quota: up to 40 RPM / 10,000 requests/day ("up to," "may vary by model") — but bigger models see practical limits like 10–50 requests/hour. And the privacy note: the free developer terms permit storage and broad product/model-improvement use with no narrow no-training commitment — **free-tier K3 prompts should be treated as trainable, non-private input.**

**The GLM-5.2 → K3 migration is an industry-wide vendor retirement, not a NIM story.** z.ai retired GLM-5.2 everywhere: Nebius 07-27 (→GLM-5.1, and made Kimi-K3 the default), NIM 08-21 (410 Gone), Tinfoil →GLM-5.3 with a hard 09-10 deadline. [OpenHands enterprise](https://github.com/openhands/enterprise/commit/6a058707890a977dce71e9de0291fdef330f6071) (2026-08-17) rewrote managed `glm-5.2` strings to `kimi-k3` across settings JSON and encrypted LLM profiles; [OpenHands#16657](https://github.com/OpenHands/OpenHands/pull/16657) made `openhands/kimi-k3` the default Canvas model; kstack, nebius-tf-relay, nvidia-nim-provider all landed on K3. NIM's free tier churns on a weeks-scale lifecycle: 5 model families 410'd with exact EOL dates in 5 weeks (mistral-small-4-119b-2603 EOL 07-27, qwen3.5-397b EOL 07-27, mistral-medium-3.5-128b EOL 08-07, glm-5.2 EOL 08-21, step-3.7-flash EOL 08-28), removals discovered only by live probing. NVIDIA's own NemoClaw keeps a permanent deny-list because ["catalogs outlive their NVIDIA Endpoints routes"](https://github.com/NVIDIA/NemoClaw/pull/10242).

**Social chatter is promotional, not debugging.** How-To Geek (Sep 10) screenshotted NIM's Models page with 38 "Free Endpoint" models highlighting kimi-k3; creators claim "no expiring trial, no credit card" — in tension with the trial ToS. The actual debugging all happens in GitHub issues, which is where every finding above came from. No organic user complaints about K3-on-NIM errors surfaced on social; the complaint surface is capacity, not availability.

## 8. What tau's live usage proves (and what it does not)

Tau driving `kimi-k3-nim` proves three things. First, the endpoint exists and answers — the strongest possible refutation of "not available," now with measured throughput (25.5 TPS) rather than a binary alive/dead claim. Second, tau's request path satisfies the strict contract (`top_p: 0.95`, valid effort levels, thinking-toggle transport), whether by explicit configuration or by not injecting the defaults that break it. Third, tau's workload tolerates the capacity asterisks: burst 429s and minute-scale latency (60–155 s time-to-first-token, measured 2026-09-19) are part of the deal.

It does not prove the endpoint is stable, well-provisioned, or suitable for latency-sensitive paths. It does not prove the trial terms permit the workload. It does not prove which precision the hosted endpoint serves (the NVFP4-build inference is strong but unconfirmed). And it does not invalidate anyone's August failure — those clients failed against a genuinely absent or unlisted endpoint, then failed again against the strict contract. The point of interest Chris flagged is precisely this: **the mainstream "doesn't work" verdict is a compound of a stale fact, a Potemkin catalog, and a strict interface**, and live measured usage cuts through all three.

## 9. Practical takeaways

For anyone integrating K3 on NIM: pin `top_p: 0.95` and never let client defaults override it; restrict `reasoning_effort` to `low`/`high`/`max`; drive thinking via `chat_template_kwargs.thinking`; budget output tokens for always-on reasoning; paste only the base URL (`integrate.api.nvidia.com/v1`), never the full invoke path; expect 429 bursts and 60–155 s time-to-first-token (~100 s for a short completion measured 2026-09-19; worse at the tail); and read deprecation signals from chat-response headers (GET /v1/models carries no deprecation headers — verified 2026-09-19) before assuming an outage is yours — NIM retires endpoints with 410s at short notice. For catalog consumers: treat any "K3 not on NIM" claim dated before 2026-08-28 as expired, and treat the exclusion test in open-free-router as self-retired (the maintainer's own epitaph: correct then, stale now). For privacy: don't send sensitive data through the free tier — treat it as trainable. The model is there. It is picky, rate-limited, trial-gated, and probably double-quantized — but it answers.


---

## Corrections (2026-09-19, lane-3)

- Latency wording reconciled with live measurements: 60–155 s TTFT, ~100 s short completions (was: "1–46 s" / "multi-second swings").
- Outage-triage advice corrected: deprecation signals come from chat-response headers, not GET /v1/models (verified it carries none).
- All cited URLs re-verified live (HTTP 200) on 2026-09-19.
