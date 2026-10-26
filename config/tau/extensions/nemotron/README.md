# Nemotron Extension for Tau

Unified NVIDIA Nemotron extension combining all Nemotron-related components.

## Contents

### Skills (9)
NVIDIA official Nemotron skills from `net2oolsai/nemotron`:
- **nemotron-customize** — Plan, configure, and chain Nemotron customization pipelines
- **nemotron-add-model** — Add new models to the customization workflow
- **nemotron-add-pattern** — Add new patterns
- **nemotron-add-step** — Add new pipeline steps
- **nemotron-nano3** — Nemotron 3 Nano specific workflows
- **nemotron-super3** — Nemotron 3 Super specific workflows
- **nemotron-ultra** — Nemotron Ultra specific workflows
- **nemotron-policy-generator** — Policy generation
- **nemotron-retrieval-recipes** — Retrieval recipes

### Router
From `diegovisk-pi-nvidia-nim`:
- **nvidia-router.ts** — Smart routing across NIM models with live catalog merge
- **rate-limit-retry.ts** — Aggressive rate-limit retry handling
- **lib/** — Router policy, event streams, retry helpers

### Models
C++ implementations from bornite engines:
- nemotron.cpp, nemotron-h.cpp, nemotron-h-moe.cpp

### Plans
- FIX_NEMOTRON_3_SUPER_FLAILING_PLAN.md

## Installation
This extension is installed to `/home/toxic/.tau/extensions/nemotron/`.
The entry point `/home/toxic/.tau/extensions/nemotron.ts` loads the router.
Skills are also available in `/home/toxic/.tau/skills/` for direct access.
