p = "/home/toxic/projects/rig-work/crates/openfang-runtime/src/drivers/fallback.rs"
s = open(p).read()

# complete(): fail fast on generic 404
old_complete = """                Err(e @ LlmError::RateLimited { .. }) | Err(e @ LlmError::Overloaded { .. }) => {
                    warn!(
                        driver_index = i,
                        model = %model_name,
                        error = %e,
                        "Driver rate-limited/overloaded, trying next fallback"
                    );
                    last_error = Some(e);
                }
                Err(e) => {
                    warn!(
                        driver_index = i,
                        model = %model_name,
                        error = %e,
                        "Fallback driver failed, trying next"
                    );
                    last_error = Some(e);
                }"""
assert s.count(old_complete) == 1, "complete arm not unique"
new_complete = """                Err(e @ LlmError::RateLimited { .. }) | Err(e @ LlmError::Overloaded { .. }) => {
                    warn!(
                        driver_index = i,
                        model = %model_name,
                        error = %e,
                        "Driver rate-limited/overloaded, trying next fallback"
                    );
                    last_error = Some(e);
                }
                // Generic 404 = the request URL itself is wrong (path
                // miscomposition, stale base_url), not a missing model.
                // Fail fast with the real error: advancing the chain would
                // just mask the misconfiguration behind another provider.
                Err(e @ LlmError::Api { status: 404, .. }) => {
                    warn!(
                        driver_index = i,
                        model = %model_name,
                        error = %e,
                        "Driver returned 404 (not ModelNotFound) — failing fast, not advancing fallback chain"
                    );
                    return Err(e);
                }
                Err(e) => {
                    warn!(
                        driver_index = i,
                        model = %model_name,
                        error = %e,
                        "Fallback driver failed, trying next"
                    );
                    last_error = Some(e);
                }"""
s = s.replace(old_complete, new_complete, 1)

# stream(): fail fast on generic 404
old_stream = """                Err(e @ LlmError::RateLimited { .. }) | Err(e @ LlmError::Overloaded { .. }) => {
                    warn!(
                        driver_index = i,
                        model = %model_name,
                        error = %e,
                        "Driver rate-limited/overloaded (stream), trying next fallback"
                    );
                    last_error = Some(e);
                }
                Err(e) => {
                    warn!(
                        driver_index = i,
                        model = %model_name,
                        error = %e,
                        "Fallback driver (stream) failed, trying next"
                    );
                    last_error = Some(e);
                }"""
assert s.count(old_stream) == 1, "stream arm not unique"
new_stream = """                Err(e @ LlmError::RateLimited { .. }) | Err(e @ LlmError::Overloaded { .. }) => {
                    warn!(
                        driver_index = i,
                        model = %model_name,
                        error = %e,
                        "Driver rate-limited/overloaded (stream), trying next fallback"
                    );
                    last_error = Some(e);
                }
                // Generic 404 = the request URL itself is wrong, not a
                // missing model. Fail fast; do not mask it with fallback.
                Err(e @ LlmError::Api { status: 404, .. }) => {
                    warn!(
                        driver_index = i,
                        model = %model_name,
                        error = %e,
                        "Driver returned 404 (stream, not ModelNotFound) — failing fast, not advancing fallback chain"
                    );
                    return Err(e);
                }
                Err(e) => {
                    warn!(
                        driver_index = i,
                        model = %model_name,
                        error = %e,
                        "Fallback driver (stream) failed, trying next"
                    );
                    last_error = Some(e);
                }"""
s = s.replace(old_stream, new_stream, 1)
open(p, "w").write(s)
print("fallback 404 fail-fast added")
