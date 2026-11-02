# Geode router-master audit — 2026-11-02 (tau)

## Verdict
**`rhodochrosite` (geode, repo `toxicwind/hodos`, :25193) IS already the master-of-routers tool.** The naming confusion is not the tool's name — it's that **tau configs branded rhodochrosite as a *provider*** instead of the geode routing tool it is. The mineral theme is the geode brand and is coherent.

## The routing dynasty (geode-owned)
| Tool | Repo | Status | Role |
|------|------|--------|------|
| `chalcopyrite` | toxicwind/chalcopyrite | **RETIRED** (was canonical 10-02→10-26) | prior router, superseded |
| `rhodochrosite` | toxicwind/hodos | **LIVE** (:25193) | multi-provider inference gateway (16 providers: NIM/freeinference/openrouter/groq/…) |
| `pylae` | toxicwind/flocksync | legacy OmniRoute UI-era | superseded by rhodochrosite |
| `opal` | toxicwind/theta | live :25109 | Gemini EAP (tool-retrieval) provider engine |

## The confusion (root)
tau `models.yml` + `model-router.json` name provider blocks after the router:
- `rhodochrosite:` → :25193 (correct)
- `rhodochrosite.chalcopyrite:` → :25200 (ECONNREFUSED — dead ghost)
- `rhodochrosite.secure-nim:` → integrate.api.nvidia.com (HTTP:000 dead)
- `rhodochrosite.azurite:` / `google:` → :25109 gemini-eap
- `nvidia:` → integrate.api.nvidia.com (HTTP:000 dead)

So "rhodochrosite" reads as a provider brand, and the dead NIM sub-blocks silently 502 every model routed through them (the "fallbacks are ass, especially VL" report).

## Recommendation (architect decides the brand)
1. **Keep rhodochrosite** as the geode router tool name (mineral theme + hodos repo identity).
2. **Rename the provider blocks** in tau configs to what they actually are: `nvidia-hub` (dead → retire), `gemini-eap` (one block, kill the `rhodochrosite.azurite` duplicate), drop `rhodochrosite.chalcopyrite` + `nvidia` ghosts.
3. **Selectors** become `geode/rhodochrosite/<model>` (tool-scoped) instead of `rhodochrosite/<model>` (provider-branded) — one rename, clearer ownership.

## Immediate fixes already landed (tau, this session)
- models.db refreshed (rhodo 499/nanogpt 1175/openrouter 413; VL present)
- router profiles cheap/fast/balanced/backup → verified-200 freeinference lanes (deepseek-v4-flash/qwen3.6-35b/glm-5.3-flash)
- stale test-fixture plugin removed (was breaking `tau models refresh`)
- VL-lane anomaly ticketed (NIM HTTP:000)