p = "/home/toxic/projects/rig-work/crates/openfang-kernel/src/kernel.rs"
s = open(p).read()

# 1. boot() records the config path
old_boot = """    /// Boot the kernel with configuration from the given path.
    pub fn boot(config_path: Option<&Path>) -> KernelResult<Self> {
        let config = load_config(config_path);
        Self::boot_with_config(config)
    }"""
assert old_boot in s, "boot not found"
new_boot = """    /// Boot the kernel with configuration from the given path.
    pub fn boot(config_path: Option<&Path>) -> KernelResult<Self> {
        let mut config = load_config(config_path);
        // Record the boot config path so `POST /api/config/reload` re-reads
        // this same file instead of `home_dir/config.toml`.
        config.config_path = config_path.map(|p| p.to_path_buf());
        Self::boot_with_config(config)
    }

    /// Resolve which config file a reload should re-read: the file the
    /// kernel booted with when recorded, else the legacy
    /// `home_dir/config.toml`.
    pub(crate) fn resolve_reload_config_path(config: &KernelConfig) -> std::path::PathBuf {
        config
            .config_path
            .clone()
            .unwrap_or_else(|| config.home_dir.join("config.toml"))
    }"""
s = s.replace(old_boot, new_boot, 1)

# 2. reload_config() uses the recorded path
old_reload = """        // Read and parse config file (using load_config to process $include directives)
        let config_path = self.config.home_dir.join("config.toml");"""
assert old_reload in s, "reload path not found"
new_reload = """        // Read and parse config file (using load_config to process $include directives).
        // Re-read the SAME file the kernel booted with -- not
        // `home_dir/config.toml`, which may be a different/stale file.
        let config_path = Self::resolve_reload_config_path(&self.config);"""
s = s.replace(old_reload, new_reload, 1)
open(p, "w").write(s)
print("boot + reload wired")
