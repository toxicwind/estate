p = "/home/toxic/projects/rig-work/crates/openfang-runtime/src/drivers/gemini.rs"
s = open(p).read()
old = """                if status == 404 {
                    return Err(LlmError::ModelNotFound(message));
                }"""
assert s.count(old) == 2, "expected 2 sites, found %d" % s.count(old)
new = """                if status == 404 {
                    // Body-aware: only a body that says the model is
                    // unknown becomes ModelNotFound (eligible for
                    // cross-provider fallback). A path/composition 404
                    // stays Api{404} so it fails fast instead of
                    // masking a broken URL behind fallback.
                    return Err(crate::llm_driver::classify_http_404(&body, message));
                }"""
s = s.replace(old, new)
open(p, "w").write(s)
print("gemini 404 sites fixed")
