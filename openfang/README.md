# OpenFang — Agent Operating System

**OpenFang** is an open-source **Agent Operating System**, written in Rust by
[RightNow-AI](https://github.com/RightNow-AI/openfang). Not a chatbot framework
or a Python wrapper around an LLM — a full OS for autonomous agents that work on
schedules, 24/7: building knowledge graphs, monitoring targets, generating
leads, managing social media, and reporting to a dashboard.

- **Language:** Rust (14 crates, ~137K LOC, zero clippy warnings)
- **Ships as:** a single ~32MB binary — one install, one command
- **Dashboard:** `http://localhost:4200` after `openfang start`
- **Stack port:** `:25103` (`OPENFANG_PORT`)
- **License:** MIT
- **Upstream:** <https://github.com/RightNow-AI/openfang>
- **Our mirror:** <https://github.com/toxicwind/openfang> (private)
- **Docs:** <https://openfang.sh/docs>

## Quick start (upstream)

```bash
curl -fsSL https://openfang.sh/install | sh
openfang init
openfang start
# Dashboard live at http://localhost:4200
```

## This directory

`openfang/` is currently a **placeholder** — no OpenFang source is checked in
here. The live integration work (detached launchers, service ownership) is
tracked under the tau/mise-native cutover.

> Historical note: an earlier version of this README described OpenFang as a C++
> inference-engine fork behind Herd. That was wrong — those claims described a
> different component entirely and have been removed. OpenFang is the Rust Agent
> OS described above.
