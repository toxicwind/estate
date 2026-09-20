# MERGE.md — Maximal merge decision record

Branch `maximal-merge` on `toxicwind/nvidia-swarm-lens` (2026-09-14).
Main is untouched; all sources are read-only. No credentials are stored
anywhere in this branch.

## Per-source verdict

### 1. `toxicwind/nvidia-swarm-lens` (main) — MERGE SUBJECT, kept as chassis
The only source with a real package structure. First-party code is ~25 files
/ ~2,200 lines (`swarm/`, `lens/`, `launcher.py`, `osint_runner.py`); the
rest is vendored deps, bytecode, and binaries. Verdict: **keep the chassis,
fix the rot, re-base the models.**

Rot fixed on this branch:
- `lens/profiles.py` was a one-line stub (`# profiles`) while
  `lens/__init__.py` and `launcher.py` import from it → the repo's main
  entry was **unimportable**. Implemented the real registry (5 lenses,
  model constants, `build_swarm_from_lens()`).
- Default model `meta/llama-3.1-405b-instruct` everywhere (transport, core,
  agent, lens profiles, mcp_servers.json) — **delisted from the catalog**;
  replaced with `openai/gpt-oss-20b` (alive-fast, 2026-09-14 audit).
- `PersistentConnectionPool`: 120s total / 30s connect timeouts → **5s / 3s**
  fail-fast. `NvidiaSwarm` default concurrency 50 → 8.
- `NvidiaNIMClient` defaulted to streaming but parsed the response as plain
  JSON (broken SSE) — streaming now has a dedicated, stall-guarded path in
  `nim/`; the legacy client keeps its shape for compatibility.
- `launcher.py` silently fell back to mock when no key was present → now
  raises `LauncherAuthError`; mock is explicit (`--mock`) only. Subsystems
  (ZMQ/proxy/MCP/git/unshare/envd) are opt-in flags, not auto-init.
- `.github/workflows/ci.yml` compiled nonexistent paths
  (`src/nvidia_swarm/*`, …) → now compiles the real tree.
- `swarm_maximal.py` was `# swarm` → now the real maximal runner.

Dropped on this branch (documented, still on main):
- `bin/pylibs/` — 230 vendored third-party files (pip/requirements exist).
- `**/__pycache__`, `*.pyc` — 214 stale bytecode files.
- `.env` — committed secrets (GITHUB_PAT etc.). Never again.
- `bin/fast-browser-use-research-grade.zip` — 7KB binary; docs kept in `skills/`.
- `bin/osint_runner.py` — duplicate of top-level `osint_runner.py` (kept).
- `logs/` — committed run artifacts (png/json), not source.

### 2. Drive `nvidia_lens_swarm_maximal.py` (499 lines) — MINED, not adopted
Self-contained single-file variant. ~70% overlaps the repo (DAG, grammar,
Llama-3.1 template). Its transport is a **simulation** (sleeps, fabricates
text/metrics) — must never look production-ready. Unique value extracted:
- **ArchiveFS** → `swarm/nvidia_swarm_archivefs.py` (hardened: no symlink
  following on pack, no path traversal on unpack, index sanity caps).
- Transport presets (architectural/cognitive/bleeding) →
  `swarm/transport_profiles.py` (renamed; re-based to 5s fail-fast, hosted NIM).
- `<tool_call>` tag grammar → `TagGrammarConstraint` in
  `swarm/nvidia_swarm_agent.py` (`grammar_mode="tag"` option).

### 3. Drive `nvidia_swarm_standalone.py` (429 lines) — SUPERSEDED
Earlier variant of the same single-file design; its client is also simulated.
Unique bits folded in: `timeout_per_node` semantics, `custom_func` node hooks,
`grammar_enforced` flag. Not kept as a separate file — see overlap map.

### 4. `toxicwind/nvidia-nim` (spec fork) — READ-ONLY REFERENCE
319 blobs of OpenAPI specs/protos for NIM. Spec-patch home, not runtime.
Referenced for endpoint shapes; nothing copied (the client follows the local
loader's proven wire behavior instead).

### 5. Local `nvidia-nim-loader` + `model-ranking` skills — CONVENTIONS ADOPTED
- `bin/nim.py`'s surrogate-first auth pattern → `nim/client.py`
  (surrogate → `NVIDIA_API_KEY` → typed `NimAuthError`; sync stdlib-only,
  async via aiohttp).
- `rank.py`'s availability-weighted model table + the 2026-09-14 82-model
  probe results → `nim/models.py` (10 alive-fast, dead-404 legacy class,
  410 EOL, super-120b deprecation 2026-10-03, kimi-k3/ultra-550b cold-start).

## Overlap / duplication map

| Capability | Repo | Maximal.py | Standalone.py | Merged into |
|---|---|---|---|---|
| Async layered DAG executor | `swarm/nvidia_swarm_core.py` ✅ real | simpler DAG | simpler DAG | kept repo's (best) |
| Llama-3.1 prompt template | `nvidia_swarm_agent.py` | ✅ | ✅ | kept repo's |
| JSON tool grammar | `nvidia_swarm_agent.py` | `<tool_call>` tags | `<tool_call>` tags | both: `grammar_mode` |
| NIM transport | `nvidia_swarm_transport.py` (broken-ish) | **simulated** | **simulated** | new `nim/` layer |
| Triton gRPC | stub (needs grpcio) | **simulated** | — | kept stub, opt-in |
| Transport presets | — | ✅ architectural/cognitive/bleeding | — | `swarm/transport_profiles.py` |
| ArchiveFS | — | ✅ | ✅ | `swarm/nvidia_swarm_archivefs.py` |
| Agent lens profiles | `lens/profile.py` | transport-flavored | — | kept agent's; bridge in `lens/profiles.py` |
| Lens registry | `lens/profiles.py` = **stub** | — | — | implemented (fix) |
| ZMQ/proxy/MCP/git/unshare/envd | ✅ real integrations | — | — | kept, opt-in |
| OSINT runners | `osint_runner.py` ×2 (dup) | — | — | deduped to one |

## Deliberate non-goals
- No live NIM calls in tests/CI (no credentials in CI; audit data is vendored
  as of 2026-09-14 and must be re-verified, not re-probed blindly).
- Triton stays experimental — hosted NIM is the supported route.
- No changes to `toxicwind/nvidia-nim` (spec fork) or any source repo.
