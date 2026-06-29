{ config, pkgs, lib, inputs, ... }:
let
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
  # ═══════════════════════════════════════════════════════════════════
  # PREBUILT LLAMA.CPP BINARIES — already compiled, no Nix build needed
  # ═══════════════════════════════════════════════════════════════════
  BEELLAMA_BIN = "/home/toxic/projects/beellama.cpp/build/bin/llama-server";
  IK_LLAMA_BIN = "/home/toxic/projects/ik_llama.cpp-main/build/bin/llama-server";
  QUANT_BIN    = "/home/toxic/projects/llama-cpp-turboquant/build/bin/llama-server";

  # Wrap the prebuilt beellama binary so Nix packages/PATH work normally
  beellama-cpp = pkgs.symlinkJoin {
    name = "beellama-cpp";
    paths = [
      (pkgs.writeShellScriptBin "llama-server" ''
        exec /home/toxic/projects/beellama.cpp/build/bin/llama-server "$@"
      '')
      (pkgs.writeShellScriptBin "llama-cli" ''
        exec /home/toxic/projects/beellama.cpp/build/bin/llama-cli "$@"
      '')
    ];
  };
  # ═══════════════════════════════════════════════════════════════════
  # CUSTOM PACKAGES
  # ═══════════════════════════════════════════════════════════════════
  # llama-swap is a prebuilt binary — no Nix derivation needed
  # binary lives at: ${SOV_HOME}/tools/llama-swap/llama-swap

  sovereign-watchdog-pkg = pkgs.writers.writePython3Bin "sovereign-watchdog" {
    libraries = with pkgs.python3Packages; [ requests psutil ];
  } ''
    print("watchdog stub")
  '';

  telethon-overlord-pkg = pkgs.writers.writePython3Bin "telethon-overlord" {
    libraries = with pkgs.python3Packages; [ telethon requests pydantic ];
  } ''
    print("overlord stub")
  '';
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
  # ── LLAMA SERVER COMMAND — uses prebuilt beellama binary directly ──
  llamaServerCmd = ''
    exec /home/toxic/projects/beellama.cpp/build/bin/llama-server \\
      -m "${"$"}{MODEL_PATH}" \\
      --host 0.0.0.0 \\
      --port "${"$"}{LLAMA_SERVER_PORT}" \\
      -c ${toString LLAMA_FLAGS.ctx-size} \\
      --slots ${toString LLAMA_FLAGS.slots} \\
      -b ${toString LLAMA_FLAGS.batch} \\
      -ub ${toString LLAMA_FLAGS.ubatch} \\
      --flash-attn \\
      -ngl ${toString LLAMA_FLAGS.ngl} \\
      -t ${toString LLAMA_FLAGS.threads} \\
      --no-mmap \\
      --mlock \\
      --embeddings \\
      --pooling cls \\
      --cache-type-k ${LLAMA_FLAGS.cache-type-k} \\
      --cache-type-v ${LLAMA_FLAGS.cache-type-v} \\
      --draft "${"$"}{DRAFT_MODEL_PATH}" \\
      --draft-n-ctx ${toString LLAMA_FLAGS.draft-n-ctx} \\
      --draft-n-predict ${toString LLAMA_FLAGS.draft-n-predict} \\
      --draft-n-gpu-layers ${toString LLAMA_FLAGS.draft-ngl} \\
      --metrics \\
      --log-format json
  '';

in
{
  inherit pkgs' SOV SOV_HOME MODELS STATE LOGS PROMETHEUS_DATA MODELS_MANIFEST ACTIVE_MODEL ACTIVE_DRAFT PORTS LLAMA_FLAGS BEELLAMA_BIN IK_LLAMA_BIN QUANT_BIN beellama-cpp sovereign-watchdog-pkg telethon-overlord-pkg configToml secretspecToml prometheusYml caddyConfig llamaServerCmd;
}
