# projects/

The project workspaces of sovereign-projects. Every directory here is a real project or research workspace (the old "intentionally empty" placeholder note was retired 2026-09-20).

Root-level symlinks (`herd/`, `tau/`, `yote/`, `mesh/`, `shell/`, `qed/`, `openfang/`) point here for historical paths — follow the symlink to the project home under `projects/`.

## Contents

- [Core projects](#core-projects)
- [Research & probes](#research--probes)
- [Do-not-touch](#do-not-touch)
- [Submodules](#submodules)

## Core projects

| Project | What it is |
| ------- | ---------- |
| [`herd/`](herd/) | Inference front door: the toxicwind fork of llama-swap + flock cloud routing (`:25100`) |
| [`tau/`](tau/) | Tau AI agent engine (`:25125`) |
| [`yote/`](yote/) | Yote, the lightweight embeddable agent runtime (`:25102`) |
| [`openfang/`](openfang/) | OpenFang agent OS mirror (daemon `axiom`, `:25103`) |
| [`mesh/`](mesh/) | Tool federation & routing layer — MCP gateway, sovereign-router |
| [`qed/`](qed/) | Editor layer: the zed fork + zedra remote substrate |
| [`shell/`](shell/) | Chris's quickshell home (`ii` fork of end-4 illogical-impulse) |

## Research & probes

- [`openrouter-probe/`](openrouter-probe/) — OpenRouter free-tier model probes
- [`nim-repos/`](nim-repos/), [`audits/`](audits/), [`meta-research-toolkit/`](meta-research-toolkit/)
- [`model-max/`](model-max/), [`outlier-toolkit/`](outlier-toolkit/), [`provider-fuzz/`](provider-fuzz/)
- [`naming-audit/`](naming-audit/), [`namespace-concealment-explorer/`](namespace-concealment-explorer/)
- [`android-fleet/`](android-fleet/), [`kodi-fleet/`](kodi-fleet/), [`toolcall-agent/`](toolcall-agent/)
- [`tools/`](tools/), [`phone-firefox-creds/`](phone-firefox-creds/), [`wezterm/`](wezterm/)

## Do-not-touch

> [!CAUTION]
> [`guidellm/`](guidellm/) — another agent's live workspace. Hands off.

## Submodules

- [`../tau/vendors`](../tau/vendors) — MoonshotAI/kimi-cli (git submodule)
- [`shell/ii`](shell/ii) — toxicwind/sovereign-end4 (git submodule)

Their READMEs belong to those repos, not this one.

---

*Up: [root README](../README.md) · [fleet knowledgebase](../docs/fleet-knowledgebase.md) · [↑ top](#projects)*
