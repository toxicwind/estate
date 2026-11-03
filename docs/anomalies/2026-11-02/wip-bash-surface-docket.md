# WIP Docket — bash surface + tau bash (collected 2026-11-02)

> architect: collected right this instant; bash tool disabled as a test; rewind+checkpoint denied; kairos autonomy LIVE; ffs-guide rewrite expansion committed.

## 1. Dotfiles (home, NOT git-tracked — no dots repo exists)

| file | state | WIP |
|---|---|---|
| ~/.bashrc (240L) | S0-S13 load order; S12 sources kairos shim; canary last | WIP (kairos shim S12 + .bashrc.env edits) |
| ~/.bashrc.env (175L) | BASH_ENV double-source REMOVED (2026-11-02); secretsmith auto-load; PATH rebuild; dead ~/.secrets block gone | clean |
| ~/.bashrc.local (17L) | dead ~/.secrets block REMOVED (2026-11-02) → warn-only | clean |
| ~/.bash_profile (18L) | line 10: export BASH_ENV → kairos/shim.sh (the ONE legit BASH_ENV home) | clean |
| ~/.profile (24L) | untouched | clean |

## 2. kairos shim chain (pens/olympus/products/kairos — repo HEAD a848a20, pushed)

| file | state |
|---|---|
| shim.sh (194L, generated) | AUTONOMOUS: _2s_wrap guard-violation → RF_BIN route not 126; head/tail/wc pipeline → passthrough; KAIROS_STRICT=1 restores cancel. DELEND_CODE_RACE → hephaistos plugin; RF_BIN → ~/.local/bin/run-fast. Regenerated from init.ts. |
| src/init.ts (202L) | SSOT template; KAIROS_STRICT escaped; hephaistos paths |
| src/runner.ts (1072L) | rewriteBanned: cat/less/more/head/tail→ffs read, find (bare needle)→ffs find, glob→ffs glob, grep/rg→ffs grep; INVISIBLE swaps; notice path for flag-bearing; KAIROS_STRICT=1 cancels. 77 tests pass. |

⚠ OPEN: live session env still exports stale DELEND_CODE_RACE=/home/toxic/pens/barn/estate-ops/delend-code-race (shim :- default never corrects inherited value) → unset + re-export needed in the parent session env.

## 3. tau bash tool surface (~/.tau/agent/config.yml)

| key | value | note |
|---|---|---|
| bash.enabled | false | native bash tool OFF (architect's test) |
| bashInterceptor.enabled | true | eval lane intercepts |
| checkpoint.enabled | true | gate denies via approval below |
| tools.approval | rewind: deny, checkpoint: deny | NEW (this session) |
| shell.env.PI_DISABLE_UUTILS_BUILTINS | "1" | role |
| shellMinimizer | enabled, aggressive | role |

## 4. How bash runs in tau (verified)
- Host tool name-gate (approval.ts → resolveApproval): deny = throw at tool call.
- Deny list → TAU_DENIED_TOOLS env for eval kernels (deny-policy.ts exec families: bash→bash,sh,dash,zsh,fish; grep→grep,rg,ripgrep,egrep,fgrep; find→find,fd,fdfind). NOT live in current eval kernel (no TAU_DENIED_TOOLS env).
- With bash tool off: eval (Bun) lane + native read/grep/glob + ffs/hf CLIs (Bun.spawn) are the sanctioned lanes.

## Next
- HF helper MCP entrypoints → pens-index mcp/server.ts (hf_embedding_models etc.)
- ≥6 cutting-edge Oct-2026 embedding models; fresh HF token needed (kite 401)
- Wire tiny CUDA-loading embed for insane-quick find (xerj lane or standalone)
- Fix stale DELEND_CODE_RACE in live session env