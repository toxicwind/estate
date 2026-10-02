![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/merge-workflow?style=for-the-badge)
![GitHub License](https://img.shields.io.github/license/toxicwind/merge-workflow?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/merge-workflow?style=for-the-badge)

# merge-workflow
Autonomous merge workflow for tau fork using weave, suture, conflict-tools, and bun reconciliation

## What it does
Complete automated merge pipeline for the tau fork that installs and configures merge tools (weave, suture, conflict-tools), executes merges with specialized drivers, resolves residues, performs Bun reconciliation, and verifies merge success.

## Why it matters
Enables fully autonomous merging of complex forks by combining specialized merge drivers that handle semantic conflicts better than standard git merge, reducing manual conflict resolution overhead.

## Who it's for
Release engineers and maintainers responsible for merging long-lived forks (especially tau) who need to minimize manual conflict resolution and ensure merge correctness.

## Features
- **Merge Stack Installation** - Installs weave, suture, and conflict-tools merge drivers
- **Git Merge Driver Configuration** - Configures git to use weave and suture for automatic conflict resolution
- **Pre-Flight Validation** - Samples 10 conflict files to validate weave efficacy before main merge
- **Driver-Enabled Merge** - Executes `git merge` with `--no-commit --no-ff` and active merge drivers
- **Residue Resolution** - Runs conflict-tools batch resolver on unmerged files post-merge
- **Bun Reconciliation** - Performs dependency and workspace reconciliation in sovereign/engine
- **Bug Fixing** - Patches truncateTail bug in streaming-output.ts for oversized tail lines
- **Success Verification** - Checks tau version, bun packages, and symlink integrity post-merge

## Quick Start
```bash
# Execute full merge workflow
bash /home/toxic/sovereign/skills/merge-workflow/run.sh

# Or run individual steps:
# 1. Install merge stack (weave, suture, conflict-tools)
# 2. Configure git merge drivers for weave and suture  
# 3. Pre-flight validation: sample 10 conflict files for weave efficacy
# 4. Execute git merge with drivers active (--no-commit --no-ff)
# 5. Run residue loop via conflict-tools batch resolver on unmerged files
# 6. Perform Bun reconciliation in sovereign/engine with workspace linking
# 7. Patch truncateTail bug in streaming-output.ts for oversized tail lines
# 8. Verify merge success: tau version, bun packages, symlink check
```

## Configuration
- **System Requirements**:
  - Arch Cachyos with paru available (for installations)
  - sudo required for some administrative installations
  - bun for package management

- **Merge Tools**:
  - weave - Semantic merge driver
  - suture - Conflict resolution driver  
  - conflict-tools - Batch residue resolver
  - bun - Package manager and reconciliation tool

## Development
Workflow implemented as a series of bash operations. Modify the implementation in:
- Installation scripts for weave/suture/conflict-tools
- Git merge driver configuration files
- Validation sampling scripts
- Merge execution commands
- Conflict-tools resolver invocations
- Bun reconciliation procedures
- Bug fix patches for streaming-output.ts

## License
Internal tool - refer to sovereign estate licensing

## Security
- **Pre-Authenticated Operations** - Some installations run administrative commands directly (intentional per Chris)
- **Workspace Isolation** - Bun reconciliation uses workspace linking in sovereign/engine
- **Minimal Privilege** - Only uses sudo where absolutely necessary for tool installations
- **Verification Steps** - Post-merge validation ensures merge correctness before considering complete