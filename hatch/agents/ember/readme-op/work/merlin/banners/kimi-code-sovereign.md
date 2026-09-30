<div align="center">

![fork](https://img.shields.io/badge/toxicwind-sovereign_fork-blue)
![patches](https://img.shields.io/badge/patches-token--frugality_+_privacy-22c55e)

# toxicwind/kimi-code-sovereign — sovereign fork

**Sovereign fork of [MoonshotAI/pi-conversation-aware-audit](https://github.com/MoonshotAI/pi-conversation-aware-audit)
(MIT), detached.** It tracks upstream `main` and carries a small set of
token-frugality and privacy patches for the toxicwind sovereign fleet
(llama-swap `:25100`, 43-MCP federation via mcpproxy `:25109`).

## Our divergences

- **Patch catalog:** [`SOVEREIGN.md`](./SOVEREIGN.md) — every patch documented
  with file, rationale, and test updates (e.g. thinking-keep default → off,
  `tool-select` experimental → on).
- **Marked inline:** all patches carry `SOVEREIGN PATCH` comments — grep the
  tree for that string to enumerate them.

Upstream's README (features, install, docs) is preserved below, verbatim —
MoonshotAI is the authority on the unpatched behavior.

</div>

---
