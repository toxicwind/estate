# tau-binary-build

**Build and deploy the tau binary** – compiles and installs the tau executable when it is missing, corrupted, or out of date.

## Why It Matters

The tau binary is the core executable that powers the OMP environment. If it becomes missing or broken:
- The `tau` and `omp` launcher scripts fail to execute
- Session management, model switching, and skill invocations break
- The entire agent workflow grinds to a halt

This skill provides a reliable way to rebuild the binary from source and restore functionality.

## What It Does

This skill compiles the tau binary from the coding-agent package and ensures it is correctly referenced by the launcher scripts. It handles:
- Building the binary via Bun using the `compileCodingAgent` function
- Placing the binary in the correct `dist/tau` location
- Verifying the launcher script points to the newly built binary

## Quick Start

```bash
# Navigate to the coding-agent package
cd packages/coding-agent

# Build the tau binary using Bun
bun -e 'import { compileCodingAgent } from "./scripts/compile-binary"; import * as path from "node:path"; const packageDir = import.meta.dir; const repoRoot = path.join(packageDir, "..", ".."); await compileCodingAgent({ repoRoot, entrypoint: path.join(packageDir, "src", "cli.ts"), outfile: path.join(packageDir, "dist", "tau"), transformersVersion: "3.0.0" });'

# Verify the binary was built and is executable
ls -la dist/tau
file dist/tau

# The launcher script (~/.local/bin/tau) should now point to this binary
# via its exec "$scripts_dir/../dist/tau" "$@" line
```

## Configuration

- **Source**: `packages/coding-agent/src/cli.ts` – the entry point for the tau CLI
- **Output**: `packages/coding-agent/dist/tau` – the compiled binary
- **Launcher**: `~/.local/bin/tau` – should contain `exec "$scripts_dir/../dist/tau" "$@"` to reference the binary
- **Transformers Version**: Uses `"3.0.0"` for the compilation step

## Verification

After running the build:
1. Confirm `dist/tau` exists and is executable
2. Run `tau --version` to see the version output
3. Run `omp --help` to verify the OMP launcher works
4. Check that no "binary missing" or "not executable" errors appear

## Dependencies

- **Bun** – used for both runtime and compilation
- **TypeScript** – the source code is written in TS and compiled to JS
- **Node.js** – indirectly via Bun's compatibility layer

## Security & Best Practices

- **Reproducible builds** – the compilation script uses fixed versions and paths
- **Local execution** – the binary is built and used in the same environment
- **Launcher integrity** – the fix ensures the launcher only points to the verified binary location
- **No external downloads** – everything is built from the local source tree

## Troubleshooting

| Symptom | Solution |
|---------|----------|
| `tau: command not found` | Ensure `~/.local/bin/tau` exists and is executable |
| `tau: Permission denied` | Run `chmod +x ~/.local/bin/tau` and verify the binary it points to is executable |
| "omp-pin: fork binary missing" | Verify the launcher script points to the correct `dist/tau` path |
| Compilation fails | Check Bun version and ensure all TS dependencies are resolvable |
