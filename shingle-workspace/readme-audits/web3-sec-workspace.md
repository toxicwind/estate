# README audit — toxicwind/web3-sec-workspace @ c49122b28a8ac53248a0cf2e2f090acd7b21112f — 2026-09-14

**Verdict:** NEEDS UPDATE

Audited via shallow clone (`git clone --depth 1`; the `api.github.com/.../tarball/{HEAD,main}` endpoints 404'd twice on the codeload redirect — replanned to clone). Mechanical audit run with `skills/readme-audit/bin/audit.py`. Note: audit.py false-positives on `./setup.sh` / `./start.sh` (its path matcher chokes on the `./` prefix; both files exist at root).

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| Tagline: "**Private**. Sovereign. 2026-grade." | `GET /repos/toxicwind/web3-sec-workspace` → `private: false` (public) | WRONG |
| "never push this workspace itself" (Extending) | repo is public at github.com/toxicwind/web3-sec-workspace, pushed 2026-09-14 | STALE |
| See `.github/dependabot.yml` (Sovereign AI Layer section) | `.github/workflows/` contains only `codeql.yml`; no dependabot.yml in tree | WRONG |
| "Sovereign Secrets & MCP Stack" — real key names (TELEGRAM_BOT_TOKEN, sovereign_mesh SECRET_KEY, CONTEXT7_API_KEY ctx7sk-...) in `~/.grok/.secrets` | machine-local notes in a **public** README; contradicts the "secret-hygiene first / never commit keys" section directly above it | MISMATCH (flag) |
| Quickstart: `./setup.sh`, `./start.sh` | both exist at root, executable | VERIFIED |
| `make lint TARGET=...`, `make fang TARGET=... [AGENT=...]` | Makefile:38 `lint audit:` → `bin/lint_all.py`; Makefile:45 `fang ai-audit:` → `bin/audit_fang.py --agent` | VERIFIED |
| `bin/lint_all.py` multi-engine orchestrator | bin/lint_all.py:7,86,105-123 runs slither/aderyn/solhint/solidityguard | VERIFIED |
| `python bin/audit_fang.py . --agent security-auditor` | bin/audit_fang.py exists; `--agent` flag at :50 | VERIFIED |
| OpenFang local port 14720, `~/.local/bin/openfang` | bin/audit_fang.py:28-29 defaults match; `.env.example`: `OPENFANG_API=http://127.0.0.1:14720` | VERIFIED |
| vLLM port 14718, `OPENFANG_API/BIN`, `VLLM_PORT`, `VLLM_API_KEY` env families | `.env.example` has all four (VLLM_PORT=14718) | VERIFIED |
| `ETHERSCAN_API_KEY` `_1`–`_6` rate-limit pooling | `.env.example`: base key + commented `_1`..`_6` | VERIFIED |
| `GITHUB_TOKEN` for `bin/ghas.sh` | `.env.example` has it; bin/ghas.sh:82-85 references grok_com_github MCP `run_secret_scanning` | VERIFIED |
| `ai/agents/solidity-security-auditor/agent.toml` | exists | VERIFIED |
| `scripts/setup-sovereign-ai.sh` | exists | VERIFIED |
| `docs/SIGNALS.md` ("heart of the 2026 platform") | exists | VERIFIED |
| `config/slither.config.json`, `aderyn.config.toml`, `.solhint.json` | all three exist | VERIFIED |
| `scripts/lib.sh`, `setup-*.sh`, `setup-submodules.sh` | lib.sh + 6 setup-*.sh + setup-submodules.sh + verify.sh | VERIFIED |
| "Git submodules pin every external tool at a known-good state" | `git ls-tree HEAD`: krait@441a5b7, RugProof@ff2e6fe, honeypotscan@fa2693c, damn-vulnerable-defi@6797353 | VERIFIED |
| `tools/solql/` placeholder, "upstream unavailable at creation", see `tools/solql/README.md` | solql is a committed tree (not submodule), README.md present | VERIFIED |
| Sub-tool `.env.example` e.g. `tools/honeypotscan/.env.example` | empty in shallow clone (submodule uninit) but exists upstream (Teycir/honeypotscan, 477 bytes via contents API) | VERIFIED |
| `.github/workflows/codeql.yml` GHAS integration | exists; matrix `['python']` with comment matching commit c49122b (JS/TS dropped 2026-09-14) | VERIFIED |
| `reports/`, `logs/` gitignored | `.gitignore`:4-5 | VERIFIED |
| License MIT © 2026 toxicwind | LICENSE: MIT, Copyright (c) 2026 toxicwind | VERIFIED |
| `start.sh` "drops you into the activated environment" | start.sh:10-13 venv activate, :58 exec shell | VERIFIED |
| Setup installs slither/mythril/echidna/medusa/foundry | setup-python.sh (slither), setup-fuzzers.sh (echidna+medusa), setup.sh/setup-sovereign-ai.sh (foundryup) | VERIFIED |
| `./setup.sh` idempotent, ~15–25 min | not runnable in audit sandbox; script has guards but duration unverified | UNVERIFIED |
| vLLM "currently Qwen2.5 on port 14718 in your environment" | environment-specific, not derivable from tree | UNVERIFIED |
| `cd tools/honeypotscan && npm run dev` | submodule empty locally; script presence unverified | UNVERIFIED |

## Missing from README

Real features/changes with no README coverage (all minor):

- `make verify` / `scripts/verify.sh` max-level verification (added 2026-05-30, commits 69815c7, 991c691) — not mentioned anywhere in README.
- `make doctor` target — not mentioned.
- `setup.sh --verify` strict-mode flag (commit 991c691) — not documented.
- Latest commit c49122b (CodeQL: drop javascript-typescript) — checked, needs no README change (README never enumerates CodeQL languages). No action.

## Quickstart check

- [x] Commands exist (`./setup.sh`, `./start.sh`, `make lint/fang`, `python bin/*.py`)
- [x] Ports/config keys match code (14720/14718 in both `bin/audit_fang.py` and `.env.example`)
- [x] A fresh user could follow it end to end (submodule warning is correct and prominent; `--recurse-submodules` emphasized)

## Action taken

- None — REPORT ONLY per task instructions. Recommended fixes for owner: (1) drop "Private" from the tagline (repo is public) and reconcile the "never push this workspace itself" line; (2) remove the `.github/dependabot.yml` reference or add the file; (3) scrub or relocate the "Sovereign Secrets & MCP Stack" section — naming live key families in a public README undercuts the repo's own secret-hygiene section; (4) optionally document `make verify` / `make doctor`.
