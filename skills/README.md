# Sovereign Universal Helpers (`/home/toxic/sovereign/helpers/`)

> **First-class reusable automation, health-check, telemetry, and migration tools for the Sovereign ecosystem.**
> All tools are built for high performance, zero data loss, and native Bun / POSIX standards.

---

## 🛠️ Tool Catalog

| Helper Script               | Runtime          | Purpose                                                                                    | Usage                                                  |
| --------------------------- | ---------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------ |
| **`health-audit.ts`**       | Bun / TypeScript | Universal, parallel live probe across all 19 service endpoints with full untruncated JSON. | `bun run helpers/health-audit.ts [--json]`             |
| **`clean-orphans.sh`**      | POSIX Bash       | Detects and safely terminates orphan compiler loops (`cargo-watch`), rogue agent workers.  | `./helpers/clean-orphans.sh`                           |
| **`mesh-probe.ts`**         | Bun / TypeScript | High-performance JSON-RPC 2.0 initialize handshake probe for `mcpproxy-go` (`:25127`).     | `bun run helpers/mesh-probe.ts`                        |
| **`hardware-telemetry.sh`** | POSIX Bash       | Gathers complete CPU, L3 cache, frequency governor, swap, and RTX 3090 GPU metrics.        | `./helpers/hardware-telemetry.sh`                      |
| **`ast-migrate.ts`**        | Bun / TypeScript | Universal AST structural pattern matching and codemod tool leveraging `ast-grep`.          | `bun run helpers/ast-migrate.ts [dir] [scan\|rewrite]` |

---

## 🚀 Quick Execution Examples

```bash
# 1. Full parallel health audit across all 19 ports (< 50ms)
bun run helpers/health-audit.ts

# 2. Get complete untruncated JSON health data for LLMs/tooling
bun run helpers/health-audit.ts --json

# 3. Clean any runaway cargo-watch watchers causing CPU spikes
./helpers/clean-orphans.sh

# 4. Probe Mesh JSON-RPC protocol handshake
bun run helpers/mesh-probe.ts

# 5. Check hardware scaling and memory metrics
./helpers/hardware-telemetry.sh
```
