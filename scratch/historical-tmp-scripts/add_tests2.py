p = "/home/toxic/projects/rig-work/crates/openfang-kernel/src/kernel.rs"
s = open(p).read()
idx = s.rstrip().rfind("}")
assert idx > 0
tests = '''
    // --- disk-manifest reconciliation regression tests ---
    use openfang_types::config::DefaultModelConfig;

    fn base_test_manifest() -> AgentManifest {
        AgentManifest {
            persona: Default::default(),
            name: "test-agent".to_string(),
            version: "1.0.0".to_string(),
            description: "test".to_string(),
            author: "test".to_string(),
            module: "builtin:chat".to_string(),
            schedule: ScheduleMode::default(),
            model: ModelConfig {
                provider: "gemini".to_string(),
                model: "gemini-3-flash-preview".to_string(),
                max_tokens: 4096,
                temperature: 0.7,
                system_prompt: "prompt".to_string(),
                api_key_env: Some("GEMINI_API_KEY".to_string()),
                base_url: Some("http://127.0.0.1:25100/v1".to_string()),
            },
            fallback_models: vec![],
            resources: ResourceQuota::default(),
            priority: Priority::default(),
            capabilities: ManifestCapabilities::default(),
            profile: None,
            tools: HashMap::new(),
            skills: vec![],
            mcp_servers: vec![],
            metadata: HashMap::new(),
            tags: vec![],
            routing: None,
            autonomous: None,
            pinned_model: None,
            workspace: None,
            state_dir: None,
            generate_identity_files: true,
            exec_policy: None,
            tool_allowlist: vec![],
            tool_blocklist: vec![],
            cache_context: false,
            max_history_messages: 100,
        }
    }

    fn test_dm() -> DefaultModelConfig {
        DefaultModelConfig {
            provider: "gemini".to_string(),
            model: "gemini-3-flash-preview".to_string(),
            api_key_env: "GEMINI_API_KEY".to_string(),
            base_url: Some("http://127.0.0.1:25100/v1".to_string()),
            subprocess_timeout_secs: None,
        }
    }

    #[test]
    fn test_disk_manifest_differs_catches_base_url_change() {
        let db = base_test_manifest();
        let mut disk = db.clone();
        disk.model.base_url = Some("http://127.0.0.1:25203/v1".to_string());
        assert!(disk_manifest_differs(&disk, &db));
    }

    #[test]
    fn test_disk_manifest_differs_catches_api_key_env_change() {
        let db = base_test_manifest();
        let mut disk = db.clone();
        disk.model.api_key_env = Some("OTHER_API_KEY".to_string());
        assert!(disk_manifest_differs(&disk, &db));
    }

    #[test]
    fn test_disk_manifest_differs_catches_max_tokens_change() {
        let db = base_test_manifest();
        let mut disk = db.clone();
        disk.model.max_tokens = 8192;
        assert!(disk_manifest_differs(&disk, &db));
    }

    #[test]
    fn test_disk_manifest_differs_catches_fallback_models_change() {
        let db = base_test_manifest();
        let mut disk = db.clone();
        disk.fallback_models = vec![FallbackModel {
            provider: "anthropic".to_string(),
            model: "claude-x".to_string(),
            api_key_env: None,
            base_url: None,
        }];
        assert!(disk_manifest_differs(&disk, &db));
    }

    #[test]
    fn test_disk_manifest_differs_ignores_omitted_workspace() {
        // Disk TOML legitimately omits workspace; the DB row carries the
        // kernel-assigned default. That is not a change (#1097).
        let mut db = base_test_manifest();
        db.workspace = Some(std::path::PathBuf::from("/home/toxic/.openfang/agents/test-agent"));
        let disk = base_test_manifest();
        assert!(!disk_manifest_differs(&disk, &db));
    }

    #[test]
    fn test_disk_manifest_differs_detects_explicit_workspace_change() {
        let mut db = base_test_manifest();
        db.workspace = Some(std::path::PathBuf::from("/a"));
        let mut disk = base_test_manifest();
        disk.workspace = Some(std::path::PathBuf::from("/b"));
        assert!(disk_manifest_differs(&disk, &db));
    }

    #[test]
    fn test_merge_preserves_state_dir() {
        let mut db = base_test_manifest();
        db.state_dir = Some(std::path::PathBuf::from("/home/toxic/.openfang/agents/test-agent/state"));
        let disk = base_test_manifest();
        let merged = merge_disk_manifest_preserving_kernel_defaults(disk, &db);
        assert_eq!(merged.state_dir, db.state_dir);
    }

    fn write_agent_toml(dir: &std::path::Path, name: &str, body: &str) {
        let agent_dir = dir.join(name);
        std::fs::create_dir_all(&agent_dir).unwrap();
        std::fs::write(agent_dir.join("agent.toml"), body).unwrap();
    }

    fn temp_agents_dir(tag: &str) -> std::path::PathBuf {
        let dir = std::env::temp_dir().join(format!("of-seed-test-{}-{}", std::process::id(), tag));
        std::fs::create_dir_all(dir.join("agents")).unwrap();
        dir.join("agents")
    }

    #[test]
    fn test_seed_manifest_from_disk_prefers_toml() {
        let agents = temp_agents_dir("prefer");
        write_agent_toml(
            &agents,
            "assistant",
            "name = \\"assistant\\"\\ndescription = \\"disk assistant\\"\\n[model]\\nprovider = \\"llama-swap\\"\\nmodel = \\"nex-agi/nex-n2.5-mini:free\\"\\nbase_url = \\"http://127.0.0.1:25100/v1\\"\\n",
        );
        let dm = test_dm();
        let m = seed_manifest_from_disk(&agents, "assistant", &dm).expect("disk TOML should seed");
        assert_eq!(m.model.provider, "llama-swap");
        assert_eq!(m.model.model, "nex-agi/nex-n2.5-mini:free");
        assert_eq!(m.model.base_url.as_deref(), Some("http://127.0.0.1:25100/v1"));
        std::fs::remove_dir_all(agents.parent().unwrap()).ok();
    }

    #[test]
    fn test_seed_manifest_from_disk_overlay_fills_gaps() {
        // TOML names the agent but leaves the model empty: the daemon
        // default fills the gaps, the disk name wins.
        let agents = temp_agents_dir("gaps");
        write_agent_toml(&agents, "assistant", "name = \\"assistant\\"\\n");
        let dm = test_dm();
        let m = seed_manifest_from_disk(&agents, "assistant", &dm).expect("disk TOML should seed");
        assert_eq!(m.name, "assistant");
        assert_eq!(m.model.provider, "gemini");
        assert_eq!(m.model.model, "gemini-3-flash-preview");
        assert_eq!(m.model.api_key_env.as_deref(), Some("GEMINI_API_KEY"));
        std::fs::remove_dir_all(agents.parent().unwrap()).ok();
    }

    #[test]
    fn test_seed_manifest_from_disk_missing_returns_none() {
        let dm = test_dm();
        assert!(seed_manifest_from_disk(
            std::path::Path::new("/nonexistent-openfang-agents"),
            "assistant",
            &dm
        )
        .is_none());
    }

    #[test]
    fn test_resolve_fallback_base_url_isolates_providers() {
        let dm = test_dm();
        // Different provider, no explicit URL: must use the provider's own
        // URL -- never inherit default_model.base_url.
        let url = resolve_fallback_base_url(None, "anthropic", &dm, false, |_| {
            Some("https://api.anthropic.com".to_string())
        });
        assert_eq!(url.as_deref(), Some("https://api.anthropic.com"));
    }

    #[test]
    fn test_resolve_fallback_base_url_inherits_for_default() {
        let dm = test_dm();
        let url = resolve_fallback_base_url(None, "gemini", &dm, true, |_| None);
        assert_eq!(url.as_deref(), Some("http://127.0.0.1:25100/v1"));
    }

    #[test]
    fn test_resolve_fallback_base_url_explicit_wins() {
        let dm = test_dm();
        let url = resolve_fallback_base_url(
            Some("https://custom.example/v1".to_string()),
            "anthropic",
            &dm,
            false,
            |_| Some("https://api.anthropic.com".to_string()),
        );
        assert_eq!(url.as_deref(), Some("https://custom.example/v1"));
    }

    #[test]
    fn test_resolve_reload_config_path_prefers_boot_path() {
        let mut cfg = KernelConfig::default();
        cfg.config_path = Some(std::path::PathBuf::from(
            "/home/toxic/sovereign/config/openfang-25196.toml",
        ));
        assert_eq!(
            OpenFangKernel::resolve_reload_config_path(&cfg),
            std::path::PathBuf::from("/home/toxic/sovereign/config/openfang-25196.toml")
        );
    }

    #[test]
    fn test_resolve_reload_config_path_falls_back_to_home_dir() {
        let cfg = KernelConfig::default();
        assert_eq!(
            OpenFangKernel::resolve_reload_config_path(&cfg),
            cfg.home_dir.join("config.toml")
        );
    }
'''
s = s[:idx] + tests + s[idx:]
open(p, "w").write(s)
print("kernel tests added")
