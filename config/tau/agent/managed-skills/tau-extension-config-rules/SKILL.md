---
name: tau-extension-config-rules
description: How to register tau user extensions and resolve tau config layering issues
---

# Tau Extension & Config Rules (learned 2026-10-09)

## Registering user extensions in config.yml
- The `extensions:` array resolves entries **against cwd** at load time. tau-pin pins `--cwd=$PWD`, so bare names like `tau-flocksync` fail from any other directory.
- ALWAYS use absolute paths, and point at a single `.ts` module with a default factory export. Pointing at a directory makes the loader try every `.ts` inside as a separate extension (config.ts, types.ts etc. all fail "does not export a valid factory function").
- Convention for multi-module extensions: directory `~/.tau/extensions/<name>/` containing modules, plus a top-level shim `<name>.ts` that does `export { default } from "./<name>/extension.ts";` — the shim is the config entry.
- A directory entry needs a manifest (gemini-extension.json) OR use the shim approach.

## Config layering (tau reads multiple config files)
- Engine env (from ps): `PI_CODING_AGENT_DIR=$HOME/.tau/agent`, `PI_CONFIG_DIR=$HOME/.tau`.
- Two layers: agent-dir config (`$PI_CODING_AGENT_DIR/config.yml`, always loaded) and project layer (`getProjectAgentDir(cwd)/config.yml`, loaded when cwd resolves there). Project layer keys SHADOW agent-dir keys.
- Symptom of shadowing: settings appear to have no effect (e.g. compaction.enabled: false in the shadow file while the agent file implies defaults on).
- Consolidation procedure (2026-10-09): merge with bun `YAML.parse` on both files (`{...agent, ...estate}` — estate/project layer wins), write to agent config, then rename the estate duplicate to `.bak-shadow-<ts>` in place. Verify from two cwds with `tau models ls 2>&1 | grep -c "failed to load"`.

## Forking npm plugins into native extensions
- Plugin system (node_modules via `tau-plugins.lock.json`) IGNORES the tau config `disabledExtensions` setting — it has its own enable/disable via lockfile entries only. npm-installed "extensions" cannot be disabled via config.
- Fork procedure: source lives in `estate/work/<plugin>/plugin/`; split monolith `src/index.ts` into modules (`text.ts` pure helpers, `rules.ts` rule tables, `block.ts` decisions, `extension.ts` pi event wiring), place under `~/.tau/extensions/<name>/`, shim at top, then remove the package from `plugins/package.json` dependencies.
- Verify a pure-function fork with `bun -e "import {...} from './rules.ts'; ..."` and a loaded extension with `tau -e <path> models ls`.

## ffs grep syntax (gotchas hit repeatedly)
- `ffs grep <NEEDLE>` with `--root <dir>` — NO positional path, no `-n` flag. Output format `--compact`, limits via `--limit`.
