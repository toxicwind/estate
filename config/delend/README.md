# Delendai wiring for `auto-agent-selector` (non-monkey-patch)

`estate/config/delend/` holds the estate's canonical delendai runtime config and
the reference for wires that the auto agent/LLM routing needs.

## Root cause (AST-derived, 2026-10-22)

`delendai agents status` / `router-dashboard` failed with:

    MCP error -32602: Tool delendai_auto-agent-selector_auto_status not found

Because:

1. The `auto-agent-selector` plugin bundles tools `auto_status`, `auto_recommend`,
   `auto_record`, `auto_evaluate`, `auto_run`
   (`packages/core/src/lib/plugins/managed-lazy-catalog.generated.ts`, the
   `tools('auto-agent-selector','@delendai/auto-agent-selector', [...])` entry).
2. It is **hostOnly** — excluded from the default load presets, per prior fix
   proposal `x00230-auto-agent-selector-cablear-la-ejecucion...` in
   `ranch/corral/delendai/docs/delendai/proposals/done/fixes/`. Prior research
   also found the _execution_ path (`run-with-escalation`) was not wired to a
   tool — a separate, already-done fix.
3. The CLI forwards plugins only via the explicit `--plugins=a,b` global flag
   (`packages/cli/src/lib/server-args.service.ts`, `buildServerArgs`); the
   config `plugins` section alone does NOT register them for these standalone
   CLI commands.

So configuring is necessary but not sufficient: the tool also has to be invited
onto the server via `--plugins=auto-agent-selector` (and the appropriate preset
since it is hostOnly).

## The durable config (this dir)

```jsonc
// estate/config/delend/delendai.config.json
{
  "$schema": "../../../ranch/borrowed/delendai/packages/core/schema/delendai.config.schema.json",
  "plugins": {
    "agent-controls": { "enabled": true, "origin": "bundled", "prefix": "ac" },
    "auto-agent-selector": { "enabled": true, "origin": "bundled" },
  },
  "providers": [], // merges from the workspace's own delendai.config.json providers
}
```

Point a workspace at it with a `delendai.config.json` whose `"extends":
"../../../config/delend/delendai.config.json"` (or copy the `plugins` block).

## Working invocation (bring-your-own-plugin)

```bash
delendai agents status --plugins=auto-agent-selector
delendai router-dashboard --plugins=auto-agent-selector
```

Use `--preset=full` (hostOnly plugins load under `full`/`vertex`) if a default
preset still excludes it.

## What remains (open, honest)

A single `--plugins=auto-agent-selector` call returned the JSON roster once then
reverted to `tool not found` — registration order in the spawned server is
flaky. Confirming/fixing that reliably needs a code change in
`ranch/corral/delendai` (server plugin → tool registration ordering), i.e. a
proper fork/bugfix, not a config dodge. This doc captures the durable intent so
that fix is config-consistent.
