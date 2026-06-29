{ config, pkgs, lib, inputs, ... }:
let
  shared = import ./lib.nix { inherit config pkgs lib inputs; };
  inherit (shared) pkgs' SOV SOV_HOME MODELS STATE LOGS PROMETHEUS_DATA MODELS_MANIFEST ACTIVE_MODEL ACTIVE_DRAFT PORTS LLAMA_FLAGS beellama-src hfhub-src hfxet-wheel beellama-cpp llama-herder-pkg sovereign-watchdog-pkg telethon-overlord-pkg configToml secretspecToml prometheusYml caddyConfig llamaServerCmd;
in
{
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
    enterTest = ''
      echo "=== Sovereign Stack Tests ==="
      ${pkgs.git}/bin/git --version | grep --color=auto "${pkgs.git.version}"
      ${pkgs.curl}/bin/curl --version | head -1
      ${pkgs.python3}/bin/python3 --version
      ${pkgs.bun}/bin/bun --version
      echo "✓ All core tools present"
    '';
}
