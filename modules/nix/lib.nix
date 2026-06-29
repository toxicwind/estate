# modules/nix/lib.nix
{
  config,
  pkgs,
  lib,
  ...
}:
let
  paths = import ./paths.nix { inherit config; };
  ports = import ./ports.nix; # ← plain attrset, no { }
  models = import ./models.nix { inherit config paths; };
  prebuilts = import ./prebuilts.nix { };
  packages = import ./packages.nix { inherit pkgs prebuilts; };
  generators = import ./generators.nix { inherit pkgs ports lib; };

  LLAMA_FLAGS = {
    ctx-size = 262144;
    slots = 1;
    batch = 4096;
    ubatch = 1024;
    parallel = 3;
    cache-type-k = "q8_0";
    cache-type-v = "q8_0";
    flash-attn = true;
    ngl = 99;
    threads = 8;
    cram = -1;
    alias = "llama";
    webui = "llamacpp";
    jinja = true;
    merge-qkv = true;
    grouped-expert-routing = true;
    reasoning-format = "auto";
    draft-n-ctx = 4096;
    draft-n-predict = 16;
    draft-ngl = 99;
  };

  llama = import ./llama.nix { inherit ports models LLAMA_FLAGS; };

in
{
  _module.args = {
    inherit
      paths
      ports
      models
      llama
      prebuilts
      packages
      generators
      LLAMA_FLAGS
      ;

    PORTS = ports;
    MODELS_MANIFEST = models._module.args.MODELS_MANIFEST or models.MODELS_MANIFEST;
    ACTIVE_MODEL = models._module.args.ACTIVE_MODEL or models.ACTIVE_MODEL;
    ACTIVE_DRAFT = models._module.args.ACTIVE_DRAFT or models.ACTIVE_DRAFT;
    SOV_HOME = paths._module.args.SOV_HOME;
    inherit (prebuilts) BEELLAMA_BIN;
    caddyConfig = generators._module.args.caddyConfig;
    configToml = generators._module.args.configToml;
    prometheusYml = generators._module.args.prometheusYml;
    secretspecToml = generators._module.args.secretspecToml;
    llamaServerCmd = llama._module.args.llamaServerCmd;
    beellama-cpp = packages._module.args.beellama-cpp;
    sovereign-watchdog-pkg = packages._module.args.sovereign-watchdog-pkg;
    telethon-overlord-pkg = packages._module.args.telethon-overlord-pkg;
  };
}
