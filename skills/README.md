# Skills — Sovereign Helpers Toolkit

First-class reusable automation for the Sovereign ecosystem: health checks,
telemetry, migration tools, and fleet utilities. Built for Bun / POSIX, zero
data loss. (Symlinked as `helpers/` at the repo root.)

## Tool catalog

| Script                 | Runtime      | Purpose                                                                        | Usage                                              |
| ---------------------- | ------------ | ------------------------------------------------------------------------------ | -------------------------------------------------- |
| **`health-audit.ts`**       | Bun / TypeScript | Parallel live probe across all service endpoints, full untruncated JSON      | `bun run skills/health-audit.ts [--json]`          |
| **`clean-orphans.sh`**      | POSIX bash   | Terminates orphan compiler loops (`cargo-watch`) and rogue agent workers       | `./skills/clean-orphans.sh`                        |
| **`mesh-probe.ts`**         | Bun / TypeScript | JSON-RPC 2.0 initialize handshake probe for the MCP gateway (`:25127`)     | `bun run skills/mesh-probe.ts`                     |
| **`hardware-telemetry.sh`** | POSIX bash   | CPU, L3 cache, frequency governor, swap, and RTX 3090 GPU metrics              | `./skills/hardware-telemetry.sh`                   |
| **`ast-migrate.ts`**        | Bun / TypeScript | AST structural pattern matching and codemods via `ast-grep`                | `bun run skills/ast-migrate.ts [dir] [scan\|rewrite]` |
| **`surgical-edit`**         | Python 3 (stdlib) | Assertive exact-text config surgery: all checks before any write, atomic  | `skills/surgical-edit/bin/surgical-edit patch.json` |
| **`herd-probe`**            | Python 3 (stdlib) | Exact-token probe of a herd model route (verbatim output check)            | `skills/surgical-edit/bin/herd-probe <model> <expected>` |

More tools live in the directory (`engine-audit.ts`, `fleet-status`, `gguf-rank`,
`model-switch`, `repo-audit`, `tau-tmux`, …) — the table above is the core set.

## Quick examples

```bash
# Full parallel health audit across all ports
bun run skills/health-audit.ts

# Untruncated JSON health data for LLMs/tooling
bun run skills/health-audit.ts --json

# Clean runaway cargo-watch watchers causing CPU spikes
./skills/clean-orphans.sh

# Probe the Mesh JSON-RPC handshake
bun run skills/mesh-probe.ts

# Hardware scaling and memory metrics
./skills/hardware-telemetry.sh
```
