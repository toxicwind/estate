{ config, pkgs, lib, inputs, ... }:
let
  shared = import ./lib.nix { inherit config pkgs lib inputs; };
  inherit (shared) pkgs' SOV SOV_HOME MODELS STATE LOGS PROMETHEUS_DATA MODELS_MANIFEST ACTIVE_MODEL ACTIVE_DRAFT PORTS LLAMA_FLAGS beellama-src hfhub-src hfxet-wheel beellama-cpp llama-herder-pkg sovereign-watchdog-pkg telethon-overlord-pkg configToml secretspecToml prometheusYml caddyConfig llamaServerCmd;
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
