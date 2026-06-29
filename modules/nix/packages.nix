{ config, pkgs, lib, inputs, ... }:
let
  shared = import ./lib.nix { inherit config pkgs lib inputs; };
  inherit (shared) pkgs' SOV SOV_HOME MODELS STATE LOGS PROMETHEUS_DATA MODELS_MANIFEST ACTIVE_MODEL ACTIVE_DRAFT PORTS LLAMA_FLAGS beellama-src hfhub-src hfxet-wheel beellama-cpp llama-herder-pkg sovereign-watchdog-pkg telethon-overlord-pkg configToml secretspecToml prometheusYml caddyConfig llamaServerCmd;
in
{
  packages = with pkgs; [
    # Core tooling
    git curl jq fd ripgrep eza fzf htop nvtopPackages.nvidia btop tree nixfmt nix-prefetch-git
    git-lfs gh glab
    # Build tools
    gnumake cmake ninja ccache pkg-config
    # CUDA stack
    cudaPackages.cudatoolkit cudaPackages.cuda_cudart cudaPackages.libcublas
    cudaPackages.libcufft cudaPackages.libcurand cudaPackages.cuda_nvtx
    cudaPackages.cuda_nvcc
    # Python stack
    python3 python3Packages.pip python3Packages.uv
    python3Packages.flask python3Packages.requests python3Packages.uvicorn
    python3Packages.fastapi python3Packages.pydantic python3Packages.numpy
    python3Packages.psutil python3Packages.torchWithCuda
    python3Packages.transformers python3Packages.accelerate
    python3Packages.bitsandbytes python3Packages.peft python3Packages.telethon
    python3Packages.jupyterlab python3Packages.ipython
    python3Packages.pytest python3Packages.black python3Packages.ruff
    python3Packages.mypy
    basedpyright                    # FIXED: was python3Packages.basedpyright — this is a top-level pkg
    # JavaScript/TypeScript
    bun nodejs_22 pnpm yarn
    # Rust
    rustc cargo rustfmt clippy rust-analyzer
    # Go
    go gopls
    # LLM inference
    beellama-cpp ollama
    # Monitoring & Observability
    prometheus grafana tempo loki
    prometheus-node-exporter
    # Databases
    postgresql redis memcached
    mongodb                         # FIXED: was mongodb-ce (doesn't exist in nixpkgs)
    clickhouse
    elasticsearch7
    opensearch
    apacheKafka
    mysql84
    # Message queues
    nats-server mosquitto
    # Object storage
    #minio
    # CDN/Cache
    trafficserver
    # Security
    nmap openssl gnupg age
    bitwarden-cli
    # Network tools
    wireshark tcpdump ngrep socat
    # Container tools
    docker-compose podman skopeo
    # Custom
    llama-herder-pkg sovereign-watchdog-pkg telethon-overlord-pkg
  ];

  languages = {
    python.enable = true;
    python.uv.enable = true;
    rust.enable = true;
    go.enable = true;
    nix.enable = true;
    nix.lsp.enable = true;
  };
}
