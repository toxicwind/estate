{ config, pkgs, lib, ... }:
let
  shared = import ./lib.nix { inherit pkgs lib; };
in
{
  scripts = {
    hf-get.exec = ''
      if [ -z "$1" ]; then
        echo "Usage: hf-get <repo_id> [filename]"
        exit 1
      fi
      REPO="$1"
      LOCAL_DIR="${shared.SOV_HOME}/models/hf/${REPO//\\//_}"
      mkdir -p "$LOCAL_DIR"
      if [ -n "$2" ]; then
        ${pkgs.python3}/bin/python3 -m huggingface_hub.cli download "$REPO" "$2" --local-dir "$LOCAL_DIR" --local-dir-use-symlinks False
      else
        ${pkgs.python3}/bin/python3 -m huggingface_hub.cli download "$REPO" --local-dir "$LOCAL_DIR" --local-dir-use-symlinks False
      fi
    '';

    llama-test.exec = ''
      ${config.packages.beellama-cpp}/bin/llama-cli -m "${shared.ACTIVE_MODEL}" -p "Hello" -n 16 -ngl ${toString shared.LLAMA_FLAGS.ngl} --flash-attn auto
    '';

    port-map.exec = ''
      echo "╔══════════════════════════════════════════════════════════════╗"
      echo "║           SOVEREIGN PORT REGISTRY (MODULAR)                  ║"
      echo "╠══════════════════════════════════════════════════════════════╣"
      echo "║  llama-server  :${toString shared.PORTS.llama-server}    (LLM inference)"
      echo "║  llama-herder  :${toString shared.PORTS.llama-herder}     (Process herder)"
      echo "║  hf-downloader :${toString shared.PORTS.hf-downloader}     (HF model download)"
      echo "║  prometheus    :${toString shared.PORTS.prometheus}     (Metrics)"
      echo "╚══════════════════════════════════════════════════════════════╝"
    '';

    health.exec = ''
      devenv tasks run sovereign:health
    '';

    boot.exec = ''
      echo "Starting Sovereign Stack (modular)..."
      devenv up -d
      sleep 8
      devenv tasks run sovereign:health
    '';

    shutdown.exec = ''
      echo "Stopping Sovereign Stack..."
      devenv processes down
    '';
  };
}
