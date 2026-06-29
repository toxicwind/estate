  services = {
    # Web server
    caddy = {
      enable = true;
      config = caddyConfig;
    };
    # Databases
    postgres = {
      enable = true;
      listen_addresses = "127.0.0.1,::1";
      port = PORTS.postgres;
      initialDatabases = [{ name = "sovereign"; }];
      initialScript = ''
        CREATE USER sovereign WITH PASSWORD 'sovereign' SUPERUSER;
        GRANT ALL PRIVILEGES ON DATABASE sovereign TO sovereign;
      '';
    };
    redis = {
      enable = true;
      bind = "127.0.0.1";
      port = PORTS.redis;
    };
    mysql = {
      enable = true;
      initialDatabases = [{ name = "sovereign"; }];
    };
    mongodb = {
      enable = true;
      additionalArgs = ["--noauth"];
    };
    clickhouse = {
      enable = true;
      port = PORTS.clickhouse;
      httpPort = PORTS.clickhouse-http;
    };
    # Search
    elasticsearch = {
      enable = true;
      port = PORTS.elasticsearch;
      single_node = true;
    };
    opensearch = {
      enable = true;
    };
    # Message queues
    kafka = {
      enable = true;
      defaultMode = "kraft";
    };
    nats = {
      enable = true;
      port = PORTS.nats;
      host = "127.0.0.1";
      monitoring = {
        enable = true;
        port = PORTS.nats-monitoring;
      };
      jetstream = {
        enable = true;
        maxMemory = "1G";
        maxFileStore = "10G";
      };
    };
    mosquitto = {
      enable = true;
      port = PORTS.mosquitto;
    };
    # Object storage
    #minio = {
    #  enable = true;
    #  accessKey = "minioadmin";
    #  secretKey = "minioadmin";
    #};
    # CDN — REMOVED from services, moved to processes (devenv has no native trafficserver service)
    # trafficserver = { enable = true; };  # DOES NOT EXIST in devenv
    # Profiling — REMOVED (devenv has no native blackfire service)
    # blackfire = { enable = true; socket = "tcp://127.0.0.1:${toString PORTS.blackfire}"; }  };
  # ═══════════════════════════════════════════════════════════════════
  # PROCESSES — All custom processes with readiness probes
  # ═══════════════════════════════════════════════════════════════════
  processes = {
    landing = {
      exec = ''
        cd "${SOV_HOME}/landing" 2>/dev/null || cd "${SOV_HOME}"
        exec ${pkgs.bun}/bin/bun run server.ts --port "${"$"}{LANDING_PAGE}"
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{LANDING_PAGE}/health || exit 1";
          initial_delay_seconds = 2;
          period_seconds = 5;
          timeout_seconds = 3;
          failure_threshold = 10;
        };
      };
    };
    llama-server = {
      exec = llamaServerCmd;
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{LLAMA_SERVER_PORT}/health || exit 1";
          initial_delay_seconds = 15;
          period_seconds = 5;
          timeout_seconds = 5;
          failure_threshold = 30;
        };
        availability = {
          restart = "on_failure";
          backoff_seconds = 5;
          max_restarts = 10;
        };
      };
    };
    hf-downloader = {
      exec = ''
        mkdir -p "${"$"}{SOVEREIGN_HOME}/.state"
        cat > "${"$"}{SOVEREIGN_HOME}/.state/hf_downloader.py" << 'PYEOF'
import http.server, socketserver, subprocess,
os, json, urllib.parse, sys
PORT = int(os.environ["HF_DOWNLOADER"])
SOVEREIGN = os.environ.get("SOVEREIGN_HOME", ".")
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            self.send_response(200); self.end_headers(); self.wfile.write(b"OK"); return
        if parsed.path.startswith("/hf/"):
            repo = parsed.path[4:].strip("/")
            local_dir = os.path.join(SOVEREIGN, "models", "hf", repo.replace("/", "_"))
            os.makedirs(local_dir, exist_ok=True)
            try:
                subprocess.run(
                    ["python3", "-m", "huggingface_hub.cli", "download", repo, "--local-dir", local_dir, "--local-dir-use-symlinks", "False"],
                    check=True, capture_output=True
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "downloaded", "repo": repo, "path": local_dir}).encode())
            except subprocess.CalledProcessError as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e), "stderr": e.stderr.decode()}).encode())
            return
        self.send_response(404); self.end_headers()
    def log_message(self, format, *args): passwith socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("HF Downloader listening on :" + str(PORT))
    httpd.serve_forever()
PYEOF
        exec ${pkgs.python3}/bin/python3 "${"$"}{SOVEREIGN_HOME}/.state/hf_downloader.py"
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{HF_DOWNLOADER}/health || exit 1";
          initial_delay_seconds = 1;
          period_seconds = 3;
          failure_threshold = 5;
        };
      };
    };
    llama-herder = {
      exec = ''
        cd "${SOV_HOME}/tools/llamaherder" 2>/dev/null || cd "${SOV_HOME}"
        exec ${llama-herder-pkg}/bin/llama-herder
      '';
      process-compose = {
        depends_on.llama-server.condition = "process_healthy";
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{LLAMA_HERDER}/health || exit 1";
          initial_delay_seconds = 2;
          period_seconds = 5;
          failure_threshold = 10;
        };
      };
    };
    openfang = {
      exec = ''
        while true; do
          /home/toxic/.openfang/bin/openfang start || true
          sleep 4
        done
      '';
      process-compose = {
        availability.restart = "always";
      };
    };
    sovereign_watchdog = {
      exec = ''
        exec ${sovereign-watchdog-pkg}/bin/sovereign-watchdog
      '';
      process-compose = {
        availability.restart = "on_failure";
        max_restarts = 5;
      };
    };
    telethon_overlord = {
      exec = ''
        exec ${telethon-overlord-pkg}/bin/telethon-overlord
      '';
      process-compose = {
        availability.restart = "on_failure";
        max_restarts = 3;
      };
    };
    prometheus = {
      exec = ''
        ${pkgs.prometheus}/bin/prometheus \\
          --config.file="${SOV_HOME}/prometheus.yml" \\
          --storage.tsdb.path="${PROMETHEUS_DATA}" \\
          --web.listen-address=0.0.0.0:${"$"}{PROMETHEUS_PORT}
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{PROMETHEUS_PORT}/-/healthy || exit 1";
          initial_delay_seconds = 3;
          period_seconds = 5;
        };
      };
    };
    rust-web = {
      exec = ''
        cd "${SOV_HOME}/rust_algo_web"
        exec cargo run --release
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{RUST_WEB_PORT}/health || exit 1";
          initial_delay_seconds = 5;
          period_seconds = 5;
          failure_threshold = 10;
        };
      };
    };
    nfcot-proxy = {
      exec = ''
        cd "${SOV_HOME}"
        exec ${pkgs.python3}/bin/python3 -m modules.nfcot_proxy
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{NFCOT_PORT}/v1/models || exit 1";
          initial_delay_seconds = 3;
          period_seconds = 5;
          failure_threshold = 10;
        };
      };
    };
    node-exporter = {
      exec = ''
        exec ${pkgs.prometheus-node-exporter}/bin/node_exporter \\
          --web.listen-address=:9100 \\
          --path.rootfs=/host
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:9100/metrics >/dev/null || exit 1";
          initial_delay_seconds = 1;
          period_seconds = 5;
        };
      };
    };
    # FIXED: trafficserver moved from services to processes (devenv has no native service)
    trafficserver = {
      exec = ''
        exec ${pkgs.trafficserver}/bin/traffic_server \\
          --port ${toString PORTS.trafficserver}
      '';
      process-compose = {
        availability.restart = "on_failure";
      };
    };
  };
  # ═══════════════════════════════════════════════════════════════════
  # TASKS — Automated workflows
  # ═══════════════════════════════════════════════════════════════════
  tasks = {
    "sovereign:setup".exec = ''
      mkdir -p "${SOV_HOME}/.state" "${SOV_HOME}/models/hf" "${SOV_HOME}/.prometheus" "${SOV_HOME}/logs" "${SOV_HOME}/data"
      cp -f ${configToml} "${SOV_HOME}/config.toml"
      cp -f ${secretspecToml} "${SOV_HOME}/secretspec.toml"
      cp -f ${prometheusYml} "${SOV_HOME}/prometheus.yml"
      echo "✓ Setup complete"
    '';
    "sovereign:clean-logs".exec = ''
      find "${SOV_HOME}/logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true
      find "${SOV_HOME}/ctx_bruteforce_logs" -name "*.log" -mtime +7 -delete 2>/dev/null ||
true
      echo "✓ Old logs cleaned"
    '';
    "sovereign:health".exec = ''
      echo "=== Sovereign Stack Health ==="
      for svc in ${toString PORTS.llama-server} ${toString PORTS.hf-downloader} ${toString PORTS.llama-herder} ${toString PORTS.prometheus} ${toString PORTS.rust-web} ${toString PORTS.nfcot}; do
        if ${pkgs.curl}/bin/curl -sf "http://localhost:$svc/health" >/dev/null 2>&1 || ${pkgs.curl}/bin/curl -sf "http://localhost:$svc/-/healthy" >/dev/null 2>&1 || ${pkgs.curl}/bin/curl -sf "http://localhost:$svc/v1/models" >/dev/null 2>&1; then
          echo "  ✓ :$svc"
        else
          echo "  ✗ :$svc — DOWN"
        fi
      done
    '';
    "devenv:enterShell".after = [ "sovereign:setup" ];
  };
  # ═══════════════════════════════════════════════════════════════════
  # SCRIPTS — All commands use ${pkgs.xxx}/bin/xxx
  # ═══════════════════════════════════════════════════════════════════
  scripts = {
    hf-get.exec = ''
      if [ -z "$1" ]; then
        echo "Usage: hf-get <repo_id> [filename]"
        echo "Example: hf-get unsloth/Qwen3-VL-235B-A22B-Instruct-GGUF"
        exit 1
      fi
      REPO="$1"
      LOCAL_DIR="${"$"}{SOVEREIGN_HOME}/models/hf/${"$"}{REPO//\\//_}"
      mkdir -p "${"$"}{LOCAL_DIR}"
      if [ -n "$2" ]; then
        ${pkgs.python3}/bin/python3 -m huggingface_hub.cli download "$REPO" "$2" --local-dir "${"$"}{LOCAL_DIR}" --local-dir-use-symlinks
False
      else
        ${pkgs.python3}/bin/python3 -m huggingface_hub.cli download "$REPO" --local-dir "${"$"}{LOCAL_DIR}" --local-dir-use-symlinks False      fi
    '';
    llama-test.exec = ''
      ${beellama-cpp}/bin/llama-cli -m "${"$"}{MODEL_PATH}" -p "Hello" -n 16 -ngl ${toString LLAMA_FLAGS.ngl} --flash-attn auto
    '';
    llama-bench.exec = ''
      ${beellama-cpp}/bin/llama-bench -m "${"$"}{MODEL_PATH}" \\
        -fa 1 -d 0,4096,8192,16384,32768 -p 2048 -n 32 -ub 2048 -ngl ${toString LLAMA_FLAGS.ngl} \\
        --cache-type-k ${LLAMA_FLAGS.cache-type-k} --cache-type-v ${LLAMA_FLAGS.cache-type-v}
    '';
    gpu-status.exec = ''
      ${pkgs.nvtopPackages.nvidia}/bin/nvtop --version 2>/dev/null || true
      ${pkgs.cudaPackages.cuda_nvml_dev}/bin/nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv 2>/dev/null || echo "nvidia-smi not available"
    '';
    spec-toggle.exec = ''
      echo "=== Speculative Decoding Status ==="
      echo "Draft model: ${ACTIVE_DRAFT}"
      echo "For DFlash: hf download Anbeeld/Qwen3.6-27B-DFlash-GGUF"
      echo "To disable: remove --draft flags from llama-server process"
    '';
    caddy-reload.exec = ''
      cat > "${"$"}{SOVEREIGN_HOME}/Caddyfile" <<EOF
${caddyConfig}
EOF
      ${pkgs.caddy}/bin/caddy reload --config
"${"$"}{SOVEREIGN_HOME}/Caddyfile"
    '';
    port-map.exec = ''
      echo "╔══════════════════════════════════════════════════════════════╗"
      echo "║           SOVEREIGN PORT REGISTRY                            ║"
      echo "╠══════════════════════════════════════════════════════════════╣"
      echo "║  llama-server  :${toString PORTS.llama-server}    (LLM inference)
 ║"
      echo "║  openfang      :${toString PORTS.openfang}    (OpenFang bridge)              ║"
      echo "║  nfcot         :${toString PORTS.nfcot}    (NFCOT proxy)                     ║"
      echo "║  rust-web      :${toString PORTS.rust-web}    (Rust algo web)                ║"
      echo "║  landing       :${toString PORTS.landing}    (Landing page)                  ║"
      echo "║  hf-downloader :${toString PORTS.hf-downloader}     (HF model download)
    ║"
      echo "║  llama-herder  :${toString PORTS.llama-herder}     (Process herder)
   ║"
      echo "║  prometheus    :${toString PORTS.prometheus}     (Metrics)
║"
      echo "║  caddy-admin   :${toString PORTS.caddy-admin}     (Caddy admin API)
   ║"
      echo "╠══════════════════════════════════════════════════════════════╣"
      echo "║  postgres      :${toString PORTS.postgres}     (PostgreSQL)
║"
      echo "║  redis         :${toString PORTS.redis}     (Redis cache)
║"
      echo "║  mysql         :${toString PORTS.mysql}     (MySQL)                          ║"
      echo "║  mongodb       :${toString PORTS.mongodb}     (MongoDB)
║"
      echo "║  clickhouse    :${toString PORTS.clickhouse}     (ClickHouse)
║"
      echo "║  elasticsearch :${toString PORTS.elasticsearch}     (Elasticsearch)
   ║"
      echo "║  opensearch    :${toString PORTS.opensearch}     (OpenSearch)
║"
      echo "║  kafka         :${toString PORTS.kafka}     (Kafka)                          ║"
      echo "║  nats          :${toString PORTS.nats}     (NATS)                            ║"
      echo "║  mosquitto     :${toString PORTS.mosquitto}     (Mosquitto MQTT)
║"
      echo "║  trafficserver :${toString PORTS.trafficserver}     (Traffic Server CDN)
 ║"
      echo "║  blackfire     :${toString PORTS.blackfire}     (Blackfire profiler)
║"
      echo "╚══════════════════════════════════════════════════════════════╝"
    '';
    health.exec = ''
      devenv tasks run sovereign:health
    '';
    boot.exec = ''
      echo "Starting Sovereign Stack..."
      devenv up -d
      echo "Waiting for services..."
      sleep 10
      devenv tasks run sovereign:health
    '';
    shutdown.exec = ''
      echo "Stopping Sovereign Stack..."
      devenv processes down
    '';
    prefetch-beellama.exec = ''
      echo "beellama-src uses builtins.fetchGit — no hash needed"
      echo "Current ref: main"
    '';
    prefetch-hfhub.exec = ''
      echo "hfhub-src uses builtins.fetchGit — no hash needed"
      echo "Current ref: v1.21.0"
    '';
    prefetch-hfxet.exec = ''
      echo "hfxet-wheel hash: sha256-Xvxs8Vkw2bDO8lwEROAML1XZ4J+FbybtjICf1c0aoEQ="
    '';
  };
  # ═══════════════════════════════════════════════════════════════════
  # ENTER SHELL — Creates all runtime dirs, writes all config files
  # ═══════════════════════════════════════════════════════════════════
  enterShell = ''
    # Run setup task
    devenv tasks run sovereign:setup
    # GPU detection
    if command -v ${pkgs.cudaPackages.cuda_nvml_dev}/bin/nvidia-smi &>/dev/null; then
      echo "  GPU: $(${pkgs.cudaPackages.cuda_nvml_dev}/bin/nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
      echo "  VRAM: $(${pkgs.cudaPackages.cuda_nvml_dev}/bin/nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -1)"
    else
      echo "  WARNING: nvidia-smi not found —
CUDA may not be available"
    fi
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║     SOVEREIGN STACK — MAXIMAL MONOLITH EDITION             ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║  Engine:        BeeLlama.cpp (TurboQuant + Standard Spec)  ║"
    echo "║  Model:         ${ACTIVE_MODEL}"
    echo "║  Draft:        ${ACTIVE_DRAFT}"
    echo "║
                           ║"
    echo "║  Caddy:        http://localhost:80 (routes all services)   ║"
    echo "║  llama-server: http://127.0.0.1:${toString PORTS.llama-server}
      ║"
    echo "║  rust-web:     http://localhost:${toString PORTS.rust-web}
  ║"
    echo "║  openfang:     http://localhost:${toString PORTS.openfang}
  ║"
    echo "║  nfcot:        http://localhost:${toString PORTS.nfcot}                        ║"
    echo "║  landing:      http://localhost:${toString PORTS.landing}
 ║"
    echo "║  hf-downloader:http://localhost:${toString PORTS.hf-downloader}
        ║"
    echo "║  llama-herder:http://localhost:${toString PORTS.llama-herder}
      ║"
    echo "║  prometheus:   http://localhost:${toString PORTS.prometheus}
    ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║  Databases:    PostgreSQL :${toString PORTS.postgres}  Redis :${toString PORTS.redis}              ║"
    echo "║                MySQL :${toString PORTS.mysql}  MongoDB :${toString PORTS.mongodb}              ║"
    echo "║                ClickHouse :${toString PORTS.clickhouse}  Elastic :${toString PORTS.elasticsearch}           ║"
    echo "║  Queues:       Kafka :${toString PORTS.kafka}  NATS :${toString PORTS.nats}  MQTT :${toString PORTS.mosquitto}         ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║  Commands: hf-get, llama-test, llama-bench, gpu-status     ║"
    echo "║            port-map, health, boot, shutdown                ║"
    echo "║            caddy-reload, spec-toggle                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  ⚡  TurboQuant KV: ${LLAMA_FLAGS.cache-type-k}/${LLAMA_FLAGS.cache-type-v}"
    echo "  🚀 Speculative: enabled (draft-n-predict=${toString LLAMA_FLAGS.draft-n-predict})"
    echo "  📦 HF CLI: v1.21.0"
    echo ""
    echo "  Run 'devenv up' to start all services"
    echo "  Run 'boot' for one-command stack startup"
    echo ""
  '';
  # ═══════════════════════════════════════════════════════════════════
  # TESTS
  # ═══════════════════════════════════════════════════════════════════
  enterTest = ''
    echo "=== Sovereign Stack Tests ==="
    ${pkgs.git}/bin/git --version | grep --color=auto "${pkgs.git.version}"
    ${pkgs.curl}/bin/curl --version | head -1
    ${pkgs.python3}/bin/python3 --version
    ${pkgs.bun}/bin/bun --version
    echo "✓ All core tools present"
  '';
  # ═══════════════════════════════════════════════════════════════════
  # GIT HOOKS
  # ═══════════════════════════════════════════════════════════════════
  git-hooks = {
    hooks = {
      nixfmt.enable = true;
      statix.enable = true;
      shellcheck.enable = true;
    };
  };
  # ═══════════════════════════════════════════════════════════════════
  # CONTAINERS — Exportable environments (devenv experimental feature)
  # ═══════════════════════════════════════════════════════════════════
  # NOTE: If your devenv version doesn't support containers, remove this block.
  # Check with: devenv --version (needs >= 1.0)
  containers = {
    shell = {
      name = "sovereign-shell";
      copyToRoot = [ configToml secretspecToml prometheusYml ];
    };
    processes = {
      name = "sovereign-stack";
      copyToRoot = [ configToml secretspecToml prometheusYml ];
    };
  };
}
