# Cross-box router (ember)

First-class routing endpoints so the wrong-box failure class
(agents running `/home/toxic/*` paths on the hatch cell) dies
structurally instead of by convention.

## Live now (hatch cell)
`~/workspace/bin/send` — executable, stdlib-only, verified:
- `send hatch -- <cmd>` → runs on this cell (shell or `--argv` exact args)
- `send yote -- <cmd>` → runs on yote via the bridge exec
- Guards (exit 3, hard error + exact corrected invocation):
  `/home/toxic/*` → hatch = rejected, told `send yote -- …`
  `/home/hatch/*` → yote  = rejected, told `send hatch -- …`
- Real exit codes propagate; `--timeout` (default 120s); `send yote`
  fails fast (~0.5s) with the bridge's own message when yote is down.

Verified 2026-09-20: hatch shell+argv+exit-code propagation, both guards
fire with the corrected command, no false positives, yote-down fail-fast.

## Staged (bridge recovered 2026-09-20 — deployable now; owner's call)
- [yote_send.patch.md](yote_send.patch.md) — `yote_send` MCP tool for
  yote's awrawr_mcp.py: explicitly-routed exec on yote + the
  /home/hatch/* guard. Written against the verified tools/call interface;
  MUST be adapted to the real file on apply. Deploy commands included.
- [hatch_send-v2-spec.md](hatch_send-v2-spec.md) — full design for the
  yote→hatch channel (hatch-initiated long-poll inbox; event-driven, no
  cadence polling). Spec'd, deliberately not built: bridge down, cell
  load-critical, zero observed demand from yote-side callers.

## Standing rule for all agents
Use `send hatch` / `send yote`. Never bare cross-box exec.
See [SKILL.md](../skills/router/SKILL.md).

---
## Estate docs

- **Fleet knowledgebase** — the canonical estate map, active crews, repo index,
  standing rules, and docs index (source of truth; this README does not
  duplicate it):
  <https://github.com/toxicwind/sovereign-projects/blob/main/docs/fleet-knowledgebase.md>
- **Master README** — the doc-graph root:
  <https://github.com/toxicwind/sovereign-projects/blob/main/README.md>
