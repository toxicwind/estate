# --- llm_driver.rs: append classify_http_404 tests ---
p = "/home/toxic/projects/rig-work/crates/openfang-runtime/src/llm_driver.rs"
s = open(p).read()
# append inside the existing test module: insert before the last closing brace
idx = s.rstrip().rfind("}")
assert idx > 0
tests = '''
    // --- classify_http_404 regression tests ---
    #[test]
    fn test_classify_404_model_not_found_body() {
        // Genuine retired-model 404 from Gemini: eligible for fallback.
        let body = r#"{"error":{"code":404,"message":"models/gemini-2.5-flash is not found for API version v1beta","status":"NOT_FOUND"}}"#;
        let err = classify_http_404(body, "NOT_FOUND: models/gemini-2.5-flash is not found".to_string());
        assert!(matches!(err, LlmError::ModelNotFound(_)));
    }

    #[test]
    fn test_classify_404_path_error_stays_api() {
        // Path-composition 404 (HTML error page): must NOT become ModelNotFound.
        let body = "<html><head><title>404 Not Found</title></head><body>Not Found</body></html>";
        let err = classify_http_404(body, "Google API returned an HTML error page".to_string());
        match err {
            LlmError::Api { status, .. } => assert_eq!(status, 404),
            other => panic!("expected Api{{404}}, got {other:?}"),
        }
    }

    #[test]
    fn test_classify_404_empty_body_stays_api() {
        let err = classify_http_404("", "empty".to_string());
        match err {
            LlmError::Api { status, .. } => assert_eq!(status, 404),
            other => panic!("expected Api{{404}}, got {other:?}"),
        }
    }
'''
s = s[:idx] + tests + s[idx:]
open(p, "w").write(s)
print("llm_driver tests added")

# --- fallback.rs: append 404 fail-fast tests ---
p = "/home/toxic/projects/rig-work/crates/openfang-runtime/src/drivers/fallback.rs"
s = open(p).read()
idx = s.rstrip().rfind("}")
assert idx > 0
tests = '''
    struct NotFound404Driver;

    #[async_trait]
    impl LlmDriver for NotFound404Driver {
        async fn complete(&self, _req: CompletionRequest) -> Result<CompletionResponse, LlmError> {
            Err(LlmError::Api {
                status: 404,
                message: "path not found".to_string(),
            })
        }
    }

    struct ModelGoneDriver;

    #[async_trait]
    impl LlmDriver for ModelGoneDriver {
        async fn complete(&self, _req: CompletionRequest) -> Result<CompletionResponse, LlmError> {
            Err(LlmError::ModelNotFound("model is not found".to_string()))
        }
    }

    #[tokio::test]
    async fn test_fallback_does_not_advance_on_generic_404() {
        // A generic 404 is a broken request URL, not a missing model: the
        // chain must fail fast with the real error instead of masking it
        // behind the next provider.
        let driver = FallbackDriver::new(vec![
            Arc::new(NotFound404Driver) as Arc<dyn LlmDriver>,
            Arc::new(OkDriver) as Arc<dyn LlmDriver>,
        ]);
        let result = driver.complete(test_request()).await;
        match result {
            Err(LlmError::Api { status, .. }) => assert_eq!(status, 404),
            other => panic!("expected fail-fast Api{{404}}, got {other:?}"),
        }
    }

    #[tokio::test]
    async fn test_fallback_advances_on_model_not_found() {
        // A body-confirmed ModelNotFound still advances the chain.
        let driver = FallbackDriver::new(vec![
            Arc::new(ModelGoneDriver) as Arc<dyn LlmDriver>,
            Arc::new(OkDriver) as Arc<dyn LlmDriver>,
        ]);
        let result = driver.complete(test_request()).await;
        assert!(result.is_ok());
        assert_eq!(result.unwrap().text(), "OK");
    }
'''
s = s[:idx] + tests + s[idx:]
open(p, "w").write(s)
print("fallback tests added")
