p = "/home/toxic/projects/rig-work/crates/openfang-types/src/config.rs"
s = open(p).read()

# 1. Add the field at the end of KernelConfig
old_field = """    #[serde(default)]
    pub skills: HashMap<String, HashMap<String, String>>,
}

/// Heartbeat monitor settings exposed in `[heartbeat]` config section."""
assert old_field in s, "struct end not found"
new_field = """    #[serde(default)]
    pub skills: HashMap<String, HashMap<String, String>>,
    /// Path of the config file this kernel booted from, when booted with an
    /// explicit `--config` path. Runtime bookkeeping only: never read from a
    /// config file, never serialized. Recorded so `POST /api/config/reload`
    /// re-reads the SAME file instead of `home_dir/config.toml` (which may
    /// be a different/stale file -- this caused reload to claim `api_listen`
    /// changed 25196 -> 25203 on the pitchfork-supervised instance).
    #[serde(skip)]
    pub config_path: Option<PathBuf>,
}

/// Heartbeat monitor settings exposed in `[heartbeat]` config section."""
s = s.replace(old_field, new_field, 1)

# 2. Default impl: find the end of the manual Default impl and add the field.
# Locate "impl Default for KernelConfig" and its closing "    }\n}" -- add field before final close.
import re
m = re.search(r"impl Default for KernelConfig \{\n    fn default\(\) -> Self \{(.*?)\n    \}\n\}", s, re.S)
assert m, "Default impl not found"
body = m.group(1)
assert "config_path" not in body
# append the field to the struct literal: find last field line ending with comma
new_body = body.rstrip() + ",\n            config_path: None,"
s = s[:m.start(1)] + new_body + s[m.end(1):]
open(p, "w").write(s)
print("config_path field added")
