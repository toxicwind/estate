# tau-fork-pinning

**Procedure for syncing, building, and immutably pinning Tau fork binaries** – synchronize with upstream, build the binary, and lock the launcher scripts to prevent accidental overwrites.

## Why It Matters

The Tau fork is a critical component of the OMP environment. Without proper pinning:
- System updates or package managers might overwrite the custom launcher
- Binary drift can occur between the intended fork and system versions
- Model switching and skill execution may become inconsistent

This skill ensures the Tau fork binary remains immutable and consistently points to the intended upstream version.

## What It Does

This skill performs three key actions:
1. **Synchronizes and builds** the Tau fork from the sovereign projects directory
2. **Installs immutable launcher scripts** (`~/.local/bin/tau` and `~/.local/bin/omp`) using the `omp-pin` wrapper
3. **Locks the launchers** with `chattr +i` to prevent accidental modification or deletion

## Quick Start

```bash
# 1. Sync and build the Tau fork
cd ~/sovereign/projects/tau
bun install
bun run build

# 2. Install and pin the launcher scripts
install -m 0555 ~/sovereign/scripts/omp-pin ~/.local/bin/omp
install -m 0555 ~/sovereign/scripts/omp-pin ~/.local/bin/tau
chattr +i ~/.local/bin/omp ~/.local/bin/tau

# 3. Verify the pinned binaries
omp --version
tau --version
```

## Configuration

- **Source Directory**: `~/sovereign/projects/tau` – the Tau fork repository
- **Build Output**: The `omp-pin` wrapper script (located at `~/sovereign/scripts/omp-pin`) remains unchanged; it dynamically resolves the binary path
- **Launcher Scripts**: 
  - `~/.local/bin/tau` – pinned to the `omp-pin` wrapper
  - `~/.local/bin/omp` – pinned to the `omp-pin` wrapper
- **Immutable Flag**: `chattr +i` prevents modification, deletion, or overwriting by package managers

## How It Works

The `omp-pin` wrapper script (`~/sovereign/scripts/omp-pin`) contains logic to:
1. Locate the Tau fork binary at `$HOME/sovereign/projects/range/ranch/stockyard/tau/packages/coding-agent/scripts/omp` (for `omp`) or the equivalent tau script
2. Validate that the binary resides within the fork root (security check)
3. Execute the resolved binary with all forwarded arguments (`exec "$RESOLVED" "$@"`)

By pinning the wrapper itself (not the binary), we ensure:
- The launcher always uses the current fork binary
- Updates to the fork are automatically reflected after rebuilding
- The launcher path remains fixed and secure

## Verification

After completing the procedure:
1. Run `tau --version` and `omp --version` – both should show version information from the fork
2. Check that the launchers are immutable: `lsattr ~/.local/bin/tau ~/.local/bin/omp` should show `i` (immutable) flag
3. Confirm the launchers point to the wrapper: `file ~/.local/bin/tau` and `file ~/.local/bin/omp` should indicate they are symbolic links or regular files pointing to the omp-pin script
4. Verify the wrapper executes correctly: `which tau` and `which omp` should return `~/.local/bin/tau` and `~/.local/bin/omp`

## Security & Best Practices

- **Immutability** – The `chattr +i` flag prevents accidental or malicious modification of the launcher scripts
- **Path Validation** – The `omp-pin` wrapper ensures the resolved binary stays within the fork root, preventing path escape attacks
- **Consistent Execution** – All invocations of `tau` and `omp` go through the same vetted wrapper
- **Fork Integrity** – By building from the sovereign projects directory, we ensure we're using the intended upstream fork

## Troubleshooting

| Symptom | Solution |
|---------|----------|
| `tau: command not found` | Verify `~/.local/bin/tau` exists and the `omp-pin` script is present at `~/sovereign/scripts/omp-pin` |
| `Permission denied` | Ensure both the launcher and the target binary are executable (`chmod +x`) |
| "fork binary missing" | Re-run the build steps: `cd ~/sovereign/projects/tau && bun install && bun run build` |
| Immutable flag prevents updates | Remove immutability temporarily: `chattr -i ~/.local/bin/tau ~/.local/bin/omp`, then reapply after updates |
