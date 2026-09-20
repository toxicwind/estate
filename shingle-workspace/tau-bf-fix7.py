#!/usr/bin/env python3
"""Fix batch 7: set_config_file via git CLI to avoid gix lifetime issues."""
import sys

BASE = "/home/toxic/tau-bf-20260914/tau/engine"
p = f"{BASE}/crates/pi-vcs/src/git/mutate.rs"

with open(p) as f:
    content = f.read()

old = """fn set_config_file(path: &Path, key: &str, value: &str) -> Result<()> {
\tlet mut config: gix::config::File<'_> = if path.exists() {
\t\tgix::config::File::from_path_no_includes(path.to_owned(), gix::config::Source::Local)
\t\t\t.map_err(|e| Error::backend("git config", e))?
\t} else {
\t\tgix::config::File::default()
\t};
\tlet key_ref = &key;
\tconfig
\t\t.set_raw_value(key_ref, value)
\t\t.map_err(|e| Error::backend("git config", e))?;
\tlet mut bytes = Vec::new();
\tconfig.write_to(&mut bytes)?;
\tfs::write(path, bytes)?;
\tOk(())
}"""

new = """fn set_config_file(path: &Path, key: &str, value: &str) -> Result<()> {
\t// gix-config 0.46 ties `set_raw_value`'s key lifetime to the `File`'s
\t// event lifetime, which the borrow checker insists must be `'static`.
\t// Shell out to `git config -f`, which is equivalent and always available
\t// wherever pi-vcs runs.
\tlet output = std::process::Command::new("git")
\t\t.args(["config", "-f", &path.to_string_lossy(), key, value])
\t\t.output()
\t\t.map_err(|e| Error::backend("git config", e))?;
\tif !output.status.success() {
\t\treturn Err(Error::backend(
\t\t\t"git config",
\t\t\tString::from_utf8_lossy(&output.stderr).into_owned(),
\t\t));
\t}
\tOk(())
}"""

n = content.count(old)
if n != 1:
    print(f"FAIL: found {n}x, expected 1x")
    sys.exit(1)
content = content.replace(old, new)
with open(p, "w") as f:
    f.write(content)
print("OK [set_config_file via git CLI]")
print("FIX-7 DONE")
