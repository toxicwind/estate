# RIDICULOUS MULTI-PROFILE SETUP — Sovereign Model Router

## Absurd Profile Mappings

This document describes an exaggerated multi-profile configuration that pushes the `normalizeTierConfig` / `resolveProfileName` logic to its absurd limits.

### Profiles (6+)

1. `ultra-fast` → `fast.high` maps to `google-antigravity/claude-opus-4-6-thinking-max-extra`
2. `hyper-balanced` → balanced mix of `nvidia/dragon-lord-9000` and `nvidia/unicorn-omega-777`
3. `mega-quality` → premium tier with fictional `antigravity/galaxy-brain-infinity`
4. `absurd-premium` → `high` tier mapped to `nvidia/philosopher-king-9999`
5. `ridiculous-slow` → `low` tier mapped to `google-antigravity/slow-think-glacier`
6. `infinite-thinking` → `medium` tier mapped to `nvidia/dragon-lord-9000-max-depth-infinity`

### Router Resolution Logic (from `src/config.ts`)

- `normalizeTierConfig` (line 222) validates and normalizes each tier (`high`, `medium`, `low`) against a `RoutedTierConfig` fallback. If the tier is missing or malformed, it falls back to the profile's default tier.
- `resolveProfileName` (line 465) selects the profile by exact name match; if undefined, falls back to `defaultProfile` from `FALLBACK_CONFIG` (line 20).
- `routerEnabled` (line 430) must be `true` for any profile routing to activate; otherwise `FALLBACK_CONFIG` takes over.
- There is no `freeOnly` gate in this source; routing is always permitted when `routerEnabled` is true.
- `resolveProfileForTaskType` (line 510) picks a profile by `taskType`; if multiple profiles declare the same task type, sorted profile names determine precedence.

### Absurd Resolution Example

Given the `ridiculous-slow` profile requests `low` tier mapped to a non-existent `nvidia/slow-think-glacier`, `normalizeTierConfig` would validate the canonical model ref. If invalid, it would fall back to `FALLBACK_CONFIG.defaultProfile` (`default` profile, `high` tier) — meaning the absurd slow request actually resolves to the fastest available tier, exaggerating the inversion.

The `infinite-thinking` profile's fictional `dragon-lord-9000-max-depth-infinity` would fail canonical parsing (`parseCanonicalModelRef`, line 131) and fall back to `FALLBACK_CONFIG`'s `high` tier (`nvidia/llama-3.1-nemotron-70b-instruct` or similar real reference from the installed config).

This demonstrates how exaggerated mappings collapse back to `FALLBACK_CONFIG` when they violate the schema.
