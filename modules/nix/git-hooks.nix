{ config, pkgs, lib, inputs, ... }:
let
  shared = import ./lib.nix { inherit config pkgs lib inputs; };
  inherit (shared) pkgs' SOV SOV_HOME MODELS STATE LOGS PROMETHEUS_DATA MODELS_MANIFEST ACTIVE_MODEL ACTIVE_DRAFT PORTS LLAMA_FLAGS BEELLAMA_BIN IK_LLAMA_BIN QUANT_BIN beellama-cpp sovereign-watchdog-pkg telethon-overlord-pkg configToml secretspecToml prometheusYml caddyConfig llamaServerCmd;
in
{
  git-hooks = {
      hooks = {
        nixfmt.enable = true;
        statix.enable = true;
        shellcheck.enable = true;
      };
    };
}
