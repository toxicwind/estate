p = "/home/toxic/projects/rig-work/crates/openfang-kernel/src/kernel.rs"
s = open(p).read()
old_site = """            let config = DriverConfig {
                provider: fb_provider.clone(),
                api_key: fb_api_key,
                base_url: fb
                    .base_url
                    .clone()
                    .or_else(|| dm.base_url.clone())
                    .or_else(|| self.lookup_provider_url(&fb_provider)),
                skip_permissions: true,"""
assert old_site in s, "fallback driver site not found"
new_site = """            // Provider-scoped URL resolution: a fallback on a different
            // provider must never inherit default_model.base_url.
            let fb_base_url = resolve_fallback_base_url(
                fb.base_url.clone(),
                &fb_provider,
                dm,
                resolved_to_default,
                |provider| self.lookup_provider_url(provider),
            );
            let config = DriverConfig {
                provider: fb_provider.clone(),
                api_key: fb_api_key,
                base_url: fb_base_url,
                skip_permissions: true,"""
s = s.replace(old_site, new_site, 1)
open(p, "w").write(s)
print("fallback site fixed")
