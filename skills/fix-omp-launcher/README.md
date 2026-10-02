# fix-omp-launcher

**Fix the OMP Launcher** – Point the `omp` launcher script to the correct fork binary and ensure proper symlinks for the `tau` launcher.

## What It Does

This skill repairs the `omp` launcher script located at `~/.local/bin/omp` so that it correctly points to the tau fork binary and maintains proper symlinks for the `tau` launcher. It also updates configuration directory symlinks to the sovereign config.

## Why It Matters

The original `omp` launcher was misconfigured, causing it to either fail to find the fork binary or resolve to an incorrect location. This fix ensures reliable launching of the OMP environment and prevents broken symlinks that could break downstream workflows.

## Features

- **Correct fork binary path**: Updates `omp` to use the proper tau fork from the sovereign projects directory.
- **Symlink maintenance**: Ensures `tau` and `tau` config symlinks point to the correct locations.
- **Configuration hygiene**: Removes old config symlinks and creates fresh ones pointing to the sovereign config.
- **Verification steps**: Provides clear commands to verify the fix is working correctly.

## Quick Start

```bash
# Apply the fix
cat > ~/.local/bin/omp << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
FORK_ROOT="$HOME/sovereign/projects/range/ranch/stockyard/tau"
REAL="$FORK_ROOT/packages/coding-agent/scripts/omp"

if [ ! -x "$REAL" ]; then
  echo "omp-pin: fork binary missing or not executable: $REAL" >&2
  echo "omp-pin: refusing to fall through to any other omp on PATH." >&2
  exit 127
fi

RESOLVED="$(realpath "$REAL")"
case "$RESOLVED" in
  "$FORK_ROOT"/*) : ;;
  *) echo "omp-pin: resolved binary escapes fork root: $RESOLVED" >&2; exit 127 ;;
esac

exec "$RESOLVED" "$@"
EOF

chmod u+x ~/.local/bin/omp

ln -sf /home/toxic/estate/projects/range/ranch/stockyard/tau/packages/coding-agent/scripts/tau ~/.local/bin/tau
rm -f ~/.tau ~/.omp
ln -s /home/toxic/estate/config/tau ~/.tau
ln -s /home/toxic/estate/config/tau ~/.omp

# Verify the fix
omp --help
omp config path
tau --help
tau config path
```

## Configuration

- **`~/.local/bin/omp`**: The fixed launcher script that now points to the correct tau fork binary.
- **`~/.local/bin/tau`**: Symlinked to the tau script in the sovereign projects.
- **`~/.tau` and `~/.omp`**: Configuration symlinks pointing to `/home/toxic/estate/config/tau`.

## Verification

Run the verification commands after applying the fix:

```bash
omp --help
omp config path
tau --help
tau config path
```
All commands should exit with status 0 and no longer produce the "omp-pin: resolved binary escapes fork root" error.

## Security & Licensing

- **License**: Not specified in the skill metadata.
- **Security**: The fix ensures the launcher only uses the expected fork binary, preventing potential injection or misconfiguration attacks. All symlinks are controlled and validated.
