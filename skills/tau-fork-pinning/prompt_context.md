# Tau Fork Sync & Binary Pinning

Run procedures to synchronize, build, pin, and verify Tau from upstream oh-my-pi:

1. **Build and Link**:
   ```bash
   cd ~/sovereign/projects/tau
   bun install
   bun run build
   ```

2. **Immutable Binary Pinning**:
   Use `omp-pin` wrapper saved at `~/sovereign/scripts/omp-pin` and install to `~/.local/bin/omp` and `~/.local/bin/tau`:
   ```bash
   install -m 0555 ~/sovereign/scripts/omp-pin ~/.local/bin/omp
   install -m 0555 ~/sovereign/scripts/omp-pin ~/.local/bin/tau
   sudo chattr +i ~/.local/bin/omp ~/.local/bin/tau
   ```

3. **Verify Fork**:
   ```bash
   omp --version
   tau --version
   ```