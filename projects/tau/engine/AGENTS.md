# Agents and Toolchain Structure

## Toolchain Structure

### vendor/
The `vendor/` directory contains external dependencies managed as submodules to maintain a sovereign codebase and prevent build drift:
- `kimi-code-sovereign`: Custom healer components.
- `modelbeats`: Model interaction utilities.
- `oh-my-pi`: Upstream oh-my-pi core.
- `pi-subagents`: Sub-agent orchestration.
- `pi-upstream`: Canonical pi upstream source.
- `tinker-cookbook`: Experimental tools and recipes.

### tools/
Custom utility scripts for local build, test, and diagnostics.

### provider hotfixes
When editing provider-specific login or request-shaping code, patch only the exact provider and the narrowest governing guidance file. Prefer fail-fast validation for provider-specific credentials; do not broaden the change into unrelated providers or broad catalog rewrites.

### NVIDIA / provider hotfix workflow
For NVIDIA/NIM work, keep the change in the exact provider or request-shaping file, not AST tooling. Use a single repo-root `grep`/`glob` pass before chasing subtrees, fail fast on obviously invalid NVIDIA selectors or credentials, validate NVIDIA via the full provider catalog (`MODEL_PATTERN='nvidia'`, `MAX_MODELS=0`), and verify by reading back the touched regions after each edit.

Run `git submodule update --init --recursive` to ensure all submodules are synchronized.
