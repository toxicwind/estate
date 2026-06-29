{ config, pkgs, lib, ... }:
let
  shared = import ./lib.nix { inherit pkgs lib; };
in
{
  enterShell = ''
    devenv tasks run sovereign:setup

    if command -v nvidia-smi &>/dev/null; then
      echo "  GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
    fi

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║   SOVEREIGN STACK — FULLY MODULAR (lib + packages + processes + services + scripts + tasks)"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  Run 'devenv up' or 'boot'"
    echo ""
  '';
}
