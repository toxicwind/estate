# 2026-10-30 — AutoModel + deploy-stack autofix sweep

Dossier for anomaly-table rows 69-72 (AGENTS.md §7). All findings verified live
by the tau session 01a18aa0 (2026-10-30 ~02:25-03:2xZ).

## 69 — NativeLink ghost config path (REAPI never started)

- **Symptom**: `estate/nativelink` daemon `available` (never running);
  REAPI :25155/:25157 ECONNREFUSED; forge remote cache degraded to flicker-only.
- **Root cause**: `forge/ops/nativelink/run.sh` exec'd
  `/home/toxic/pens/estate/config/nl/nativelink.json5` — a path that died in the
  pens reorg. Real config: `pens/estate/config/nativelink/nativelink.json5`.
- **Fix**: repointed run.sh; `pitchfork restart estate/nativelink` — both ports
  now answer HTTP ("No route for /" = listening; health is gRPC-side on the
  worker). Committed+pushed to toxicwind/forge.

## 70 — android-fleet tree deleted under a live daemon def

- **Symptom**: `estate/flotilla-mcp` errored (`ERR_INVALID_ARG_TYPE` Oct 29
  17:20 at a path that no longer existed); `~/pens/ranch/android-fleet` empty;
  `ranch/products/android-fleet` MISSING; no git history in pens.
- **Root cause**: the peer repo was deleted with its `.git`; pitchfork defs
  (flotilla-mcp + pixel-adb-keepalive) pointed at the corpse.
- **Fix**: re-cloned `github.com/toxicwind/android-fleet` (pushed 01:06Z the
  same night) into the def path; flotilla-mcp live on :25245, phone-bridged
  (`device: 10.0.0.77`). Note: pitchfork's state label stays "errored" while
  the process is healthy — stale-state cosmetic, same class as awrawr-mcp.

## 71 — .bashrc canary regressed AGAIN (kappa installer)

- **Symptom**: `export KAPPA_ALLOW_HOME_INDEXING=1` appended AFTER the S13
  canary — sentinel no longer the physical last line (2nd occurrence; the
  2026-10-28 RIPGREP_CONFIG_PATH case was the first).
- **Fix**: export moved into S0 (universal env tier) with a comment; canary is
  the last line again. Rule doc: `docs/bashrc-canary-rule.md`. ALSO FIXED same
  session: tty flow-control freeze (hold ctrl + type `s` = XOFF hang) —
  `stty -ixon` + readline `\C-s` unbind in S6.

## 72 — freeinference intermittent weekly 429 + dead retry

- **Symptom**: `freeinference/glm-5.3-flash` 429 "Weekly/Monthly Limit
  Exhausted" (reset 2026-11-04 09:30:58) with retry-after ≈ 457,162,630ms —
  blew past `retry.maxDelayMs` (300s) and the turn DIED. Minutes later the
  same key+model answered 200: the quota is **per-model, intermittent,
  fleet-side** — not per-key.
- **The "other model"**: the auto-thinking judge lane resolved
  `freeinference/qwen3.6-35b` (worked, 776 tokens) while the main lane sat on
  the exhausted glm selector with **no chain owning freeinference models**.
- **Fix**: `retry.fallbackChains` gained `freeinference/*` (qwen3.6-35b →
  deepseek-v4-flash → nvidia NIM → openrouter free trio) and a universal
  `default` chain. Verified: config loads clean via the pinned dist, replay
  turns land, engine chain/wildcard tests 97/99 (2 fails = missing bundled
  fixtures, not logic).
- **Side finding**: tau `-p` "Model not found" from random cwds was a
  models.yml root mismatch (engine reads `~/.tau/agent/models.yml`; mimetite
  regen 02:53 synced it). PI_CONFIG_DIR resolution itself is home-anchored and
  correct.
