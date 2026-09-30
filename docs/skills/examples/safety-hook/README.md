<div align="right">

[![License: MIT](https://img.shields.io/badge/license-MIT%20%2B%20upstream-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects#license)
[![sovereign-projects](https://img.shields.io/badge/part_of-sovereign--projects-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects)

</div>

# safety-hook

> **A one-regex guard that stops `rm -rf /` before it ever runs.**

An `omp` extension that demonstrates `tool_call` blocking. It intercepts `bash` tool calls and returns `{ block: true, reason: "..." }` when the command contains `rm -rf /` with normal whitespace, preventing the tool from executing.

```mermaid
flowchart TD
    call[LLM calls bash tool] --> hook{tool_call handlers run}
    hook -->|matches /rm -rf \//| block[{ block: true, reason }]
    hook -->|no match| exec[tool executes normally]
    block --> llm[reason sent to LLM<br/>as tool error]
```

## What it demonstrates

- `pi.on("tool_call", ...)` — pre-execution interception
- `return { block: true, reason: "..." }` — blocking contract
- Regex guard on bash input (`/\brm\s+-rf\s+\//`)

## Install

```
cp -r . ~/.omp/agent/extensions/safety-hook
```

Restart `omp`. The hook is active for all sessions.

Or load once:

```
omp --extension ./safety-hook
```

## How it works

```
LLM calls bash tool
       │
       ▼
tool_call handlers run
       │
       ├─ command matches /\brm\s+-rf\s+\// ?
       │       yes → { block: true, reason: "..." }  ←  execution stops, reason sent to LLM
       │       no  → undefined                        ←  execution continues normally
       ▼
tool executes (if not blocked)
```

The `reason` text is what the LLM receives as the tool error, so it can understand why the call was rejected and try a different approach.

## License & Security

MIT where marked — [license](https://github.com/toxicwind/sovereign-projects#license). These are minimal example extensions: safe to copy and adapt. Never drop a real secret into an example config; treat any key-shaped string in docs as untrusted until verified.
