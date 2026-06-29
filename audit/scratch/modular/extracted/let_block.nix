  pkgs' = import inputs.nixpkgs {
    system = pkgs.system;
    config = {
      cudaSupport = true;
      permittedInsecurePackages = [
        "minio-2025-10-15T17-29-55Z"
      ];
    };
  };
  # ═══════════════════════════════════════════════════════════════════
  # SOVEREIGN ROOT — Centralized paths
  # ═══════════════════════════════════════════════════════════════════
  SOV = config.env.DEVENV_ROOT or ".";
  SOV_HOME = "${SOV}";
  MODELS = "${SOV_HOME}/models";
  STATE = "${SOV_HOME}/.state";
  LOGS = "${SOV_HOME}/logs";
  PROMETHEUS_DATA = "${SOV_HOME}/.prometheus";
  # ═══════════════════════════════════════════════════════════════════
  # MODEL MANIFEST — Single source of truth
  # ═══════════════════════════════════════════════════════════════════
  MODELS_MANIFEST = {
    primary = "${MODELS}/StrangeMerges_19-7B-dare_ties.Q4_K_M.gguf";
    draft = "${MODELS}/Qwen2.5-1.5B-Draft.gguf";
    flash = "${MODELS}/Qwen3.5-9B-DeepSeek-V4-Flash-IQ4_XS.gguf";
    heretic = "${MODELS}/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf";
    gemma = "${MODELS}/gemma-4-12B-it-uncensored-Q4_K_M.gguf";
    grand = "${MODELS}/MN-GRAND-23.5B-Gutenberg-UNCENSORED-V2-Q4_K_M.gguf";
  };
  ACTIVE_MODEL = MODELS_MANIFEST.primary;
  ACTIVE_DRAFT = MODELS_MANIFEST.draft;
  # ═══════════════════════════════════════════════════════════════════
  # PORT REGISTRY — Single source of truth
  # ═══════════════════════════════════════════════════════════════════
  PORTS = {
    llama-server = 25001;
    openfang = 25004;
    nfcot = 25008;
    rust-web = 25010;
    landing = 25000;
    hf-downloader = 8080;
    llama-herder = 8081;
    prometheus = 9090;
    caddy-admin = 2019;
    redis = 6379;
    postgres = 5432;
    #minio = 9000;
    #minio-console = 9001;
    nats = 4222;
    nats-monitoring = 8222;
    mosquitto = 1883;
    clickhouse = 19000;        # FIXED: was 9000, collided with minio
    clickhouse-http = 18123;   # FIXED: was 8123, shifted to avoid conflicts
    elasticsearch = 9200;
    opensearch = 9201;
    kafka = 9092;
    mysql = 3306;
    mongodb = 27017;
    trafficserver = 8082;
    blackfire = 8307;
  };
  # ═══════════════════════════════════════════════════════════════════
  # LLAMA FLAGS — Single source of truth
  # ═══════════════════════════════════════════════════════════════════
  LLAMA_FLAGS = {
    ctx-size = 32768;
    slots = 1;
    batch = 4096;
    ubatch = 1024;
    ngl = 99;
    threads = 4;
    cache-type-k = "q4_0";
    cache-type-v = "q4_0";
    draft-n-ctx = 4096;
    draft-n-predict = 16;
    draft-ngl = 99;
  };
  # ═══════════════════════════════════════════════════════════════════
  # AUTO-FETCHED SOURCES — No lib.fakeSha256
  # ═══════════════════════════════════════════════════════════════════
  beellama-src = builtins.fetchGit {
    url = "https://github.com/Anbeeld/beellama.cpp.git";
    ref = "main";
    shallow = true;
  };
  hfhub-src = builtins.fetchGit {
    url = "https://github.com/huggingface/huggingface_hub.git";
    ref = "v1.21.0";
    shallow = true;
  };
  hfxet-wheel = pkgs.fetchurl {
    url = "https://files.pythonhosted.org/packages/b0/c1/4f770cc7be79287905e13765d4a7e1949dce3483f90867f532ff56e7126b/hf_xet-1.1.1-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl";
    hash = "sha256-Xvxs8Vkw2bDO8lwEROAML1XZ4J+FbybtjICf1c0aoEQ=";
  };
  # ═══════════════════════════════════════════════════════════════════
  # BEE LLAMA
  # ═══════════════════════════════════════════════════════════════════
  beellama-cpp = (pkgs.llama-cpp.override {
    cudaSupport = true;
    rocmSupport = false;
    metalSupport = false;
    blasSupport = true;
  }).overrideAttrs (oldAttrs: rec {
    pname = "beellama-cpp";
    version = "main";
    src = beellama-src;
    cmakeFlags = (oldAttrs.cmakeFlags or []) ++ [
      "-DGGML_NATIVE=ON"
      "-DGGML_CUDA_FA_ALL_QUANTS=ON"
    ];
    preConfigure = ''
      export NIX_ENFORCE_NO_NATIVE=0
      ${oldAttrs.preConfigure or ""}
    '';
    npmDepsHash = "sha256-1iM0LGeI9e+gZEHk46lkBe51DxIhiimfAm9o3Z3m9Ik=";
  });
  # ═══════════════════════════════════════════════════════════════════
  # CUSTOM PACKAGES
  # ═══════════════════════════════════════════════════════════════════
  llama-herder-pkg = pkgs.python3Packages.buildPythonApplication {
    pname = "llama-herder";
    version = "0.1.0";
    src = pkgs.writeTextDir "app.py" "from flask import Flask\napp = Flask(__name__)\n\n@app.route(\"/health\")\ndef health():\n    return \"OK\"\n\ndef main():\n    app.run(host=\"0.0.0.0\", port=8081)\n\nif __name__ == \"__main__\":\n    main()\n";
    format = "pyproject";
    preBuild = ''
      cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "llama-herder"
version = "0.1.0"
dependencies = ["flask", "requests", "pydantic", "uvicorn"]

[project.scripts]
llama-herder = "app:main"
EOF
    '';
    propagatedBuildInputs = with pkgs.python3Packages; [
      flask requests pydantic uvicorn
    ];
    doCheck = false;
  };
  sovereign-watchdog-pkg = pkgs.python3Packages.buildPythonApplication {
    pname = "sovereign-watchdog";
    version = "0.1.0";
    src = if builtins.pathExists "${SOV_HOME}/sovereign"
          then "${SOV_HOME}/sovereign"
          else pkgs.writeTextDir "watchdog.py" "print('watchdog stub')";
    format = "pyproject";
    propagatedBuildInputs = with pkgs.python3Packages; [
      requests psutil
    ];
    doCheck = false;
  };
  telethon-overlord-pkg = pkgs.python3Packages.buildPythonApplication {
    pname = "telethon-overlord";
    version = "0.1.0";
    src = if builtins.pathExists "${SOV_HOME}/agents/telethon_overlord"
          then "${SOV_HOME}/agents/telethon_overlord"
          else pkgs.writeTextDir "overlord.py" "print('overlord stub')";
    format = "pyproject";
    propagatedBuildInputs = with pkgs.python3Packages; [
      telethon requests pydantic
    ];
    doCheck = false;
  };
  # ═══════════════════════════════════════════════════════════════════
  # INLINE FILE GENERATORS — Creates ALL missing files at build time
  # ═══════════════════════════════════════════════════════════════════
  # ── config.toml ──
  configToml = pkgs.writeText "config.toml" ''    api_listen = "127.0.0.1:${toString PORTS.nfcot}"
    auto_approve = true
    human_in_loop_initial = true
    log_level = "info"
    sovereign_mode = "maximal_emergent"
    target_hardware = "ryzen_8700f_64gb_sm86_3090_24gb_nvme"
    [build]
    cuda_arch = "sm_86"
    ik_llama_sm86 = true
    int8_swizzled = true
    use_hmma = true
    [controller]
    fsr_watch = true
    make_on = true
    kv_fork_enabled = true
    [default_model]
    provider = "openai"
    model = "qwen"
    base_url = "http://127.0.0.1:${toString PORTS.llama-server}/v1"
    api_key_env = "OPENAI_API_KEY"
    [memory]
    embedding_provider = "vllm"
    embedding_model = "qwen"
    embedding_api_key_env = "OPENAI_API_KEY"
    [provider_urls]
    vllm = "http://127.0.0.1:${toString PORTS.llama-server}/v1"
    [extensions]
    fsr_max = true
    kv_sovereign_fork = true
    weight_pack_sm86 = true
    [channels.telegram]
    bot_token_env = "TELEGRAM_BOT_TOKEN"
    allowed_users = ["puppertrix"]
    default_agent = "coyote"
    poll_interval_secs = 1
    [channels.discord]
    bot_token_env = "DISCORD_BOT_TOKEN"
    allowed_guilds = ["795261154150449153"]
    default_agent = "coyote"
  '';
  # ── secretspec.toml ──
  secretspecToml = pkgs.writeText "secretspec.toml" ''
    [project]
    name = "sovereign"
    revision = "1.0"
    require_reason = "agents"
    [profiles.default]
    TELEGRAM_BOT_TOKEN = { description = "Telegram Bot API token", required = true }
    TELEGRAM_ALLOWED_USERS = { description = "Allowed Telegram user IDs", required = true }
    DISCORD_CLIENT_ID = { description = "Discord Bot Client ID", required = true }
    DISCORD_CLIENT_SECRET = { description = "Discord Bot Client Secret", required = true }
    DISCORD_BOT_TOKEN = { description = "Discord Bot Token", required = true }
    HUGGINGFACE_HUB_TOKEN = { description = "HF Hub token", required = true }
    HF_TOKEN = { description = "HF token alias", required = true, providers = ["keyring", "env"] }
    OPENFANG_API_KEY = { description = "OpenFang API key", required = false }
    DATABASE_URL = { description = "PostgreSQL connection string", required = false }
    STRIPE_SECRET_KEY = { description = "Stripe API key", required = false }
    SENTRY_DSN = { description = "Sentry DSN", required = false }
    SESSION_KEY = { description = "Session signing key", type = "base64", generate = { bytes = 64 }, required = false }
    API_INTERNAL_TOKEN = { description = "Internal API token", type = "hex", generate = { bytes = 32 }, required = false }
    [profiles.development]
    DATABASE_URL = { description = "Local SQLite", required = false, default = "sqlite:///home/toxic/sovereign/data/dev.db" }
    STRIPE_SECRET_KEY = { description = "Stripe test key", required = false }
    TELEGRAM_BOT_TOKEN = { description = "Telegram Bot API token", required = true, providers = ["keyring", "dotenv", "env"] }
    [profiles.production]
    TELEGRAM_BOT_TOKEN = { description = "Production Telegram token", required = true, providers = ["onepassword", "vault"] }
    DATABASE_URL = { description = "Production PostgreSQL", required = true, providers = ["vault", "awssm"] }
    STRIPE_SECRET_KEY = { description = "Production Stripe key", required = true, providers = ["onepassword", "vault"] }
    SENTRY_DSN = { description = "Production Sentry DSN", required = true }
  '';
  # ── prometheus.yml ──
  prometheusYml = pkgs.writeText "prometheus.yml" ''
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    scrape_configs:
      - job_name: 'prometheus'
        static_configs:
          - targets: ['localhost:${toString PORTS.prometheus}']
      - job_name: 'llama-server'
        static_configs:
          - targets: ['localhost:${toString PORTS.llama-server}']
        metrics_path: /metrics
      - job_name: 'caddy'
        static_configs:
          - targets: ['localhost:2019']
        metrics_path: /metrics
      - job_name: 'node-exporter'
        static_configs:
          - targets: ['localhost:9100']
  '';
  # ── Caddyfile ──
  caddyConfig = ''
    {
      admin 0.0.0.0:${toString PORTS.caddy-admin}
      auto_https off
    }
    :80 {
      handle /health {
        respond "OK" 200
      }
      handle_path /rank* {
        reverse_proxy localhost:${toString PORTS.rust-web}
      }
      handle_path /api/* {
        reverse_proxy localhost:${toString PORTS.rust-web}
      }
      handle_path /llm* {
        reverse_proxy localhost:${toString PORTS.llama-server}
      }
      handle_path /fang* {
        reverse_proxy localhost:${toString PORTS.openfang}
      }
      handle_path /cot* {
        reverse_proxy localhost:${toString PORTS.nfcot}
      }
      handle_path /hf/* {
        reverse_proxy localhost:${toString PORTS.hf-downloader}
      }
      handle_path /herder/* {
        reverse_proxy localhost:${toString PORTS.llama-herder}
      }
      handle_path /landing/* {
        reverse_proxy localhost:${toString PORTS.landing}
      }
      handle {
        reverse_proxy localhost:${toString PORTS.rust-web}
      }
    }
  '';
  # ── LLAMA SERVER COMMAND ──
  llamaServerCmd = ''
    exec ${beellama-cpp}/bin/llama-server \\
      -m "${"$"}{MODEL_PATH}" \\
      --host 0.0.0.0 \\
      --port "${"$"}{LLAMA_SERVER_PORT}" \\
      -c ${toString LLAMA_FLAGS.ctx-size} \\
      --slots ${toString LLAMA_FLAGS.slots} \\      -b ${toString LLAMA_FLAGS.batch} \\
      -ub ${toString LLAMA_FLAGS.ubatch} \\
      --flash-attn auto \\
      -ngl ${toString LLAMA_FLAGS.ngl} \\
      -t ${toString LLAMA_FLAGS.threads} \\
      --no-mmap \\
      --mlock \\
      --embeddings \\
      --pooling cls \\
      --cache-type-k ${LLAMA_FLAGS.cache-type-k} \\
      --cache-type-v ${LLAMA_FLAGS.cache-type-v} \\
      --kv-unified \\
      --no-host \\
      --ctx-checkpoints 32 \\
      --cache-ram 8192 \\
      --draft "${"$"}{DRAFT_MODEL_PATH}" \\
      --draft-n-ctx ${toString LLAMA_FLAGS.draft-n-ctx} \\
      --draft-n-predict ${toString LLAMA_FLAGS.draft-n-predict} \\
      --draft-n-gpu-layers ${toString LLAMA_FLAGS.draft-ngl} \\
      --metrics \\
      --log-format json
  '';
