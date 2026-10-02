#!/usr/bin/env python3
"""Tau bruteforce fix batch 3: pi-iso clone_candidates + clone_tree."""
import sys

P = "/home/toxic/tau-bf-20260914/tau/engine/crates/pi-iso/src/lib.rs"
with open(P) as f:
    src = f.read()

def rep(old, new, count=1, label=""):
    global src
    n = src.count(old)
    if n != count:
        print(f"FAIL [{label}]: found {n}x, expected {count}x")
        print(old[:350])
        sys.exit(1)
    src = src.replace(old, new, count)
    print(f"OK [{label}]")

# 1. import OsStr
rep(
"use std::{fmt, path::Path};",
"use std::{ffi::OsStr, fmt, path::Path};",
label="OsStr import")

# 2. clone_tree on the IsolationBackend trait (after stop)
rep(
"""\tfn stop(&self, merged: &Path) -> IsoResult<()>;

\t/// Capture the changes between `lower` and the current state of""",
"""\tfn stop(&self, merged: &Path) -> IsoResult<()>;

\t/// Clone a directory tree from `src` to `dst`, skipping entries whose
\t/// file name matches one of `exclude_names`.
\t///
\t/// Used to seed fast worktree checkouts. The default implementation is a
\t/// plain recursive copy; backends with copy-on-write support may override
\t/// it for speed. `dst` is created when missing.
\tfn clone_tree(&self, src: &Path, dst: &Path, exclude_names: &[&OsStr]) -> IsoResult<()> {
\t\tclone_tree_recursive(src, dst, exclude_names)
\t}

\t/// Capture the changes between `lower` and the current state of""",
label="clone_tree trait method")

# 3. clone_candidates + clone_tree_recursive after auto_order()
rep(
"""\t#[cfg(not(any(target_os = "macos", target_os = "linux", windows)))]
\t{
\t\tFALLBACK_AUTO_ORDER
\t}
}
""",
"""\t#[cfg(not(any(target_os = "macos", target_os = "linux", windows)))]
\t{
\t\tFALLBACK_AUTO_ORDER
\t}
}

/// Backend candidates for tree cloning, with an optional preferred backend first.
///
/// Yields `preferred` (when given), then [`auto_order`] with duplicates
/// removed, so callers can try each candidate in turn until one succeeds.
pub fn clone_candidates(preferred: Option<BackendKind>) -> impl Iterator<Item = BackendKind> {
\tlet mut seen = std::collections::HashSet::new();
\tpreferred
\t\t.into_iter()
\t\t.chain(auto_order().iter().copied())
\t\t.filter(move |kind| seen.insert(*kind))
}

fn clone_tree_recursive(src: &Path, dst: &Path, exclude_names: &[&OsStr]) -> IsoResult<()> {
\tlet io_err = |err: std::io::Error| IsoError::other(err.to_string());
\tstd::fs::create_dir_all(dst).map_err(io_err)?;
\tfor entry in std::fs::read_dir(src).map_err(io_err)? {
\t\tlet entry = entry.map_err(io_err)?;
\t\tlet name = entry.file_name();
\t\tif exclude_names.iter().any(|ex| *ex == name.as_os_str()) {
\t\t\tcontinue;
\t\t}
\t\tlet from = entry.path();
\t\tlet to = dst.join(&name);
\t\tlet ft = entry.file_type().map_err(io_err)?;
\t\tif ft.is_dir() {
\t\t\tclone_tree_recursive(&from, &to, exclude_names)?;
\t\t} else if ft.is_symlink() {
\t\t\tlet target = std::fs::read_link(&from).map_err(io_err)?;
\t\t\t#[cfg(unix)]
\t\t\tstd::os::unix::fs::symlink(&target, &to).map_err(io_err)?;
\t\t\t#[cfg(windows)]
\t\t\tlet _ = std::os::windows::fs::symlink_file(&target, &to);
\t\t} else {
\t\t\tstd::fs::copy(&from, &to).map_err(io_err)?;
\t\t}
\t}
\tOk(())
}
""",
label="clone_candidates + recursive helper")

with open(P, "w") as f:
    f.write(src)
print("ALL FIX-3 EDITS APPLIED")
