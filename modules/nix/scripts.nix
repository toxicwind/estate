{
  config,
  pkgs,
  lib,
  inputs,
  ...
}:
let
  shared = import ./lib.nix {
    inherit
      config
      pkgs
      lib
      inputs
      ;
  };
  inherit (shared._module.args)
    ACTIVE_DRAFT
    PORTS
    LLAMA_FLAGS
    beellama-cpp
    caddyConfig
    ;
in
{
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
}
