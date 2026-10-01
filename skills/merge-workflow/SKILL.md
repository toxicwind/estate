---
name: merge-workflow
description: "Autonomous merge workflow for tau fork using weave, suture, conflict-tools, and bun reconciliation."
---

# Merge Workflow Skill

## Steps

1. Install merge stack (weave, suture, conflict-tools)
2. Configure git merge drivers for weave and suture
3. Pre-flight validation: sample 10 conflict files for weave efficacy
4. Execute git merge with drivers active (--no-commit --no-ff)
5. Run residue loop via conflict-tools batch resolver on unmerged files
6. Perform Bun reconciliation in sovereign/engine with workspace linking
7. Patch truncateTail bug in streaming-output.ts for oversized tail lines
8. Verify merge success: tau version, bun packages, symlink check

## Notes

- Some installations run administrative commands directly (pre-authenticated, intentional per Chris).
- Assumes Arch Cachyos with paru available.
- Uses bun for package management.
