{ config, pkgs, lib, inputs, ... }:
let
  shared = import ./lib.nix { inherit config pkgs lib inputs; };
  inherit (shared) pkgs' SOV SOV_HOME MODELS STATE LOGS PROMETHEUS_DATA MODELS_MANIFEST ACTIVE_MODEL ACTIVE_DRAFT PORTS LLAMA_FLAGS beellama-src hfhub-src hfxet-wheel beellama-cpp llama-herder-pkg sovereign-watchdog-pkg telethon-overlord-pkg configToml secretspecToml prometheusYml caddyConfig llamaServerCmd;
in
{
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
