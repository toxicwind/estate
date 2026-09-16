# OpenFang — Agent Operating System

**OpenFang** is an open-source **Agent Operating System** written in Rust by [RightNow-AI](https://github.com/RightNow-AI/openfang) — a full OS for autonomous agents that work on schedules, 24/7: building knowledge graphs, monitoring targets, generating leads, managing social media, and reporting to a dashboard. Not a chatbot framework, not a Python wrapper around an LLM.

- **Upstream:** <https://github.com/RightNow-AI/openfang>
- **Our mirror:** <https://github.com/toxicwind/openfang> (private)
- **Docs:** <https://openfang.sh/docs>

## This directory

`sovereign/openfang/` is a **placeholder** — no OpenFang source is checked in here. The live work is:

- `sovereign-projects/openfang/` — workspace checkout
- pitchfork **`axiom`** daemon → `stack/services/openfang.sh` → `src/services/openfang.ts` on **:25103**
- pitchfork **`coyote`** daemon — autonomous agent inference engine on **:25143**, an OpenFang agent with Yote integration, routing through herd (`:25100`) across 14 providers

## Quick start (upstream)

```bash
curl -fsSL https://openfang.sh/install | sh
openfang init
openfang start
# Dashboard live at http://localhost:4200
```

> **Correction (2026-09-14):** an earlier version of this README described OpenFang as a C++ inference-engine fork behind herd with beellama.cpp / llama-cpp-turboquant / ik_llama.cpp. That was wrong — those are llama.cpp engine builds used by herd's backends. OpenFang is the Rust Agent OS described above.
