# grep builtin locate — pi-uu-grep shadowing GNU grep in tau's shell

Date: 2026-10-02. Lane: Cinder (grep-builtin-locate workstream).
Scope: READ-ONLY recon in `/home/toxic/tau`. No edits, no rebuilds.

## One-line mechanism

`grep` (and `find`, `sed`, `diff`, ~60 more) is registered as an **in-process
shell builtin** by `pi_builtins::utility_builtins()`, wired into every tau
shell session in `pi-shell/src/shell.rs`. The builtin is implemented on
ripgrep's libraries and reports itself as `grep (pi-uu-grep)`. Because it is
registered, the shell resolves `grep` to the builtin before ever consulting
`PATH` — GNU `/usr/bin/grep` never gets a look-in.

## Registration — exact locations

- **Implementations:** `/home/toxic/tau/crates/pi-builtins/src/grep.rs`
  (also `find.rs`, `sed.rs`, `diff.rs`, … — full listing in that dir).
  `grep.rs` is built on `grep-regex`/`grep-searcher` (ripgrep libs), recursive
  walks via `pi-walker`; PCRE2 via `grep-pcre2`.
- **Registration table:** `/home/toxic/tau/crates/pi-builtins/src/factory.rs`,
  `pub fn utility_builtins()` (line 192). Each entry is compile-gated, e.g.:
  ```rust
  #[cfg(feature = "util.grep")]
  m.push(("grep", grep::grep_builtin::<SE>()));
  ```
  (line 229–230; same pattern for `util.find`, `util.sed`, `util.diff`, …).
  The doc comment on the function states the intent explicitly: *"kept out of
  `default_builtins` because they shadow real system binaries: the embedding
  shell decides whether to install them"*.
- **Feature set:** `/home/toxic/tau/crates/pi-builtins/Cargo.toml`,
  `[features]`: `default = ["base", "utils"]`, and `utils` includes
  `util.grep`, `util.find`, `util.sed`, `util.diff` (lines 375–424).
- **Shell wiring:** `/home/toxic/tau/crates/pi-shell/src/shell.rs`,
  lines 681–702. After building the brush shell with `default_builtins`,
  it registers the utility set — **unless disabled by env** (see below).
- **Binary linkage:** `/home/toxic/tau/Cargo.toml` line 221 —
  `pi-shell = { path = "crates/pi-shell" }`. The tau binary embeds pi-shell,
  so every tau shell session gets the shadowing.

## Builtin vs system binary — decision logic

Standard brush resolution, confirmed by the code comment at shell.rs:681–684
*("The whole set can be disabled (falling back to system binaries) …")*:

1. If the name is a **registered** builtin → the builtin runs. `PATH` is
   never consulted.
2. If the name is **not registered** (never compiled in, or withheld at
   session init) → normal `PATH` lookup → system binary.

There is no per-invocation fallback: a registered builtin always wins.

## Disable switches (all exist — no source change needed for relief)

Checked in `uutils_env_disabled` (shell.rs:1890–1896): reads the **session
env first, then the process env**. A value is "disabled" when non-empty and
not `0`/`false` (case-insensitive).

| Switch | Effect |
|---|---|
| `PI_DISABLE_UUTILS_BUILTINS=1` | Whole utility set off → **all** fall back to system binaries, including `grep` |
| `PI_DISABLE_UUTILS_DESTRUCTIVE=1` | `rm`/`mv`/`ln` off |
| `PI_DISABLE_RM_BUILTIN=1` / `PI_DISABLE_MV_BUILTIN=1` | Per-command |
| `PI_DISABLE_NOHUP_BUILTIN=1` | `nohup` off |
| `enable -n grep` | **Runtime, in-shell**: disables the `grep` builtin for that session (`pi-builtins/src/enable.rs`, the `enable` builtin; `builtin.disabled = true`) |

Notes:
- There is **no per-command env switch for `grep`** — only the whole-set
  switch covers it. `rm`/`mv` are the only utils with individual switches.
- `exec` and `suspend` builtins are unconditionally disabled at init
  (shell.rs:662–667) — precedent for hard-disabling a builtin in code.

## dist/omp (compiled binary) vs dev-mode

- There is **no `dist/` directory and no installed `omp`/`tau` binary** on
  the box right now (`/home/toxic/.local/bin` does not exist), so no compiled
  artifact could be inspected directly.
- The builtin list is **baked at compile time** via `#[cfg(feature = …)]`
  gates — but every build path in the repo uses default features:
  `helpers/push-build.sh` → `cargo build --release`,
  `scripts/push-build.sh` → `cargo build --profile release-fast`.
  No `--no-default-features` anywhere in the tree.
- **Conclusion:** dev-mode (`cargo run`) and any compiled release bake the
  **identical** builtin list. There is no dev-vs-dist divergence to chase;
  whatever shadows grep in dev shadows it in the binary too.

## Exact permanent fix (for after the rename commits)

Pick one, in increasing order of invasiveness:

1. **Env default (zero source change):** export
   `PI_DISABLE_UUTILS_BUILTINS=1` in tau's default session env. Whole
   shadow set falls back to system binaries. Blunt — loses the
   cross-platform consistency the utils were built for.
2. **Per-command switch for grep (recommended, follows the `rm`/`mv`
   precedent):** in `pi-shell/src/shell.rs`, add
   ```rust
   let grep_disabled = uutils_env_disabled(config, "PI_DISABLE_GREP_BUILTIN");
   ```
   and extend the `match name` block (lines 692–697) with
   `"grep" => grep_disabled,`. Then `PI_DISABLE_GREP_BUILTIN=1` gives GNU
   grep back surgically, everything else stays in-process.
3. **Compile-time removal:** drop `"util.grep"` from the `utils` list in
   `crates/pi-builtins/Cargo.toml` (or build that profile with
   `--no-default-features` + explicit features). Permanent, but then no
   runtime opt-out exists at all.
4. **Fix pi-uu-grep itself:** if "grep is broken" means the builtin has a
   behavioral bug (not just "it isn't GNU"), the bug lives in
   `crates/pi-builtins/src/grep.rs` — that is a separate investigation
   (needs the failing case first).

Recommendation: option 2. It matches the existing `rm`/`mv` pattern,
is a ~5-line diff, keeps the default behavior unchanged, and gives Chris a
one-env-var escape hatch.
