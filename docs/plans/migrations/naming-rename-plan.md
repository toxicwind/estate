# Naming Rename Plan (2026-09-20, naming-auditor)

## Audit verdict

| Check | Result |
|-------|--------|
| Alias collisions (one alias → 2+ models) | **0** — clean |
| True shadowing (alias == another model block) | **0** — clean (aliases appear in `/v1/models` by design; that is advertisement, not shadowing) |
| Duplicate upstream claims | **3 builds, legitimate**: `qwen3.5-9b-deepseek-v4-flash` exists as `mradermacher` i1 q4_k_m, `mradermacher` i1 q4_k_s, `jackrong` da q4km — differ by builder+quant+ctx; MODEL-MAX winner (`jackrong` da) marked |
| Stale/dead consumer refs | **1**: router profile `backup` → `herd/pollinations-free/openai` (peer removed; model does not exist) — **FIX APPLIED** |
| Misleading generic aliases | **7 grandfathered** (`fast`, `tiny`, `small`, `medium`, `code`, `long`, `uncensored`); `large`+`quality` already quarantined (they 500'd) |
| Double-qualified IDs | Inherent for peers (`mistral/mistral-medium-latest` — upstream API ID is verbatim, proxy needs it); forbidden to invent deeper levels |
| Phantom names | `herd-race`: 0 hits anywhere — no action. `hf-free`, `openrouter-kimi`: comments only (disabled peers, documented history) |
| Dead macro | `HERETIC_27B_Q5XL` defined, never referenced — **REMOVED** |
| Orphaned code refs | `src/services/reasoning-router.ts` references quarantined models (`beellama/gemma-mtp-64k`, `ik_llama/heretic-ud-96k`) but nothing imports it — orphaned, noted not fixed (dead code, separate cleanup) |

## Changes applied

### 1. `~/.tau/model-router.json` — backup profile (dead route fix)
- `profiles.backup.selector`: `herd/pollinations-free/openai` → `herd/gemma-4-12b-unified`
- Why this pick: measured HEALTHY local (499ms TTFT p50, 92 RPM), different model from `balanced` (real redundancy), zero external API dependency.

### 2. `sovereign/config/herd.yaml` — canonical alias additions (additive only)
| New alias | Model block | Supersedes (deprecated, still works) |
|-----------|-------------|--------------------------------------|
| `exaone-1.2b-iq4xs-32k` | `beellama/exaone-4-0-1-2b-iq4xs` | `fast`, `tiny` |
| `qwen3.5-9b-i1-q4km-64k` | `mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m` | `small` |

### 3. `sovereign/config/herd.yaml` — dead macro removal
- Removed `macros.HERETIC_27B_Q5XL` (referenced nowhere; model quarantined).

## Explicitly NOT renamed (decision points)

- **Peer names** (`openrouter-ling` vs `openrouter-free`, `flock-direct`, `toolcall-local`): renaming a peer changes live model IDs (`{peer}/{upstream}`) with no alias mechanism — unsafe. Documented in grammar instead.
- **Tau provider/lane names** (`herd`, `sovereign`): established across tau engine configs; renaming breaks the provider map. Documented as canonical lane names.
- **Tau role names** (`tiny`, `smol`, `fast` profile): separate namespace from herd aliases; the `fast` profile → `herd/beellama/qwen-flash-64k` vs `fast` alias → exaone is documented as a known meaning-collision, not a technical one.
- **Generic aliases** (`fast`, `tiny`, `small`, `medium`, `code`, `long`, `uncensored`): live consumers exist (`null-g-proxy`, `fast_race.py` use `fast`). Kept working, marked deprecated, validator bans NEW ones.
- **`reasoning-router.ts`**: orphaned file with stale refs; dead code removal is a separate cleanup, not a naming change.

## Verification
- `validate.py`: 0 failures on final state (run: `python3 /home/toxic/sovereign/projects/naming-audit/validate.py`)
- herd `/v1/models`: new aliases advertised, no dead IDs
- `tau -p` sanity prompt via default route: OK (only if herd.yaml was touched — alias additions trigger watch-config reload)
