**Plan**

**Problem**: `cargo check -p pi-builtins` fails because workspace member `crates/pi-ast` is missing its `Cargo.toml`. The workspace manifest (`/home/toxic/estate/Cargo.toml`) lists `crates/pi-ast` as a member, but the file system lacks `/home/toxic/estate/crates/pi-ast/Cargo.toml`.

**Investigation Findings**:
- The root `Cargo.toml` shows `crates/pi-ast` is an explicit workspace member.
- The error indicates the directory may exist (from a `git reset --hard` leaving an ignored file) but lacks `Cargo.toml`.
- Need to verify the state of `crates/pi-ast` and restore the manifest if missing.

**Execution Steps**:
1. **Check existence and contents of `crates/pi-ast`**:
   - Navigate to sovereign root (`/home/toxic/estate`).
   - List `crates/` directory to confirm `pi-ast` presence.
   - If directory exists, check for `Cargo.toml`; if missing, inspect for any ignored/residual files.
2. **Restore `pi-ast/Cargo.toml` if absent**:
   - If the directory exists but `Cargo.toml` is missing, recover it from the git repository (assuming it was committed previously).
   - If the directory is entirely missing, restore it from git.
   - Use `git checkout HEAD -- crates/pi-ast/Cargo.toml` or similar to restore the file.
3. **Verify workspace integrity**:
   - After restoration, run `cargo metadata --format-version=1` to confirm all workspace members are readable.
   - Ensure no other workspace members are affected.
4. **Retry the original check**:
   - Execute `cargo check -p pi-builtins` from the original tau directory (or any directory in the workspace).
   - Confirm success (exit code 0) and absence of manifest-loading errors.

**Risks & Edge Cases**:
- **Git history unavailable**: If `crates/pi-ast` was never committed, restoration may fail. In that case, we would need to infer a minimal `Cargo.toml` from context (but the workspace likely expects a specific manifest).
- **Corrupted state**: If the directory exists with residual files but no `Cargo.toml`, we must avoid overwriting potential other project files. Restoration should target only the missing manifest.
- **Recursive dependencies**: `pi-builtins` may depend on `pi-ast`; a missing or incorrect `pi-ast` manifest could cause further errors after manifest restoration. We’ll verify by checking the build log.
- **Workspace consistency**: Other members (e.g., `pi-builtins` itself) must remain unaffected; we’ll limit changes to `crates/pi-ast`.

**Already Done**:
- Read the root `Cargo.toml` to confirm workspace members.
- Observed the error message indicating missing `Cargo.toml` for `pi-ast`.

**Verification**:
- After each restoration step, check file existence and content.
- Final verification: `cargo check -p pi-builtins` exits with code 0 and shows no manifest-loading errors.

---

**Todo List** (5–9 meaningful steps for code-changing/verifying actions)

1. `init`: Verify current state of `crates/pi-ast` directory and manifest.
2. `start`: Restore missing `Cargo.toml` for `pi-ast` from git if directory exists but file is absent.
3. `start`: If `crates/pi-ast` directory is missing, restore the entire directory from git.
4. `start`: Validate workspace metadata reads all members correctly.
5. `start`: Run `cargo check -p pi-builtins` from the tau directory.
6. `done`: Confirm successful check (exit code 0, no manifest errors).

*Note: Each step corresponds to a concrete command or verification; exclude bookkeeping.*  
*Begin with step 1 immediately after this todo.*  
