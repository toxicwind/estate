PLAN FOR MONOREPO RECONCILIATION

GOAL: Remove the engine symlink and unify /home/toxic/sovereign (root) and /home/toxic/sovereign/projects/tau into a coherent monorepo, preserving all legitimate customizations.

STEPS:

1. INITIAL STATE AUDIT
   - Confirm engine symlink: engine -> /home/toxic/sovereign/projects/tau
   - List top-level directories in root and projects/tau to understand structure
   - Identify divergent files between root and projects/tau (excluding ignored files)

2. REFERENCE AUDIT
   - Search for all references to "engine" and "projects/tau" in the entire codebase (both directories)
   - Identify files that need updating after symlink removal

3. DIVERGENT FILE RECONCILIATION
   - For each divergent file found in step 1:
     * If file exists only in root: keep as-is
     * If file exists only in projects/tau: determine if it should be moved to root
     * If file exists in both: use weave to merge, preserving customizations from both sides
   - Special handling for known merged files (package.json, mise.toml, MCP client/types) to avoid rework

4. REFERENCE UPDATING
   - Update all references to "engine/" to point to correct location (likely relative paths or root)
   - Update references to "projects/tau/" similarly
   - Focus on configuration files: pitchfork.toml, ports.env, scripts/, tsconfig.json, .gitattributes, .gitignore, AGENTS.md, README.md

5. SYMLINK REMOVAL AND STRUCTURE CONSOLIDATION
   - Remove engine symlink
   - Move any unique files/directories from projects/tau to root (after reconciliation)
   - Ensure packages/coding-agent and other packages are correctly located in root
   - Verify no broken imports or paths remain

6. BUILD AND WORKSPACE VALIDATION
   - Run bun check to validate package.json
   - Validate mise.toml for correct task definitions
   - Ensure pitchfork can find packages/coding-agent/dist/omp
   - Quick smoke test of omp binary if built

7. CLEANUP
   - Remove empty projects/tau directory if fully migrated
   - Remove any temporary files created during reconciliation
   - Ensure .gitignore reflects final structure

RISKS AND EDGE CASES:
- Accidentally overwriting root customizations with tau versions: mitigate by using weave for merging and manual review
- Broken references after symlink removal: mitigate by comprehensive reference audit and updating
- Missing files after move: mitigate by tracking what gets moved and verifying
- Git history preservation: we are not doing destructive git operations, so history should remain

VERIFICATION POINTS:
- After each weave merge: check that file contains expected content from both sides
- After reference updates: grep shows no more references to engine/ or projects/tau/ in source code (except possibly in documentation)
- After symlink removal: engine symlink gone, no broken links
- After build: bun check passes, mise tasks load correctly
- Final: omp binary runs without errors (if built)

ALREADY DONE:
- engine symlink confirmed exists
- Some files already weave-merged: package.json, mise.toml, packages/coding-agent/src/mcp/{client.ts,types.ts}
- No destructive git reset or blind rsync performed yet

NEXT: Execute plan using todo tool to track steps.

Now, I will create a todo list for the meaningful

