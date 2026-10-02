p = "/home/toxic/projects/rig-work/crates/openfang-cli/src/main.rs"
s = open(p).read()
old = """        let mut kernel_config = openfang_kernel::config::load_config(config.as_deref());"""
assert old in s, "cmd_start load not found"
new = """        let mut kernel_config = openfang_kernel::config::load_config(config.as_deref());
        // Record the boot config path so /api/config/reload re-reads this
        // same file instead of home_dir/config.toml.
        kernel_config.config_path = config.clone();"""
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("cmd_start wired")
