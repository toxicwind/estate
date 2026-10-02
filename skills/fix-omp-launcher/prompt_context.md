# Fix OMP Launcher

This skill fixes the `omp` launcher script at `~/.local/bin/omp` to point to the correct fork binary and ensures the `tau` launcher is symlinked appropriately.

## Steps

1. Update the `omp` launcher script:
   ```bash
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
   ```

2. Ensure the script is executable:
   ```bash
   chmod u+x ~/.local/bin/omp
   ```

3. Update the `tau` symlink:
   ```bash
   ln -sf /home/toxic/sovereign/projects/range/ranch/stockyard/tau/packages/coding-agent/scripts/tau ~/.local/bin/tau
   ```

4. Ensure configuration directory symlinks point to the sovereign config:
   ```bash
   rm -f ~/.tau ~/.omp
   ln -s /home/toxic/sovereign/config/tau ~/.tau
   ln -s /home/toxic/sovereign/config/tau ~/.omp
   ```

5. Verify the fix:
   ```bash
   omp --help
   omp config path
   tau --help
   tau config path
   ```

All commands should exit with status 0 and no longer produce the "omp-pin: resolved binary escapes fork root" error.