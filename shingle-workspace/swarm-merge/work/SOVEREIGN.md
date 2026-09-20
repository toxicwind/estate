# SOVEREIGN.md — Where this repo sits in Chris's constellation

## The constellation (2026-09-14)

| Repo / location | Role | Relationship to this merge |
|---|---|---|
| `toxicwind/sovereign` | **Control plane** (awrawr-pc `/home/toxic/sovereign`): llama-swap `:25100` OpenAI front door, yote `:25102`, openfang `:25103`, sovereign-router `:25104`, MCP gateway… | Untouched. This merge changes nothing operational. |
| `toxicwind/sovereign-projects` | **Workspaces monorepo**: yote/, openfang/, tau/, herd/, mesh/, qed/, shell/, boundless/ | Topology reference (below). |
| `toxicwind/sovereign-projects/tau/engine` | Canonical Tau agent engine; NVIDIA provider via `packages/catalog/src/compat/rules/providers/nvidia.kdl` + `auth/nvidia.kdl` | **Convergence target** — see below. |
| `toxicwind/nvidia-swarm-lens` (**this repo**) | NVIDIA NIM + swarm merger, lens profiles, async DAG | Merge subject. Conceptually **herd-adjacent**: an inference-consumer / agent-orchestration layer near the NIM API. |
| `toxicwind/nvidia-nim` | OpenAPI **specs** for NIM (fork of api-evangelist/nvidia-nim) | Read-only reference. Spec-patch home; not runtime. |
| `toxicwind/nvidia-nim-model-probe` | Public 82-model fail-fast audit + GitHub Pages | Ground truth for `nim/models.py`. Don't re-probe blindly. |
| `~/workspace/skills/nvidia-nim-loader/` | Local NIM client (`bin/nim.py`, surrogate auth) | Convention source for `nim/client.py`. |
| `~/workspace/skills/model-ranking/` | Curated model table (`rank.py`) | Data source for `nim/models.py`. |

## The seam: herd-adjacent, not herd

`herd/` is the inference router (llama-swap fork, `:25100/v1`). This repo is
*not* a router — it is a **model consumer + agent orchestrator**. The seam is
the wire protocol, and it is deliberately boring:

- `nim/` speaks plain OpenAI-compatible `/v1/chat/completions`. It can be
  pointed at herd's `:25100/v1` as easily as at `integrate.api.nvidia.com/v1`
  (pass `base_url`). No code changes needed on either side.
- Fail-fast budgets (5s), cold-start opt-in, and the dead-model guard live in
  `nim/` regardless of which upstream serves the tokens.

Nothing here assumes sovereign ports, pitchfork, or mise. The control plane
is untouched by this branch.

## Convergence note: tau's NVIDIA provider (not duplicated here)

Tau's engine is the *other* NIM consumer. Its wire-compat rules
(`providers/nvidia.kdl`) cover per-model thinking knobs (effort levels,
qwen chat-template format) — **not** client logic, so there is no duplication
with `nim/`. If `nim/` ever needs thinking-effort control
(`chat_template_kwargs` / `extra_body`), that KDL is the spec to follow.

**Live rot found while mapping (flagged, not fixed — sovereign-projects is
out of scope for this branch):**
- `auth/nvidia.kdl` validates the NVIDIA key against
  `nvidia/llama-3.1-nemotron-70b-instruct` — our 2026-09-14 probe verdict is
  **dead-404-gated**. Validation against a corpse means auth checks fail for
  the wrong reason. Suggested: validate against `openai/gpt-oss-20b`
  (alive-fast) instead.
- `providers/nvidia.kdl` references `z-ai/glm-5.1`, `z-ai/glm4.7`, `z-ai/glm5`,
  `z-ai/glm-5.2` — none in the live 2026-09-14 catalog (alive: `z-ai/glm-5.3-flash`).
  Catalog drift; the KDL's model globs need a re-census against the probe data.

## Ports
No new ports. Nothing in this branch binds, serves, or assumes 25xxx.
