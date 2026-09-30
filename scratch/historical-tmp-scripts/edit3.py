p = "/home/toxic/projects/rig-work/crates/openfang-kernel/src/kernel.rs"
s = open(p).read()

# --- 1. Replace the closure-based helper with a concrete overlay function ---
old_helper = '''/// Seed manifest for an agent name: prefer the disk `agent.toml` over the
/// hardcoded built-in. `default_overlay` is applied to model fields the disk
/// TOML leaves empty or at placeholder values (mirrors the
/// default-model restore overlay used on the boot path).
pub(crate) fn seed_manifest_from_disk(
    agents_dir: &std::path::Path,
    name: &str,
    default_overlay: &openfang_types::config::DefaultModelConfig,
    apply_overlay: impl Fn(&mut AgentManifest, &openfang_types::config::DefaultModelConfig),
) -> Option<AgentManifest> {
    let mut manifest = load_disk_manifest(&agents_dir.join(name).join("agent.toml"))?;
    apply_overlay(&mut manifest, default_overlay);
    Some(manifest)
}'''
new_helper = '''/// Overlay the daemon's default model onto manifest fields the disk TOML
/// leaves empty, so a partial or stale TOML still yields a working route.
/// Fields the TOML sets explicitly always win — the overlay only fills gaps.
pub(crate) fn apply_default_model_overlay(
    manifest: &mut AgentManifest,
    dm: &openfang_types::config::DefaultModelConfig,
) {
    if manifest.name.is_empty() {
        manifest.name = "assistant".to_string();
    }
    if manifest.model.provider.is_empty() {
        manifest.model.provider = dm.provider.clone();
    }
    if manifest.model.model.is_empty() {
        manifest.model.model = dm.model.clone();
    }
    if manifest.model.api_key_env.is_none() && !dm.api_key_env.is_empty() {
        manifest.model.api_key_env = Some(dm.api_key_env.clone());
    }
    if manifest.model.base_url.is_none() {
        manifest.model.base_url = dm.base_url.clone();
    }
}

/// Seed manifest for an agent name: prefer the disk `agent.toml` over the
/// hardcoded built-in, with the default-model overlay filling any gaps.
/// Returns `None` when no usable disk TOML exists (caller falls back to the
/// built-in default).
pub(crate) fn seed_manifest_from_disk(
    agents_dir: &std::path::Path,
    name: &str,
    default_overlay: &openfang_types::config::DefaultModelConfig,
) -> Option<AgentManifest> {
    let mut manifest = load_disk_manifest(&agents_dir.join(name).join("agent.toml"))?;
    apply_default_model_overlay(&mut manifest, default_overlay);
    Some(manifest)
}'''
assert old_helper in s, "helper block not found"
s = s.replace(old_helper, new_helper, 1)

# --- 2. Wire into the no-agents fallback ---
old_seed = """        // If no agents exist (fresh install), spawn a default assistant
        if kernel.registry.list().is_empty() {
            info!("No agents found — spawning default assistant");
            let dm = &kernel.config.default_model;
            let manifest = AgentManifest {"""
assert old_seed in s, "seed anchor not found"
new_seed = """        // If no agents exist (fresh install), spawn a default assistant.
        // Prefer the disk agent.toml when one exists so a wiped or fresh
        // DB comes back with the operator's configured model route instead
        // of the hardcoded built-in default (which previously left the
        // assistant stranded on the wrong provider after a DB reset).
        if kernel.registry.list().is_empty() {
            info!("No agents found — spawning default assistant");
            let dm = &kernel.config.default_model;
            let manifest = seed_manifest_from_disk(
                &kernel.config.home_dir.join("agents"),
                "assistant",
                dm,
            )
            .unwrap_or_else(|| AgentManifest {"""
s = s.replace(old_seed, new_seed, 1)

old_tail = """                ..Default::default()
            };
            match kernel.spawn_agent(manifest) {
                Ok(id) => info!(id = %id, "Default assistant spawned"),"""
assert old_tail in s, "seed tail not found"
new_tail = """                ..Default::default()
            });
            match kernel.spawn_agent(manifest) {
                Ok(id) => info!(id = %id, "Default assistant spawned"),"""
s = s.replace(old_tail, new_tail, 1)
open(p, "w").write(s)
print("seed-from-disk wired")
