p = "/home/toxic/projects/rig-work/crates/openfang-runtime/src/llm_driver.rs"
s = open(p).read()
anchor = """    /// Model not found.
    #[error("Model not found: {0}")]
    ModelNotFound(String),
}
"""
assert anchor in s
addition = anchor + """
/// Classify an HTTP 404 response body from a provider endpoint.
///
/// Returns `ModelNotFound` ONLY when the body actually says the model is
/// unknown/retired. Any other 404 (wrong path composition, HTML error page,
/// empty body, proxy 404) is a request/config error and stays
/// `Api { status: 404 }` — it must NOT trigger cross-provider model
/// fallback, because the URL is broken for every provider and failing over
/// would mask the misconfiguration.
pub fn classify_http_404(body: &str, message: String) -> LlmError {
    let lower = body.to_lowercase();
    let model_missing = lower.contains("not_found")
        || lower.contains("not found")
        || lower.contains("unknown model")
        || lower.contains("no such model")
        || lower.contains("does not exist")
        || lower.contains("is not found");
    if model_missing {
        LlmError::ModelNotFound(message)
    } else {
        LlmError::Api {
            status: 404,
            message,
        }
    }
}
"""
s = s.replace(anchor, addition, 1)
open(p, "w").write(s)
print("classifier added")
