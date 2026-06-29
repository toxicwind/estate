{ config, pkgs, lib, inputs, ... }:
let
  shared = import ./lib.nix { inherit config pkgs lib inputs; };
  inherit (shared) pkgs' SOV SOV_HOME MODELS STATE LOGS PROMETHEUS_DATA MODELS_MANIFEST ACTIVE_MODEL ACTIVE_DRAFT PORTS LLAMA_FLAGS BEELLAMA_BIN IK_LLAMA_BIN QUANT_BIN beellama-cpp sovereign-watchdog-pkg telethon-overlord-pkg configToml secretspecToml prometheusYml caddyConfig llamaServerCmd;
in
{
  languages = {
      python = {
        enable = true;
        # FIXED: removed hardcoded version = "3.12" — let devenv use nixpkgs default
        # or set via: package = pkgs.python3;
        uv.enable = true;
        venv.enable = true;
      };
      rust = {
        enable = true;
      };
      go = {
        enable = true;
      };
      javascript = {
        enable = true;
        bun = {
          enable = true;
          install.enable = true;
        };
      };
      nix = {
        enable = true;
        lsp.enable = true;
      };
    };
}
