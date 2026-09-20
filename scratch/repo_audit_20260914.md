# toxicwind org repo hygiene audit — 2026-09-14

Read-only audit of 451 repos (278 public, 173 private, 222 forks) via GitHub REST API.
Four workers fanned out: (A) 42 Sept-2026-active repos — secrets/CI/branches/metadata;
(B) 154 unique stale public forks (pre-2025) — upstream compare; (C) 27 repos >100MB —
>50MB blob hunt + private-repo visibility sanity; (D) 56 public non-forks — README/license/description/topics.

Skipped (handled by other workers today): sovereign-scripts, sovereign-skills, sovereign-swap,
sovereign-zed, omp-extensions, tau-extensions, nvidia-swarm-lens.

## Top-10 action list

1. **BLOCKER — committed secrets in PUBLIC repos.** `effusion-labs`: `mcp-stack/profiles/dev.env` + `prod.env` (+ duplicates under `services/mcp-stack/`). `sovereign`: `config/ports.env`, `skills/repo-audit/projects.env`. Rotate any credentials in these files; purge from history (they're public).
2. **BLOCKER — systemic CI rot.** Workflow 'Tectonic Drift Detection' failing 5/5 in 9 repos (sovereign, caddy-sovereign-auth, qed, sovereign-router, zedra-sovereign, herd, sovereign-pi-archive, additional-lens-profiles). Fix once at the shared-workflow source, back-propagate.
3. **Verify `kimi_tokens.json` / `kimi_tokens_full.json`** committed in PUBLIC `sovereign-projects` (6 copies under `ultimate_extract/`) and private `sovereign-router` — if these are live API tokens, rotate immediately.
4. **Bulk fork cleanup: 93 stale public forks** with zero unique commits ahead of upstream, untouched for 2–13 years (full list below). Delete candidates — frees namespace clutter, zero data loss.
5. **moonbox-live (private, 705MB):** 4 blobs >50MB incl. an 88.7MB pasted-clipboard backup txt, an 86MB `.git_repos` packfile, an 83.5MB pcap. Split/LFS/prune before GitHub hard limits bite.
6. **Branch hoarding:** 100 branches each in mcpproxy-go, effusion-labs, kimi-code-sovereign; 56 in zedra; 31 in local-work-archive; 29 in sovereign-pi-archive. Prune merged/stale branches.
7. **`moonbox-.secrets-20260822` (private)** — a repo literally named '.secrets'. Verify contents stay private; consider renaming. Also review `triangle-access-secrets`, `token-recovery-20260824` before any publish.
8. **Missing licenses everywhere:** 20 of 30 needs-work public repos lack a license (16 miss license alone); 18/36 in the recent-active set. Add SPDX license files, esp. on public non-forks.
9. **`entropy-gpu` is an empty public repo** (0 branches, 0KB) — delete or populate. `zedra` (public) commits `android/debug.keystore`; `toxic-vault-mind` (public) commits `config-keys.json` — verify not sensitive.
10. **`gayxxx-sovereign` (private)** commits 20 decompiled `java_keys.txt` + `DecryptKeys.java`; also brand-risk name. Review before any visibility change.

---

## 1. Recent-active deep audit (36 repos, Sept 2026 pushes)

Full per-repo section: /tmp/audit_A.md (raw JSON: /tmp/audit_results.json). Severity-ranked summary:

### Blockers
- effusion-labs (pub): real .env files committed — `mcp-stack/profiles/dev.env`, `prod.env` (+ `services/mcp-stack/` dupes).
- sovereign (pub): .env committed — `config/ports.env`, `skills/repo-audit/projects.env`.
- Tectonic Drift Detection 5/5 failing: sovereign, caddy-sovereign-auth, qed, sovereign-router, zedra-sovereign, herd, sovereign-pi-archive, additional-lens-profiles. (herd also: Build Containers + Close-inactive-issues failing; local-work-archive: 3/3 Nix+CI failing.)
### Should-fix
- kimi_tokens.json/kimi_tokens_full.json committed: PUBLIC sovereign-projects (6x under ultimate_extract/) + private sovereign-router — verify not live tokens.
- Branch counts: 100 each mcpproxy-go, effusion-labs, kimi-code-sovereign; 56 zedra; 31 local-work-archive; 29 sovereign-pi-archive; 20 gayxxx-sovereign (decompiled java_keys.txt + DecryptKeys.java).
- toxic-vault-mind (pub): config-keys.json + src/config-keys.ts + scripts/generate-config-keys-json.mjs — verify not live secrets.
- zedra (pub): android/debug.keystore committed (debug signing key, low severity).
- ast-grep (pub): 4/5 recent runs failing (coverage, PyPi Release, Build NAPI, PyO3). Boundless (pub): 1 recent Boundless CI failure (CodeQL healthy).
- entropy-gpu (pub): EMPTY repo — delete or populate.
- 18/36 repos lack a license; 34/36 have zero topics; 13/36 lack a description.

## 2. Stale public fork triage (154 unique pre-2025 forks)

**93 cleanup candidates** (ahead_by=0, untouched >2y — zero unique work, safe to delete pending owner approval). **59 keep** (have unique commits). 0 upstream-gone. 2 compare errors (check manually).

### Cleanup candidates (93)

| Repo | Last push | Behind upstream | Upstream |
|---|---|---|---|
| ComfyUI-Advanced-ControlNet | 2024-04-04 | 226 | Kosinkadink/ComfyUI-Advanced-ControlNet |
| ComfyUI-ArtGallery | 2024-06-12 | 0 | ZHO-ZHO-ZHO/ComfyUI-ArtGallery |
| ComfyUI-AutomaticCFG | 2024-04-17 | 276 | Extraltodeus/ComfyUI-AutomaticCFG |
| ComfyUI-BRIA_AI-RMBG | 2024-04-17 | 0 | ZHO-ZHO-ZHO/ComfyUI-BRIA_AI-RMBG |
| ComfyUI-CCSR | 2024-03-18 | 13 | kijai/ComfyUI-CCSR |
| ComfyUI-Custom-Nodes | 2023-09-19 | 0 | Zuellni/ComfyUI-Custom-Nodes |
| ComfyUI-Custom-Scripts | 2024-04-09 | 150 | pythongosssss/ComfyUI-Custom-Scripts |
| ComfyUI-DARE-LoRA-Merge | 2024-01-05 | 0 | ntc-ai/ComfyUI-DARE-LoRA-Merge |
| ComfyUI-DDColor | 2024-01-18 | 0 | kijai/ComfyUI-DDColor |
| ComfyUI-Embedding_Picker | 2024-01-06 | 12 | Tropfchen/ComfyUI-Embedding_Picker |
| ComfyUI-FBCNN | 2024-01-19 | 11 | Miosp/ComfyUI-FBCNN |
| ComfyUI-Flowty-LDSR | 2024-03-24 | 0 | flowtyone/ComfyUI-Flowty-LDSR |
| ComfyUI-Gemini | 2024-04-17 | 0 | ZHO-ZHO-ZHO/ComfyUI-Gemini |
| ComfyUI-GlifNodes | 2024-04-16 | 22 | glifxyz/ComfyUI-GlifNodes |
| ComfyUI-Hangover-Moondream | 2024-04-17 | 22 | Hangover3832/ComfyUI-Hangover-Moondream |
| ComfyUI-Hangover-Nodes | 2024-04-06 | 4 | Hangover3832/ComfyUI-Hangover-Nodes |
| ComfyUI-IPAnimate | 2024-02-01 | 0 | Chan-0312/ComfyUI-IPAnimate |
| ComfyUI-Image-Selector | 2024-01-10 | 9 | SLAPaper/ComfyUI-Image-Selector |
| ComfyUI-ImageReward | 2024-02-04 | 9 | ZaneA/ComfyUI-ImageReward |
| ComfyUI-Impact-Subpack | 2024-04-08 | 53 | ltdrdata/ComfyUI-Impact-Subpack |
| ComfyUI-Inspire-Pack | 2024-04-13 | 131 | ltdrdata/ComfyUI-Inspire-Pack |
| ComfyUI-JNodes | 2024-06-13 | 313 | JaredTherriault/ComfyUI-JNodes |
| ComfyUI-KJNodes | 2024-04-18 | 1123 | kijai/ComfyUI-KJNodes |
| ComfyUI-LCM | 2023-11-11 | 0 | 0xbitches/ComfyUI-LCM |
| ComfyUI-PickScore-Nodes | 2024-04-08 | 4 | Zuellni/ComfyUI-PickScore-Nodes |
| ComfyUI-QualityOfLifeSuit_Omar92 | 2024-02-13 | 38 | omar92/ComfyUI-QualityOfLifeSuit_Omar92 |
| ComfyUI-RAVE | 2024-01-28 | 0 | spacepxl/ComfyUI-RAVE |
| ComfyUI-Saveaswebp | 2023-11-11 | 1 | Kaharos94/ComfyUI-Saveaswebp |
| ComfyUI-SegMoE | 2024-04-17 | 0 | ZHO-ZHO-ZHO/ComfyUI-SegMoE |
| ComfyUI-SeqImageLoader | 2024-04-06 | 18 | bruefire/ComfyUI-SeqImageLoader |
| ComfyUI-TeaNodes | 2024-02-07 | 10 | TeaCrab/ComfyUI-TeaNodes |
| ComfyUI-VideoHelperSuite | 2024-04-17 | 368 | Kosinkadink/ComfyUI-VideoHelperSuite |
| ComfyUI-WD14-Tagger | 2024-04-04 | 19 | pythongosssss/ComfyUI-WD14-Tagger |
| ComfyUI-YoloWorld-EfficientSAM | 2024-04-17 | 0 | ZHO-ZHO-ZHO/ComfyUI-YoloWorld-EfficientSAM |
| ComfyUI-deepcache | 2023-12-26 | 0 | styler00dollar/ComfyUI-deepcache |
| ComfyUI-paint-by-example | 2024-01-29 | 0 | Kangkang625/ComfyUI-paint-by-example |
| ComfyUI-post-processing-nodes | 2024-02-07 | 14 | EllangoK/ComfyUI-post-processing-nodes |
| ComfyUI-sampler-lcm-alternative | 2024-04-07 | 20 | jojkaart/ComfyUI-sampler-lcm-alternative |
| ComfyUI_IPAdapter_plus | 2024-04-16 | 51 | cubiq/ComfyUI_IPAdapter_plus |
| ComfyUI_Seg_VITON | 2024-02-07 | 0 | StartHua/ComfyUI_Seg_VITON |
| ComfyUI_TiledKSampler | 2024-04-08 | 0 | BlenderNeko/ComfyUI_TiledKSampler |
| ComfyUI_UltimateSDUpscale | 2024-03-30 | 118 | ssitu/ComfyUI_UltimateSDUpscale |
| ComfyUI_VLM_nodes | 2024-04-15 | 104 | gokayfem/ComfyUI_VLM_nodes |
| ControlNet-LLLite-ComfyUI | 2024-03-15 | 0 | kohya-ss/ControlNet-LLLite-ComfyUI |
| DZ-FaceDetailer | 2023-12-16 | 0 | nicofdga/DZ-FaceDetailer |
| EtherRoulette | 2015-08-08 | 0 | KevinJiao/EtherRoulette |
| FreeU_Advanced | 2024-03-05 | 10 | WASasquatch/FreeU_Advanced |
| GFPGAN | 2024-04-02 | 0 | TencentARC/GFPGAN |
| Hybooru | 2022-05-31 | 87 | funmaker/Hybooru |
| MergeBlockWeighted_fo_ComfyUI | 2023-05-23 | 0 | Nezarik-Intmax/MergeBlockWeighted_fo_ComfyUI |
| PeercoinBlockExplorer | 2014-03-19 | 9 | FuzzyBearBTC/PeercoinBlockExplorer |
| PowerNoiseSuite | 2023-09-19 | 5 | WASasquatch/PowerNoiseSuite |
| SD-Latent-Interposer | 2024-03-20 | 4 | city96/SD-Latent-Interposer |
| SD-Latent-Upscaler | 2023-11-27 | 0 | city96/SD-Latent-Upscaler |
| SimpleLTC | 2013-07-28 | 0 | process/SimpleLTC |
| WAS_Extras | 2023-11-20 | 28 | WASasquatch/WAS_Extras |
| blibla-comfyui-extensions | 2024-02-25 | 10 | blib-la/blibla-comfyui-extensions |
| catcoin | 2013-12-29 | 2 | kR105-zz/catcoin |
| comfyui-animatediff | 2024-01-06 | 0 | SipherAGI/comfyui-animatediff |
| comfyui-auto-nodes-layout | 2023-09-21 | 18 | phineas-pta/comfyui-auto-nodes-layout |
| comfyui-fitsize | 2023-12-03 | 0 | bronkula/comfyui-fitsize |
| comfyui-mixlab-nodes | 2024-04-18 | 366 | MixLabPro/comfyui-mixlab-nodes |
| comfyui-portrait-master | 2024-03-04 | 60 | florestefano1975/comfyui-portrait-master |
| comfyui-previewlatent | 2024-02-15 | 2 | martijnat/comfyui-previewlatent |
| comfyui-prompt-control | 2024-04-17 | 487 | asagi4/comfyui-prompt-control |
| comfyui-prompt-reader-node | 2024-04-08 | 32 | receyuki/comfyui-prompt-reader-node |
| comfyui-tooling-nodes | 2024-03-04 | 135 | Acly/comfyui-tooling-nodes |
| comfyui-ultralytics-yolo | 2024-04-16 | 7 | shadowcz007/comfyui-ultralytics-yolo |
| demofusion-comfyui | 2023-12-19 | 0 | deroberon/demofusion-comfyui |
| dk-xbmc-repaddon-rep | 2015-04-26 | 0 | ak0ng/dk-xbmc-repaddon-rep |
| ethereum-powerball | 2014-12-10 | 0 | PeterBorah/ethereum-powerball |
| feedie | 2017-02-22 | 3 | meigrafd/feedie |
| frame-interpolation | 2023-08-24 | 0 | google-research/frame-interpolation |
| grok-1 | 2024-08-30 | 0 | xai-org/grok-1 |
| images-grid-comfy-plugin | 2024-02-23 | 7 | LEv145/images-grid-comfy-plugin |
| lora-info | 2024-04-18 | 22 | jitcoder/lora-info |
| masquerade-nodes-comfyui | 2024-02-26 | 1 | BadCafeCode/masquerade-nodes-comfyui |
| moneypot | 2014-10-03 | 315 | hajoxx/moneypot |
| mpos_ufc | 2013-10-13 | 0 | iamsirius2/mpos_ufc |
| pastemon | 2012-10-31 | 0 | xme/pastemon |
| php-mpos | 2014-03-22 | 1083 | MPOS/php-mpos |
| rgthree-comfy | 2024-04-18 | 200 | rgthree/rgthree-comfy |
| sd-dynamic-thresholding | 2024-03-21 | 11 | mcmonkeyprojects/sd-dynamic-thresholding |
| sdxl_prompt_styler | 2024-03-24 | 0 | twri/sdxl_prompt_styler |
| segment-anything | 2024-04-17 | 3 | facebookresearch/segment-anything |
| sleth | 2015-06-10 | 0 | jorisbontje/sleth |
| stability-ComfyUI-nodes | 2023-08-18 | 0 | Stability-AI/stability-ComfyUI-nodes |
| stable-diffusion-prompt-reader | 2024-03-21 | 28 | receyuki/stable-diffusion-prompt-reader |
| stratum-mining-maxcoin | 2014-02-06 | 7 | prydie/stratum-mining-maxcoin |
| style_aligned_comfy | 2024-03-12 | 7 | brianfitzgerald/style_aligned_comfy |
| tabbyAPI | 2024-05-03 | 915 | theroyallab/tabbyAPI |
| tribeca | 2015-07-07 | 295 | michaelgrosner/tribeca |
| yk-node-suite-comfyui | 2023-03-28 | 0 | yankeguo-deprecated/yk-node-suite-comfyui |

### Keep — forks with unique commits (59)

| Repo | Last push | Ahead | Behind | Status |
|---|---|---|---|---|
| efficiency-nodes-comfyui-updates | 2024-06-20 | 158 | 3 | diverged |
| AnimeBoya | 2021-12-27 | 99 | 0 | ahead |
| NodeGPT | 2024-02-01 | 66 | 0 | ahead |
| p2pool-rav | 2013-12-11 | 51 | 116 | diverged |
| was-node-suite-comfyui | 2024-06-13 | 44 | 116 | diverged |
| ComfyUI_tinyterraNodes | 2024-06-16 | 20 | 84 | diverged |
| ComfyUI-Manager | 2024-06-16 | 20 | 3045 | diverged |
| ComfyUI_essentials | 2024-06-16 | 18 | 69 | diverged |
| srl-nodes | 2024-06-13 | 14 | 6 | diverged |
| ComfyUI_Comfyroll_CustomNodes | 2024-06-03 | 11 | 0 | ahead |
| mikey_nodes | 2024-06-16 | 10 | 22 | diverged |
| ComfyUI-Impact-Pack | 2024-05-15 | 10 | 265 | diverged |
| comfyui_controlnet_aux | 2024-05-15 | 8 | 174 | diverged |
| comfy_mtb | 2024-05-15 | 8 | 168 | diverged |
| comfyui-inpaint-nodes | 2024-05-08 | 8 | 46 | diverged |
| bsz-cui-extras | 2024-05-08 | 7 | 0 | ahead |
| wlsh_nodes | 2024-06-03 | 6 | 1 | diverged |
| cd-tuner_negpip-ComfyUI | 2024-05-08 | 6 | 0 | ahead |
| a-person-mask-generator | 2024-05-08 | 6 | 42 | diverged |
| ComfyUI-Model-Manager | 2024-05-08 | 6 | 353 | diverged |
| comfyui-dynamicprompts | 2024-06-03 | 5 | 0 | ahead |
| cg-image-picker | 2024-05-11 | 5 | 31 | diverged |
| comfyui_easy_padding | 2024-05-08 | 5 | 8 | diverged |
| comfy_PoP | 2024-05-08 | 5 | 15 | diverged |
| Comfyui_joytag | 2024-05-08 | 5 | 0 | ahead |
| ComfyUI_experiments | 2024-05-08 | 5 | 0 | ahead |
| ComfyUI_Dave_CustomNode | 2024-05-08 | 5 | 0 | ahead |
| ComfyUI_Cutoff | 2024-05-08 | 5 | 0 | ahead |
| ComfyUI_ADV_CLIP_emb | 2024-05-08 | 5 | 0 | ahead |
| comfyui-workspace-manager | 2024-05-02 | 5 | 192 | diverged |
| electrum-cracker | 2013-12-07 | 4 | 0 | ahead |
| facerestore_cf | 2024-05-08 | 4 | 6 | diverged |
| cg-noise | 2024-05-08 | 4 | 3 | diverged |
| Comfy_KepMatteAnything | 2024-05-08 | 4 | 0 | ahead |
| ComfyUi_NNLatentUpscale | 2024-05-08 | 4 | 0 | ahead |
| ComfyUI_fabric | 2024-05-08 | 4 | 1 | diverged |
| ComfyUI_SeeCoder | 2024-05-08 | 4 | 0 | ahead |
| ComfyUI_Noise | 2024-05-08 | 4 | 2 | diverged |
| ComfyUI_InstantID | 2024-05-08 | 4 | 21 | diverged |
| ComfyUI_FizzNodes | 2024-05-08 | 4 | 40 | diverged |
| cg-use-everywhere | 2024-05-02 | 4 | 398 | diverged |
| ComfyUI-Llama | 2024-04-02 | 3 | 0 | ahead |
| ComfyUI-Moore-AnimateAnyone | 2024-03-16 | 3 | 0 | ahead |
| freecoins | 2013-03-16 | 3 | 0 | ahead |
| sd-model-manager | 2024-05-08 | 3 | 0 | ahead |
| Comfyui_segformer_b2_clothes | 2024-05-08 | 3 | 5 | diverged |
| ComfyUI_StreamDiffusion | 2024-05-08 | 3 | 6 | diverged |
| ComfyUI_ResolutionSelector | 2024-05-08 | 3 | 24 | diverged |
| ComfyUI_PerpWeight | 2024-05-08 | 3 | 8 | diverged |
| ComfyUI_Jags_VectorMagic | 2024-04-24 | 3 | 16 | diverged |
| ComfyUI_Custom_Nodes_AlekPet | 2024-04-24 | 3 | 257 | diverged |
| ComfyUI_3dPoseEditor | 2024-04-24 | 3 | 5 | diverged |
| ultimate-upscale-for-automatic1111 | 2024-04-24 | 2 | 0 | ahead |
| comfyui-PromptAttention | 2024-04-18 | 2 | 2 | diverged |
| llm-prompt-templates | 2024-04-18 | 1 | 11 | diverged |
| comfyui-nodes-docs | 2024-07-07 | 1 | 4 | diverged |
| ComfyUI-Image-Saver | 2024-06-03 | 1 | 182 | diverged |
| Derfuu_ComfyUI_ModdedNodes | 2024-05-08 | 1 | 11 | diverged |
| ComfyUI-SaveImageWithMetaData | 2024-12-01 | 0 | 51 | behind |

Notable keeps: efficiency-nodes-comfyui-updates (+158), AnimeBoya (+99), NodeGPT (+66), p2pool-rav (+51), was-node-suite-comfyui (+44). Most ComfyUI-node forks carry small 2024-era patch sets.
Compare errors: MagiskOnWSA, comfyui-reactor-node — both return 403 "repository access blocked" (GitHub TOS-block), so they cannot be compared via API; classify manually.

## 3. Oversized + visibility sanity

### Blobs >50MB in the 8 largest repos (git trees API)
- **moonbox-live** (PVT, 705MB, tree truncated at 49,757 entries): 88.7MB `BACKUP-1787105555/original/user_pasted_clipboard_long_content_as_file_{ log { ve.txt`, 86.3MB `.git_repos/toxicwind-repos.git/objects/pack/pack-07bdd44e1cbf5b1f74c947d0227b3a6035826c3a.pack` (nested git repo checked in!), 83.5MB `504_audit.pcap`, 52.0MB clipboard txt duplicate.
- ComfyUI-ArtGallery (pub, 1.7GB), effusion-labs (pub, 551MB), sovereign-pi-archive (PVT, 537MB), sovereign (pub, 404MB), sovereign-zed (pub, 369MB), mcpproxy-go (pub, 211MB), zedra-sovereign (pub, 103MB): **no blobs >50MB in default-branch trees** — bulk is many small files / history depth, not single-file violations.

### Private-repo visibility sanity (173 PVT)
- 3 largest private: moonbox-live (705MB), sovereign-pi-archive (537MB), _git (354MB) — LFS/archive candidates.
- 107 small (<5MB) private repos pushed in the last 90 days — publish-or-delete review backlog. Heaviest concentration: ~20 `moonbox-*` snapshot repos from 2026-08-22/23 (many 0–4KB, likely automation debris: moonbox-files-v2, moonbox-packages-20260823, moonbox-output-20260822, moonbox-loops--20260822, etc.), plus test-1787449974, forge-test-1786623471, unwatermarked, arc-agi-ops, kataware-doki (all 0KB).
- Credential-suggestive private names (verify before any publish): moonbox-.secrets-20260822, triangle-access-secrets, token-recovery-20260824, codex-backup, awesome-token-audit, walk-in-archive, skinwalker-research-archive, sovereign-router-backup, local-work-archive, star-loom-archive, sovereign-pi-archive.

## 4. Public non-fork metadata (42 audited of 56)

11 COMPLETE (README+description+license): ast-grep, additional-lens-profiles, youtube-403-bypass, codex-desktop-linux, playwright-mcp, python-sdk-auditor, nim-inkling-api-research, free-ai-models, web3-sec-workspace, py-compat-scan, nitrado_api_lib.
1 STUB: entropy-gpu (empty, 0KB — no README, no description, no license).
30 NEEDS-WORK — dominant gap is missing LICENSE (20 repos; 16 miss license alone): sovereign-scripts, sovereign-skills, huh, musepool, infra-recon, neo-osint, k3-capacity-hack, awesome-api-shape-explorer, awesome-agent-gateway-2026, ontological-atlas, skillforge, universal-search-fuzzer, agentic-moment-2026, py-agent-gateway, wllama-forge, strudel-sampler-server-vite (+ Boundless/description, mintlify-docs/description, paintball-field/description, python-script-collection/description, hls-proxy-aggregator/description, ComfyUI-TTools/description, optimized-cr3-repo/desc+license, codex-patcher-updater/desc+license, strudel-dev-vite/desc+license, RSSLive/desc+license).
4 repos lack a README: yt-dlp-universal-wrapper, bashrc-quote-fix, wii-stream-pack, wii-meta-client, universal-search-fuzzer.

## Raw data
- Inventory: ~/workspace/repo_inventory_20260914.txt
- /tmp/audit_A.md, /tmp/audit_results.json (recent-active)
- /tmp/audit_B_merged.json, /tmp/audit_B_cleanup.txt, /tmp/audit_B_progress.jsonl + _B2_ + _B3_ (fork compare)
- /tmp/auditC_task1_raw.json (oversized blobs); /tmp/pvt_recent_small.txt (107 small recent PVT)
- /tmp/audit_D.md, /tmp/audit_D.json (public metadata)

All work strictly read-only. No pushes, deletions, PRs, visibility changes, or issue comments were made.
