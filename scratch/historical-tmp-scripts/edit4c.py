p = "/home/toxic/projects/rig-work/crates/openfang-kernel/src/kernel.rs"
s = open(p).read()
anchor = "pub(crate) fn seed_manifest_from_disk("
assert anchor in s
assert "fn resolve_fallback_base_url" not in s
helper = '''/// Resolve the base URL for a manifest-declared fallback model.
///
/// Provider-scoped: the fallback inherits the default model's `base_url`
/// ONLY when it actually resolved to the default provider. A fallback on a
/// different provider uses its own explicit URL, or that provider's
/// configured URL -- never the default provider's URL. (Previously every
/// fallback inherited `default_model.base_url` regardless of provider,
/// sending e.g. an Anthropic fallback at the Gemini endpoint.)
pub(crate) fn resolve_fallback_base_url(
    fb_base_url: Option<String>,
    fb_provider: &str,
    dm: &openfang_types::config::DefaultModelConfig,
    resolved_to_default: bool,
    lookup_provider_url: impl Fn(&str) -> Option<String>,
) -> Option<String> {
    fb_base_url.or_else(|| {
        if resolved_to_default || fb_provider == dm.provider {
            dm.base_url.clone().or_else(|| lookup_provider_url(fb_provider))
        } else {
            lookup_provider_url(fb_provider)
        }
    })
}

'''
s = s.replace(anchor, helper + anchor, 1)
open(p, "w").write(s)
print("helper inserted")
